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
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ._encode import instance_payload
from .config.meta import __LP_SOLVER__
from .errors import InvalidInstanceError, SolverFailedError
from .model import Instance, Objective, OptimizationMode, Rotation, UnloadingConstraint
from .result import PackedBin, Placement, ProgressEvent, Result, RunRecord, Stack, Status

__all__ = ['solve_instance', 'ProgressCallback']

#: Signature of the ``progress_callback`` of both solvers: it receives one
#: :class:`~packingsolver3d.result.ProgressEvent` per improvement and may return
#: ``False`` to stop the solve; any other return value continues it.
ProgressCallback = Callable[[ProgressEvent], Optional[bool]]

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
        stop_when_unimproved_for: Optional[float] = None,
        stop_when_unimproved_after: Optional[float] = None,
        stop_when_unimproved_ratio: Optional[float] = None,
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
    :param stop_when_unimproved_for: Seconds without a new incumbent after
        which the solve is stopped; ``None`` leaves the search to the time
        limit alone.
    :param stop_when_unimproved_after: Seconds from the start before that
        stop may fire; ``None`` means ``0``.  Only meaningful together with
        ``stop_when_unimproved_for``.
    :param stop_when_unimproved_ratio: Makes the patience relative: the solve
        stops once no improvement has arrived for the larger of
        ``stop_when_unimproved_for`` and this many times the time of the last
        improvement, and never before a first solution exists.  Only
        meaningful together with ``stop_when_unimproved_for``.
    :return: The rendered options.
    :raise ValueError: When ``stop_when_unimproved_for`` is not positive, when
        ``stop_when_unimproved_after`` is negative, when
        ``stop_when_unimproved_ratio`` is not positive, or when either of the
        last two is given without ``stop_when_unimproved_for``.

    Example::

        >>> from packingsolver3d._solve import core_options
        >>> core_options()
        {'verbosity_level': 0, 'linear_programming_solver': 'highs'}
        >>> core_options(time_limit=5, memory_limit=1024)['time_limit']
        5.0
        >>> core_options(stop_when_unimproved_for=5, stop_when_unimproved_ratio=2)['stop_when_unimproved_ratio']
        2.0
        >>> core_options(stop_when_unimproved_for=5, stop_when_unimproved_after=10)['stop_when_unimproved_after']
        10.0
        >>> core_options(stop_when_unimproved_for=0)
        Traceback (most recent call last):
            ...
        ValueError: stop_when_unimproved_for must be positive, got 0
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
    if stop_when_unimproved_for is not None:
        if not stop_when_unimproved_for > 0:
            raise ValueError('stop_when_unimproved_for must be positive, got {value!r}'.format(value=stop_when_unimproved_for))
        options['stop_when_unimproved_for'] = float(stop_when_unimproved_for)
    if stop_when_unimproved_after is not None:
        if stop_when_unimproved_for is None:
            raise ValueError('stop_when_unimproved_after needs stop_when_unimproved_for')
        if stop_when_unimproved_after < 0:
            raise ValueError('stop_when_unimproved_after must not be negative, got {value!r}'.format(value=stop_when_unimproved_after))
        options['stop_when_unimproved_after'] = float(stop_when_unimproved_after)
    if stop_when_unimproved_ratio is not None:
        if stop_when_unimproved_for is None:
            raise ValueError('stop_when_unimproved_ratio needs stop_when_unimproved_for')
        if not stop_when_unimproved_ratio > 0:
            raise ValueError('stop_when_unimproved_ratio must be positive, got {value!r}'.format(value=stop_when_unimproved_ratio))
        options['stop_when_unimproved_ratio'] = float(stop_when_unimproved_ratio)
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


def _forward_progress(
        progress_callback: ProgressCallback,
        failure: List[BaseException],
) -> Callable[[Dict[str, Any]], bool]:
    """
    Wrap a user's progress callback for the bridge.

    The bridge calls the returned function with a plain dict on every
    improvement, on whichever thread found it.  The wrapper turns the dict into
    a :class:`~packingsolver3d.result.ProgressEvent`, answers ``True`` to
    continue and ``False`` to stop, keeps an exception raised by the user's
    callback in ``failure`` (the caller re-raises it once the solver has
    returned) and, once a stop was requested for either reason, answers
    ``False`` to any later event without calling the user again -- upstream's
    worker threads may still report an improvement between the request and
    the actual stop.

    :param progress_callback: The user's callback.
    :param failure: List that receives the exception, if the callback raises.
    :return: The function handed to the bridge.

    Example::

        >>> from packingsolver3d._solve import _forward_progress
        >>> seen, failure = [], []
        >>> forward = _forward_progress(lambda event: seen.append(event.number_of_items) is None and event.number_of_items < 5, failure)
        >>> forward({'time': 0.1, 'number_of_items': 3, 'number_of_bins': 1, 'profit': 3.0, 'cost': 1.0, 'label': 'a'})
        True
        >>> forward({'time': 0.2, 'number_of_items': 5, 'number_of_bins': 1, 'profit': 5.0, 'cost': 1.0, 'label': 'b'})
        False
        >>> forward({'time': 0.3, 'number_of_items': 6, 'number_of_bins': 1, 'profit': 6.0, 'cost': 1.0, 'label': 'c'})
        False
        >>> seen, failure
        ([3, 5], [])
    """
    state = {'stopped': False}

    def forward(event: Dict[str, Any]) -> bool:
        if state['stopped']:
            return False
        try:
            keep_going = progress_callback(ProgressEvent(**event)) is not False
        except BaseException as err:  # kept for the caller, re-raised unchanged once the solver has stopped
            failure.append(err)
            keep_going = False
        if not keep_going:
            state['stopped'] = True
        return keep_going

    return forward


def solve_instance(
        problem_type: str,
        instance: Instance,
        options: Dict[str, Any],
        unloading_constraint: Optional[UnloadingConstraint] = None,
        progress_callback: Optional[ProgressCallback] = None,
) -> Result:
    """
    Encode an instance, run the native solver in-process and decode the result.

    The progress callback is wrapped before it reaches the bridge: every event
    dict becomes a :class:`~packingsolver3d.result.ProgressEvent`, an exception
    raised by the callback is kept aside, the solve is stopped, and the
    exception is re-raised here unchanged once the solver has returned -- so a
    ``ValueError`` from user code is never mistaken for one of upstream's.

    :param problem_type: ``'box'`` or ``'boxstacks'``.
    :param instance: The instance to solve, already validated by the caller.
    :param options: Fully rendered options, see :func:`core_options`.  They are
        recorded as-is in the :class:`RunRecord`; the callback is not part of
        them.
    :param unloading_constraint: Override for the instance's own setting.
    :param progress_callback: Called on every improvement of the incumbent;
        return ``False`` to stop the solve.
    :return: The decoded :class:`~packingsolver3d.result.Result`.
    :raise InvalidInstanceError: When upstream's ``InstanceBuilder`` rejects
        the instance; the message is upstream's own.
    :raise SolverFailedError: When upstream threw during the solve; the message
        is upstream's own and the partial :class:`RunRecord` is attached.

    .. note::
        Calls may run concurrently from several threads: each one builds its
        own upstream instance and parameters and receives upstream's log
        through a per-call stream, and the GIL is released while upstream
        runs. Sixteen threads solving at once is part of the test suite.
    """
    payload = instance_payload(instance, unloading_constraint)
    native_options = dict(options)
    failure = []  # type: List[BaseException]
    if progress_callback is not None:
        native_options['progress_callback'] = _forward_progress(progress_callback, failure)
    started = time.perf_counter()
    try:
        raw = _solver(problem_type)(payload, native_options)
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
    if failure:
        raise failure[0]

    output = json.loads(raw['output'])
    bins = _decode_bins(raw['bins'])
    record = RunRecord(
        problem_type=problem_type,
        options=dict(options),
        stdout=raw['stdout'],
        stderr=raw['stderr'],
        wall_time=wall_time,
        stop_reason=raw.get('stop_reason'),
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
