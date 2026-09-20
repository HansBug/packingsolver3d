import json
import time

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
        assert set(raw) == {'output', 'stdout', 'stderr', 'bins', 'stop_reason'}
        assert raw['stop_reason'] is None
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

    # A 90 x 10 x 10 rod placed under each rotation, in a bin shaped for it;
    # the extents follow upstream's ItemType::x/y/z(Rotation) tables.
    @pytest.mark.parametrize('rotation, bin_dims, extents', [
        ('XYZ', (90, 10, 10), (90, 10, 10)),
        ('YXZ', (10, 90, 10), (10, 90, 10)),
        ('ZYX', (10, 10, 90), (10, 10, 90)),
        ('YZX', (10, 10, 90), (10, 10, 90)),
        ('XZY', (90, 10, 10), (90, 10, 10)),
        ('ZXY', (10, 90, 10), (10, 90, 10)),
    ])
    def test_every_rotation(self, rotation, bin_dims, extents):
        payload = _payload(
            bins=[{'x': bin_dims[0], 'y': bin_dims[1], 'z': bin_dims[2], 'copies': 1}],
            items=[{'x': 90, 'y': 10, 'z': 10, 'rotations': [rotation]}],
            objective='knapsack',
        )
        raw = _core.box_solve(payload, {'time_limit': 1.0, 'linear_programming_solver': 'highs'})
        placement = raw['bins'][0]['placements'][0]
        assert (placement['lx'], placement['ly'], placement['lz']) == extents
        assert placement['rotation'] == rotation
        # boxstacks keeps z vertical: only the two upright rotations are placed;
        # the others are refused by boxstacks.validate before reaching the bridge.
        if rotation in ('XYZ', 'YXZ'):
            raw = _core.boxstacks_solve(payload, {'time_limit': 1.0, 'linear_programming_solver': 'highs'})
            placement = raw['bins'][0]['placements'][0]
            assert (placement['lx'], placement['ly'], placement['lz']) == extents
            assert placement['rotation'] == rotation

    def test_semi_trailer_truck(self):
        payload = _payload(
            bins=[{'x': 1360, 'y': 240, 'z': 260, 'cost': 1, 'copies': 1, 'maximum_weight': 24000.0,
                   'maximum_stack_density': 1000.0,
                   'semi_trailer_truck': {
                       'tractor_weight': 8000.0, 'front_axle_middle_axle_distance': 380,
                       'front_axle_tractor_gravity_center_distance': 100, 'front_axle_harness_distance': 320,
                       'empty_trailer_weight': 6000.0, 'harness_rear_axle_distance': 800,
                       'trailer_gravity_center_rear_axle_distance': 400, 'trailer_start_harness_distance': 100,
                       'rear_axle_maximum_weight': 20000.0, 'middle_axle_maximum_weight': 9300.0}}],
            items=[{'x': 100, 'y': 200, 'z': 200, 'weight': 100.0, 'copies': 2, 'stackability_id': 0,
                    'maximum_stackability': 1}],
        )
        raw = _core.boxstacks_solve(payload, {'time_limit': 2.0, 'linear_programming_solver': 'highs'})
        assert json.loads(raw['output'])['Solution']['NumberOfItems'] == 2

    def test_semi_trailer_truck_check(self):
        # Upstream's SemiTrailerTruckData::check rejects a truck without geometry.
        payload = _payload(bins=[{'x': 10, 'y': 10, 'z': 10, 'semi_trailer_truck': {'tractor_weight': 1.0}}])
        with pytest.raises(ValueError):
            _core.boxstacks_solve(payload, {})

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


def _container_payload():
    cargo = [(530, 290, 370, 300, 8), (530, 230, 290, 300, 6), (430, 210, 270, 400, 4), (1200, 800, 1200, 24, 450),
             (1200, 1000, 1150, 12, 1100)]
    return _payload(
        objective='knapsack',
        bins=[{'x': 12032, 'y': 2352, 'z': 2698, 'cost': 1, 'copies': 1, 'maximum_weight': 26460.0}],
        items=[{'x': x, 'y': y, 'z': z, 'copies': c, 'weight': float(w), 'rotations': ['XYZ', 'YXZ'], 'stackability_id': i}
               for i, (x, y, z, c, w) in enumerate(cargo)],
    )


@pytest.mark.unittest
class TestProgressCallback:
    OPTIONS = {'linear_programming_solver': 'highs'}

    def test_events_are_plain_dicts(self):
        events = []
        raw = _core.box_solve(_payload(), dict(self.OPTIONS, time_limit=2.0, progress_callback=events.append))
        assert events
        assert set(events[0]) == {'time', 'number_of_items', 'number_of_bins', 'profit', 'cost', 'label'}
        assert isinstance(events[0]['label'], str)
        assert events[-1]['number_of_items'] == json.loads(raw['output'])['Solution']['NumberOfItems']
        assert raw['stop_reason'] is None

    def test_none_callback_is_ignored(self):
        raw = _core.box_solve(_payload(), dict(self.OPTIONS, progress_callback=None))
        assert raw['stop_reason'] is None

    def test_returning_false_stops_the_solve(self):
        # Without the callback this anytime solve runs to its 20 s limit.
        started = time.perf_counter()
        raw = _core.boxstacks_solve(_container_payload(), dict(self.OPTIONS, time_limit=20.0, progress_callback=lambda event: False))
        assert time.perf_counter() - started < 10.0
        assert raw['stop_reason'] == 'callback'
        assert json.loads(raw['output'])['Solution']['NumberOfItems'] > 0

    def test_exception_stops_and_propagates(self):
        def explode(event):
            raise KeyError('from the callback')
        started = time.perf_counter()
        with pytest.raises(KeyError, match='from the callback'):
            _core.box_solve(_container_payload(), dict(self.OPTIONS, time_limit=20.0, progress_callback=explode))
        assert time.perf_counter() - started < 10.0


@pytest.mark.unittest
class TestStopWhenUnimproved:
    OPTIONS = {'linear_programming_solver': 'highs'}

    def test_stops_once_the_incumbent_stalls(self):
        # boxstacks improves at ~0.2 s, ~0.7 s, ~2 s and then only after a long pass: a one-second patience
        # ends the solve long before the 30 s limit, with a solution.
        started = time.perf_counter()
        raw = _core.boxstacks_solve(_container_payload(), dict(self.OPTIONS, time_limit=30.0, stop_when_unimproved_for=1.0))
        assert time.perf_counter() - started < 15.0
        assert raw['stop_reason'] == 'unimproved'
        assert json.loads(raw['output'])['Solution']['NumberOfItems'] > 0

    def test_after_delays_the_stop(self):
        started = time.perf_counter()
        raw = _core.boxstacks_solve(_container_payload(), dict(self.OPTIONS, time_limit=30.0, stop_when_unimproved_for=0.5,
                                                              stop_when_unimproved_after=3.0))
        elapsed = time.perf_counter() - started
        assert 3.0 <= elapsed < 15.0
        assert raw['stop_reason'] == 'unimproved'

    def test_callback_stop_takes_precedence(self):
        # The callback stops the run at its first event; the watchdog must not get there first, so it is held back
        # until well after the first solution (which took more than its 1 s patience on a slow macOS runner once).
        events = []

        def stop_at_once(event):
            events.append(event)
            return False

        raw = _core.boxstacks_solve(_container_payload(), dict(self.OPTIONS, time_limit=30.0, stop_when_unimproved_for=1.0,
                                                              stop_when_unimproved_after=15.0, progress_callback=stop_at_once))
        assert raw['stop_reason'] == 'callback'
        assert len(events) == 1

    def test_watchdog_and_callback_together(self):
        events = []
        raw = _core.boxstacks_solve(_container_payload(), dict(self.OPTIONS, time_limit=30.0, stop_when_unimproved_for=1.0,
                                                              progress_callback=events.append))
        assert raw['stop_reason'] == 'unimproved'
        assert events and events[-1]['number_of_items'] == json.loads(raw['output'])['Solution']['NumberOfItems']

    def test_ratio_waits_for_the_first_solution_and_scales_the_patience(self):
        # boxstacks on the container reports its first solution within a second; with a ratio the watchdog cannot
        # fire before it, and afterwards waits ratio x (time of the last improvement), at least the floor.
        events = []
        started = time.perf_counter()
        result = _core.boxstacks_solve(_container_payload(), {
            'time_limit': 30.0, 'linear_programming_solver': 'highs', 'optimization_mode': 'anytime',
            'stop_when_unimproved_for': 0.5, 'stop_when_unimproved_ratio': 0.5,
            'progress_callback': lambda event: events.append(event['time']) or None})
        wall = time.perf_counter() - started
        assert result['stop_reason'] == 'unimproved'
        assert events, 'a ratio never stops a run before its first solution'
        assert sum(len(b['placements']) for b in result['bins']) > 0
        assert wall >= events[-1] + max(0.5, 0.5 * events[-1]) - 0.2
        assert wall < 30.0

    def test_not_triggered_when_the_solve_ends_first(self):
        raw = _core.box_solve(_payload(), dict(self.OPTIONS, time_limit=2.0, stop_when_unimproved_for=5.0))
        assert raw['stop_reason'] is None
        assert json.loads(raw['output'])['Solution']['NumberOfItems'] == 6
