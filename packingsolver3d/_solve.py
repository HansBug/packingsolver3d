"""
Overview:
    Shared solve pipeline behind :mod:`packingsolver3d.box` and
    :mod:`packingsolver3d.boxstacks`.

    Both solvers take the same instance files, the same core options and the
    same output files, so the pipeline -- encode, invoke, decode -- lives here
    once.  The problem-specific modules only contribute their extra command
    line options and their validation rules.
"""

import json
import math
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ._csv import parse_certificate, write_instance
from ._runner import run_solver
from .config.meta import __LP_SOLVER__
from .errors import SolverFailedError
from .model import Instance, Objective, OptimizationMode
from .result import PackedBin, Result, RunRecord, Status

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


def _read_output(path: str) -> Dict[str, Any]:
    """
    Load the solver's JSON output, tolerating the case where it wrote none.

    :param path: Path of the ``--output`` file.
    :return: The ``Output`` object of the document, or an empty mapping.
    """
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, 'r') as f:
            document = json.load(f)
    except ValueError:
        return {}
    output = document.get('Output')
    return output if isinstance(output, dict) else {}


def _number(value) -> Optional[float]:
    """
    Coerce a JSON number, mapping ``null`` and non-finite values to ``None``.

    ``KnapsackBound`` is ``null`` whenever the objective is not a knapsack, and
    the open-dimension bounds can come back as infinities.

    :param value: The raw JSON value.
    :return: A finite float, or ``None``.
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
    :param output: The ``Output`` block of the solver's JSON output.
    :param bins: The parsed certificate.
    :return: ``(status, value, bound)``.
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
        seed: Optional[int] = None,
        verbosity_level: int = 0,
        optimization_mode: Optional[OptimizationMode] = None,
        linear_programming_solver: Optional[str] = None,
) -> List[str]:
    """
    Render the command line options both solvers accept.

    ``--linear-programming-solver`` is always passed.  Upstream's default
    solver name is ``CLP``, the bundled executables are built with
    ``PACKINGSOLVER_USE_CLP=OFF``, and the factory that resolves the name is a
    chain of ``#if <BACKEND>_FOUND`` guards ending in a bare ``throw``.  Left
    to the default, every column generation path dies with "no linear
    programming solver found" -- which small instances hide, because they
    finish in tree search before column generation is ever reached.

    :param seed: Value for ``--seed``.  Upstream currently ignores it; it is
        forwarded so runs stay reproducible if that changes.
    :param verbosity_level: Value for ``--verbosity-level``.
    :param optimization_mode: Value for ``--optimization-mode``.
    :param linear_programming_solver: Override for
        ``--linear-programming-solver``.  Only useful against a custom build.
    :return: The rendered options.
    """
    options = [
        '--verbosity-level', str(int(verbosity_level)),
        '--linear-programming-solver', linear_programming_solver or __LP_SOLVER__,
    ]
    if seed is not None:
        options.extend(['--seed', str(int(seed))])
    if optimization_mode is not None:
        options.extend(['--optimization-mode', optimization_mode.value])
    return options


def solve_instance(
        problem_type: str,
        instance: Instance,
        options: Sequence[str],
        time_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
        grace_seconds: Optional[float] = None,
        keep_files: Optional[str] = None,
) -> Result:
    """
    Encode an instance, run a native solver and decode what came back.

    :param problem_type: ``'box'`` or ``'boxstacks'``.
    :param instance: The instance to solve, already validated by the caller.
    :param options: Fully rendered command line options.
    :param time_limit: Seconds for ``--time-limit``.
    :param memory_limit: Mebibytes for ``--memory-limit`` and for the POSIX
        address space limit.
    :param grace_seconds: Seconds allowed past ``time_limit`` before the child
        is killed.  ``None`` uses
        :data:`packingsolver3d._runner.DEFAULT_GRACE_SECONDS`.
    :param keep_files: Directory to copy the instance and output files into
        before the temporary directory is removed.  Useful when a run needs to
        be reproduced by hand.
    :return: The decoded :class:`~packingsolver3d.result.Result`.
    :raise SolverFailedError: When the solver exited non-zero.
    :raise SolverTimeoutError: When the solver outran its wall clock guard.
    """
    from ._runner import DEFAULT_GRACE_SECONDS

    if grace_seconds is None:
        grace_seconds = DEFAULT_GRACE_SECONDS

    directory = tempfile.mkdtemp(prefix='packingsolver3d-')
    try:
        paths = write_instance(instance, directory)
        paths['output'] = os.path.join(directory, 'output.json')
        paths['certificate'] = os.path.join(directory, 'certificate.csv')

        record, _ = run_solver(
            problem_type,
            paths,
            options=options,
            time_limit=time_limit,
            memory_limit=memory_limit,
            grace_seconds=grace_seconds,
        )

        output = _read_output(paths['output'])
        bins = parse_certificate(paths['certificate'])

        if keep_files is not None:
            _copy_artifacts(paths, keep_files)
    finally:
        shutil.rmtree(directory, ignore_errors=True)

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


def _copy_artifacts(paths: Dict[str, str], destination: str) -> None:
    """
    Copy every produced file into a directory that outlives the solve.

    :param paths: The file paths used for the solve.
    :param destination: Directory to copy into; created when absent.
    """
    if not os.path.isdir(destination):
        os.makedirs(destination)
    for path in paths.values():
        if os.path.isfile(path):
            shutil.copy2(path, os.path.join(destination, os.path.basename(path)))
