"""
Overview:
    Shared solve pipeline behind :mod:`packingsolver3d.box` and
    :mod:`packingsolver3d.boxstacks`.

    Both solvers take the same instance payload, the same core options and
    return the same shape of result, so the pipeline -- encode, call the
    native module, decode -- lives here once.  The problem-specific modules
    only contribute their extra options and their validation rules.
"""

import json
import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ._encode import instance_payload
from .config.meta import __LP_SOLVER__
from .errors import InvalidInstanceError, SolverFailedError
from .model import Instance, Objective, OptimizationMode, Rotation, UnloadingConstraint
from .result import PackedBin, Placement, Result, RunRecord, Stack, Status

__all__ = ['solve_instance']

#: How each objective reads its achieved value and its reported bound.
#:
#: The third element is the optimisation sense: ``-1`` for minimisation, where
#: the bound is a lower bound, and ``+1`` for maximisation, where it is an
#: upper bound.  Objectives absent from this table get no bound, so they can
#: never be reported as proven optimal.
_OBJECTIVE_METRICS = {
    Objective.BIN_PACKING: ('NumberOfBins', 'BinPackingBound', -1),
    Objective.VARIABLE_SIZED_BIN_PACKING: ('BinCost', 'VariableSizedBinPackingBound', -1),
    Objective.KNAPSACK: ('ItemProfit', 'KnapsackBound', 1),
    Objective.OPEN_DIMENSION_X: ('XMax', 'OpenDimensionXBound', -1),
    Objective.OPEN_DIMENSION_Y: ('YMax', 'OpenDimensionYBound', -1),
    Objective.OPEN_DIMENSION_Z: ('ZMax', 'OpenDimensionZBound', -1),
}



def _solver(problem_type: str):
    """
    Resolve the native entry point for a problem type.

    The extension is imported here rather than at package import time, so the
    pure-Python surface (models, errors, documentation builds) stays importable
    on an interpreter that has no compiled module; the first solve reports the
    missing build instead.

    :param problem_type: ``'box'`` or ``'boxstacks'``.
    :return: The native ``<problem_type>_solve`` callable.
    :raise ImportError: When the extension is not built for this interpreter.
    """
    try:
        from . import _core
    except ImportError as err:  # missing build for this interpreter, not a circular import
        raise ImportError(
            'packingsolver3d._core is not built for this interpreter ({err}); install a wheel or run '
            '"make build" (needs CMake >= 3.28 and a C++17 compiler)'.format(err=err)
        )
    return getattr(_core, problem_type + '_solve')


def _number(value) -> Optional[float]:
    """
    Coerce a JSON number, mapping ``null`` and non-finite values to ``None``.

    ``KnapsackBound`` is ``null`` whenever the objective is not a knapsack, and
    the open-dimension bounds can come back as infinities.

    :param value: The raw JSON value.
    :return: A finite float, or ``None``.

    Example::

        >>> from packingsolver3d._solve import _number
        >>> _number(3), _number(2.5), _number(None), _number(float('inf')), _number(True)
        (3.0, 2.5, None, None, None)
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return float(value)


def _classify(
        objective: Objective,
        output: Dict[str, Any],
        bins: Sequence[PackedBin],
) -> Tuple[Status, Optional[float], Optional[float]]:
    """
    Decide the status and pull out the achieved value and the proven bound.

    ``OPTIMAL`` requires a bound the solver reported for *this* objective and
    an achieved value that meets it.  Without such a bound the result stays
    ``FEASIBLE`` however good the packing looks, which keeps a heuristic
    incumbent from being mistaken for a proven optimum.

    :param objective: The objective the instance was solved for.
    :param output: The ``Output`` document of the solver.
    :param bins: The decoded bins.
    :return: ``(status, value, bound)``.

    Example::

        >>> from packingsolver3d import Objective, PackedBin, Status
        >>> from packingsolver3d._solve import _classify
        >>> packed = (PackedBin(bin_id=0, bin_type_id=0, copies=1, x=1, y=1, z=1),)
        >>> output = {'BinPackingBound': 1, 'Solution': {'NumberOfItems': 4, 'NumberOfBins': 1}}
        >>> _classify(Objective.BIN_PACKING, output, packed)
        (<Status.OPTIMAL: 'optimal'>, 1.0, 1.0)
        >>> output['Solution']['NumberOfBins'] = 2
        >>> _classify(Objective.BIN_PACKING, output, packed)
        (<Status.FEASIBLE: 'feasible'>, 2.0, 1.0)
        >>> _classify(Objective.BIN_PACKING, {'Solution': {}}, ())
        (<Status.NO_SOLUTION: 'no-solution'>, None, None)
    """
    statistics = output.get('Solution') or {}

    if output.get('IsProvenInfeasible'):
        return Status.INFEASIBLE, None, None
    if not bins or not statistics.get('NumberOfItems'):
        return Status.NO_SOLUTION, None, None

    if objective == Objective.FEASIBILITY:
        unpacked = statistics.get('NumberOfUnpackedItems')
        status = Status.OPTIMAL if unpacked == 0 else Status.FEASIBLE
        return status, _number(unpacked), None

    metrics = _OBJECTIVE_METRICS.get(objective)
    if metrics is None:
        return Status.FEASIBLE, None, None

    value_key, bound_key, sense = metrics
    value = _number(statistics.get(value_key))
    bound = _number(output.get(bound_key))
    if value is None or bound is None:
        return Status.FEASIBLE, value, bound

    reached = value <= bound if sense < 0 else value >= bound
    return (Status.OPTIMAL if reached else Status.FEASIBLE), value, bound


def core_options(
        time_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
        verbosity_level: int = 0,
        optimization_mode: Optional[OptimizationMode] = None,
        linear_programming_solver: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Render the options both solvers accept.

    ``linear_programming_solver`` is always set.  Upstream's default solver
    name is ``CLP``, the bundled build has ``PACKINGSOLVER_USE_CLP=OFF``, and
    the factory that resolves the name is a chain of ``#if <BACKEND>_FOUND``
    guards ending in a bare ``throw``.  Left to the default, every column
    generation path dies with "no linear programming solver found" -- which
    small instances hide, because they finish in tree search before column
    generation is ever reached.

    :param time_limit: Seconds for upstream's timer.
    :param memory_limit: Mebibytes for upstream's own memory check.
    :param verbosity_level: Upstream's ``verbosity_level``; the log is captured
        into :attr:`~packingsolver3d.result.RunRecord.stdout`.
    :param optimization_mode: Anytime versus fixed-schedule search.
    :param linear_programming_solver: Override for the LP backend name.  Only
        useful against a custom build.
    :return: The rendered options.

    Example::

        >>> from packingsolver3d._solve import core_options
        >>> core_options()
        {'verbosity_level': 0, 'linear_programming_solver': 'highs'}
        >>> core_options(time_limit=5, memory_limit=1024)['time_limit']
        5.0
    """
    options = {
        'verbosity_level': int(verbosity_level),
        'linear_programming_solver': linear_programming_solver or __LP_SOLVER__,
    }  # type: Dict[str, Any]
    if time_limit is not None:
        options['time_limit'] = float(time_limit)
    if memory_limit is not None:
        options['memory_limit'] = int(memory_limit)
    if optimization_mode is not None:
        options['optimization_mode'] = optimization_mode.value
    return options


def _decode_bins(raw_bins: Sequence[Dict[str, Any]]) -> Tuple[PackedBin, ...]:
    """
    Turn the native module's plain bins into result dataclasses.

    :param raw_bins: ``bins`` as returned by the native module.
    :return: The decoded bins, numbered in order.
    """
    bins = []  # type: List[PackedBin]
    for bin_id, raw in enumerate(raw_bins):
        stacks = tuple(
            Stack(stack_id=s['stack_id'], bin_id=bin_id, x=s['x'], y=s['y'], lx=s['lx'], ly=s['ly'], lz=s['lz'])
            for s in raw['stacks']
        )
        placements = tuple(
            Placement(
                item_type_id=p['item_type_id'], bin_id=bin_id,
                x=p['x'], y=p['y'], z=p['z'], lx=p['lx'], ly=p['ly'], lz=p['lz'],
                rotation=Rotation(p['rotation']),
                stack_id=p.get('stack_id'), group_id=p.get('group_id'),
            )
            for p in raw['placements']
        )
        bins.append(PackedBin(
            bin_id=bin_id, bin_type_id=raw['bin_type_id'], copies=raw['copies'],
            x=raw['x'], y=raw['y'], z=raw['z'], placements=placements, stacks=stacks,
        ))
    return tuple(bins)


def solve_instance(
        problem_type: str,
        instance: Instance,
        options: Dict[str, Any],
        unloading_constraint: Optional[UnloadingConstraint] = None,
) -> Result:
    """
    Encode an instance, run the native solver in-process and decode the result.

    :param problem_type: ``'box'`` or ``'boxstacks'``.
    :param instance: The instance to solve, already validated by the caller.
    :param options: Fully rendered options, see :func:`core_options`.
    :param unloading_constraint: Override for the instance's own setting.
    :return: The decoded :class:`~packingsolver3d.result.Result`.
    :raise InvalidInstanceError: When upstream's ``InstanceBuilder`` rejects
        the instance; the message is upstream's own.
    :raise SolverFailedError: When upstream threw during the solve; the message
        is upstream's own and the partial :class:`RunRecord` is attached.
    """
    payload = instance_payload(instance, unloading_constraint)
    started = time.perf_counter()
    try:
        raw = _solver(problem_type)(payload, options)
    except ValueError as err:
        # std::invalid_argument from InstanceBuilder: the input is at fault.
        raise InvalidInstanceError('{problem_type}: {err}'.format(problem_type=problem_type, err=err))
    except RuntimeError as err:
        # std::runtime_error (or any other std::exception) from the solver itself.
        record = RunRecord(problem_type=problem_type, options=dict(options), stdout='', stderr='',
                           wall_time=time.perf_counter() - started)
        raise SolverFailedError(
            '{problem_type} solver failed: {err}'.format(problem_type=problem_type, err=err), run=record,
        )
    wall_time = time.perf_counter() - started

    output = json.loads(raw['output'])
    bins = _decode_bins(raw['bins'])
    record = RunRecord(
        problem_type=problem_type,
        options=dict(options),
        stdout=raw['stdout'],
        stderr=raw['stderr'],
        wall_time=wall_time,
    )

    status, value, bound = _classify(instance.objective, output, bins)
    return Result(
        status=status,
        bins=bins,
        objective=instance.objective,
        value=value,
        bound=bound,
        statistics=output.get('Solution') or {},
        solve_time=_number(output.get('Time')),
        run=record,
    )
