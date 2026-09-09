"""
Overview:
    Pythonic bindings for the 3D solvers of `PackingSolver
    <https://github.com/fontanf/packingsolver>`_.

    This distribution is unofficial and covers only the two three-dimensional
    problem types, ``box`` and ``boxstacks``.  The native executables are
    precompiled into the wheel, so nothing has to be built at install time and
    no C++ lifetime ever reaches Python: an instance is encoded to CSV, a
    short-lived process solves it, and the answer comes back as plain value
    objects.

    Example::

        >>> from packingsolver3d import BinType, Instance, ItemType, Objective, box
        >>> instance = Instance(
        ...     bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5)],
        ...     item_types=[ItemType(x=20, y=30, z=40, copies=6)],
        ...     objective=Objective.BIN_PACKING,
        ... )
        >>> result = box.solve(instance, time_limit=5.0)
        >>> result.status
        <Status.OPTIMAL: 'optimal'>
"""

from . import box, boxstacks
from ._runner import available_binaries, binary_path
from .config.meta import __VERSION__ as __version__
from .errors import BinaryNotFoundError, InvalidInstanceError, PackingSolverError, \
    SolverFailedError, StackSemanticsError, SolverTimeoutError, UnsupportedFeatureError
from .model import ALL_ROTATIONS, BinType, Defect, Instance, ItemType, Objective, \
    OptimizationMode, Rotation, UnloadingConstraint
from .result import PackedBin, Placement, Result, RunRecord, Stack, Status

__all__ = [
    'ALL_ROTATIONS',
    'BinType',
    'BinaryNotFoundError',
    'Defect',
    'Instance',
    'InvalidInstanceError',
    'ItemType',
    'Objective',
    'OptimizationMode',
    'PackedBin',
    'PackingSolverError',
    'Placement',
    'Result',
    'Rotation',
    'RunRecord',
    'SolverFailedError',
    'SolverTimeoutError',
    'Stack',
    'StackSemanticsError',
    'Status',
    'UnloadingConstraint',
    'UnsupportedFeatureError',
    'available_binaries',
    'binary_path',
    'box',
    'boxstacks',
]
