import json
import os

import pytest

from packingsolver3d import BinType, Instance, ItemType, Objective, OptimizationMode, PackedBin, Status
from packingsolver3d import _solve
from packingsolver3d.result import Result

_BIN = PackedBin(bin_id=0, bin_type_id=0, copies=1, x=10, y=10, z=10, placements=(), stacks=())


@pytest.mark.unittest
class TestNumber:
    @pytest.mark.parametrize('value, expected', [
        (1, 1.0), (2.5, 2.5), (0, 0.0), (None, None), ('3', None), (True, None),
        (float('nan'), None), (float('inf'), None), (-float('inf'), None),
    ])
    def test_cases(self, value, expected):
        assert _solve._number(value) == expected


@pytest.mark.unittest
class TestReadOutput:
    def test_missing(self, tmp_path):
        assert _solve._read_output(str(tmp_path / 'none.json')) == {}

    def test_invalid(self, tmp_path):
        path = tmp_path / 'bad.json'
        path.write_text('{not json')
        assert _solve._read_output(str(path)) == {}

    def test_no_output_block(self, tmp_path):
        path = tmp_path / 'odd.json'
        path.write_text(json.dumps({'Output': [1, 2]}))
        assert _solve._read_output(str(path)) == {}

    def test_valid(self, tmp_path):
        path = tmp_path / 'ok.json'
        path.write_text(json.dumps({'Output': {'Time': 1.5, 'Solution': {'NumberOfBins': 1}}}))
        assert _solve._read_output(str(path)) == {'Time': 1.5, 'Solution': {'NumberOfBins': 1}}


@pytest.mark.unittest
class TestClassify:
    def test_infeasible(self):
        output = {'IsProvenInfeasible': True, 'Solution': {'NumberOfItems': 3}}
        assert _solve._classify(Objective.BIN_PACKING, output, (_BIN,)) == (Status.INFEASIBLE, None, None)

    def test_no_solution(self):
        assert _solve._classify(Objective.BIN_PACKING, {}, ()) == (Status.NO_SOLUTION, None, None)
        output = {'Solution': {'NumberOfItems': 0, 'NumberOfBins': 0}}
        assert _solve._classify(Objective.BIN_PACKING, output, (_BIN,)) == (Status.NO_SOLUTION, None, None)

    def test_bin_packing_optimal(self):
        output = {'BinPackingBound': 1, 'Solution': {'NumberOfItems': 10, 'NumberOfBins': 1}}
        assert _solve._classify(Objective.BIN_PACKING, output, (_BIN,)) == (Status.OPTIMAL, 1.0, 1.0)

    def test_bin_packing_gap(self):
        output = {'BinPackingBound': 1, 'Solution': {'NumberOfItems': 10, 'NumberOfBins': 2}}
        assert _solve._classify(Objective.BIN_PACKING, output, (_BIN,)) == (Status.FEASIBLE, 2.0, 1.0)

    def test_knapsack_sense(self):
        output = {'KnapsackBound': 12, 'Solution': {'NumberOfItems': 3, 'ItemProfit': 12}}
        assert _solve._classify(Objective.KNAPSACK, output, (_BIN,)) == (Status.OPTIMAL, 12.0, 12.0)
        output['Solution']['ItemProfit'] = 10
        assert _solve._classify(Objective.KNAPSACK, output, (_BIN,)) == (Status.FEASIBLE, 10.0, 12.0)

    def test_missing_bound_never_optimal(self):
        output = {'KnapsackBound': None, 'Solution': {'NumberOfItems': 10, 'NumberOfBins': 1}}
        assert _solve._classify(Objective.BIN_PACKING, output, (_BIN,)) == (Status.FEASIBLE, 1.0, None)

    def test_feasibility(self):
        output = {'Solution': {'NumberOfItems': 10, 'NumberOfUnpackedItems': 0}}
        assert _solve._classify(Objective.FEASIBILITY, output, (_BIN,)) == (Status.OPTIMAL, 0.0, None)
        output['Solution']['NumberOfUnpackedItems'] = 2
        assert _solve._classify(Objective.FEASIBILITY, output, (_BIN,)) == (Status.FEASIBLE, 2.0, None)

    def test_objective_without_metrics(self):
        others = [o for o in Objective if o not in _solve._OBJECTIVE_METRICS and o != Objective.FEASIBILITY]
        assert others, 'expected at least one objective without a reported bound'
        output = {'BinPackingBound': 1, 'Solution': {'NumberOfItems': 10, 'NumberOfBins': 1}}
        for objective in others:
            assert _solve._classify(objective, output, (_BIN,)) == (Status.FEASIBLE, None, None)


@pytest.mark.unittest
class TestCoreOptions:
    def test_always_pins_lp_solver(self):
        assert _solve.core_options() == ['--verbosity-level', '0', '--linear-programming-solver', 'highs']

    def test_all_options(self):
        options = _solve.core_options(
            seed=7, verbosity_level=2, optimization_mode=OptimizationMode.NOT_ANYTIME,
            linear_programming_solver='clp',
        )
        assert options == [
            '--verbosity-level', '2', '--linear-programming-solver', 'clp',
            '--seed', '7', '--optimization-mode', 'not-anytime',
        ]


@pytest.mark.unittest
class TestSolveInstance:
    def test_keep_files(self, box_instance, tmp_path):
        keep = tmp_path / 'kept'
        result = _solve.solve_instance(
            'box', box_instance, options=_solve.core_options(), time_limit=2.0, keep_files=str(keep),
        )
        assert isinstance(result, Result)
        assert result.status == Status.OPTIMAL
        assert sorted(os.listdir(str(keep))) == [
            'bins.csv', 'certificate.csv', 'items.csv', 'output.json', 'parameters.csv',
        ]
        assert result.solve_time is not None and result.solve_time >= 0
        assert result.statistics['NumberOfItems'] == 10
        assert result.objective == Objective.BIN_PACKING

    def test_temporary_directory_removed(self, box_instance, tmp_path, monkeypatch):
        monkeypatch.setattr(_solve.tempfile, 'tempdir', str(tmp_path))
        _solve.solve_instance('box', box_instance, options=_solve.core_options(), time_limit=1.0)
        assert os.listdir(str(tmp_path)) == []

    def test_no_solution_when_nothing_is_mandatory(self, tmp_path):
        # copies_min=0 on every item under bin packing: zero bins is the optimum,
        # and upstream reports it as an empty solution.
        instance = Instance(
            bin_types=[BinType(x=100, y=100, z=100)],
            item_types=[ItemType(x=20, y=30, z=40, copies=6, copies_min=0)],
            objective=Objective.BIN_PACKING,
        )
        result = _solve.solve_instance('box', instance, options=_solve.core_options(), time_limit=1.0)
        assert result.status == Status.NO_SOLUTION
        assert result.number_of_bins == 0
        assert result.placements == ()
