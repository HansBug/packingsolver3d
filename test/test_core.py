import json

import pytest

from packingsolver3d import _core


def _payload(**overrides):
    payload = {
        'objective': 'bin-packing',
        'bins': [{'x': 100, 'y': 100, 'z': 100, 'cost': 10, 'copies': 5}],
        'items': [{'x': 20, 'y': 30, 'z': 40, 'copies': 6}],
        'defects': [],
        'unloading_constraint': None,
    }
    payload.update(overrides)
    return payload


@pytest.mark.unittest
class TestModule:
    def test_surface(self):
        assert callable(_core.box_solve)
        assert callable(_core.boxstacks_solve)
        assert 'PackingSolver' in _core.__doc__

    def test_box_roundtrip(self):
        raw = _core.box_solve(_payload(), {'time_limit': 2.0, 'linear_programming_solver': 'highs'})
        assert set(raw) == {'output', 'stdout', 'stderr', 'bins'}
        output = json.loads(raw['output'])
        assert output['Solution']['NumberOfItems'] == 6
        assert output['BinPackingBound'] == 1
        assert isinstance(output['Time'], float)
        assert raw['stdout'] == '' and raw['stderr'] == ''
        assert len(raw['bins']) == 1
        bin_ = raw['bins'][0]
        assert (bin_['bin_type_id'], bin_['copies'], bin_['x'], bin_['y'], bin_['z']) == (0, 1, 100, 100, 100)
        assert bin_['stacks'] == []
        assert len(bin_['placements']) == 6
        first = bin_['placements'][0]
        assert set(first) == {'item_type_id', 'x', 'y', 'z', 'lx', 'ly', 'lz', 'rotation'}
        assert (first['lx'], first['ly'], first['lz'], first['rotation']) == (20, 30, 40, 'XYZ')

    def test_boxstacks_roundtrip(self):
        payload = _payload(
            bins=[{'x': 100, 'y': 100, 'z': 100, 'cost': 10, 'copies': 5, 'maximum_weight': 1000.0}],
            items=[{'x': 20, 'y': 30, 'z': 40, 'copies': 6, 'weight': 5.0, 'stackability_id': 0,
                    'maximum_stackability': 3, 'maximum_weight_above': 100.0}],
        )
        raw = _core.boxstacks_solve(payload, {'time_limit': 2.0, 'linear_programming_solver': 'highs'})
        bin_ = raw['bins'][0]
        assert len(bin_['stacks']) >= 2
        stack = bin_['stacks'][0]
        assert set(stack) == {'stack_id', 'x', 'y', 'lx', 'ly', 'lz'}
        assert (stack['lx'], stack['ly']) == (20, 30)
        first = bin_['placements'][0]
        assert set(first) >= {'stack_id', 'group_id'}
        assert first['group_id'] == 0

    def test_log_capture(self):
        raw = _core.box_solve(_payload(), {'time_limit': 1.0, 'verbosity_level': 1, 'linear_programming_solver': 'highs'})
        assert 'Solution' in raw['stdout']
        assert raw['stderr'] == ''

    def test_rotation_tokens(self):
        payload = _payload(
            bins=[{'x': 10, 'y': 90, 'z': 10, 'copies': 1}],
            items=[{'x': 90, 'y': 10, 'z': 10, 'rotations': ['YXZ']}],
            objective='knapsack',
        )
        raw = _core.box_solve(payload, {'time_limit': 1.0, 'linear_programming_solver': 'highs'})
        placement = raw['bins'][0]['placements'][0]
        assert (placement['lx'], placement['ly'], placement['lz'], placement['rotation']) == (10, 90, 10, 'YXZ')

    @pytest.mark.parametrize('payload, options, message', [
        (_payload(objective='bogus'), {}, 'unknown objective'),
        (_payload(), {'linear_programming_solver': 'nope'}, 'unknown linear programming solver'),
        (_payload(), {'optimization_mode': 'later'}, 'unknown optimization mode'),
        (_payload(items=[{'x': 1, 'y': 1, 'z': 1, 'rotations': ['XYZW']}]), {}, 'XYZW'),
    ])
    def test_bad_tokens(self, payload, options, message):
        with pytest.raises(ValueError) as exc_info:
            _core.box_solve(payload, options)
        assert message in str(exc_info.value)

    def test_upstream_builder_rejection(self):
        # Upstream's own validation: bin copies_min above copies.
        with pytest.raises(ValueError) as exc_info:
            _core.box_solve(_payload(bins=[{'x': 10, 'y': 10, 'z': 10, 'copies': 1, 'copies_min': 2}]), {})
        assert 'copies_min' in str(exc_info.value)
