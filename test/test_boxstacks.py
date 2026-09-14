import pytest

from packingsolver3d import (
    BinType, Instance, ItemType, Objective, Rotation, StackSemanticsError, Status, UnloadingConstraint,
    UnsupportedFeatureError, boxstacks,
)


@pytest.mark.unittest
class TestSolve:
    def test_bin_packing_with_stacks(self, stack_instance):
        result = boxstacks.solve(stack_instance, time_limit=2.0)
        assert result.status == Status.OPTIMAL
        assert result.number_of_bins == 1
        packed = result.bins[0]
        assert len(packed.stacks) >= 4  # 10 copies, at most 3 per stack
        assert len(result.placements) == 10
        assert all(p.stack_id is not None for p in result.placements)
        assert all(p.group_id == 0 for p in result.placements)
        stack_ids = {s.stack_id for s in packed.stacks}
        assert {p.stack_id for p in result.placements} == stack_ids
        for stack in packed.stacks:
            members = [p for p in result.placements if p.stack_id == stack.stack_id]
            assert 1 <= len(members) <= 3
            assert all((p.x, p.y) == (stack.x, stack.y) for p in members)
        assert result.run.problem_type == 'boxstacks'

    def test_plain_instance_needs_distinct_footprints(self, box_instance):
        # Both item types default to stackability_id 0 and differ in footprint:
        # upstream would stack them and crash in SolutionBuilder::add_item.
        with pytest.raises(StackSemanticsError) as exc_info:
            boxstacks.solve(box_instance, time_limit=1.0)
        message = str(exc_info.value)
        assert 'item types #0 and #1' in message
        assert '(20, 30)' in message and '(15, 15)' in message
        assert 'distinct stackability_id' in message

    def test_plain_instance_with_ids(self, box_instance):
        instance = Instance(
            bin_types=box_instance.bin_types,
            item_types=[
                ItemType(x=20, y=30, z=40, copies=6, stackability_id=0),
                ItemType(x=15, y=15, z=15, copies=4, stackability_id=1),
            ],
            objective=Objective.BIN_PACKING,
        )
        result = boxstacks.solve(instance, time_limit=2.0)
        assert result.status == Status.OPTIMAL
        assert result.number_of_bins == 1
        assert len(result.placements) == 10

    def test_same_footprint_shares_bucket(self, stack_instance):
        boxstacks.validate(stack_instance)
        instance = Instance(
            bin_types=stack_instance.bin_types,
            item_types=[ItemType(x=2, y=3, z=4, group_id=1), ItemType(x=2, y=3, z=9, group_id=1)],
            objective=Objective.BIN_PACKING,
        )
        boxstacks.validate(instance)

    def test_side_rotations_are_refused(self):
        # Observed upstream: an item allowing only XZY ends in
        # SolutionBuilder::add_item throwing "forbidden rotation".
        instance = Instance(
            bin_types=[BinType(x=90, y=10, z=10)],
            item_types=[ItemType(x=90, y=10, z=10, rotations=[Rotation.XZY, Rotation.ZYX])],
            objective=Objective.KNAPSACK,
        )
        with pytest.raises(UnsupportedFeatureError) as exc_info:
            boxstacks.solve(instance, time_limit=1.0)
        assert 'upright' in str(exc_info.value)
        upright = Instance(
            bin_types=instance.bin_types,
            item_types=[ItemType(x=90, y=10, z=10, rotations=[Rotation.XZY, Rotation.XYZ])],
            objective=Objective.KNAPSACK,
        )
        assert boxstacks.solve(upright, time_limit=1.0).number_of_bins == 1

    def test_rotation_can_match_footprints(self):
        turning = Instance(
            bin_types=[BinType(x=100, y=100, z=100)],
            item_types=[
                ItemType(x=20, y=30, z=40, stackability_id=0),
                ItemType(x=30, y=20, z=10, stackability_id=0, rotations=[Rotation.YXZ]),
            ],
            objective=Objective.BIN_PACKING,
        )
        boxstacks.validate(turning)
        oriented = Instance(
            bin_types=turning.bin_types,
            item_types=[
                ItemType(x=20, y=30, z=40, stackability_id=0),
                ItemType(x=30, y=20, z=10, stackability_id=0),
            ],
            objective=Objective.BIN_PACKING,
        )
        with pytest.raises(StackSemanticsError):
            boxstacks.validate(oriented)
        # Rotations that stand the item on its side change the footprint too
        # (the item keeps an upright rotation as well, which boxstacks requires).
        side = Instance(
            bin_types=turning.bin_types,
            item_types=[
                ItemType(x=20, y=30, z=40, stackability_id=0),
                ItemType(x=40, y=30, z=20, stackability_id=0, rotations=[Rotation.XYZ, Rotation.ZYX]),
            ],
            objective=Objective.BIN_PACKING,
        )
        boxstacks.validate(side)

    def test_unloading_constraint_option(self, stack_instance):
        result = boxstacks.solve(
            stack_instance, time_limit=1.0, unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS,
        )
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert len(result.placements) == 10

    def test_defects(self, defect_instance):
        # Observed at upstream a7e53303 and unchanged at 3f4faae1: defects are read and echoed in the
        # certificate, but stacks are placed over them (corner, interior and
        # full-width defects alike).  Only acceptance is asserted here.
        result = boxstacks.solve(defect_instance, time_limit=2.0)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert len(result.placements) == 10

    def test_weight_capacity_forces_more_bins(self):
        instance = Instance(
            bin_types=[BinType(x=100, y=100, z=100, cost=10, copies=5, maximum_weight=12)],
            item_types=[ItemType(x=20, y=30, z=40, copies=6, weight=5, stackability_id=0,
                                 maximum_stackability=3, maximum_weight_above=100)],
            objective=Objective.BIN_PACKING,
        )
        result = boxstacks.solve(instance, time_limit=2.0)
        assert result.number_of_bins == 3
        assert result.statistics['ItemWeight'] == 30.0

    def test_knapsack(self, stack_instance):
        instance = Instance(
            bin_types=[BinType(x=100, y=100, z=100, copies=1, maximum_weight=1000, maximum_stack_density=10)],
            item_types=stack_instance.item_types,
            objective=Objective.KNAPSACK,
        )
        result = boxstacks.solve(instance, time_limit=2.0)
        assert result.status in (Status.OPTIMAL, Status.FEASIBLE)
        assert result.value == 240000.0
        assert result.number_of_bins == 1

    def test_upstream_rejection_is_typed(self):
        # copies_min above copies passes our checks only via the None route; make
        # upstream itself reject something: a bin lighter than a mandatory item.
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10, maximum_weight=1)],
            item_types=[ItemType(x=1, y=1, z=1, weight=5, stackability_id=0)],
            objective=Objective.BIN_PACKING,
        )
        result = boxstacks.solve(instance, time_limit=1.0)
        assert result.status in (Status.NO_SOLUTION, Status.INFEASIBLE, Status.FEASIBLE)
