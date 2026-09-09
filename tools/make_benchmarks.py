"""
Solve the benchmark cases with packingsolver3d, re-check every solution (ours
and the third-party ones shipped in ``tools/benchmarks/third_party.json``) with
an independent geometry validator, and render the leaderboards, the summary
table and the gallery figures used by ``docs/source/benchmarks``.

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
import sys
from collections import Counter, OrderedDict, defaultdict

from packingsolver3d import ALL_ROTATIONS, BinType, Instance, ItemType, Objective, Rotation, box
from packingsolver3d.result import PackedBin, Placement, Result, Status

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'tools', 'benchmarks')
UPSTREAM_DATA = os.path.join(ROOT, 'upstream', 'packingsolver', 'data', 'box')
GENERATED_DIR = os.path.join(ROOT, 'docs', 'source', 'benchmarks', '_generated')
FIGURE_DIR = os.path.join(ROOT, 'docs', 'source', '_static', 'benchmarks')
OURS = 'packingsolver3d'
TOLERANCE = 1e-6

#: Display name, link and role of every participant; the order is the order of the roster.
PARTICIPANTS = OrderedDict([
    (OURS, dict(name='packingsolver3d (PackingSolver box)', url='https://github.com/HansBug/packingsolver3d', role='participant')),
    ('py3dbp', dict(name='py3dbp', url='https://github.com/enzoruiz/3dbinpacking', role='participant')),
    ('jerry', dict(name='jerry800416/3D-bin-packing', url='https://github.com/jerry800416/3D-bin-packing', role='participant')),
    ('go_bp3d', dict(name='gedex/bp3d', url='https://github.com/gedex/bp3d', role='participant')),
    ('rust_extreme_point', dict(name='U-Nesting ExtremePoint', url='https://github.com/iyulab/U-Nesting', role='participant')),
    ('rust_layer', dict(name='U-Nesting BottomLeftFill', url='https://github.com/iyulab/U-Nesting', role='participant')),
    ('rust_ga', dict(name='U-Nesting GA', url='https://github.com/iyulab/U-Nesting', role='participant')),
    ('rust_brkga', dict(name='U-Nesting BRKGA', url='https://github.com/iyulab/U-Nesting', role='participant')),
    ('rust_sa', dict(name='U-Nesting SA', url='https://github.com/iyulab/U-Nesting', role='participant')),
    ('cp_sat', dict(name='OR-Tools CP-SAT exact model', url='https://developers.google.com/optimization/cp/cp_solver', role='reference')),
    ('mpv_official', dict(name='Martello-Pisinger-Vigo 3dbpp.c', url='http://hjemmesider.diku.dk/~pisinger/codes.html', role='reference')),
])

BENCHMARKS = OrderedDict([
    ('ep3d', dict(
        title='Egeblad-Pisinger 3D knapsack, 20 items, one bin', sense='max', unit='profit', fixed_pose=True,
        cases=['ep3d-20-%s-%s-50' % (a, b) for a in 'CDFLU' for b in 'CR'],
        label=lambda case: case[8:11])),
    ('mpv_t9', dict(
        title='Martello-Pisinger-Vigo generator class 9, 30 items', sense='min', unit='bins', fixed_pose=True,
        cases=['MPV-GEN-T9-N30-R%02d' % k for k in range(1, 11)],
        label=lambda case: case[-3:])),
    ('imm', dict(
        title='Ivancic-Mathur-Mohanty THPACK9, eight instances', sense='min', unit='bins', fixed_pose=False,
        cases=['IMM-%02d' % k for k in (1, 18, 19, 20, 24, 25, 26, 46)],
        label=lambda case: case[4:])),
])

#: Gallery: (benchmark, case, participants drawn side by side).
GALLERY = [
    ('ep3d', 'ep3d-20-C-C-50', [OURS, 'rust_sa', 'py3dbp']),
    ('mpv_t9', 'MPV-GEN-T9-N30-R01', [OURS, 'py3dbp', 'rust_layer']),
    ('imm', 'IMM-26', [OURS, 'py3dbp', 'rust_sa']),
]

TEXT = {
    'en': dict(participant='Participant', total='Total', bound='Bound (gap)', bound_row='Theoretical bound', relaxed='rotation relaxed',
               reference='reference', invalid='invalid', missing='n/a', valid_of='%d/%d valid', benchmark='Benchmark',
               summary_caption='Totals over all cases of each benchmark; a gap of 0 means every case reached the bound.'),
    'zh': dict(participant='参与者', total='总计', bound='理论界（差距）', bound_row='理论界', relaxed='放松旋转约束',
               reference='参照', invalid='非法解', missing='无', valid_of='%d/%d 合法', benchmark='基准',
               summary_caption='每个基准所有 case 的总计；差距为 0 表示每个 case 都达到了理论界。'),
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
                    bound=entry.get('bound'), proof=entry.get('proof'), elapsed=entry.get('elapsed_s', entry.get('solve_time')))
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


def leaderboard(benchmark, cells, cache, lang):
    """Rows of the leaderboard of one benchmark: ``[[participant cell, total, bound(gap), per case...], ...]``."""
    spec, text = BENCHMARKS[benchmark], TEXT[lang]
    cases = spec['cases']
    bounds = [case_bound(benchmark, case, cells[(benchmark, case)], cache) for case in cases]
    bound_total = sum(b for b in bounds if b is not None) if all(b is not None for b in bounds) else None
    rows = []
    participants = [p for p in PARTICIPANTS if any(p in cells[(benchmark, case)] for case in cases)]
    for participant in participants:
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
        meta = PARTICIPANTS[participant]
        name = '`%s <%s>`__' % (meta['name'], meta['url'])
        notes = []
        if any(cells[(benchmark, case)].get(participant, {}).get('relaxed') for case in cases):
            notes.append(text['relaxed'])
        if meta['role'] == 'reference':
            notes.append(text['reference'])
        if notes:
            name += ' (%s)' % ', '.join(notes)
        rows.append((sort_key, participant, [name, fmt(total, spec['unit']) if total is not None else text['missing'],
                                             '%s (%s)' % (fmt(bound_total, spec['unit']), gap) if bound_total is not None else '', *marks]))
    rows.sort(key=lambda r: r[0])
    header = [text['participant'], text['total'], text['bound']] + [spec['label'](case) for case in cases]
    bound_row = [text['bound_row'], fmt(bound_total, spec['unit']), ''] + [fmt(b, spec['unit']) for b in bounds]
    return header, bound_row, [(r[1], r[2]) for r in rows], bound_total


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


def render_tables(cells, cache, lang):
    """Write the per-benchmark leaderboards and the summary table for one language."""
    summary_rows = {}
    for benchmark, spec in BENCHMARKS.items():
        header, bound_row, rows, bound_total = leaderboard(benchmark, cells, cache, lang)
        path = os.path.join(GENERATED_DIR, '%s_%s.rst' % (benchmark, lang))
        with open(path, 'w') as handle:
            handle.write(list_table(header, [bound_row] + [row for _, row in rows]))
        print('wrote', path, flush=True)
        for participant, row in rows:
            summary_rows.setdefault(participant, {})[benchmark] = (row[1], row[2])
    text = TEXT[lang]
    header = [text['participant']] + ['%s: %s / %s' % (BENCHMARKS[b]['title'].split(',')[0], text['total'], text['bound']) for b in BENCHMARKS]
    rows = []
    for participant in PARTICIPANTS:
        per = summary_rows.get(participant)
        if per:
            meta = PARTICIPANTS[participant]
            rows.append(['`%s <%s>`__' % (meta['name'], meta['url'])] + [('%s / %s' % per[b]) if b in per else text['missing'] for b in BENCHMARKS])
    path = os.path.join(GENERATED_DIR, 'summary_%s.rst' % lang)
    with open(path, 'w') as handle:
        handle.write(list_table(header, rows))
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
            suffix = ' (rotation relaxed)' if cell['relaxed'] else (' (proven optimal)' if participant == OURS and entry.get('status') == 'optimal' else '')
            figure = plot_result(result, show_ids=cell['items'] <= 60, title='%s: %s, %s%s' % (meta['name'], case, what, suffix))
            name = '%s__%s__%s' % (benchmark, case, participant)
            html = os.path.join(FIGURE_DIR, name + '.html')
            figure.write_html(html, include_plotlyjs='cdn', full_html=False, default_width='100%', default_height='520px')
            print('wrote', html, os.path.getsize(html), 'bytes', flush=True)
            if not no_png:
                png = os.path.join(FIGURE_DIR, name + '.png')
                figure.write_image(png, width=width, height=height, scale=2)
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
        os.makedirs(GENERATED_DIR, exist_ok=True)
        os.makedirs(FIGURE_DIR, exist_ok=True)
        for lang in ('en', 'zh'):
            render_tables(cells, cache, lang)
        render_figures(entries, cells, cache, args.no_png, args.width, args.height)
    return 0


if __name__ == '__main__':
    sys.exit(main())
