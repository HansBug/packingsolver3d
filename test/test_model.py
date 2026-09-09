import dataclasses

import pytest

from packingsolver3d import (
    ALL_ROTATIONS, BinType, Defect, Instance, ItemType, Objective, OptimizationMode, Rotation, SemiTrailerTruck,
    UnloadingConstraint,
)


@pytest.mark.unittest
class TestEnums:
    def test_objective_tokens(self):
        assert Objective.BIN_PACKING.value == 'bin-packing'
        assert Objective.KNAPSACK.value == 'knapsack'
        assert Objective.VARIABLE_SIZED_BIN_PACKING.value == 'variable-sized-bin-packing'
        assert Objective.OPEN_DIMENSION_X.value == 'open-dimension-x'
        assert len(Objective) == 11
        assert len({o.value for o in Objective}) == 11

    def test_rotations(self):
        assert len(ALL_ROTATIONS) == 6
        assert set(ALL_ROTATIONS) == set(Rotation)
        assert Rotation.XYZ.value == 'XYZ'

    def test_other_tokens(self):
        assert OptimizationMode.ANYTIME.value == 'anytime'
        assert UnloadingConstraint.NONE.value == 'none'
        assert len(UnloadingConstraint) == 5


@pytest.mark.unittest
class TestItemType:
    def test_defaults(self):
        item = ItemType(x=20, y=30, z=40)
        assert item.profit is None
        assert item.weight == 0.0
        assert item.copies == 1
        assert item.copies_min is None
        assert item.rotations is None
        assert not item.is_stackable

    def test_stackable(self):
        assert ItemType(x=1, y=1, z=1, stackability_id=0).is_stackable
        assert ItemType(x=1, y=1, z=1, maximum_weight_above=0.0).is_stackable
        assert not ItemType(x=1, y=1, z=1, rotations=ALL_ROTATIONS, weight=3.0).is_stackable

    def test_frozen(self):
        item = ItemType(x=1, y=1, z=1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            item.x = 2

    def test_terse_repr(self):
        assert repr(ItemType(x=20, y=30, z=40, copies=6)) == 'ItemType(x=20, y=30, z=40, copies=6)'
        assert 'stackability_id=0' in repr(ItemType(x=1, y=1, z=1, stackability_id=0))


@pytest.mark.unittest
class TestBinType:
    def test_defaults(self):
        bin_type = BinType(x=100, y=100, z=100)
        assert bin_type.cost is None
        assert bin_type.copies == 1
        assert bin_type.copies_min == 0
        assert bin_type.maximum_weight is None
        assert not bin_type.is_stackable

    def test_stackable(self):
        assert BinType(x=1, y=1, z=1, maximum_stack_density=1.0).is_stackable
        assert BinType(x=1, y=1, z=1, semi_trailer_truck=SemiTrailerTruck()).is_stackable
        assert not BinType(x=1, y=1, z=1, maximum_weight=1.0).is_stackable

    def test_terse_repr(self):
        assert repr(BinType(x=100, y=100, z=100, cost=10, copies=5)) == 'BinType(x=100, y=100, z=100, cost=10, copies=5)'
        assert 'semi_trailer_truck=SemiTrailerTruck(' in repr(BinType(x=1, y=1, z=1, semi_trailer_truck=SemiTrailerTruck()))

    def test_truck_defaults(self):
        truck = SemiTrailerTruck()
        assert truck.tractor_weight == 0.0
        assert truck.harness_rear_axle_distance == 0
        assert truck.rear_axle_maximum_weight is None
        assert truck.middle_axle_maximum_weight is None


@pytest.mark.unittest
class TestInstance:
    def test_tuplized(self, box_instance):
        assert isinstance(box_instance.bin_types, tuple)
        assert isinstance(box_instance.item_types, tuple)
        assert isinstance(box_instance.defects, tuple)
        assert box_instance.defects == ()
        assert box_instance.unloading_constraint is None

    def test_objective_is_required(self):
        # Upstream's 'default' token is its unset placeholder, so the model does not default to it.
        with pytest.raises(TypeError):
            Instance(bin_types=[BinType(x=1, y=1, z=1)], item_types=[ItemType(x=1, y=1, z=1)])  # noqa
        assert Objective.DEFAULT.value == 'default'

    def test_needs_stacking(self, box_instance, stack_instance, defect_instance):
        assert not box_instance.needs_stacking
        assert stack_instance.needs_stacking
        assert defect_instance.needs_stacking
        unloading = Instance(
            bin_types=box_instance.bin_types, item_types=box_instance.item_types, objective=box_instance.objective,
            unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS,
        )
        assert unloading.needs_stacking
        bin_only = Instance(
            bin_types=[BinType(x=1, y=1, z=1, maximum_stack_density=2.0)],
            item_types=box_instance.item_types, objective=box_instance.objective,
        )
        assert bin_only.needs_stacking

    def test_defect(self):
        defect = Defect(bin_type_id=0, x=1, y=2, lx=3, ly=4)
        assert (defect.bin_type_id, defect.x, defect.y, defect.lx, defect.ly) == (0, 1, 2, 3, 4)
