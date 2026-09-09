"""
Overview:
    Result objects of :mod:`packingsolver3d`.

    A result is a snapshot, not a handle.  Everything the native process
    produced -- the packing itself, the statistics block, the bound it managed
    to prove, and the raw record of how it was invoked -- is copied into plain
    Python objects before the process is reaped, so a result stays valid and
    picklable forever.
"""

import json
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from dataclasses import dataclass, field

from .model import Objective, Rotation

__all__ = [
    'Status',
    'Placement',
    'Stack',
    'PackedBin',
    'RunRecord',
    'Result',
]


class Status(Enum):
    """
    How much the solver managed to establish about the instance.

    ``OPTIMAL`` is only reported when the objective value equals a bound the
    solver itself reported, so it always means *proven* optimal rather than
    "the heuristic stopped improving".
    """

    OPTIMAL = 'optimal'
    FEASIBLE = 'feasible'
    NO_SOLUTION = 'no-solution'
    INFEASIBLE = 'infeasible'


@dataclass(frozen=True)
class Placement:
    """
    One packed copy of an item type.

    :param item_type_id: Index into ``Instance.item_types``.
    :param bin_id: Index of the bin group this copy sits in, matching
        :attr:`PackedBin.bin_id`.
    :param x: Lower-left-bottom x coordinate inside the bin.
    :param y: Lower-left-bottom y coordinate inside the bin.
    :param z: Lower-left-bottom z coordinate inside the bin.
    :param lx: Occupied extent along x, i.e. the item extent *after* rotation.
    :param ly: Occupied extent along y, after rotation.
    :param lz: Occupied extent along z, after rotation.
    :param rotation: Rotation the copy was placed under.
    :param stack_id: Stack this copy belongs to, or ``None`` for ``box``
        results which have no stacks.
    :param group_id: Unloading group, ``boxstacks`` only.
    """

    item_type_id: int
    bin_id: int
    x: int
    y: int
    z: int
    lx: int
    ly: int
    lz: int
    rotation: Optional[Rotation] = None
    stack_id: Optional[int] = None
    group_id: Optional[int] = None


@dataclass(frozen=True)
class Stack:
    """
    A vertical pile of items standing on one footprint of a bin floor.

    Only ``boxstacks`` produces stacks; the ``box`` solver places every item
    independently and reports none.

    :param stack_id: Index of the stack within its bin.
    :param bin_id: Index of the bin group this stack sits in.
    :param x: Lower-left x coordinate of the footprint.
    :param y: Lower-left y coordinate of the footprint.
    :param lx: Footprint extent along x.
    :param ly: Footprint extent along y.
    :param lz: Total height of the pile.
    """

    stack_id: int
    bin_id: int
    x: int
    y: int
    lx: int
    ly: int
    lz: int


@dataclass(frozen=True)
class PackedBin:
    """
    One used bin, or several identical used bins collapsed into one entry.

    PackingSolver reports identical bins once with a ``copies`` count rather
    than repeating the packing, so :attr:`copies` may exceed one and the
    placements below describe *each* of those copies.

    :param bin_id: Position of this bin group in the solution.
    :param bin_type_id: Index into ``Instance.bin_types``.
    :param copies: How many identical bins share this packing.
    :param x: Extent of the bin along x.
    :param y: Extent of the bin along y.
    :param z: Extent of the bin along z.
    :param placements: Item copies packed into one of these bins.
    :param stacks: Stacks in one of these bins, ``boxstacks`` only.
    """

    bin_id: int
    bin_type_id: int
    copies: int
    x: int
    y: int
    z: int
    placements: Tuple[Placement, ...] = field(default_factory=tuple)
    stacks: Tuple[Stack, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RunRecord:
    """
    Exactly what was executed, so a result can be reproduced or blamed.

    :param argv: The full command line, executable path included.
    :param returncode: Process exit status.
    :param stdout: Captured standard output.
    :param stderr: Captured standard error.
    :param wall_time: Wall clock seconds spent in the process.
    :param binary_sha256: Hex digest of the executable that produced the
        result, which pins the answer to a specific build.
    :param timed_out: Whether the wall clock guard had to kill the process.
    """

    argv: Tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    wall_time: float
    binary_sha256: str
    timed_out: bool = False


@dataclass(frozen=True)
class Result:
    """
    Outcome of one solve.

    :param status: See :class:`Status`.
    :param bins: Used bins, in solution order.
    :param objective: The objective the instance was solved for.
    :param value: Objective value of :attr:`bins`, or ``None`` when there is
        no solution.  This is what the solver *achieved*.
    :param bound: The bound the solver reported for this objective, or ``None``
        when it proved none.  This is what the solver *proved*, and it is
        deliberately kept separate from :attr:`value`.
    :param statistics: The raw ``Output.Solution`` block of the solver's JSON
        output, verbatim.
    :param solve_time: Seconds the solver reports having spent, from
        ``Output.Time``.
    :param run: How the process was invoked, see :class:`RunRecord`.
    """

    status: Status
    bins: Tuple[PackedBin, ...]
    objective: Objective
    value: Optional[float] = None
    bound: Optional[float] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    solve_time: Optional[float] = None
    run: Optional[RunRecord] = None

    @property
    def is_proven_optimal(self) -> bool:
        """
        Whether the achieved value provably cannot be improved.

        :return: ``True`` only when :attr:`status` is :attr:`Status.OPTIMAL`,
            which in turn requires a solver-reported bound equal to the
            achieved value.  A heuristic solution that merely looks good is
            never reported as optimal.
        """
        return self.status == Status.OPTIMAL

    @property
    def number_of_bins(self) -> int:
        """
        Total bins used, counting repeated identical bins separately.

        :return: The sum of :attr:`PackedBin.copies` over :attr:`bins`.
        """
        return sum(b.copies for b in self.bins)

    @property
    def placements(self) -> Tuple[Placement, ...]:
        """
        Every placement of every bin, flattened.

        :return: A tuple of placements in bin order.  A bin with several
            copies contributes its placements once, so this is the packing
            *plan* rather than a per-physical-copy listing.
        """
        result = []
        for b in self.bins:
            result.extend(b.placements)
        return tuple(result)

    def to_json(self) -> str:
        """
        Render the result as JSON, for logs and fixtures.

        :return: A JSON document with the status, the bins and the statistics.
            The :class:`RunRecord` is left out because it carries absolute
            paths that would make golden files machine dependent.
        """
        return json.dumps({
            'status': self.status.value,
            'objective': self.objective.value,
            'value': self.value,
            'bound': self.bound,
            'solve_time': self.solve_time,
            'bins': [
                {
                    'bin_id': b.bin_id,
                    'bin_type_id': b.bin_type_id,
                    'copies': b.copies,
                    'x': b.x, 'y': b.y, 'z': b.z,
                    'stacks': [
                        {
                            'stack_id': s.stack_id,
                            'x': s.x, 'y': s.y,
                            'lx': s.lx, 'ly': s.ly, 'lz': s.lz,
                        }
                        for s in b.stacks
                    ],
                    'placements': [
                        {
                            'item_type_id': p.item_type_id,
                            'x': p.x, 'y': p.y, 'z': p.z,
                            'lx': p.lx, 'ly': p.ly, 'lz': p.lz,
                            'rotation': None if p.rotation is None else p.rotation.value,
                            'stack_id': p.stack_id,
                            'group_id': p.group_id,
                        }
                        for p in b.placements
                    ],
                }
                for b in self.bins
            ],
            'statistics': self.statistics,
        }, sort_keys=True, indent=2)
