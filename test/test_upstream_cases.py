"""
Upstream's own unit-test instances, solved through this package.

Every case under ``test/testfile/upstream`` is a verbatim copy of
``data/box/tests/*`` or ``data/boxstacks/tests/*`` from fontanf/packingsolver
(see ``SOURCE.md`` there).  Each test replays what the corresponding upstream
gtest does -- same instance files, same optimisation parameters -- and checks
the result against ``solution.csv`` with the comparison upstream's
``Solution::operator<`` applies for the objective: profit for knapsack, cost for
variable-sized bin packing, ``x_max`` for open dimension x, and the number of
bins for bin packing.
"""

import csv
import os
from typing import Any, Dict, List, Optional

import pytest

from packingsolver3d import (
    ALL_ROTATIONS, BinType, Instance, ItemType, Objective, OptimizationMode, Rotation, SemiTrailerTruck, Status,
    UnloadingConstraint, box, boxstacks,
)

CASES_DIR = os.path.join(os.path.dirname(__file__), 'testfile', 'upstream')

_TRUCK_COLUMNS = {
    'TRACTOR_WEIGHT': ('tractor_weight', float),
    'FRONT_AXLE_MIDDLE_AXLE_DISTANCE': ('front_axle_middle_axle_distance', int),
    'FRONT_AXLE_TRACTOR_GRAVITY_CENTER_DISTANCE': ('front_axle_tractor_gravity_center_distance', int),
    'FRONT_AXLE_HARNESS_DISTANCE': ('front_axle_harness_distance', int),
    'EMPTY_TRAILER_WEIGHT': ('empty_trailer_weight', float),
    'HARNESS_REAR_AXLE_DISTANCE': ('harness_rear_axle_distance', int),
    'TRAILER_GRAVITY_CENTER_REAR_AXLE_DISTANCE': ('trailer_gravity_center_rear_axle_distance', int),
    'TRAILER_START_HARNESS_DISTANCE': ('trailer_start_harness_distance', int),
    'REAR_AXLE_MAXIMUM_WEIGHT': ('rear_axle_maximum_weight', float),
    'MIDDLE_AXLE_MAXIMUM_WEIGHT': ('middle_axle_maximum_weight', float),
}


def _rows(path: str) -> List[Dict[str, str]]:
    with open(path, 'r', newline='') as f:
        return [row for row in csv.DictReader(f) if any(v.strip() for v in row.values() if v is not None)]


def _optional(row: Dict[str, str], column: str, cast):
    """Upstream's CSV readers treat an absent column like an absent value."""
    value = row.get(column)
    if value is None or value.strip() == '':
        return None
    return cast(value)


def _item_type(row: Dict[str, str]) -> ItemType:
    rotations = None
    if any(column.startswith('ROTATION_') for column in row):
        rotations = [r for r in ALL_ROTATIONS if row.get('ROTATION_' + r.value, '0').strip() == '1']
    return ItemType(
        x=int(row['X']), y=int(row['Y']), z=int(row['Z']),
        profit=_optional(row, 'PROFIT', float),
        weight=_optional(row, 'WEIGHT', float) or 0.0,
        copies=_optional(row, 'COPIES', int) or 1,
        copies_min=_optional(row, 'COPIES_MIN', int),
        rotations=rotations,
        group_id=_optional(row, 'GROUP_ID', int),
        stackability_id=_optional(row, 'STACKABILITY_ID', int),
        nesting_height=_optional(row, 'NESTING_HEIGHT', int),
        maximum_stackability=_optional(row, 'MAXIMUM_STACKABILITY', int),
        maximum_weight_above=_optional(row, 'MAXIMUM_WEIGHT_ABOVE', float),
    )


def _bin_type(row: Dict[str, str]) -> BinType:
    truck = None
    if row.get('IS_SEMI_TRAILER_TRUCK', '0').strip() == '1':
        truck = SemiTrailerTruck(**{
            field: cast(row[column]) for column, (field, cast) in _TRUCK_COLUMNS.items() if column in row
        })
    return BinType(
        x=int(row['X']), y=int(row['Y']), z=int(row['Z']),
        cost=_optional(row, 'COST', float),
        copies=_optional(row, 'COPIES', int) or 1,
        copies_min=_optional(row, 'COPIES_MIN', int) or 0,
        maximum_weight=_optional(row, 'MAXIMUM_WEIGHT', float),
        maximum_stack_density=_optional(row, 'MAXIMUM_STACK_DENSITY', float),
        semi_trailer_truck=truck,
    )


def load_case(directory: str) -> Instance:
    """Read ``items.csv``, ``bins.csv`` and ``parameters.csv`` the way upstream's readers do."""
    parameters = {row['NAME']: row['VALUE'] for row in _rows(os.path.join(directory, 'parameters.csv'))}
    unloading = parameters.get('unloading-constraint')
    return Instance(
        bin_types=[_bin_type(row) for row in _rows(os.path.join(directory, 'bins.csv'))],
        item_types=[_item_type(row) for row in _rows(os.path.join(directory, 'items.csv'))],
        objective=Objective(parameters.get('objective', 'default')),
        unloading_constraint=None if unloading is None else UnloadingConstraint(unloading),
    )


class Reference:
    """The objective quantities of upstream's ``solution.csv`` certificate."""

    def __init__(self, instance: Instance, path: str):
        rows = _rows(path)
        self.bins = [row for row in rows if row['TYPE'] == 'BIN']
        self.items = [row for row in rows if row['TYPE'] == 'ITEM']
        self.number_of_bins = sum(int(row['COPIES']) for row in self.bins)
        self.cost = 0.0
        for row in self.bins:
            bin_type = instance.bin_types[int(row['ID'])]
            cost = bin_type.cost if bin_type.cost is not None else float(bin_type.x * bin_type.y)
            self.cost += cost * int(row['COPIES'])
        self.profit = 0.0
        for row in self.items:
            item_type = instance.item_types[int(row['ID'])]
            profit = item_type.profit if item_type.profit is not None else float(item_type.x * item_type.y * item_type.z)
            self.profit += profit * int(row['COPIES'])
        self.x_max = max([int(row['X']) + int(row['LX']) for row in self.items] or [0])


def assert_same_quality(result, reference: Reference, objective: Objective) -> None:
    """Mirror ``!(a < b) && !(b < a)`` from upstream's tests for the objective at hand."""
    if not reference.items:
        # Upstream's certificate is empty: nothing could be packed.
        assert result.placements == ()
        return
    assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
    if objective == Objective.KNAPSACK:
        assert result.value == pytest.approx(reference.profit)
    elif objective == Objective.VARIABLE_SIZED_BIN_PACKING:
        assert result.value == pytest.approx(reference.cost)
    elif objective == Objective.OPEN_DIMENSION_X:
        assert result.value == reference.x_max
    elif objective == Objective.BIN_PACKING:
        assert result.number_of_bins == reference.number_of_bins
    else:  # pragma: no cover - no upstream case uses another objective
        raise AssertionError('no comparison rule for {objective!r}'.format(objective=objective))
    assert len(result.placements) == sum(int(row['COPIES']) for row in reference.items)


# (case directory, how upstream's test invokes the solver)
BOX_CASES = [
    # test/box/box_test.cpp
    ('variable_sized_bin_packing_two_bin_types', dict(optimization_mode=OptimizationMode.NOT_ANYTIME_SEQUENTIAL)),
    # test/box/tree_search_test.cpp
    ('knapsack_1_item', dict(use_tree_search=True)),
    ('knapsack_4_items', dict(use_tree_search=True)),
    ('knapsack_20_items', dict(use_tree_search=True)),
    ('open_dimension_x_4_different_items_xy', dict(use_tree_search=True)),
    ('open_dimension_x_4_different_items_xz', dict(use_tree_search=True)),
    ('open_dimension_x_4_different_items_yz', dict(use_tree_search=True)),
]

BOXSTACKS_CASES = [
    # test/boxstacks/optimize_test.cpp
    ('variable_sized_bin_packing_two_bin_types', dict(optimization_mode=OptimizationMode.NOT_ANYTIME_SEQUENTIAL)),
    # The three *_time_limit cases run with a 3 s limit upstream (BoxStacksOptimizeTestParams::time_limit): they are the
    # reproducers of fontanf/packingsolver#570, where the box relaxation solved for the bound used to consume the whole
    # time limit and optimize() returned nothing; since #571 the bound comes from closed-form relaxations and the limit
    # is only a regression check.
    ('knapsack_two_item_types_pallet_time_limit',
     dict(optimization_mode=OptimizationMode.NOT_ANYTIME_SEQUENTIAL, time_limit=3.0)),
    ('bin_packing_two_item_types_pallets_time_limit',
     dict(optimization_mode=OptimizationMode.NOT_ANYTIME_SEQUENTIAL, time_limit=3.0)),
    ('variable_sized_bin_packing_two_pallet_types_time_limit',
     dict(optimization_mode=OptimizationMode.NOT_ANYTIME_SEQUENTIAL, time_limit=3.0)),
    # test/boxstacks/sequential_onedimensional_rectangle_test.cpp calls the
    # sequential one-dimensional / rectangle algorithm directly, whose reference
    # is empty for both instances (they enter the axle weight repair loop
    # upstream fixed in #540).  The public entry point here is optimize(); where
    # its answer differs from that sub-algorithm, the case directory carries
    # solution_optimize.csv, the certificate written by upstream's own
    # packingsolver_boxstacks executable on the same files (see SOURCE.md).
    ('semi_trailer_truck_middle_axle_bin_packing', dict()),
    ('semi_trailer_truck_middle_axle_knapsack', dict()),
]


def reference_path(directory: str) -> str:
    optimize_reference = os.path.join(directory, 'solution_optimize.csv')
    return optimize_reference if os.path.isfile(optimize_reference) else os.path.join(directory, 'solution.csv')


@pytest.mark.unittest
class TestUpstreamBoxCases:
    @pytest.mark.parametrize('case, kwargs', BOX_CASES, ids=[case for case, _ in BOX_CASES])
    def test_case(self, case, kwargs):
        directory = os.path.join(CASES_DIR, 'box', case)
        instance = load_case(directory)
        reference = Reference(instance, os.path.join(directory, 'solution.csv'))
        result = box.solve(instance, **kwargs)
        assert_same_quality(result, reference, instance.objective)


@pytest.mark.unittest
class TestUpstreamBoxStacksCases:
    @pytest.mark.parametrize('case, kwargs', BOXSTACKS_CASES, ids=[case for case, _ in BOXSTACKS_CASES])
    def test_case(self, case, kwargs):
        directory = os.path.join(CASES_DIR, 'boxstacks', case)
        instance = load_case(directory)
        reference = Reference(instance, reference_path(directory))
        result = boxstacks.solve(instance, **kwargs)
        assert_same_quality(result, reference, instance.objective)


@pytest.mark.unittest
class TestLoader:
    def test_rotations_and_truck(self):
        instance = load_case(os.path.join(CASES_DIR, 'boxstacks', 'semi_trailer_truck_middle_axle_bin_packing'))
        assert instance.objective == Objective.BIN_PACKING
        assert instance.item_types[0].rotations == [Rotation.XYZ]
        assert instance.item_types[0].weight == 2000.0
        truck = instance.bin_types[0].semi_trailer_truck
        assert truck is not None
        assert (truck.tractor_weight, truck.rear_axle_maximum_weight, truck.middle_axle_maximum_weight) == (8000.0, 20000.0, 9300.0)
        assert truck.harness_rear_axle_distance == 800

    def test_all_rotations(self):
        instance = load_case(os.path.join(CASES_DIR, 'box', 'variable_sized_bin_packing_two_bin_types'))
        assert instance.item_types[0].rotations == list(ALL_ROTATIONS)
        assert instance.bin_types[1].cost == 10.0
        assert instance.objective == Objective.VARIABLE_SIZED_BIN_PACKING
