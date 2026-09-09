"""
Overview:
    Instance model of :mod:`packingsolver3d`.

    These are plain value objects.  Nothing here owns a native resource, holds
    a pointer or needs to be closed, which is deliberate: the native solvers
    keep their solutions as references into their own ``Instance`` object, so
    mirroring that object graph in Python would drag C++ lifetimes into the
    Python layer.  Instead an :class:`Instance` is encoded to CSV, handed to a
    short-lived process and forgotten.

    ``ItemType`` and ``BinType`` carry the union of the ``box`` and
    ``boxstacks`` fields.  The stacking fields
    (:attr:`ItemType.stackability_id` and friends) mean nothing to ``box``, and
    :func:`packingsolver3d.box.solve` rejects an instance that sets them
    instead of dropping them quietly.
"""

from enum import Enum
from typing import Optional, Sequence, Tuple

try:  # pragma: no cover
    from dataclasses import dataclass, field
except ImportError:  # pragma: no cover
    raise

__all__ = [
    'Objective',
    'Rotation',
    'UnloadingConstraint',
    'OptimizationMode',
    'ItemType',
    'BinType',
    'Defect',
    'Instance',
]


class Objective(Enum):
    """
    Objective of a packing problem, as understood by ``--objective``.

    The values are the exact tokens PackingSolver's ``operator>>`` accepts, so
    ``Objective.BIN_PACKING.value`` can go straight onto a command line.
    """

    DEFAULT = 'default'
    FEASIBILITY = 'feasibility'
    BIN_PACKING = 'bin-packing'
    BIN_PACKING_WITH_LEFTOVERS = 'bin-packing-with-leftovers'
    OPEN_DIMENSION_X = 'open-dimension-x'
    OPEN_DIMENSION_Y = 'open-dimension-y'
    OPEN_DIMENSION_Z = 'open-dimension-z'
    OPEN_DIMENSION_XY = 'open-dimension-xy'
    KNAPSACK = 'knapsack'
    VARIABLE_SIZED_BIN_PACKING = 'variable-sized-bin-packing'
    BIN_PACKING_CUTTING_COST = 'bin-packing-cutting-cost'


class Rotation(Enum):
    """
    One of the six axis permutations an item may be placed under.

    The name reads as the axis order after rotation: ``YXZ`` means the item's
    own ``x`` extent runs along the bin's ``y`` axis.  The values double as the
    suffix of the ``ROTATION_*`` instance columns and as the token found in the
    ``ROTATION`` column of a certificate.
    """

    XYZ = 'XYZ'
    YXZ = 'YXZ'
    ZYX = 'ZYX'
    YZX = 'YZX'
    XZY = 'XZY'
    ZXY = 'ZXY'


#: Every rotation, for the common "this item may be turned any way" case.
ALL_ROTATIONS = (
    Rotation.XYZ,
    Rotation.YXZ,
    Rotation.ZYX,
    Rotation.YZX,
    Rotation.XZY,
    Rotation.ZXY,
)


class UnloadingConstraint(Enum):
    """
    Order in which stacks must remain reachable while unloading a bin.

    Only ``boxstacks`` reads this; it is the truck-loading constraint from the
    upstream paper.  ``box`` has no notion of an unloading order.
    """

    NONE = 'none'
    ONLY_X_MOVEMENTS = 'only-x-movements'
    ONLY_Y_MOVEMENTS = 'only-y-movements'
    INCREASING_X = 'increasing-x'
    INCREASING_Y = 'increasing-y'


class OptimizationMode(Enum):
    """
    Whether the solver should improve continuously or run a fixed schedule.

    ``ANYTIME`` keeps refining until the time limit and is the upstream
    default.  The ``NOT_ANYTIME*`` modes run a fixed amount of work and stop,
    which makes runs reproducible at the price of ignoring spare time.
    """

    ANYTIME = 'anytime'
    NOT_ANYTIME = 'not-anytime'
    NOT_ANYTIME_DETERMINISTIC = 'not-anytime-deterministic'
    NOT_ANYTIME_SEQUENTIAL = 'not-anytime-sequential'


@dataclass(frozen=True)
class ItemType:
    """
    One kind of box to pack, together with how many of it exist.

    :param x: Extent along the x axis, must be positive.
    :param y: Extent along the y axis, must be positive.
    :param z: Extent along the z axis, must be positive.
    :param profit: Value gained by packing one copy.  ``None`` lets the solver
        default it to ``x * y * z``, which makes a knapsack objective maximise
        packed volume.
    :param weight: Weight of one copy, used by the bin weight capacity and by
        the ``boxstacks`` axle-weight constraints.
    :param copies: Number of available copies.
    :param copies_min: Number of copies that *must* be packed.  ``None``
        defers to the upstream default: every copy is mandatory, except under
        the knapsack objective where none is.
    :param rotations: Allowed rotations.  ``None`` means the item is oriented,
        matching upstream's behaviour of defaulting an empty rotation set to
        ``{XYZ}``.
    :param group_id: Unloading group; higher groups must be unloaded first.
        ``boxstacks`` only.
    :param stackability_id: Items stack on each other only when their
        stackability ids match.  ``boxstacks`` only.
    :param nesting_height: Height by which a copy sinks into the one below it.
        ``boxstacks`` only.
    :param maximum_stackability: Maximum number of copies in one stack.
        ``boxstacks`` only.
    :param maximum_weight_above: Maximum weight this item tolerates above it.
        ``boxstacks`` only.

    Example::

        >>> from packingsolver3d import ItemType, ALL_ROTATIONS
        >>> ItemType(x=20, y=30, z=40, copies=6)
        ItemType(x=20, y=30, z=40, copies=6)
        >>> ItemType(x=20, y=30, z=40, rotations=ALL_ROTATIONS).is_stackable
        False
    """

    x: int
    y: int
    z: int
    profit: Optional[float] = None
    weight: float = 0.0
    copies: int = 1
    copies_min: Optional[int] = None
    rotations: Optional[Sequence[Rotation]] = None
    group_id: Optional[int] = None
    stackability_id: Optional[int] = None
    nesting_height: Optional[int] = None
    maximum_stackability: Optional[int] = None
    maximum_weight_above: Optional[float] = None

    #: Fields that only ``boxstacks`` understands.
    STACKING_FIELDS = (
        'group_id',
        'stackability_id',
        'nesting_height',
        'maximum_stackability',
        'maximum_weight_above',
    )

    @property
    def is_stackable(self) -> bool:
        """
        Whether any ``boxstacks``-only field is set on this item type.

        :return: ``True`` when at least one of :attr:`STACKING_FIELDS` is not
            ``None``, in which case only ``boxstacks`` can honour the instance.
        """
        return any(getattr(self, name) is not None for name in self.STACKING_FIELDS)

    def __repr__(self) -> str:
        return _terse_repr(self, ('x', 'y', 'z'))


@dataclass(frozen=True)
class BinType:
    """
    One kind of container to pack into, together with how many are available.

    :param x: Extent along the x axis, must be positive.
    :param y: Extent along the y axis, must be positive.
    :param z: Extent along the z axis, must be positive.
    :param cost: Cost of using one copy.  ``None`` lets the solver default it
        to ``x * y`` -- note that this upstream default is an *area*, not a
        volume, so pass an explicit cost whenever bins differ in height.
    :param copies: Number of available copies.
    :param copies_min: Number of copies that must be used.
    :param maximum_weight: Weight capacity of one copy.  ``None`` means
        unlimited.
    :param maximum_stack_density: Upper bound on weight per unit of floor area
        of a stack.  ``boxstacks`` only.

    Example::

        >>> from packingsolver3d import BinType
        >>> BinType(x=100, y=100, z=100, cost=10, copies=5)
        BinType(x=100, y=100, z=100, cost=10, copies=5)
    """

    x: int
    y: int
    z: int
    cost: Optional[float] = None
    copies: int = 1
    copies_min: int = 0
    maximum_weight: Optional[float] = None
    maximum_stack_density: Optional[float] = None

    #: Fields that only ``boxstacks`` understands.
    STACKING_FIELDS = ('maximum_stack_density',)

    @property
    def is_stackable(self) -> bool:
        """
        Whether any ``boxstacks``-only field is set on this bin type.

        :return: ``True`` when at least one of :attr:`STACKING_FIELDS` is not
            ``None``.
        """
        return any(getattr(self, name) is not None for name in self.STACKING_FIELDS)

    def __repr__(self) -> str:
        return _terse_repr(self, ('x', 'y', 'z'))


@dataclass(frozen=True)
class Defect:
    """
    An unusable rectangle on the floor of a bin type.

    Defects are two dimensional because ``boxstacks`` places stacks on a
    floor plan: a defect blocks the whole column above it.  ``box`` has no
    defect support at all.

    :param bin_type_id: Index of the affected bin type in
        :attr:`Instance.bin_types`.
    :param x: Lower-left x coordinate of the defect.
    :param y: Lower-left y coordinate of the defect.
    :param lx: Extent of the defect along x.
    :param ly: Extent of the defect along y.
    """

    bin_type_id: int
    x: int
    y: int
    lx: int
    ly: int


@dataclass(frozen=True)
class Instance:
    """
    A complete problem statement: what to pack, into what, optimising what.

    :param bin_types: Available bin types, at least one.
    :param item_types: Item types to pack, at least one.
    :param objective: What to optimise.
    :param defects: Unusable floor rectangles.  ``boxstacks`` only.
        At the pinned upstream commit ``boxstacks`` reads them but does not
        keep stacks off them; see :func:`packingsolver3d.boxstacks.solve`.
    :param unloading_constraint: Unloading order constraint.  ``boxstacks``
        only.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective
        >>> instance = Instance(
        ...     bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
        ...     item_types=[ItemType(x=20, y=30, z=40, copies=6)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> len(instance.item_types)
        1
    """

    bin_types: Tuple[BinType, ...]
    item_types: Tuple[ItemType, ...]
    objective: Objective = Objective.DEFAULT
    defects: Tuple[Defect, ...] = field(default_factory=tuple)
    unloading_constraint: Optional[UnloadingConstraint] = None

    def __post_init__(self):
        object.__setattr__(self, 'bin_types', tuple(self.bin_types))
        object.__setattr__(self, 'item_types', tuple(self.item_types))
        object.__setattr__(self, 'defects', tuple(self.defects))

    @property
    def needs_stacking(self) -> bool:
        """
        Whether this instance uses any ``boxstacks``-only feature.

        :return: ``True`` when a stacking field, a defect or an unloading
            constraint is present, meaning ``box`` would silently drop part of
            the problem statement.
        """
        if self.defects or self.unloading_constraint is not None:
            return True
        return any(t.is_stackable for t in self.item_types) \
            or any(t.is_stackable for t in self.bin_types)


def _terse_repr(obj, always) -> str:
    """
    Render a dataclass showing required fields plus whatever was customised.

    Value objects here have a dozen mostly-``None`` fields, and the generated
    ``__repr__`` prints all of them.  This keeps the noise out of doctests and
    log lines.

    :param obj: The dataclass instance to render.
    :param always: Field names to show even when they hold their default.
    :return: A ``ClassName(field=value, ...)`` string.
    """
    from dataclasses import fields as dataclass_fields

    parts = []
    for f in dataclass_fields(obj):
        value = getattr(obj, f.name)
        if f.name in always or value != f.default:
            parts.append('{name}={value!r}'.format(name=f.name, value=value))
    return '{cls}({parts})'.format(cls=type(obj).__name__, parts=', '.join(parts))
