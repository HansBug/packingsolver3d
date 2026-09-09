import pytest

from packingsolver3d import (
    ALL_ROTATIONS, BinType, Defect, Instance, InvalidInstanceError, ItemType, Objective, Rotation, UnloadingConstraint,
)
from packingsolver3d._encode import instance_payload


@pytest.mark.unittest
class TestInstancePayload:
    def test_plain(self, box_instance):
        payload = instance_payload(box_instance)
        assert set(payload) == {'objective', 'bins', 'items', 'defects', 'unloading_constraint'}
        assert payload['objective'] == 'bin-packing'
        assert payload['bins'] == [{'x': 100, 'y': 100, 'z': 100, 'cost': 10, 'copies': 5, 'copies_min': 0}]
        # None fields are left out so upstream's own defaults apply.
        assert payload['items'] == [
            {'x': 20, 'y': 30, 'z': 40, 'weight': 0.0, 'copies': 6},
            {'x': 15, 'y': 15, 'z': 15, 'weight': 0.0, 'copies': 4},
        ]
        assert payload['defects'] == []
        assert payload['unloading_constraint'] is None

    def test_explicit_fields(self):
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10)],
            item_types=[ItemType(x=1, y=2, z=3, profit=7.5, copies=4, copies_min=2,
                                 rotations=[Rotation.XYZ, Rotation.ZYX])],
            objective=Objective.KNAPSACK,
        )
        payload = instance_payload(instance)
        assert payload['objective'] == 'knapsack'
        assert payload['bins'] == [{'x': 10, 'y': 10, 'z': 10, 'copies': 1, 'copies_min': 0}]
        assert payload['items'] == [{
            'x': 1, 'y': 2, 'z': 3, 'profit': 7.5, 'weight': 0.0, 'copies': 4, 'copies_min': 2,
            'rotations': ['XYZ', 'ZYX'],
        }]

    def test_all_rotations_tokens(self):
        item = ItemType(x=1, y=1, z=1, rotations=ALL_ROTATIONS)
        payload = instance_payload(Instance(bin_types=[BinType(x=5, y=5, z=5)], item_types=[item]))
        assert payload['items'][0]['rotations'] == ['XYZ', 'YXZ', 'ZYX', 'YZX', 'XZY', 'ZXY']

    def test_stacking_fields(self, stack_instance):
        payload = instance_payload(stack_instance)
        assert payload['bins'][0] == {
            'x': 100, 'y': 100, 'z': 100, 'cost': 10, 'copies': 5, 'copies_min': 0,
            'maximum_weight': 1000, 'maximum_stack_density': 10,
        }
        assert payload['items'][0] == {
            'x': 20, 'y': 30, 'z': 40, 'weight': 5, 'copies': 6,
            'group_id': 0, 'stackability_id': 0, 'nesting_height': 0,
            'maximum_stackability': 3, 'maximum_weight_above': 100,
        }
        assert 'nesting_height' not in payload['items'][1]

    def test_defects_and_unloading(self, defect_instance):
        payload = instance_payload(defect_instance)
        assert payload['defects'] == [{'bin_type_id': 0, 'x': 0, 'y': 0, 'lx': 10, 'ly': 10}]
        assert payload['unloading_constraint'] is None
        instance = Instance(
            bin_types=defect_instance.bin_types, item_types=defect_instance.item_types,
            unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS,
        )
        assert instance_payload(instance)['unloading_constraint'] == 'only-x-movements'
        assert instance_payload(instance, UnloadingConstraint.NONE)['unloading_constraint'] == 'none'
        assert instance_payload(instance)['objective'] == 'default'


@pytest.mark.unittest
class TestValidate:
    @pytest.mark.parametrize('kwargs, message', [
        (dict(bin_types=[], item_types=[ItemType(x=1, y=1, z=1)]), 'no bin types'),
        (dict(bin_types=[BinType(x=1, y=1, z=1)], item_types=[]), 'no item types'),
        (dict(bin_types=[BinType(x=0, y=1, z=1)], item_types=[ItemType(x=1, y=1, z=1)]), 'non-positive x'),
        (dict(bin_types=[BinType(x=1, y=1, z=1)], item_types=[ItemType(x=1, y=-2, z=1)]), 'non-positive y'),
        (dict(bin_types=[BinType(x=1, y=1, z=1)], item_types=[ItemType(x=1, y=1, z=1, copies=0)]),
         'non-positive copies'),
        (dict(bin_types=[BinType(x=1, y=1, z=1)], item_types=[ItemType(x=1, y=1, z=1, copies=2, copies_min=3)]),
         'copies_min outside'),
        (dict(bin_types=[BinType(x=1, y=1, z=1, copies=1, copies_min=2)], item_types=[ItemType(x=1, y=1, z=1)]),
         'copies_min outside'),
        (dict(bin_types=[BinType(x=1, y=1, z=1)], item_types=[ItemType(x=1, y=1, z=1)],
              defects=[Defect(bin_type_id=3, x=0, y=0, lx=1, ly=1)]), 'unknown bin type'),
        (dict(bin_types=[BinType(x=1, y=1, z=1)], item_types=[ItemType(x=1, y=1, z=1)],
              defects=[Defect(bin_type_id=0, x=0, y=0, lx=0, ly=1)]), 'non-positive extent'),
    ])
    def test_rejects(self, kwargs, message):
        with pytest.raises(InvalidInstanceError) as exc_info:
            instance_payload(Instance(**kwargs))
        assert message in str(exc_info.value)
