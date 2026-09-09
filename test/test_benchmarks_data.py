"""The benchmark data shipped with the docs stays consistent: every stored solution passes the independent checker."""
import json
import os

import pytest

pytest.importorskip('tools.make_benchmarks')
from tools import make_benchmarks as mb

pytestmark = pytest.mark.skipif(not os.path.isdir(mb.UPSTREAM_DATA), reason='upstream instance files (submodule) are not checked out')


def _entries(name):
    with open(os.path.join(mb.DATA_DIR, name)) as handle:
        return json.load(handle)['results']


@pytest.mark.parametrize('entry', _entries('ours.json'), ids=lambda e: '%s/%s' % (e['benchmark'], e['case']))
def test_our_solutions_are_valid_and_consistent(entry):
    instance, profits, pose = mb.load_case(entry['benchmark'], entry['case'])
    errors, objective, bins_used, placed = mb.check(instance, profits, entry['placements'], pose,
                                                    complete=mb.BENCHMARKS[entry['benchmark']]['sense'] == 'min')
    assert errors == []
    assert objective == pytest.approx(entry['value'])
    assert placed == entry['items']


@pytest.mark.parametrize('entry', [e for e in _entries('third_party.json') if e.get('placements')],
                         ids=lambda e: '%s/%s/%s' % (e['benchmark'], e['case'], e['participant']))
def test_third_party_solutions_are_checked_not_trusted(entry):
    instance, profits, pose = mb.load_case(entry['benchmark'], entry['case'])
    errors, objective, bins_used, placed = mb.check(instance, profits, entry['placements'], entry['pose'],
                                                    complete=mb.BENCHMARKS[entry['benchmark']]['sense'] == 'min')
    assert bool(errors) == bool(entry.get('invalid')), errors[:3]


def test_every_case_has_our_result():
    have = {(e['benchmark'], e['case']) for e in _entries('ours.json')}
    want = {(b, c) for b, spec in mb.BENCHMARKS.items() for c in spec['cases']}
    assert have == want


def test_cube_case_matches_proven_optimum():
    entry = next(e for e in _entries('ours.json') if e['case'] == 'ep3d-20-C-C-50')
    assert entry['value'] == 1388961.0
    assert entry['items'] == 14
