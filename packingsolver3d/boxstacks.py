"""
Overview:
    The ``boxstacks`` solver: 3D bin packing where items form vertical stacks.

    ``boxstacks`` is the truck-loading engine.  It builds piles of items on a
    floor plan and enforces the constraints that come with real pallets --
    which items may sit on which (``stackability_id``), how many may be piled
    (``maximum_stackability``), how much weight one may carry
    (``maximum_weight_above``), how dense a stack may be
    (``maximum_stack_density``), plus floor defects and unloading order.

    It is not a superset of :mod:`packingsolver3d.box` in practice.  On the
    general 3D benchmarks ``box`` solves, ``boxstacks`` frequently returns no
    solution, and it exposes none of ``box``'s algorithm switches.  Use it when
    the problem genuinely has stacking rules; use ``box`` otherwise.

    Watching and bounding a long solve: ``progress_callback`` sees every new
    incumbent and ``stop_when_unimproved_for`` ends the run once the search
    has stalled, with the incumbent as the result.  A 40' HQ container with
    five cargo types and 1036 items does not pack fully, so the anytime search
    would otherwise run to its time limit.  The single-bin algorithm reports
    nothing before its first pass is done, and the stall clock runs from the
    start until then, so ``stop_when_unimproved_after`` covers that first pass.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, Rotation, boxstacks
        >>> cargo = [(530, 290, 370, 300, 8), (530, 230, 290, 300, 6), (430, 210, 270, 400, 4),
        ...          (1200, 800, 1200, 24, 450), (1200, 1000, 1150, 12, 1100)]
        >>> container = Instance(
        ...     bin_types=[BinType(x=12032, y=2352, z=2698, maximum_weight=26460)],
        ...     item_types=[ItemType(x=x, y=y, z=z, copies=copies, weight=weight, stackability_id=index,
        ...                          rotations=(Rotation.XYZ, Rotation.YXZ))
        ...                 for index, (x, y, z, copies, weight) in enumerate(cargo)],
        ...     objective=Objective.KNAPSACK,
        ... )
        >>> improvements = []
        >>> result = boxstacks.solve(container, time_limit=60.0, progress_callback=improvements.append,
        ...                          stop_when_unimproved_for=1.0, stop_when_unimproved_after=3.0)
        >>> result.run.stop_reason, len(improvements) > 0, improvements[-1].number_of_items == len(result.placements)
        ('unimproved', True, True)
"""

from typing import Dict, FrozenSet, Optional, Tuple

from ._solve import ProgressCallback, core_options, solve_instance
from .errors import StackSemanticsError, UnsupportedFeatureError
from .model import Instance, ItemType, OptimizationMode, Rotation, UnloadingConstraint
from .result import Result

__all__ = ['solve', 'validate']


#: Which of an item's own extents become its x and y after each rotation,
#: transcribed from ``ItemType::x(Rotation)`` / ``y(Rotation)`` in upstream's
#: ``include/packingsolver/boxstacks/instance.hpp``.
_FOOTPRINT_AXES = {
    Rotation.XYZ: ('x', 'y'),
    Rotation.YXZ: ('y', 'x'),
    Rotation.ZYX: ('z', 'y'),
    Rotation.YZX: ('y', 'z'),
    Rotation.XZY: ('x', 'z'),
    Rotation.ZXY: ('z', 'x'),
}


def _footprints(item_type: ItemType) -> FrozenSet[Tuple[int, int]]:
    """
    Every ``(x, y)`` footprint an item type can present, over its rotations.

    :param item_type: The item type.
    :return: The reachable footprints; just ``(x, y)`` for an oriented item.
    """
    rotations = item_type.rotations or (Rotation.XYZ,)
    return frozenset(
        (getattr(item_type, _FOOTPRINT_AXES[r][0]), getattr(item_type, _FOOTPRINT_AXES[r][1]))
        for r in rotations
    )


def validate(instance: Instance) -> None:
    """
    Refuse stacks upstream would assemble and then reject.

    ``tree_search.cpp`` buckets item types by ``(group_id, stackability_id)``
    and never compares footprints, so two item types sharing a bucket with no
    footprint in common end up in one stack and ``SolutionBuilder::add_item``
    throws.  Both ids default to ``0`` upstream, which makes this the first
    thing a plain instance with two item shapes runs into.

    Footprints are compared over the allowed rotations: a ``20 x 30`` item and
    a ``30 x 20`` item that may turn (:attr:`~packingsolver3d.model.Rotation.YXZ`)
    do share a footprint and pass.

    ``boxstacks`` also keeps every item's z axis vertical: the sequential
    one-dimensional / rectangle phase only ever considers ``XYZ`` and ``YXZ``
    (``sequential_onedimensional_rectangle.cpp``), and an item type that allows
    neither ends in ``SolutionBuilder::add_item`` throwing "forbidden
    rotation" mid-solve.  Such item types are refused up front.

    :param instance: The instance to check.
    :raise StackSemanticsError: When two item types share a stackability
        bucket but no footprint.
    :raise UnsupportedFeatureError: When an item type allows only rotations
        that tip it on its side.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks
        >>> instance = Instance(
        ...     bin_types=[BinType(x=10, y=10, z=10)],
        ...     item_types=[ItemType(x=2, y=2, z=2), ItemType(x=3, y=3, z=3)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> boxstacks.validate(instance)
        Traceback (most recent call last):
            ...
        packingsolver3d.errors.StackSemanticsError: ...
    """
    upright = {Rotation.XYZ, Rotation.YXZ}
    for index, item_type in enumerate(instance.item_types):
        if item_type.rotations is not None and not upright & set(item_type.rotations):
            raise UnsupportedFeatureError(
                'item type #{index} allows only {rotations}; the boxstacks solver keeps items '
                'upright and places them in XYZ or YXZ only'.format(
                    index=index, rotations=sorted(r.value for r in item_type.rotations),
                )
            )

    buckets = {}  # type: Dict[Tuple[int, int], Tuple[int, FrozenSet[Tuple[int, int]]]]
    for index, item_type in enumerate(instance.item_types):
        bucket = (item_type.group_id or 0, item_type.stackability_id or 0)
        footprints = _footprints(item_type)
        first_index, first_footprints = buckets.setdefault(bucket, (index, footprints))
        if not first_footprints & footprints:
            raise StackSemanticsError(
                'item types #{first} and #{second} share group_id {group} and '
                'stackability_id {stackability} but have no footprint in common '
                '({a} vs {b}); upstream stacks them together and then rejects the '
                'stack, so give them distinct stackability_id values'.format(
                    first=first_index, second=index, group=bucket[0], stackability=bucket[1],
                    a=sorted(first_footprints), b=sorted(footprints),
                )
            )

def solve(
        instance: Instance,
        time_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
        verbosity_level: int = 0,
        optimization_mode: Optional[OptimizationMode] = None,
        unloading_constraint: Optional[UnloadingConstraint] = None,
        linear_programming_solver: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
        stop_when_unimproved_for: Optional[float] = None,
        stop_when_unimproved_after: Optional[float] = None,
) -> Result:
    """
    Solve a stacked 3D bin packing instance with the ``boxstacks`` solver.

    The solver runs in-process; a crash inside upstream would take the
    interpreter with it.  Callers that need isolation run this in a worker
    process of their own.

    :param instance: The instance to solve.
    :param time_limit: Seconds of search.  ``None`` lets the solver run until
        it proves optimality; in the default ``ANYTIME`` mode that means
        indefinitely on any instance that does not pack fully (upstream
        ``2a598481`` made the single-bin algorithm anytime too), so pass a
        limit for anything but tiny inputs.
    :param memory_limit: Mebibytes the solver may use, checked by upstream at
        its own checkpoints; there is no hard limit.
    :param verbosity_level: Upstream's ``verbosity_level``; the log ends up in
        :attr:`~packingsolver3d.result.RunRecord.stdout`.
    :param optimization_mode: Anytime versus fixed-schedule search.
    :param unloading_constraint: Overrides
        :attr:`packingsolver3d.model.Instance.unloading_constraint` for this
        call.

    .. note::
        At the pinned upstream commit the ``boxstacks`` solver accepts
        :attr:`~packingsolver3d.model.Instance.defects` but places stacks over
        them all the same; this was observed with corner, interior and
        full-width defects.  The field is forwarded faithfully and nothing is
        claimed about the placements avoiding it until upstream changes.

    :param linear_programming_solver: Override the linear programming backend
        name.  The bundled module has HiGHS only.
    :param progress_callback: Called with a
        :class:`~packingsolver3d.result.ProgressEvent` each time the incumbent
        improves (one per queue-size level of the single-bin algorithm, one per
        iteration of the multi-bin one).  Return ``False`` to stop the solve
        early (``result.run.stop_reason`` is then ``'callback'``); an exception
        raised inside it stops the solve and is re-raised unchanged.
    :param stop_when_unimproved_for: Stop once this many seconds have passed
        without a new incumbent (``result.run.stop_reason`` is then
        ``'unimproved'``).  This is upstream's own stop signal, the same one a
        time limit raises, so the incumbent is returned intact.  Until a first
        solution exists the clock runs from the start of the solve, and the
        single-bin algorithm reports nothing before its first pass is done, so
        cover that with ``stop_when_unimproved_after``.
    :param stop_when_unimproved_after: Do not apply that stop before this many
        seconds have elapsed since the start.  ``None`` means ``0``.
    :return: The :class:`~packingsolver3d.result.Result`.  Bins carry
        :attr:`~packingsolver3d.result.PackedBin.stacks` here, which ``box``
        results never do.
    :raise StackSemanticsError: When item types sharing a stackability bucket
        differ in footprint, see :func:`validate`.
    :raise InvalidInstanceError: When the instance is structurally invalid, or
        upstream's ``InstanceBuilder`` rejects it.
    :raise SolverFailedError: When upstream threw during the solve.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, boxstacks
        >>> instance = Instance(
        ...     bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5,
        ...                        maximum_weight=1000)],
        ...     item_types=[ItemType(x=20, y=30, z=40, copies=6, weight=5,
        ...                          stackability_id=0, maximum_stackability=3,
        ...                          maximum_weight_above=100)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> result = boxstacks.solve(instance, time_limit=2.0)
        >>> result.number_of_bins
        1
        >>> len(result.bins[0].stacks) > 0
        True

        Watching a solve, and stopping it: the callback receives one
        :class:`~packingsolver3d.result.ProgressEvent` per improvement;
        returning ``False`` ends the solve with the incumbent.

        >>> seen = []
        >>> result = boxstacks.solve(instance, time_limit=2.0, progress_callback=seen.append)
        >>> seen[-1].number_of_items == len(result.placements), result.run.stop_reason
        (True, None)
        >>> result = boxstacks.solve(instance, time_limit=2.0,
        ...                          progress_callback=lambda event: event.number_of_items < 6)
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
        stop_when_unimproved_for=stop_when_unimproved_for,
        stop_when_unimproved_after=stop_when_unimproved_after,
    )
    return solve_instance('boxstacks', instance, options, unloading_constraint=unloading_constraint,
                          progress_callback=progress_callback)
