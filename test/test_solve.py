import pytest

from packingsolver3d import (
    BinType, Instance, InvalidInstanceError, ItemType, Objective, OptimizationMode, PackedBin, ProgressEvent, Rotation,
    SolverFailedError, Status,
)
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
        assert _solve.core_options() == {'verbosity_level': 0, 'linear_programming_solver': 'highs'}

    def test_all_options(self):
        options = _solve.core_options(
            time_limit=3, memory_limit=512, verbosity_level=2,
            optimization_mode=OptimizationMode.NOT_ANYTIME, linear_programming_solver='clp',
        )
        assert options == {
            'verbosity_level': 2, 'linear_programming_solver': 'clp',
            'time_limit': 3.0, 'memory_limit': 512, 'optimization_mode': 'not-anytime',
        }

    def test_stop_when_unimproved(self):
        options = _solve.core_options(stop_when_unimproved_for=5, stop_when_unimproved_after=10)
        assert options['stop_when_unimproved_for'] == 5.0 and options['stop_when_unimproved_after'] == 10.0
        assert 'stop_when_unimproved_after' not in _solve.core_options(stop_when_unimproved_for=5)
        assert _solve.core_options(stop_when_unimproved_for=5, stop_when_unimproved_ratio=2)['stop_when_unimproved_ratio'] == 2.0
        assert 'stop_when_unimproved_ratio' not in _solve.core_options(stop_when_unimproved_for=5)

    @pytest.mark.parametrize('kwargs, message', [
        (dict(stop_when_unimproved_for=0), 'must be positive'),
        (dict(stop_when_unimproved_for=-1.5), 'must be positive'),
        (dict(stop_when_unimproved_after=3), 'needs stop_when_unimproved_for'),
        (dict(stop_when_unimproved_for=2, stop_when_unimproved_after=-1), 'must not be negative'),
        (dict(stop_when_unimproved_ratio=2), 'needs stop_when_unimproved_for'),
        (dict(stop_when_unimproved_for=2, stop_when_unimproved_ratio=0), 'must be positive'),
    ])
    def test_stop_when_unimproved_validation(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            _solve.core_options(**kwargs)


@pytest.mark.unittest
class TestSolveInstance:
    def test_result_and_record(self, box_instance):
        options = _solve.core_options(time_limit=2.0)
        result = _solve.solve_instance('box', box_instance, options)
        assert isinstance(result, Result)
        assert result.status == Status.OPTIMAL
        assert result.solve_time is not None and result.solve_time >= 0
        assert result.statistics['NumberOfItems'] == 10
        assert result.objective == Objective.BIN_PACKING
        assert result.run.problem_type == 'box'
        assert result.run.options == options
        assert result.run.options is not options
        assert result.run.stdout == '' and result.run.stderr == ''
        assert result.run.wall_time >= 0  # a sub-millisecond solve may round to zero

    def test_decode_bins_numbering(self):
        raw = [
            {'bin_type_id': 1, 'copies': 2, 'x': 5, 'y': 6, 'z': 7, 'stacks': [],
             'placements': [{'item_type_id': 3, 'x': 0, 'y': 1, 'z': 2, 'lx': 1, 'ly': 1, 'lz': 1, 'rotation': 'ZYX'}]},
            {'bin_type_id': 0, 'copies': 1, 'x': 5, 'y': 6, 'z': 7,
             'stacks': [{'stack_id': 0, 'x': 0, 'y': 0, 'lx': 1, 'ly': 1, 'lz': 4}],
             'placements': [{'item_type_id': 0, 'x': 0, 'y': 0, 'z': 0, 'lx': 1, 'ly': 1, 'lz': 4, 'rotation': 'XYZ',
                             'stack_id': 0, 'group_id': 2}]},
        ]
        bins = _solve._decode_bins(raw)
        assert [b.bin_id for b in bins] == [0, 1]
        assert bins[0].placements[0].bin_id == 0
        assert bins[0].placements[0].rotation == Rotation.ZYX
        assert bins[0].placements[0].stack_id is None
        assert bins[1].stacks[0].bin_id == 1
        assert bins[1].placements[0].group_id == 2

    def test_upstream_rejection_is_typed(self, box_instance, monkeypatch):
        def reject(payload, options):
            raise ValueError('InstanceBuilder::build: item type 0 has copies_min > copies')
        monkeypatch.setattr(_solve, '_solver', lambda problem_type: reject)
        with pytest.raises(InvalidInstanceError) as exc_info:
            _solve.solve_instance('box', box_instance, _solve.core_options())
        assert 'copies_min' in str(exc_info.value)

    def test_upstream_failure_is_typed(self, box_instance, monkeypatch):
        def fail(payload, options):
            raise RuntimeError('ERROR, no linear programming solver found')
        monkeypatch.setattr(_solve, '_solver', lambda problem_type: fail)
        with pytest.raises(SolverFailedError) as exc_info:
            _solve.solve_instance('box', box_instance, _solve.core_options())
        assert 'no linear programming solver' in str(exc_info.value)
        assert exc_info.value.run.problem_type == 'box'
        assert exc_info.value.run.options == _solve.core_options()

    def test_unknown_problem_type(self, box_instance):
        with pytest.raises(AttributeError):
            _solve.solve_instance('rectangle', box_instance, _solve.core_options())

    def test_missing_extension_message(self, monkeypatch):
        import builtins
        real_import = builtins.__import__

        def no_core(name, globals=None, locals=None, fromlist=(), level=0):
            if level and fromlist and '_core' in fromlist:
                raise ImportError('No module named packingsolver3d._core')
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, '__import__', no_core)
        with pytest.raises(ImportError) as exc_info:
            _solve._solver('box')
        assert 'make build' in str(exc_info.value)

    def test_no_solution_when_nothing_is_mandatory(self):
        # copies_min=0 on every item under bin packing: zero bins is the optimum,
        # and upstream reports it as an empty solution.
        instance = Instance(
            bin_types=[BinType(x=100, y=100, z=100)],
            item_types=[ItemType(x=20, y=30, z=40, copies=6, copies_min=0)],
            objective=Objective.BIN_PACKING,
        )
        result = _solve.solve_instance('box', instance, _solve.core_options(time_limit=1.0))
        assert result.status == Status.NO_SOLUTION
        assert result.number_of_bins == 0
        assert result.placements == ()


@pytest.mark.unittest
class TestConcurrency:
    def test_concurrent_solves(self, box_instance):
        # The bridge used to swap std::cout's buffer per call, which crashed under concurrency; the log now
        # goes through upstream's own per-call stream, so many threads may solve at once.
        import threading
        from packingsolver3d import box
        results, errors = [], []

        def work():
            try:
                for _ in range(2):
                    results.append(box.solve(box_instance, time_limit=0.5).number_of_bins)
            except Exception as err:  # pragma: no cover - a failure here is the finding
                errors.append(err)

        threads = [threading.Thread(target=work) for _ in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert not errors
        assert len(results) == 32
        assert set(results) == {1}


class _Boom(Exception):
    pass


@pytest.mark.unittest
class TestProgressCallback:
    def test_events_are_snapshots(self, box_instance):
        events = []
        result = _solve.solve_instance('box', box_instance, _solve.core_options(time_limit=2.0), progress_callback=events.append)
        assert events and all(isinstance(event, ProgressEvent) for event in events)
        assert events[-1].number_of_items == len(result.placements)
        assert 'progress_callback' not in result.run.options
        assert result.run.stop_reason is None

    def test_false_stops_and_is_recorded(self, container_stack_instance):
        result = _solve.solve_instance('boxstacks', container_stack_instance, _solve.core_options(time_limit=20.0),
                                       progress_callback=lambda event: False)
        assert result.run.stop_reason == 'callback'
        assert result.run.wall_time < 10.0
        assert len(result.placements) > 0

    def test_exception_is_reraised_unchanged(self, container_stack_instance):
        def explode(event):
            raise _Boom('mine')
        with pytest.raises(_Boom, match='mine'):
            _solve.solve_instance('boxstacks', container_stack_instance, _solve.core_options(time_limit=20.0),
                                  progress_callback=explode)

    def test_value_error_is_not_mistaken_for_upstream(self, box_instance):
        def explode(event):
            raise ValueError('not from InstanceBuilder')
        with pytest.raises(ValueError, match='not from InstanceBuilder'):
            _solve.solve_instance('box', box_instance, _solve.core_options(time_limit=2.0), progress_callback=explode)


@pytest.mark.unittest
class TestForwardProgress:
    EVENT = {'time': 0.5, 'number_of_items': 7, 'number_of_bins': 1, 'profit': 7.0, 'cost': 1.0, 'label': 'TSMS n 1'}

    def test_none_and_true_continue(self):
        seen, failure = [], []
        forward = _solve._forward_progress(seen.append, failure)
        assert forward(dict(self.EVENT)) is True
        assert forward(dict(self.EVENT)) is True
        assert len(seen) == 2 and isinstance(seen[0], ProgressEvent) and seen[0].label == 'TSMS n 1'
        assert failure == []

    def test_false_stops_and_later_events_are_not_delivered(self):
        seen, failure = [], []
        forward = _solve._forward_progress(lambda event: seen.append(event) is None and False, failure)
        assert forward(dict(self.EVENT)) is False
        assert forward(dict(self.EVENT)) is False
        assert len(seen) == 1
        assert failure == []

    def test_exception_is_kept_and_stops(self):
        seen, failure = [], []

        def explode(event):
            seen.append(event)
            raise _Boom('kept')

        forward = _solve._forward_progress(explode, failure)
        assert forward(dict(self.EVENT)) is False
        assert forward(dict(self.EVENT)) is False
        assert len(seen) == 1
        assert len(failure) == 1 and isinstance(failure[0], _Boom)
