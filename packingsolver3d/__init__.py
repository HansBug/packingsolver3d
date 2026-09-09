"""
Overview:
    Pythonic bindings for the 3D solvers of `PackingSolver
    <https://github.com/fontanf/packingsolver>`_.

    This distribution is unofficial and covers only the two three-dimensional
    problem types, ``box`` and ``boxstacks``.  The upstream solvers are
    compiled into the extension module :mod:`packingsolver3d._core` together
    with a thin pybind11 bridge, so nothing has to be built at install time and
    no C++ lifetime ever reaches Python: an instance goes in as plain values,
    ``optimize()`` runs in-process, and the best solution comes back copied
    into plain value objects.

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
from .config.meta import __VERSION__ as __version__
from .errors import InvalidInstanceError, PackingSolverError, SolverFailedError, StackSemanticsError, \
    UnsupportedFeatureError
from .model import ALL_ROTATIONS, BinType, Defect, Instance, ItemType, Objective, \
    OptimizationMode, Rotation, SemiTrailerTruck, UnloadingConstraint
from .result import PackedBin, Placement, Result, RunRecord, Stack, Status

__all__ = [
    'ALL_ROTATIONS',
    'BinType',
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
    'SemiTrailerTruck',
    'SolverFailedError',
    'Stack',
    'StackSemanticsError',
    'Status',
    'UnloadingConstraint',
    'UnsupportedFeatureError',
    'box',
    'boxstacks',
]
