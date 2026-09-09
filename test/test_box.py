import json

import pytest

from packingsolver3d import (
    BinType, Instance, ItemType, Objective, OptimizationMode, Rotation, Status, UnsupportedFeatureError, box,
)


@pytest.mark.unittest
class TestValidate:
    def test_accepts_plain(self, box_instance):
        box.validate(box_instance)

    def test_rejects_item_stacking(self, stack_instance):
        with pytest.raises(UnsupportedFeatureError) as exc_info:
            box.validate(stack_instance)
        message = str(exc_info.value)
        assert 'item stacking fields' in message
        assert 'bin stacking fields' in message
        assert 'boxstacks' in message

    def test_rejects_defects(self, defect_instance):
        with pytest.raises(UnsupportedFeatureError) as exc_info:
            box.validate(defect_instance)
        assert 'defects' in str(exc_info.value)

    def test_rejects_unloading(self, box_instance):
        from packingsolver3d import UnloadingConstraint
        instance = Instance(
            bin_types=box_instance.bin_types, item_types=box_instance.item_types,
            unloading_constraint=UnloadingConstraint.ONLY_X_MOVEMENTS,
        )
        with pytest.raises(UnsupportedFeatureError) as exc_info:
            box.solve(instance, time_limit=1.0)
        assert 'unloading constraint' in str(exc_info.value)


@pytest.mark.unittest
class TestSolve:
    def test_bin_packing(self, box_instance):
        result = box.solve(box_instance, time_limit=2.0)
        assert result.status == Status.OPTIMAL
        assert result.is_proven_optimal
        assert result.number_of_bins == 1
        assert result.value == 1.0
        assert result.bound == 1.0
        assert len(result.placements) == 10
        assert all(p.stack_id is None for p in result.placements)
        assert all(p.rotation == Rotation.XYZ for p in result.placements)
        assert result.run.returncode == 0
        assert result.run.argv[-2:] == ('--linear-programming-solver', 'highs')
        assert '--time-limit' in result.run.argv
        assert len(result.run.binary_sha256) == 64

    def test_knapsack(self, box_instance):
        instance = Instance(
            bin_types=[BinType(x=100, y=100, z=100, copies=1)],
            item_types=box_instance.item_types,
            objective=Objective.KNAPSACK,
        )
        result = box.solve(instance, time_limit=2.0)
        assert result.status == Status.OPTIMAL
        # Profit defaults to volume upstream: 6 * 24000 + 4 * 3375.
        assert result.value == 157500.0
        assert result.bound == 157500.0
        assert result.statistics['ItemProfit'] == 157500.0

    def test_rotations_honoured(self):
        # A 90x10x10 rod only fits a 10x90x10 bin if it may turn.
        oriented = Instance(
            bin_types=[BinType(x=10, y=90, z=10, copies=1)],
            item_types=[ItemType(x=90, y=10, z=10)],
            objective=Objective.KNAPSACK,
        )
        assert box.solve(oriented, time_limit=1.0).number_of_bins == 0
        turning = Instance(
            bin_types=oriented.bin_types,
            item_types=[ItemType(x=90, y=10, z=10, rotations=[Rotation.YXZ])],
            objective=Objective.KNAPSACK,
        )
        result = box.solve(turning, time_limit=1.0)
        assert result.number_of_bins == 1
        assert result.placements[0].rotation == Rotation.YXZ
        assert (result.placements[0].lx, result.placements[0].ly) == (10, 90)

    def test_switches_and_options(self, box_instance):
        result = box.solve(
            box_instance, time_limit=1.0, seed=3, verbosity_level=1,
            optimization_mode=OptimizationMode.NOT_ANYTIME,
            use_tree_search=True, use_tree_search_maximal_spaces=False,
            use_sequential_single_knapsack=False, use_sequential_value_correction=False,
            use_column_generation=False, use_dichotomic_search=False, use_dual_feasible_functions=True,
        )
        argv = result.run.argv
        pairs = list(zip(argv, argv[1:]))
        for expected in [
            ('--seed', '3'), ('--verbosity-level', '1'), ('--optimization-mode', 'not-anytime'),
            ('--use-tree-search', '1'), ('--use-tree-search-maximal-spaces', '0'),
            ('--use-sequential-single-knapsack', '0'), ('--use-sequential-value-correction', '0'),
            ('--use-column-generation', '0'), ('--use-dichotomic-search', '0'),
            ('--use-dual-feasible-functions', '1'),
        ]:
            assert expected in pairs
        assert result.run.stdout, 'verbosity 1 must leave a log on stdout'
        assert result.status == Status.OPTIMAL

    def test_to_json(self, box_instance):
        document = json.loads(box.solve(box_instance, time_limit=1.0).to_json())
        assert document['status'] == 'optimal'
        assert document['objective'] == 'bin-packing'
        assert len(document['bins']) == 1
        assert len(document['bins'][0]['placements']) == 10
        assert 'run' not in document, 'RunRecord carries absolute paths and stays out of golden files'
