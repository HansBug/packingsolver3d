"""
Overview:
    The ``box`` solver: three-dimensional bin packing without stacking rules.

    This is PackingSolver's general 3D engine and the one that carries every
    3D benchmark upstream reports.  Items are placed independently anywhere in
    a bin, subject only to the bin's own extents and weight capacity.

    Unlike :mod:`packingsolver3d.boxstacks`, the ``box`` solver exposes its
    algorithm portfolio through its parameters, so :func:`solve` can turn
    individual strategies on and off.
"""

from typing import List, Optional

from ._solve import ProgressCallback, core_options, solve_instance
from .errors import UnsupportedFeatureError
from .model import Instance, OptimizationMode
from .result import Result

__all__ = ['solve', 'validate']


def validate(instance: Instance) -> None:
    """
    Refuse instances whose constraints the ``box`` solver would drop in silence.

    The ``box`` model has no stacking rules, defects or unloading constraint,
    so an instance carrying them would be solved as if those constraints did
    not exist -- and the resulting packing would look perfectly valid.

    :param instance: The instance to check.
    :raise UnsupportedFeatureError: When the instance needs
        :mod:`packingsolver3d.boxstacks`.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, box
        >>> instance = Instance(
        ...     bin_types=[BinType(x=10, y=10, z=10)],
        ...     item_types=[ItemType(x=2, y=2, z=2, stackability_id=0)],
        ...     objective=Objective.BIN_PACKING,
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
        'the box solver has no notion of {reasons}; use packingsolver3d.boxstacks.solve '
        'instead, which honours them'.format(reasons=', '.join(reasons))
    )


def solve(
        instance: Instance,
        time_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
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
        progress_callback: Optional[ProgressCallback] = None,
) -> Result:
    """
    Solve a 3D bin packing instance with the ``box`` solver.

    The solver runs in-process; a crash inside upstream would take the
    interpreter with it.  Callers that need isolation run this in a worker
    process of their own.

    :param instance: The instance to solve.
    :param time_limit: Seconds of search.  ``None`` lets the solver run until
        it proves optimality; in the default ``ANYTIME`` mode that means
        indefinitely on any instance that does not pack fully, so pass a
        limit for anything but tiny inputs.
    :param memory_limit: Mebibytes the solver may use.  Checked by upstream at
        its own checkpoints; there is no hard limit.
    :param verbosity_level: Upstream's ``verbosity_level``; the log ends up in
        :attr:`~packingsolver3d.result.RunRecord.stdout`.
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
        name.  Only useful against a custom build; the bundled module has HiGHS
        only.
    :param progress_callback: Called with a
        :class:`~packingsolver3d.result.ProgressEvent` each time the incumbent
        improves, possibly from one of upstream's worker threads.  Return
        ``False`` to stop the solve early (``result.run.stop_reason`` is then
        ``'callback'``); an exception raised inside it stops the solve and is
        re-raised unchanged.
    :return: The :class:`~packingsolver3d.result.Result`.
    :raise UnsupportedFeatureError: When the instance needs stacking support.
    :raise InvalidInstanceError: When the instance is structurally invalid, or
        upstream's ``InstanceBuilder`` rejects it.
    :raise SolverFailedError: When upstream threw during the solve.

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

        Watching a solve: the callback receives one
        :class:`~packingsolver3d.result.ProgressEvent` per improvement, and the
        last one describes the returned packing.

        >>> seen = []
        >>> result = box.solve(instance, time_limit=2.0, progress_callback=seen.append)
        >>> seen[-1].number_of_items == len(result.placements), result.run.stop_reason
        (True, None)

        Stopping early: returning ``False`` ends the solve with the incumbent.

        >>> def good_enough(event):
        ...     return event.number_of_items < 6      # False once everything is packed
        >>> result = box.solve(instance, time_limit=2.0, progress_callback=good_enough)
        >>> len(result.placements), result.run.stop_reason
        (6, 'callback')
    """
    validate(instance)

    options = core_options(
        time_limit=time_limit,
        memory_limit=memory_limit,
        verbosity_level=verbosity_level,
        optimization_mode=optimization_mode,
        linear_programming_solver=linear_programming_solver,
    )
    switches = (
        ('use_tree_search', use_tree_search),
        ('use_tree_search_maximal_spaces', use_tree_search_maximal_spaces),
        ('use_sequential_single_knapsack', use_sequential_single_knapsack),
        ('use_sequential_value_correction', use_sequential_value_correction),
        ('use_column_generation', use_column_generation),
        ('use_dichotomic_search', use_dichotomic_search),
        ('use_dual_feasible_functions', use_dual_feasible_functions),
    )
    for name, value in switches:
        if value is not None:
            options[name] = bool(value)

    return solve_instance('box', instance, options, progress_callback=progress_callback)
