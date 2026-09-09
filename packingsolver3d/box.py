"""
Overview:
    The ``box`` solver: three-dimensional bin packing without stacking rules.

    This is PackingSolver's general 3D engine and the one that carries every
    3D benchmark upstream reports.  Items are placed independently anywhere in
    a bin, subject only to the bin's own extents and weight capacity.

    Unlike :mod:`packingsolver3d.boxstacks`, the ``box`` executable exposes its
    algorithm portfolio on the command line, so :func:`solve` can turn
    individual strategies on and off.
"""

from typing import List, Optional

from ._solve import core_options, solve_instance
from .errors import UnsupportedFeatureError
from .model import Instance, OptimizationMode
from .result import Result

__all__ = ['solve', 'validate']


def validate(instance: Instance) -> None:
    """
    Refuse instances whose constraints the ``box`` solver would drop in silence.

    The upstream CSV reader matches known column labels and ignores everything
    else without a diagnostic, so an instance carrying stacking rules, defects
    or an unloading constraint would be solved as if those constraints did not
    exist -- and the resulting packing would look perfectly valid.

    :param instance: The instance to check.
    :raise UnsupportedFeatureError: When the instance needs
        :mod:`packingsolver3d.boxstacks`.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, box
        >>> instance = Instance(
        ...     bin_types=[BinType(x=10, y=10, z=10)],
        ...     item_types=[ItemType(x=2, y=2, z=2, stackability_id=0)],
        ... )
        >>> box.validate(instance)
        Traceback (most recent call last):
            ...
        packingsolver3d.errors.UnsupportedFeatureError: ...
    """
    if not instance.needs_stacking:
        return

    reasons = []  # type: List[str]
    if instance.defects:
        reasons.append('defects')
    if instance.unloading_constraint is not None:
        reasons.append('an unloading constraint')
    if any(t.is_stackable for t in instance.item_types):
        reasons.append('item stacking fields')
    if any(t.is_stackable for t in instance.bin_types):
        reasons.append('bin stacking fields')

    raise UnsupportedFeatureError(
        'the box solver ignores {reasons}; use packingsolver3d.boxstacks.solve '
        'instead, which honours them'.format(reasons=', '.join(reasons))
    )


def solve(
        instance: Instance,
        time_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
        seed: Optional[int] = None,
        verbosity_level: int = 0,
        optimization_mode: Optional[OptimizationMode] = None,
        use_tree_search: Optional[bool] = None,
        use_tree_search_maximal_spaces: Optional[bool] = None,
        use_sequential_single_knapsack: Optional[bool] = None,
        use_sequential_value_correction: Optional[bool] = None,
        use_column_generation: Optional[bool] = None,
        use_dichotomic_search: Optional[bool] = None,
        use_dual_feasible_functions: Optional[bool] = None,
        linear_programming_solver: Optional[str] = None,
        grace_seconds: Optional[float] = None,
        keep_files: Optional[str] = None,
) -> Result:
    """
    Solve a 3D bin packing instance with the ``box`` solver.

    :param instance: The instance to solve.
    :param time_limit: Seconds of search.  ``None`` lets the solver run to its
        own completion, which on a non-trivial instance means indefinitely --
        pass a limit for anything but tiny inputs.
    :param memory_limit: Mebibytes the solver may use.  Enforced twice: as
        ``--memory-limit``, which the solver checks at its own checkpoints, and
        on POSIX as a hard address space rlimit on the child process.
    :param seed: Forwarded as ``--seed``.  Upstream ignores it today.
    :param verbosity_level: Forwarded as ``--verbosity-level``; the log ends up
        in :attr:`~packingsolver3d.result.RunRecord.stdout`.
    :param optimization_mode: Anytime versus fixed-schedule search, see
        :class:`~packingsolver3d.model.OptimizationMode`.
    :param use_tree_search: Enable or disable the tree search algorithm.
    :param use_tree_search_maximal_spaces: Enable or disable tree search over
        maximal empty spaces.
    :param use_sequential_single_knapsack: Enable or disable the sequential
        single knapsack algorithm.
    :param use_sequential_value_correction: Enable or disable sequential value
        correction.
    :param use_column_generation: Enable or disable column generation.
    :param use_dichotomic_search: Enable or disable dichotomic search.
    :param use_dual_feasible_functions: Force the dual feasible function bound
        even on instances larger than the built-in threshold.
    :param linear_programming_solver: Override the linear programming backend
        name.  Only useful against a custom build; the bundled executables ship
        HiGHS only.
    :param grace_seconds: Seconds allowed past ``time_limit`` before the child
        process is killed.
    :param keep_files: Directory to preserve the generated instance and output
        files in, for reproducing a run by hand.
    :return: The :class:`~packingsolver3d.result.Result`.
    :raise UnsupportedFeatureError: When the instance needs stacking support.
    :raise InvalidInstanceError: When the instance is structurally invalid.
    :raise SolverFailedError: When the solver exited non-zero.
    :raise SolverTimeoutError: When the solver outran its wall clock guard.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, box
        >>> instance = Instance(
        ...     bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
        ...     item_types=[ItemType(x=20, y=30, z=40, copies=6)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> result = box.solve(instance, time_limit=2.0)
        >>> result.number_of_bins
        1
    """
    validate(instance)

    options = core_options(
        seed=seed,
        verbosity_level=verbosity_level,
        optimization_mode=optimization_mode,
        linear_programming_solver=linear_programming_solver,
    )
    switches = (
        ('--use-tree-search', use_tree_search),
        ('--use-tree-search-maximal-spaces', use_tree_search_maximal_spaces),
        ('--use-sequential-single-knapsack', use_sequential_single_knapsack),
        ('--use-sequential-value-correction', use_sequential_value_correction),
        ('--use-column-generation', use_column_generation),
        ('--use-dichotomic-search', use_dichotomic_search),
        ('--use-dual-feasible-functions', use_dual_feasible_functions),
    )
    for name, value in switches:
        if value is not None:
            options.extend([name, '1' if value else '0'])

    return solve_instance(
        'box',
        instance,
        options=options,
        time_limit=time_limit,
        memory_limit=memory_limit,
        grace_seconds=grace_seconds,
        keep_files=keep_files,
    )
