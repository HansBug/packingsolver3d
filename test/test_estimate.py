import math

import pytest

from packingsolver3d import BinType, Instance, ItemType, Objective, TimeBudget, algorithm_path, count_stacks, \
    instance_features, recommend_time_budget
from packingsolver3d import _time_budget_constants as constants
from packingsolver3d import estimate


def _instance(items, bins, objective=Objective.KNAPSACK):
    return Instance(bin_types=bins, item_types=items, objective=objective)


@pytest.mark.unittest
class TestCountStacks:
    def test_full_height_and_capped(self):
        instance = _instance(
            [ItemType(x=530, y=290, z=370, copies=14), ItemType(x=430, y=210, z=270, copies=20, maximum_stackability=3)],
            [BinType(x=1200, y=800, z=1800)], Objective.BIN_PACKING)
        assert count_stacks(instance) == 4 + 7

    def test_tallest_bin_is_used_and_tall_items_count_per_copy(self):
        instance = _instance(
            [ItemType(x=1, y=1, z=10, copies=5), ItemType(x=1, y=1, z=30, copies=3)],
            [BinType(x=10, y=10, z=10), BinType(x=10, y=10, z=25)])
        # 25 // 10 = 2 per stack -> 3 stacks; taller than every bin -> one stack per copy.
        assert count_stacks(instance) == 3 + 3

    def test_zero_maximum_stackability_means_unlimited(self):
        instance = _instance([ItemType(x=1, y=1, z=1, copies=4, maximum_stackability=0)], [BinType(x=10, y=10, z=10)])
        assert count_stacks(instance) == 1

    def test_container(self, container_stack_instance):
        assert count_stacks(container_stack_instance) == 43 + 34 + 45 + 12 + 6


@pytest.mark.unittest
class TestInstanceFeatures:
    def test_values(self):
        instance = _instance(
            [ItemType(x=10, y=10, z=10, copies=3), ItemType(x=20, y=10, z=10, copies=1)],
            [BinType(x=100, y=10, z=10, copies=2), BinType(x=50, y=10, z=10)], Objective.BIN_PACKING)
        f = instance_features(instance)
        assert f['n_items'] == 4 and f['n_types'] == 2 and f['n_bins'] == 3 and f['n_stacks'] == 4
        assert f['mean_copies'] == 2.0
        assert f['fill_ratio'] == pytest.approx(5000 / 10000)
        assert f['mean_items_per_bin'] == pytest.approx(10000 / 1250)


@pytest.mark.unittest
class TestAlgorithmPath:
    """Mirrors upstream's automatic selection; the thresholds are 16 / 64 mean items per bin, copies factor 1."""

    def _single(self, per_bin, objective=Objective.KNAPSACK):
        return _instance([ItemType(x=1, y=1, z=1, copies=per_bin)], [BinType(x=per_bin, y=1, z=1)], objective)

    def _multi(self, per_bin, copies, types, objective=Objective.BIN_PACKING):
        return _instance([ItemType(x=1, y=1, z=1, copies=copies) for _ in range(types)], [BinType(x=per_bin, y=1, z=1, copies=3)], objective)

    def test_single_bin_knapsack_many_items_is_tsms(self):
        assert algorithm_path(self._single(100)) == 'TSMS'
        assert algorithm_path(self._single(100, Objective.FEASIBILITY)) == 'TSMS'

    def test_single_bin_few_items_or_other_objective_is_ts(self):
        assert algorithm_path(self._single(64)) == 'TS'
        assert algorithm_path(self._single(100, Objective.BIN_PACKING)) == 'TS'

    def test_multi_bin_copy_heavy(self):
        assert algorithm_path(self._multi(per_bin=20, copies=30, types=1)) == 'SSK'
        assert algorithm_path(self._multi(per_bin=10, copies=30, types=1)) == 'SVC'

    def test_multi_bin_heterogeneous(self):
        assert algorithm_path(self._multi(per_bin=100, copies=1, types=50)) == 'SSK'
        assert algorithm_path(self._multi(per_bin=30, copies=1, types=50)) == 'TS'

    def test_boxstacks(self, container_stack_instance):
        assert algorithm_path(container_stack_instance, 'boxstacks') == 'SOR'
        assert algorithm_path(self._multi(per_bin=10, copies=3, types=2), 'boxstacks') == 'SVC'

    def test_unknown_solver(self, box_instance):
        with pytest.raises(ValueError, match='solver must be'):
            algorithm_path(box_instance, 'stacks')

    def test_matches_recorded_campaign_paths(self, container_instance):
        # The Stowly demo instance is the anchor of the campaign: box runs TSMS on it, boxstacks runs SOR.
        assert algorithm_path(container_instance, 'box') == 'TSMS'


@pytest.mark.unittest
class TestInterpolate:
    def test_clamped_outside_and_log_linear_inside(self):
        table = {1.0: 10.0, 4.0: 20.0, 8.0: 40.0}
        assert estimate._interpolate(table, 0.1) == 10.0
        assert estimate._interpolate(table, 1.0) == 10.0
        assert estimate._interpolate(table, 9.0) == 40.0
        assert estimate._interpolate(table, 2.0) == pytest.approx(15.0)
        assert estimate._interpolate(table, 4.0) == pytest.approx(20.0)
        assert estimate._interpolate(table, 8.0) == 40.0


@pytest.mark.unittest
class TestRecommendTimeBudget:
    def test_growth_path_has_an_improvement_window(self, container_instance):
        budget = recommend_time_budget(container_instance, 'box')
        assert isinstance(budget, TimeBudget)
        assert budget.path == 'TSMS' and budget.alpha == 4.0 and budget.speed == 1.0
        assert budget.improvement > 0
        assert budget.time_limit == pytest.approx(budget.latency + budget.improvement)
        assert estimate._c.MIN_LATENCY <= budget.typical_latency < budget.latency
        assert budget.stop_when_unimproved_after == pytest.approx(budget.time_limit / 2)
        assert budget.stop_when_unimproved_for == pytest.approx(max(estimate.MIN_PATIENCE, budget.improvement / 2))
        assert budget.as_options() == {
            'time_limit': budget.time_limit,
            'stop_when_unimproved_for': budget.stop_when_unimproved_for,
            'stop_when_unimproved_after': budget.stop_when_unimproved_after,
        }

    def test_block_generation_step_applies_from_four_types(self):
        few = _instance([ItemType(x=10, y=10, z=10, copies=100) for _ in range(3)], [BinType(x=1000, y=100, z=100)])
        many = _instance([ItemType(x=10, y=10, z=10, copies=75) for _ in range(4)], [BinType(x=1000, y=100, z=100)])
        assert algorithm_path(few) == algorithm_path(many) == 'TSMS'
        assert recommend_time_budget(many).latency - recommend_time_budget(few).latency > constants.PATHS[('box', 'TSMS')]['block'] * 0.9

    def test_overfull_boxstacks_waits_longer(self):
        def stacks(copies):
            return _instance([ItemType(x=100 + t, y=100, z=100, copies=copies, stackability_id=t) for t in range(10)],
                             [BinType(x=1000, y=1000, z=1000)])
        fits = recommend_time_budget(stacks(50), 'boxstacks')        # 0.5 bin volumes of cargo
        overfull = recommend_time_budget(stacks(120), 'boxstacks')   # 1.2 bin volumes: the onedimensional stage must select
        assert fits.path == overfull.path == 'SOR'
        assert fits.latency > estimate._c.MIN_LATENCY
        assert overfull.latency > fits.latency * 3

    def test_single_pass_path_is_latency_only(self, container_stack_instance):
        instance = _instance(container_stack_instance.item_types,
                             [BinType(x=12032, y=2352, z=2698, copies=4, cost=1, maximum_weight=26460)], Objective.BIN_PACKING)
        budget = recommend_time_budget(instance, 'boxstacks')
        assert budget.path == 'SVC'
        assert budget.improvement == 0.0
        assert budget.time_limit == pytest.approx(budget.latency)
        assert budget.stop_when_unimproved_after == pytest.approx(budget.latency)
        assert budget.stop_when_unimproved_for == estimate.MIN_PATIENCE

    def test_default_alpha_depends_on_the_solver(self, container_instance, container_stack_instance):
        assert estimate.DEFAULT_ALPHA == {'box': 4.0, 'boxstacks': 8.0}
        assert recommend_time_budget(container_instance, 'box').alpha == 4.0
        assert recommend_time_budget(container_instance, 'box', alpha=None).alpha == 4.0
        assert recommend_time_budget(container_stack_instance, 'boxstacks').alpha == 8.0
        assert recommend_time_budget(container_stack_instance, 'boxstacks') == recommend_time_budget(container_stack_instance, 'boxstacks', alpha=8.0)

    def test_alpha_moves_only_the_improvement_window(self, container_instance):
        balanced = recommend_time_budget(container_instance, alpha=4.0)
        quality = recommend_time_budget(container_instance, alpha=8.0)
        between = recommend_time_budget(container_instance, alpha=6.0)
        assert balanced.latency == quality.latency == between.latency
        assert balanced.improvement < between.improvement < quality.improvement
        assert recommend_time_budget(container_instance, alpha=100.0).time_limit == quality.time_limit
        assert recommend_time_budget(container_instance, alpha=0.01).improvement == recommend_time_budget(container_instance, alpha=0.25).improvement

    def test_floor_and_cap(self, box_instance):
        tiny = recommend_time_budget(box_instance, alpha=0.25)
        assert tiny.time_limit == estimate.MIN_TIME_LIMIT
        assert tiny.stop_when_unimproved_after <= tiny.time_limit
        huge = _instance([ItemType(x=10, y=10, z=10, copies=20000, stackability_id=0) for _ in range(40)],
                         [BinType(x=1000, y=1000, z=1000, copies=5)], Objective.BIN_PACKING)
        assert recommend_time_budget(huge, 'boxstacks').time_limit == estimate.MAX_TIME_LIMIT

    def test_typical_latency_keeps_the_block_step_and_drops_the_coverage_shift(self, container_instance):
        budget = recommend_time_budget(container_instance, 'box')
        entry = constants.PATHS[('box', 'TSMS')]
        assert budget.path == 'TSMS'
        # the block-generation step is a median already: only the pass term is shifted
        assert budget.latency - entry['block'] == pytest.approx((budget.typical_latency - entry['block']) * math.exp(entry['shift']))
        tiny = recommend_time_budget(_instance([ItemType(x=1, y=1, z=1, copies=2)], [BinType(x=10, y=1, z=1)]), 'boxstacks')
        assert tiny.typical_latency == tiny.latency == estimate._c.MIN_LATENCY  # both floored

    def test_speed_divides_every_duration(self, container_instance):
        base = recommend_time_budget(container_instance)
        fast = recommend_time_budget(container_instance, speed=2.0)
        assert fast.speed == 2.0
        for field in ('time_limit', 'stop_when_unimproved_for', 'stop_when_unimproved_after', 'latency', 'typical_latency', 'improvement'):
            assert getattr(fast, field) == pytest.approx(getattr(base, field) / 2)

    @pytest.mark.parametrize('kwargs, message', [
        ({'alpha': 0}, 'alpha must be positive'),
        ({'alpha': -1.0}, 'alpha must be positive'),
        ({'speed': 0.0}, 'speed must be positive'),
        ({'solver': 'stacks'}, 'solver must be'),
    ])
    def test_validation(self, box_instance, kwargs, message):
        with pytest.raises(ValueError, match=message):
            recommend_time_budget(box_instance, **kwargs)

    def test_constants_cover_every_path(self):
        assert {key[1] for key in constants.PATHS} == {'TSMS', 'TS', 'SSK', 'SVC', 'SOR'}
        for key, entry in constants.PATHS.items():
            assert set(entry['m']) == set(entry['add']) == set(constants.ALPHAS)
            assert len(entry['beta']) == (4 if key[1] == 'SOR' else 3)
            assert all(value >= 0 for value in entry['beta'][1:])
            assert entry['shift'] >= 0 and entry['scale'] > 0
            assert entry['growth'] == (key[1] in estimate._GROWTH_PATHS)

    def test_budget_feeds_solve(self, box_instance):
        from packingsolver3d import box
        result = box.solve(box_instance, **recommend_time_budget(box_instance, alpha=0.25).as_options())
        assert result.placements
