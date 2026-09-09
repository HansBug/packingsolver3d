import os

import pytest

from packingsolver3d import (
    ALL_ROTATIONS, BinType, Defect, Instance, InvalidInstanceError, ItemType, Objective, Rotation, UnloadingConstraint,
)
from packingsolver3d._csv import parse_certificate, write_instance

TESTFILE_DIR = os.path.join(os.path.dirname(__file__), 'testfile')


def _lines(path):
    with open(path, 'rb') as f:
        raw = f.read()
    assert b'\r' not in raw, 'certificate files must be written with LF only'
    return raw.decode('utf-8').splitlines()


@pytest.mark.unittest
class TestWriteInstance:
    def test_box_layout(self, box_instance, tmp_path):
        paths = write_instance(box_instance, str(tmp_path))
        assert set(paths) == {'items', 'bins', 'parameters'}
        assert _lines(paths['items']) == [
            'X,Y,Z,PROFIT,WEIGHT,COPIES,COPIES_MIN',
            '20,30,40,-1,0.0,6,-1',
            '15,15,15,-1,0.0,4,-1',
        ]
        assert _lines(paths['bins']) == [
            'X,Y,Z,COST,COPIES,COPIES_MIN',
            '100,100,100,10,5,0',
        ]
        assert _lines(paths['parameters']) == ['NAME,VALUE', 'objective,bin-packing']

    def test_explicit_copies_min_and_profit(self, tmp_path):
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10)],
            item_types=[ItemType(x=1, y=2, z=3, profit=7.5, copies=4, copies_min=2)],
            objective=Objective.KNAPSACK,
        )
        paths = write_instance(instance, str(tmp_path))
        assert _lines(paths['items'])[1] == '1,2,3,7.5,0.0,4,2'
        assert _lines(paths['bins'])[1] == '10,10,10,-1,1,0'
        assert _lines(paths['parameters'])[1] == 'objective,knapsack'

    def test_rotation_columns(self, tmp_path):
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10)],
            item_types=[
                ItemType(x=1, y=2, z=3, rotations=[Rotation.XYZ, Rotation.ZYX]),
                ItemType(x=1, y=2, z=3),
            ],
        )
        header, first, second = _lines(write_instance(instance, str(tmp_path))['items'])
        assert header.endswith(','.join('ROTATION_' + r.value for r in ALL_ROTATIONS))
        assert first.split(',')[7:] == ['1', '0', '1', '0', '0', '0']
        # An oriented item gets an all-zero row; upstream turns that into {XYZ}.
        assert second.split(',')[7:] == ['0'] * 6

    def test_stacking_layout(self, stack_instance, tmp_path):
        paths = write_instance(stack_instance, str(tmp_path))
        header, first, second = _lines(paths['items'])
        assert header == ('X,Y,Z,PROFIT,WEIGHT,COPIES,COPIES_MIN,'
                          'GROUP_ID,STACKABILITY_ID,NESTING_HEIGHT,MAXIMUM_STACKABILITY,MAXIMUM_WEIGHT_ABOVE')
        assert first == '20,30,40,-1,5,6,-1,0,0,0,3,100'
        assert second == '20,30,40,-1,5,4,-1,0,0,0,3,100'
        assert _lines(paths['bins']) == [
            'X,Y,Z,COST,COPIES,COPIES_MIN,MAXIMUM_WEIGHT,MAXIMUM_STACK_DENSITY',
            '100,100,100,10,5,0,1000,10',
        ]

    def test_stacking_sentinels(self, tmp_path):
        # Columns appear only when some item sets them; the other items then get
        # upstream's defaults.  ItemPos is int32_t upstream: a 64-bit sentinel wraps
        # negative and fails the maximum stackability check, so it is INT32_MAX.
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10, maximum_weight=5.0)],
            item_types=[
                ItemType(x=1, y=1, z=1, stackability_id=1, maximum_stackability=2, maximum_weight_above=3.5),
                ItemType(x=1, y=1, z=1, stackability_id=2),
            ],
        )
        paths = write_instance(instance, str(tmp_path))
        header, first, second = _lines(paths['items'])
        assert header == 'X,Y,Z,PROFIT,WEIGHT,COPIES,COPIES_MIN,STACKABILITY_ID,MAXIMUM_STACKABILITY,MAXIMUM_WEIGHT_ABOVE'
        assert first == '1,1,1,-1,0.0,1,-1,1,2,3.5'
        assert second == '1,1,1,-1,0.0,1,-1,2,2147483647,inf'
        assert _lines(paths['bins'])[1] == '10,10,10,-1,1,0,5.0'

    def test_only_requested_columns(self, tmp_path):
        instance = Instance(
            bin_types=[BinType(x=10, y=10, z=10)],
            item_types=[ItemType(x=1, y=1, z=1, stackability_id=1)],
        )
        assert _lines(write_instance(instance, str(tmp_path))['items']) == [
            'X,Y,Z,PROFIT,WEIGHT,COPIES,COPIES_MIN,STACKABILITY_ID', '1,1,1,-1,0.0,1,-1,1',
        ]

    def test_defects_and_unloading(self, defect_instance, tmp_path):
        instance = Instance(
            bin_types=defect_instance.bin_types, item_types=defect_instance.item_types,
            defects=defect_instance.defects, unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS,
        )
        paths = write_instance(instance, str(tmp_path))
        assert 'defects' in paths
        assert _lines(paths['defects']) == ['BIN,X,Y,LX,LY', '0,0,0,10,10']
        assert _lines(paths['parameters']) == [
            'NAME,VALUE', 'objective,default', 'unloading-constraint,only-x-movements',
        ]


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
    ])
    def test_rejects(self, kwargs, message, tmp_path):
        with pytest.raises(InvalidInstanceError) as exc_info:
            write_instance(Instance(**kwargs), str(tmp_path))
        assert message in str(exc_info.value)


@pytest.mark.unittest
class TestParseCertificate:
    def test_box(self):
        bins = parse_certificate(os.path.join(TESTFILE_DIR, 'box_certificate.csv'))
        assert len(bins) == 1
        packed = bins[0]
        assert (packed.bin_id, packed.bin_type_id, packed.copies) == (0, 0, 1)
        assert (packed.x, packed.y, packed.z) == (100, 100, 100)
        assert packed.stacks == ()
        assert len(packed.placements) == 10
        first = packed.placements[0]
        assert (first.item_type_id, first.bin_id, first.x, first.y, first.z) == (0, 0, 0, 0, 0)
        assert (first.lx, first.ly, first.lz) == (20, 30, 40)
        assert first.rotation == Rotation.XYZ
        assert first.stack_id is None
        assert first.group_id is None
        assert sorted({p.item_type_id for p in packed.placements}) == [0, 1]

    def test_boxstacks(self):
        bins = parse_certificate(os.path.join(TESTFILE_DIR, 'boxstacks_certificate.csv'))
        assert len(bins) == 1
        packed = bins[0]
        assert len(packed.stacks) == 5
        assert len(packed.placements) == 10
        assert [s.stack_id for s in packed.stacks] == [0, 1, 2, 3, 4]
        stack = packed.stacks[0]
        assert (stack.bin_id, stack.x, stack.y, stack.lx, stack.ly, stack.lz) == (0, 0, 0, 20, 30, 80)
        assert all(p.stack_id is not None for p in packed.placements)
        assert all(p.group_id == 0 for p in packed.placements)
        assert sum(1 for p in packed.placements if p.stack_id == 0) == 2

    def test_missing_file(self, tmp_path):
        assert parse_certificate(str(tmp_path / 'nope.csv')) == ()
