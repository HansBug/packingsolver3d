"""
Solve the benchmark cases with packingsolver3d, re-check every solution (ours
and the third-party ones shipped in ``tools/benchmarks/third_party.json``) with
an independent geometry validator, and render the leaderboard pages (from
``docs/source/benchmarks/leaderboards/index*.rst.in``) and the gallery figures used by ``docs/source/benchmarks``.

The three benchmarks are small public instance families with a known or
proven optimum for most cases: Egeblad & Pisinger 3D knapsack (20 items),
Martello-Pisinger-Vigo generator class 9 (30 items, three bins by
construction) and Ivancic-Mathur-Mohanty THPACK9 (47 to 99 items). Third-party
solutions are stored as placements, never as numbers, so every objective in
the tables is recomputed here from the same instance files.

Example::

    python -m tools.make_benchmarks --solve     # box.solve on every case -> tools/benchmarks/ours.json
    python -m tools.make_benchmarks --render    # RST tables + figures from ours.json and third_party.json
"""

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

from packingsolver3d import ALL_ROTATIONS, BinType, Instance, ItemType, Objective, Rotation, box
from packingsolver3d.result import PackedBin, Placement, Result, Status

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'tools', 'benchmarks')
UPSTREAM_DATA = os.path.join(ROOT, 'upstream', 'packingsolver', 'data', 'box')
FIGURE_DIR = os.path.join(ROOT, 'docs', 'source', '_static', 'benchmarks')
OURS = 'packingsolver3d'
TOLERANCE = 1e-6

#: Every participant: display name, link, role and the bilingual roster facts.
def _p(name, url, role, language, version, method, driven):
    return dict(name=name, url=url, role=role, language=language, version=version, method=method, driven=driven)


UN = 'https://github.com/iyulab/U-Nesting'
PARTICIPANTS = OrderedDict([
    (OURS, _p('packingsolver3d (PackingSolver box)', 'https://github.com/HansBug/packingsolver3d', 'participant',
              {'en': 'C++ core, Python API', 'zh': 'C++ 核心，Python API'}, 'upstream commit a7e53303',
              {'en': 'anytime portfolio: iterative beam search on an insertion branching scheme, dual-feasible-function bounds; sequential single knapsack, sequential value correction, column generation and dichotomic search for several bins',
               'zh': 'anytime 组合：插入分支方案上的迭代束搜索、对偶可行函数界；多箱时叠加顺序单背包、顺序价值修正、列生成与二分搜索'},
              {'en': 'box.solve, time_limit=10.0, memory_limit=1024, default options', 'zh': 'box.solve，time_limit=10.0，memory_limit=1024，其余默认'})),
    ('py3dbp', _p('py3dbp', 'https://github.com/enzoruiz/3dbinpacking', 'participant', {'en': 'Python', 'zh': 'Python'}, '1.1.2 (PyPI)',
                  {'en': 'pivot-point greedy heuristic (Dube & Kanavathy): items by volume, first fitting pivot, six orientations tried', 'zh': '枢轴点贪心启发式（Dube 与 Kanavathy）：物品按体积排序，放到第一个可容纳的枢轴点，尝试六种朝向'},
                  {'en': 'best of two item orders, distribute_items=True, always rotates', 'zh': '两种物品顺序取较好者，distribute_items=True，总是旋转'})),
    ('jerry', _p('jerry800416/3D-bin-packing', 'https://github.com/jerry800416/3D-bin-packing', 'participant', {'en': 'Python', 'zh': 'Python'}, 'commit 75764a2',
                 {'en': 'py3dbp fork: pivot-point greedy plus fix-point gravity drop, optional stability and load-bearing checks', 'zh': 'py3dbp 的 fork：枢轴点贪心加定点重力下落，可选稳定性与承重检查'},
                 {'en': 'fix_point=True, check_stable=False, best of two item orders, always rotates', 'zh': 'fix_point=True，check_stable=False，两种顺序取较好者，总是旋转'})),
    ('go_bp3d', _p('gedex/bp3d', 'https://github.com/gedex/bp3d', 'participant', {'en': 'Go', 'zh': 'Go'}, 'commit 0ba3dcd',
                   {'en': 'Go port of the pivot-point greedy heuristic (after bom-d-van/binpacking), float64 geometry', 'zh': '枢轴点贪心启发式的 Go 移植（源自 bom-d-van/binpacking），float64 几何'},
                   {'en': 'one greedy pass, cannot fix the orientation', 'zh': '一次贪心遍历，无法固定朝向'})),
    ('rust_extreme_point', _p('U-Nesting ExtremePoint', UN, 'participant', {'en': 'Rust', 'zh': 'Rust'}, '0.9.0, commit 8cde85b',
                              {'en': 'extreme-point constructive heuristic (Crainic, Perboli & Tadei style)', 'zh': '极点构造式启发式（Crainic、Perboli 与 Tadei 思路）'},
                              {'en': 'single-container API repeated per bin, fixed pose honoured', 'zh': '单容器 API 逐箱重复调用，遵守固定姿态'})),
    ('rust_layer', _p('U-Nesting BottomLeftFill', UN, 'participant', {'en': 'Rust', 'zh': 'Rust'}, '0.9.0, commit 8cde85b',
                      {'en': 'layer-building bottom-left-fill constructive heuristic', 'zh': '分层构建的左下填充构造式启发式'},
                      {'en': 'single-container API repeated per bin, fixed pose honoured', 'zh': '单容器 API 逐箱重复调用，遵守固定姿态'})),
    ('rust_ga', _p('U-Nesting GA', UN, 'participant', {'en': 'Rust', 'zh': 'Rust'}, '0.9.0, commit 8cde85b',
                   {'en': 'genetic algorithm over item sequences, constructive decoder', 'zh': '作用于物品序列的遗传算法，构造式解码'},
                   {'en': 'single-container API repeated per bin, 10 s per call, fixed pose honoured', 'zh': '单容器 API 逐箱重复调用，每次 10 s，遵守固定姿态'})),
    ('rust_brkga', _p('U-Nesting BRKGA', UN, 'participant', {'en': 'Rust', 'zh': 'Rust'}, '0.9.0, commit 8cde85b',
                      {'en': 'biased random-key genetic algorithm over item sequences', 'zh': '作用于物品序列的偏置随机键遗传算法'},
                      {'en': 'single-container API repeated per bin, 10 s per call, fixed pose honoured', 'zh': '单容器 API 逐箱重复调用，每次 10 s，遵守固定姿态'})),
    ('rust_sa', _p('U-Nesting SA', UN, 'participant', {'en': 'Rust', 'zh': 'Rust'}, '0.9.0, commit 8cde85b',
                   {'en': 'simulated annealing over item sequences', 'zh': '作用于物品序列的模拟退火'},
                   {'en': 'single-container API repeated per bin, 10 s per call, fixed pose honoured', 'zh': '单容器 API 逐箱重复调用，每次 10 s，遵守固定姿态'})),
    ('cp_sat', _p('OR-Tools CP-SAT exact model', 'https://developers.google.com/optimization/cp/cp_solver', 'reference',
                  {'en': 'C++ core, Python API', 'zh': 'C++ 核心，Python API'}, 'OR-Tools 9.15',
                  {'en': 'exact constraint-programming model of the fixed-pose 3D knapsack: optional intervals per axis, pairwise non-overlap, maximise profit', 'zh': '固定姿态三维背包的精确约束规划模型：每轴可选区间、两两不重叠、最大化利润'},
                  {'en': '20 s, one thread, 4 GiB; OPTIMAL status is the proof used in the bound row', 'zh': '20 s、单线程、4 GiB；OPTIMAL 状态即理论界一行采用的证明'})),
    ('mpv_official', _p('Martello-Pisinger-Vigo 3dbpp.c', 'http://hjemmesider.diku.dk/~pisinger/codes.html', 'reference', {'en': 'C', 'zh': 'C'}, 'new3dbpp general-packing code',
                        {'en': 'branch-and-bound over bin assignments with an exact one-bin routine and lower bounds', 'zh': '对箱分配的分支定界，带单箱精确子程序与下界'},
                        {'en': '1 s, one thread, generator default parameters; reports a lower and an upper bound', 'zh': '1 s、单线程、生成器默认参数；报告下界与上界'})),
])

BENCHMARKS = OrderedDict([
    ('ep3d', dict(
        title='Egeblad-Pisinger 3D knapsack, 20 items, one bin', sense='max', unit='profit', fixed_pose=True,
        cases=['ep3d-20-%s-%s-%d' % (a, b, r) for a in 'CDFLU' for b in 'CR' for r in (50, 90)],
        label=lambda case: case[8:])),
    ('mpv_t9', dict(
        title='Martello-Pisinger-Vigo generator class 9, 30 to 90 items', sense='min', unit='bins', fixed_pose=True,
        cases=['MPV-GEN-T9-N%d-R%02d' % (n, k) for n in (30, 60, 90) for k in range(1, 11)],
        label=lambda case: case[11:])),
    ('imm', dict(
        title='Ivancic-Mathur-Mohanty THPACK9, all 47 instances', sense='min', unit='bins', fixed_pose=False,
        cases=['IMM-%02d' % k for k in range(1, 48)],
        label=lambda case: case[4:])),
])

#: Gallery: (benchmark, case, participants drawn side by side); duplicates of an identical packing are left out.
GALLERY = [
    ('ep3d', 'ep3d-20-C-C-50', [OURS, 'cp_sat', 'rust_sa', 'rust_ga', 'rust_layer', 'py3dbp']),
    ('mpv_t9', 'MPV-GEN-T9-N30-R01', [OURS, 'py3dbp', 'rust_extreme_point', 'go_bp3d', 'rust_sa', 'rust_layer']),
    ('imm', 'IMM-26', [OURS, 'py3dbp', 'go_bp3d', 'rust_extreme_point', 'rust_sa']),
]

TEXT = {
    'en': dict(participant='Participant', total='Total', bound='Bound (gap)', bound_row='Theoretical bound', relaxed='rotation relaxed',
               reference='reference', invalid='invalid', missing='n/a', valid_of='%d/%d valid', language='Language', version='Version tested',
               method='Method', driven='Driven as / budget', role='Role', variant='Variant: knapsack / class 9 / THPACK9', fixed='fixed', any='all rotations',
               case='Case', bin='Bin (x y z)', items='Items (types)', ratio='Item volume / bin volume', bound_source='Bound source', ours_status='packingsolver3d status, time',
               items_of='items placed of %d', time='time (s)', proof_cpsat='CP-SAT proof (20 s)', proof_closed='PackingSolver bound, closed', proof_open='PackingSolver bound, open',
               proof_construction='construction: three bins cut', proof_volume='volume bound', proof_ps_bound='PackingSolver bound (volume bound %d)',
               role_participant='participant', role_reference='reference', summary_title='Total / bound (gap)'),
    'zh': dict(participant='参与者', total='总计', bound='理论界（差距）', bound_row='理论界', relaxed='放松旋转约束',
               reference='参照', invalid='非法解', missing='无', valid_of='%d/%d 合法', language='语言', version='测试版本',
               method='方法', driven='驱动方式 / 预算', role='角色', variant='变体：背包 / 第 9 类 / THPACK9', fixed='固定姿态', any='全部旋转',
               case='Case', bin='箱子（x y z）', items='物品数（种类）', ratio='物品体积 / 箱子体积', bound_source='界的来源', ours_status='packingsolver3d 状态、用时',
               items_of='装入件数（共 %d）', time='用时（s）', proof_cpsat='CP-SAT 证明（20 s）', proof_closed='PackingSolver 界，已收口', proof_open='PackingSolver 界，未收口',
               proof_construction='构造：三箱切割', proof_volume='体积界', proof_ps_bound='PackingSolver 界（体积界 %d）',
               role_participant='参与者', role_reference='参照', summary_title='总计 / 理论界（差距）'),
}


# --------------------------------------------------------------------------- instances

def _rows(path):
    with open(path, newline='') as handle:
        return [row for row in csv.DictReader(handle) if any((value or '').strip() for value in row.values())]


def _optional(row, key, cast):
    value = row.get(key)
    return None if value is None or not value.strip() else cast(value)


def case_files(benchmark, case):
    """Return ``(items_csv, bins_csv)`` for a case of a benchmark."""
    if benchmark == 'ep3d':
        base = os.path.join(UPSTREAM_DATA, 'egeblad2009', case + '.3kp')
    elif benchmark == 'mpv_t9':
        base = os.path.join(DATA_DIR, 'instances', 'mpv_t9', case)
    else:
        base = os.path.join(UPSTREAM_DATA, 'ivancic1989', 'thpack9.txt_%d' % int(case.split('-')[1]))
    return base + '_items.csv', base + '_bins.csv'


def load_case(benchmark, case):
    """Build the :class:`Instance` of a case plus the profit of each item type and the pose semantics."""
    spec = BENCHMARKS[benchmark]
    items_csv, bins_csv = case_files(benchmark, case)
    items, profits = [], []
    for row in _rows(items_csv):
        rotations = None
        if any(key.startswith('ROTATION_') for key in row):
            rotations = [r for r in ALL_ROTATIONS if (row.get('ROTATION_' + r.value) or '0').strip() == '1']
        if spec['fixed_pose']:
            rotations = [Rotation.XYZ]
        x, y, z = int(row['X']), int(row['Y']), int(row['Z'])
        profit = _optional(row, 'PROFIT', float)
        items.append(ItemType(x=x, y=y, z=z, profit=profit, copies=_optional(row, 'COPIES', int) or 1, rotations=rotations))
        profits.append(profit if profit is not None else float(x * y * z))
    number_of_items = sum(item.copies for item in items)
    bins = []
    for row in _rows(bins_csv):
        copies = 1 if spec['sense'] == 'max' else number_of_items  # bin packing: as many bins as items, like --bin-infinite-copies
        bins.append(BinType(x=int(row['X']), y=int(row['Y']), z=int(row['Z']), copies=copies))
    objective = Objective.KNAPSACK if spec['sense'] == 'max' else Objective.BIN_PACKING
    return Instance(bin_types=bins, item_types=items, objective=objective), profits, ('fixed' if spec['fixed_pose'] else 'any')


# --------------------------------------------------------------------------- checking

def check(instance, profits, placements, pose, complete):
    """Validate compact placements ``[type, bin, x, y, z, lx, ly, lz]`` independently of any solver.

    Returns ``(errors, objective, bins_used, items_placed)``; the objective is the packed profit for
    knapsack instances and the number of bins used otherwise.
    """
    errors, counts, by_bin = [], Counter(), defaultdict(list)
    bin_type = instance.bin_types[0]
    for index, (type_id, bin_index, x, y, z, lx, ly, lz) in enumerate(placements):
        item = instance.item_types[type_id]
        if pose == 'fixed' and (lx, ly, lz) != (item.x, item.y, item.z):
            errors.append('placement %d: orientation %s differs from the fixed pose %s' % (index, (lx, ly, lz), (item.x, item.y, item.z)))
        elif sorted((lx, ly, lz)) != sorted((item.x, item.y, item.z)):
            errors.append('placement %d: extents %s are not a rotation of item type %d' % (index, (lx, ly, lz), type_id))
        if min(x, y, z) < -TOLERANCE or x + lx > bin_type.x + TOLERANCE or y + ly > bin_type.y + TOLERANCE or z + lz > bin_type.z + TOLERANCE:
            errors.append('placement %d: outside the %dx%dx%d bin' % (index, bin_type.x, bin_type.y, bin_type.z))
        counts[type_id] += 1
        by_bin[bin_index].append((x, y, z, x + lx, y + ly, z + lz, index))
    for bin_index, boxes in by_bin.items():
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] < b[3] - TOLERANCE and b[0] < a[3] - TOLERANCE and a[1] < b[4] - TOLERANCE and b[1] < a[4] - TOLERANCE \
                        and a[2] < b[5] - TOLERANCE and b[2] < a[5] - TOLERANCE:
                    errors.append('bin %s: placements %d and %d overlap' % (bin_index, a[6], b[6]))
    for type_id, number in counts.items():
        if number > instance.item_types[type_id].copies:
            errors.append('item type %d placed %d times, only %d copies exist' % (type_id, number, instance.item_types[type_id].copies))
    placed = sum(counts.values())
    if complete and placed != sum(item.copies for item in instance.item_types):
        errors.append('only %d of %d items placed' % (placed, sum(item.copies for item in instance.item_types)))
    if instance.objective == Objective.KNAPSACK:
        objective = sum(profits[type_id] for type_id, *_ in placements)
    else:
        objective = len(by_bin)
    return errors, objective, len(by_bin), placed


def compact_placements(result):
    """Flatten a :class:`Result` into compact placements, expanding identical bins reported with ``copies``."""
    out, next_bin = [], 0
    for packed in result.bins:
        for _ in range(packed.copies):
            for p in packed.placements:
                out.append([p.item_type_id, next_bin, p.x, p.y, p.z, p.lx, p.ly, p.lz])
            next_bin += 1
    return out


def result_from_placements(instance, placements, value):
    """Rebuild a :class:`Result` from compact placements so third-party solutions can be drawn with :mod:`packingsolver3d.visual`."""
    bin_type = instance.bin_types[0]
    by_bin = defaultdict(list)
    for type_id, bin_index, x, y, z, lx, ly, lz in placements:
        by_bin[bin_index].append(Placement(item_type_id=type_id, bin_id=bin_index, x=int(round(x)), y=int(round(y)), z=int(round(z)),
                                           lx=int(round(lx)), ly=int(round(ly)), lz=int(round(lz))))
    bins = tuple(PackedBin(bin_id=b, bin_type_id=0, copies=1, x=bin_type.x, y=bin_type.y, z=bin_type.z, placements=tuple(by_bin[b]))
                 for b in sorted(by_bin))
    return Result(status=Status.FEASIBLE, bins=bins, objective=instance.objective, value=value)


# --------------------------------------------------------------------------- solving ours

def solve_all(time_limit, memory_limit):
    """Solve every case with :func:`packingsolver3d.box.solve` and return the entries of ``ours.json``."""
    entries = []
    for benchmark, spec in BENCHMARKS.items():
        for case in spec['cases']:
            instance, profits, pose = load_case(benchmark, case)
            result = box.solve(instance, time_limit=time_limit, memory_limit=memory_limit)
            placements = compact_placements(result)
            errors, objective, bins_used, placed = check(instance, profits, placements, pose, complete=spec['sense'] == 'min')
            if errors:
                raise RuntimeError('%s/%s: our own solution failed validation: %s' % (benchmark, case, errors[:3]))
            entries.append(dict(benchmark=benchmark, case=case, participant=OURS, pose=pose, budget_s=time_limit, placements=placements,
                                status=result.status.value, value=result.value, bound=result.bound, solve_time=result.solve_time,
                                wall_time=result.run.wall_time, items=placed, bins=bins_used))
            print('%-7s %-22s %-9s value=%s bound=%s bins=%d items=%d %.1fs' % (benchmark, case, result.status.value, result.value,
                                                                            result.bound, bins_used, placed, result.solve_time), flush=True)
    return entries


# --------------------------------------------------------------------------- tables

def evaluate(entries):
    """Recompute objective and validity of every entry; returns ``{(benchmark, case): {participant: cell}}``."""
    cells = defaultdict(dict)
    cache = {}
    for entry in entries:
        key = (entry['benchmark'], entry['case'])
        if key not in cache:
            cache[key] = load_case(*key)
        instance, profits, pose = cache[key]
        spec = BENCHMARKS[entry['benchmark']]
        cell = dict(participant=entry['participant'], pose=entry['pose'], relaxed=(spec['fixed_pose'] and entry['pose'] != 'fixed'),
                    bound=entry.get('bound'), proof=entry.get('proof'), status=entry.get('status'),
                    elapsed=entry.get('elapsed_s', entry.get('solve_time')))
        if entry.get('placements') is None:
            cell.update(value=entry.get('bins'), valid=entry.get('bins') is not None, errors=[], items=None)
        else:
            errors, objective, bins_used, placed = check(instance, profits, entry['placements'], entry['pose'], complete=spec['sense'] == 'min')
            cell.update(value=objective if not errors else None, valid=not errors, errors=errors, items=placed, bins=bins_used)
        cells[key][entry['participant']] = cell
    return cells, cache


def case_bound(benchmark, case, cells, cache):
    """Best available bound for a case: tightest upper bound (knapsack) or highest lower bound (bin packing)."""
    spec = BENCHMARKS[benchmark]
    bounds = [c['bound'] for c in cells.values() if c.get('bound') is not None and not c['relaxed']]
    if spec['sense'] == 'max':
        return min(bounds) if bounds else None
    instance, _, _ = cache[(benchmark, case)]
    bin_type = instance.bin_types[0]
    volume = sum(item.x * item.y * item.z * item.copies for item in instance.item_types)
    bounds.append(int(math.ceil(volume / float(bin_type.x * bin_type.y * bin_type.z) - TOLERANCE)))
    return max(bounds)


def fmt(value, unit):
    if value is None:
        return ''
    if unit == 'bins':
        return '%d' % int(round(value))
    return '{:,}'.format(int(round(value)))


def link(participant):
    meta = PARTICIPANTS[participant]
    return '`%s <%s>`__' % (meta['name'], meta['url'])


def leaderboard(benchmark, cells, cache, lang):
    """Rows of the leaderboard of one benchmark: ``(participant, [name, total, bound(gap), per case...])``."""
    spec, text = BENCHMARKS[benchmark], TEXT[lang]
    cases = spec['cases']
    bounds = [case_bound(benchmark, case, cells[(benchmark, case)], cache) for case in cases]
    bound_total = sum(b for b in bounds if b is not None) if all(b is not None for b in bounds) else None
    rows = []
    for participant in participants_of(benchmark, cells):
        values, marks = [], []
        for case, bound in zip(cases, bounds):
            cell = cells[(benchmark, case)].get(participant)
            if cell is None:
                values.append(None); marks.append(text['missing'])
            elif not cell['valid']:
                values.append(None); marks.append(text['invalid'])
            else:
                values.append(cell['value'])
                star = '*' if bound is not None and not cell['relaxed'] and abs(cell['value'] - bound) < 0.5 else ''
                marks.append(fmt(cell['value'], spec['unit']) + star)
        complete = all(v is not None for v in values)
        total = sum(values) if complete else None
        if total is None:
            gap = text['valid_of'] % (sum(v is not None for v in values), len(cases))
            sort_key = (1, 0)
        elif bound_total is None:
            gap = ''
            sort_key = (0, -total if spec['sense'] == 'max' else total)
        elif spec['sense'] == 'max':
            gap = '%.1f%%' % (100.0 * (total - bound_total) / bound_total) if total != bound_total else '0'
            sort_key = (0, -total)
        else:
            gap = '+%d' % (total - bound_total) if total != bound_total else '0'
            sort_key = (0, total)
        name = link(participant) + notes_for(benchmark, participant, cells, lang)
        rows.append((sort_key, participant, [name, fmt(total, spec['unit']) if total is not None else text['missing'],
                                             '%s (%s)' % (fmt(bound_total, spec['unit']), gap) if bound_total is not None else '', *marks]))
    rows.sort(key=lambda r: r[0])
    header = [text['participant'], text['total'], text['bound']] + [spec['label'](case) for case in cases]
    bound_row = [text['bound_row'], fmt(bound_total, spec['unit']), ''] + [fmt(b, spec['unit']) for b in bounds]
    return header, bound_row, [(r[1], r[2]) for r in rows], bound_total


def participants_of(benchmark, cells):
    return [p for p in PARTICIPANTS if any(p in cells[(benchmark, case)] for case in BENCHMARKS[benchmark]['cases'])]


def notes_for(benchmark, participant, cells, lang):
    text, notes = TEXT[lang], []
    if any(cells[(benchmark, case)].get(participant, {}).get('relaxed') for case in BENCHMARKS[benchmark]['cases']):
        notes.append(text['relaxed'])
    if PARTICIPANTS[participant]['role'] == 'reference':
        notes.append(text['reference'])
    return ' (%s)' % ', '.join(notes) if notes else ''


def ranking_order(benchmark, cells, cache, lang):
    """Participants of a benchmark in leaderboard order, so every table of a benchmark lists them the same way."""
    _, _, rows, _ = leaderboard(benchmark, cells, cache, lang)
    return [participant for participant, _ in rows]


def facts_table(benchmark, cells, cache, lang):
    """Per case: bin, items, volume ratio, bound and where it comes from, and our status."""
    spec, text = BENCHMARKS[benchmark], TEXT[lang]
    rows = []
    for case in spec['cases']:
        instance, _, _ = cache[(benchmark, case)]
        bin_type, per = instance.bin_types[0], cells[(benchmark, case)]
        n_items = sum(i.copies for i in instance.item_types)
        volume = sum(i.x * i.y * i.z * i.copies for i in instance.item_types)
        bin_volume = bin_type.x * bin_type.y * bin_type.z
        bound = case_bound(benchmark, case, per, cache)
        ours, cp = per.get(OURS, {}), per.get('cp_sat')
        if spec['sense'] == 'max':
            source = text['proof_cpsat'] if cp and cp.get('proof') == 'optimal' else (text['proof_closed'] if ours.get('status') == 'optimal' else text['proof_open'])
        elif benchmark == 'mpv_t9':
            source = text['proof_construction']
        else:
            volume_bound = int(math.ceil(volume / float(bin_volume) - TOLERANCE))
            source = text['proof_ps_bound'] % volume_bound if bound > volume_bound else text['proof_volume']
        status = '%s, %.1f s' % (ours.get('status', text['missing']), ours.get('elapsed') or 0.0) if ours else text['missing']
        rows.append([case, '%d x %d x %d' % (bin_type.x, bin_type.y, bin_type.z), '%d (%d)' % (n_items, len(instance.item_types)),
                     '%.2f' % (volume / float(bin_volume)), fmt(bound, spec['unit']), source, status])
    header = [text['case'], text['bin'], text['items'], text['ratio'], text['bound_row'], text['bound_source'], text['ours_status']]
    return list_table(header, rows)


def per_case_table(benchmark, cells, cache, lang, field):
    """One row per participant, one column per case, showing ``items`` placed or ``time`` in seconds."""
    spec, text = BENCHMARKS[benchmark], TEXT[lang]
    rows = []
    for participant in ranking_order(benchmark, cells, cache, lang):
        row = [link(participant) + notes_for(benchmark, participant, cells, lang)]
        for case in spec['cases']:
            cell = cells[(benchmark, case)].get(participant)
            if cell is None:
                row.append(text['missing'])
            elif field == 'items':
                row.append(text['invalid'] if not cell['valid'] else ('%d' % cell['items'] if cell['items'] is not None else text['missing']))
            else:
                elapsed = cell.get('elapsed')
                row.append(text['missing'] if elapsed is None else ('%.2f' % elapsed if elapsed < 1 else '%.1f' % elapsed))
        rows.append(row)
    n_items = sum(i.copies for i in cache[(benchmark, spec['cases'][0])][0].item_types)
    label = (text['items_of'] % n_items) if field == 'items' else text['time']
    header = ['%s (%s)' % (text['participant'], label)] + [spec['label'](case) for case in spec['cases']]
    return list_table(header, rows)


def roster_table(cells, lang):
    """Every participant with language, version, method, how it was driven, its variant per benchmark and role."""
    text = TEXT[lang]
    rows = []
    for participant, meta in PARTICIPANTS.items():
        variants = []
        for benchmark, spec in BENCHMARKS.items():
            present = [cells[(benchmark, case)].get(participant) for case in spec['cases']]
            present = [c for c in present if c]
            if not present:
                variants.append('-')
            elif any(c['relaxed'] for c in present):
                variants.append(text['relaxed'])
            else:
                variants.append(text['fixed'] if spec['fixed_pose'] else text['any'])
        rows.append([link(participant), meta['language'][lang], meta['version'], meta['method'][lang], meta['driven'][lang],
                     ' / '.join(variants), text['role_' + meta['role']]])
    header = [text['participant'], text['language'], text['version'], text['method'], text['driven'], text['variant'], text['role']]
    return list_table(header, rows, widths=[16, 8, 10, 26, 20, 12, 8])


def summary_table(cells, cache, lang):
    text = TEXT[lang]
    per_participant = {}
    for benchmark in BENCHMARKS:
        _, _, rows, _ = leaderboard(benchmark, cells, cache, lang)
        for participant, row in rows:
            per_participant.setdefault(participant, {})[benchmark] = (row[1], row[2])
    header = [text['participant']] + ['%s: %s' % (BENCHMARKS[b]['title'].split(',')[0], text['summary_title']) for b in BENCHMARKS]
    rows = [[link(p)] + [('%s / %s' % per_participant[p][b]) if b in per_participant[p] else text['missing'] for b in BENCHMARKS]
            for p in PARTICIPANTS if p in per_participant]
    return list_table(header, rows)


def list_table(header, rows, caption=None, widths=None):
    lines = ['.. list-table::' + (' ' + caption if caption else ''), '   :header-rows: 1']
    if widths:
        lines.append('   :widths: ' + ' '.join(str(w) for w in widths))
    lines.append('')
    for row in [header] + rows:
        for index, cell in enumerate(row):
            lines.append('   %s %s' % ('* -' if index == 0 else '  -', cell if cell != '' else '\\-'))
    lines.append('')
    return '\n'.join(lines)


def render_pages(cells, cache):
    """Fill the leaderboard page templates (``index.rst.in`` / ``index_zh.rst.in``) with the generated tables."""
    directory = os.path.join(ROOT, 'docs', 'source', 'benchmarks', 'leaderboards')
    for lang, name in (('en', 'index'), ('zh', 'index_zh')):
        tables = {'roster': roster_table(cells, lang), 'summary': summary_table(cells, cache, lang)}
        for benchmark in BENCHMARKS:
            header, bound_row, rows, _ = leaderboard(benchmark, cells, cache, lang)
            tables[benchmark + '.leaderboard'] = list_table(header, [bound_row] + [row for _, row in rows])
            tables[benchmark + '.facts'] = facts_table(benchmark, cells, cache, lang)
            tables[benchmark + '.times'] = per_case_table(benchmark, cells, cache, lang, 'time')
            if BENCHMARKS[benchmark]['sense'] == 'max':
                tables[benchmark + '.items'] = per_case_table(benchmark, cells, cache, lang, 'items')
        with open(os.path.join(directory, name + '.rst.in')) as handle:
            template = handle.read()
        used = set()

        def substitute(match):
            key = match.group(1).strip()
            used.add(key)
            return tables[key]
        page = re.sub(r'^\.\. TABLE:: (.+)$', substitute, template, flags=re.M)
        missing = set(tables) - used
        if missing:
            raise RuntimeError('%s template does not place these tables: %s' % (name, sorted(missing)))
        path = os.path.join(directory, name + '.rst')
        with open(path, 'w') as handle:
            handle.write('.. Generated by tools/make_benchmarks.py from %s.rst.in -- edit the template, not this file.\n\n' % name + page)
        print('wrote', path, flush=True)


# --------------------------------------------------------------------------- figures

def render_figures(entries, cells, cache, no_png, width, height):
    from packingsolver3d.visual import plot_result
    by_key = {(e['benchmark'], e['case'], e['participant']): e for e in entries}
    for benchmark, case, participants in GALLERY:
        instance, profits, pose = cache[(benchmark, case)]
        spec = BENCHMARKS[benchmark]
        for participant in participants:
            entry = by_key[(benchmark, case, participant)]
            cell = cells[(benchmark, case)][participant]
            if not cell['valid']:
                raise RuntimeError('%s/%s/%s is not a valid solution, cannot draw it' % (benchmark, case, participant))
            result = result_from_placements(instance, entry['placements'], cell['value'])
            meta = PARTICIPANTS[participant]
            what = ('profit {:,}'.format(int(cell['value'])) + ', %d of %d items' % (cell['items'], sum(i.copies for i in instance.item_types))
                    if spec['sense'] == 'max' else '%d bins, %d items' % (cell['value'], cell['items']))
            bound = case_bound(benchmark, case, cells[(benchmark, case)], cache)
            proven = bound is not None and not cell['relaxed'] and abs(cell['value'] - bound) < 0.5
            suffix = ' (rotation relaxed)' if cell['relaxed'] else (' (proven optimum)' if proven else '')
            figure = plot_result(result, show_ids=cell['items'] <= 60, title='%s: %s, %s%s' % (meta['name'], case, what, suffix))
            name = '%s__%s__%s' % (benchmark, case, participant)
            html = os.path.join(FIGURE_DIR, name + '.html')
            figure.write_html(html, include_plotlyjs='cdn', full_html=False, default_width='100%', default_height='520px')
            print('wrote', html, os.path.getsize(html), 'bytes', flush=True)
            if not no_png:
                png = os.path.join(FIGURE_DIR, name + '.png')
                figure.write_image(png, width=width, height=height, scale=1)
                print('wrote', png, os.path.getsize(png), 'bytes', flush=True)


# --------------------------------------------------------------------------- main

def load_entries():
    entries = []
    for name in ('ours.json', 'third_party.json'):
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            with open(path) as handle:
                entries.extend(json.load(handle)['results'])
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--solve', action='store_true', help='run box.solve on every case and rewrite tools/benchmarks/ours.json')
    parser.add_argument('--render', action='store_true', help='write the RST tables and the gallery figures')
    parser.add_argument('--time-limit', type=float, default=10.0)
    parser.add_argument('--memory-limit', type=int, default=1024)
    parser.add_argument('--no-png', action='store_true', help='skip the PNG export (no kaleido / Chrome needed)')
    parser.add_argument('--width', type=int, default=900)
    parser.add_argument('--height', type=int, default=650)
    args = parser.parse_args(argv)
    if not args.solve and not args.render:
        parser.error('nothing to do: pass --solve and/or --render')
    if args.solve:
        entries = solve_all(args.time_limit, args.memory_limit)
        with open(os.path.join(DATA_DIR, 'ours.json'), 'w') as handle:
            json.dump({'schema': 1, 'time_limit': args.time_limit, 'memory_limit': args.memory_limit, 'results': entries}, handle, indent=0)
    if args.render:
        entries = load_entries()
        cells, cache = evaluate(entries)
        os.makedirs(FIGURE_DIR, exist_ok=True)
        render_pages(cells, cache)
        render_figures(entries, cells, cache, args.no_png, args.width, args.height)
    return 0


if __name__ == '__main__':
    sys.exit(main())
