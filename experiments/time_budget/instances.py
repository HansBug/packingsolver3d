"""Instance sources for the time-budget campaign: upstream benchmark families, ROADEF 2022 sample, synthetic Stowly-like cargo."""
import csv
import glob
import json
import math
import os
import random
import sys
from typing import Dict, List, Optional

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, REPO)
from packingsolver3d import BinType, Instance, ItemType, Objective, Rotation, SemiTrailerTruck, UnloadingConstraint  # noqa: E402

_UNLOADING = {'None': 'none', 'OnlyXMovements': 'only-x-movements', 'OnlyYMovements': 'only-y-movements', 'IncreasingX': 'increasing-x', 'IncreasingY': 'increasing-y'}

DATA = os.path.join(REPO, 'upstream', 'packingsolver', 'data')
ROADEF = os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'data', 'boxstacks', 'roadef2022_2024-04-25_kp')
ALL_ROTATIONS = list(Rotation)
UPRIGHT = (Rotation.XYZ, Rotation.YXZ)
_TRUCK_COLUMNS = {
    'TRACTOR_WEIGHT': ('tractor_weight', float),
    'FRONT_AXLE_MIDDLE_AXLE_DISTANCE': ('front_axle_middle_axle_distance', int),
    'FRONT_AXLE_TRACTOR_GRAVITY_CENTER_DISTANCE': ('front_axle_tractor_gravity_center_distance', int),
    'FRONT_AXLE_HARNESS_DISTANCE': ('front_axle_harness_distance', int),
    'EMPTY_TRAILER_WEIGHT': ('empty_trailer_weight', float),
    'HARNESS_REAR_AXLE_DISTANCE': ('harness_rear_axle_distance', int),
    'TRAILER_GRAVITY_CENTER_REAR_AXLE_DISTANCE': ('trailer_gravity_center_rear_axle_distance', int),
    'TRAILER_START_HARNESS_DISTANCE': ('trailer_start_harness_distance', int),
    'REAR_AXLE_MAXIMUM_WEIGHT': ('rear_axle_maximum_weight', float),
    'MIDDLE_AXLE_MAXIMUM_WEIGHT': ('middle_axle_maximum_weight', float),
}


def _rows(path):
    with open(path, newline='') as f:
        return [r for r in csv.DictReader(f) if any(v.strip() for v in r.values() if v is not None)]


def _opt(row, column, cast):
    v = row.get(column)
    return None if v is None or v.strip() == '' else cast(v)


def _item(row):
    rotations = None
    if any(c.startswith('ROTATION_') for c in row):
        rotations = [r for r in ALL_ROTATIONS if row.get('ROTATION_' + r.value, '0').strip() == '1']
    return ItemType(
        x=int(row['X']), y=int(row['Y']), z=int(row['Z']),
        profit=_opt(row, 'PROFIT', float), weight=_opt(row, 'WEIGHT', float) or 0.0,
        copies=_opt(row, 'COPIES', int) or 1, copies_min=_opt(row, 'COPIES_MIN', int), rotations=rotations,
        group_id=_opt(row, 'GROUP_ID', int), stackability_id=_opt(row, 'STACKABILITY_ID', int),
        nesting_height=_opt(row, 'NESTING_HEIGHT', int), maximum_stackability=_opt(row, 'MAXIMUM_STACKABILITY', int),
        maximum_weight_above=_opt(row, 'MAXIMUM_WEIGHT_ABOVE', float))


def _bin(row, default_copies=1):
    truck = None
    if row.get('IS_SEMI_TRAILER_TRUCK', '0').strip() == '1':
        truck = SemiTrailerTruck(**{f: cast(row[c]) for c, (f, cast) in _TRUCK_COLUMNS.items() if c in row})
    return BinType(
        x=int(row['X']), y=int(row['Y']), z=int(row['Z']), cost=_opt(row, 'COST', float),
        copies=_opt(row, 'COPIES', int) or default_copies, copies_min=_opt(row, 'COPIES_MIN', int) or 0,
        maximum_weight=_opt(row, 'MAXIMUM_WEIGHT', float), maximum_stack_density=_opt(row, 'MAXIMUM_STACK_DENSITY', float),
        semi_trailer_truck=truck)


def load_pair(prefix, objective, bin_copies=None):
    """``<prefix>_items.csv`` + ``<prefix>_bins.csv`` (bischoff/davies/egeblad/loh/ivancic)."""
    items = [_item(r) for r in _rows(prefix + '_items.csv')]
    total = sum(i.copies for i in items)
    bins = [_bin(r, default_copies=(bin_copies or 1) if bin_copies != 'items' else total) for r in _rows(prefix + '_bins.csv')]
    return Instance(bin_types=bins, item_types=items, objective=objective)


def load_prefixed(prefix, objective=Objective.KNAPSACK):
    """``<prefix>_items.csv`` / ``_bins.csv`` / ``_parameters.csv`` (ROADEF 2022 knapsack derivation)."""
    params = {r['NAME']: r['VALUE'] for r in _rows(prefix + '_parameters.csv')}
    unloading = params.get('unloading-constraint')
    return Instance(
        bin_types=[_bin(r) for r in _rows(prefix + '_bins.csv')],
        item_types=[_item(r) for r in _rows(prefix + '_items.csv')],
        objective=Objective(params.get('objective', objective.value)),
        unloading_constraint=None if unloading is None else UnloadingConstraint(_UNLOADING.get(unloading, unloading)))


# --- synthetic Stowly-like cargo -------------------------------------------------------------------------------------
CONTAINERS = {
    '20gp': (5898, 2352, 2393, 28200),
    '40hq': (12032, 2352, 2698, 26460),
}
DEMO_CARGO = [(530, 290, 370, 300, 8), (530, 230, 290, 300, 6), (430, 210, 270, 400, 4),
              (1200, 800, 1200, 24, 450), (1200, 1000, 1150, 12, 1100)]


def synthetic(seed, container, n_types, fill, stacked, objective, bins=1):
    rng = random.Random(seed)
    bx, by, bz, bw = CONTAINERS[container]
    target = fill * bx * by * bz  # total cargo volume in units of ONE bin, whatever the bin count
    shares = [rng.random() + 0.2 for _ in range(n_types)]
    items = []
    for t in range(n_types):
        kind = rng.random()
        if kind < 0.6:  # carton
            x, y, z = rng.randint(300, 800), rng.randint(200, 600), rng.randint(200, 600)
            density = rng.uniform(80, 300)
        elif kind < 0.9:  # pallet / crate
            x, y, z = rng.choice([1200, 1200, 1000, 1100]), rng.choice([800, 1000, 1200]), rng.randint(600, 1500)
            density = rng.uniform(150, 450)
        else:  # long / odd
            x, y, z = rng.randint(1500, 3000), rng.randint(200, 600), rng.randint(200, 600)
            density = rng.uniform(100, 400)
        volume = x * y * z
        copies = max(1, round(target * shares[t] / sum(shares) / volume))
        weight = round(density * volume / 1e9, 1)
        extra = {}
        if stacked:
            extra['stackability_id'] = t
            if rng.random() < 0.5:
                extra['maximum_stackability'] = rng.randint(1, 4)
            rotations = UPRIGHT
        else:
            rotations = UPRIGHT if rng.random() < 0.6 else tuple(ALL_ROTATIONS)
        items.append(ItemType(x=x, y=y, z=z, copies=copies, weight=weight, rotations=rotations, **extra))
    return Instance(bin_types=[BinType(x=bx, y=by, z=bz, copies=bins, cost=1, maximum_weight=bw)], item_types=items, objective=objective)


def demo(stacked, objective=Objective.KNAPSACK, scale=1, types=1, bins=1):
    """The Stowly demo 40'HQ instance and its x2 / ten-types variants used in the upstream reports."""
    cargo = list(DEMO_CARGO)
    if types > 1:
        rng = random.Random(7)
        for _ in range(types - 1):
            for x, y, z, c, w in DEMO_CARGO:
                cargo.append((x + rng.randint(-60, 60), y + rng.randint(-40, 40), z + rng.randint(-40, 40), max(1, c // 2), w))
    items = [ItemType(x=x, y=y, z=z, copies=c * scale, weight=w, rotations=UPRIGHT, **({'stackability_id': i} if stacked else {}))
             for i, (x, y, z, c, w) in enumerate(cargo)]
    return Instance(bin_types=[BinType(x=12032, y=2352, z=2698, copies=bins, cost=1, maximum_weight=26460)], item_types=items, objective=objective)


# --- features ----------------------------------------------------------------------------------------------------------
def count_stacks(instance):
    max_z = max(b.z for b in instance.bin_types)
    total = 0
    for it in instance.item_types:
        per = max(1, max_z // it.z) if it.z else 1
        if it.maximum_stackability:
            per = min(per, it.maximum_stackability)
        total += math.ceil(it.copies / per)
    return total


def features(instance):
    items = instance.item_types
    bins = instance.bin_types
    n_items = sum(i.copies for i in items)
    item_volume = sum(i.copies * i.x * i.y * i.z for i in items)
    bin_volume_one = max(b.x * b.y * b.z for b in bins)
    n_bins = sum(b.copies for b in bins)
    mean_item_volume = item_volume / n_items
    return {
        'n_items': n_items, 'n_types': len(items), 'n_bins': n_bins, 'n_bin_types': len(bins),
        'fill_ratio': item_volume / bin_volume_one, 'fill_ratio_all_bins': item_volume / (bin_volume_one * n_bins),
        'mean_items_per_bin': bin_volume_one / mean_item_volume, 'mean_copies': n_items / len(items),
        'mean_rotations': sum(len(i.rotations) if i.rotations else 6 for i in items) / len(items),
        'weight_ratio': (sum(i.copies * (i.weight or 0) for i in items) / (bins[0].maximum_weight or float('inf'))) if bins[0].maximum_weight else 0.0,
        'n_stacks': count_stacks(instance),
    }


# --- job list ------------------------------------------------------------------------------------------------------------
def bks_tables():
    out = {}
    for name in ['data_knapsack_bischoff1995_davies1999.csv', 'data_knapsack_egeblad2009.csv']:
        for r in _rows(os.path.join(DATA, 'box', name)):
            v = r.get('Best known solution value')
            if v and v.strip():
                out[r['Path']] = float(v)
    return out


def _weight(solver, instance, f):
    """Rough core count of a solve, for the scheduler (box tree search uses 6 threads, multi-bin pools up to 8)."""
    if f['n_bins'] > 1:
        return 6 if solver == 'box' else 1  # boxstacks SVC is single-threaded (measured)
    if solver == 'boxstacks':
        return 1
    return 1 if f['mean_items_per_bin'] > 64 else 6


def build_jobs(roadef_per_family=8, t_upstream=60.0, t_synthetic=120.0, seed=2026):
    jobs = []
    bks = bks_tables()

    def add(job_id, family, solver, objective, source, t_ref, instance, reference=None):
        f = features(instance)
        jobs.append({'id': job_id, 'family': family, 'solver': solver, 'objective': objective.value, 'source': source,
                     't_ref': t_ref, 'features': f, 'weight': _weight(solver, instance, f), 'bks': reference})

    for fam in ['bischoff1995', 'davies1999', 'egeblad2009', 'loh1992']:
        for items_csv in sorted(glob.glob(os.path.join(DATA, 'box', fam, '*_items.csv'))):
            prefix = items_csv[:-len('_items.csv')]
            rel = os.path.relpath(prefix, os.path.join(DATA, 'box'))
            add('box/' + rel, fam, 'box', Objective.KNAPSACK, {'kind': 'pair', 'prefix': prefix, 'bin_copies': None},
                t_upstream, load_pair(prefix, Objective.KNAPSACK), bks.get(rel))
    for items_csv in sorted(glob.glob(os.path.join(DATA, 'box', 'ivancic1989', '*_items.csv'))):
        prefix = items_csv[:-len('_items.csv')]
        rel = os.path.relpath(prefix, os.path.join(DATA, 'box'))
        add('box/' + rel + '/bp', 'ivancic1989', 'box', Objective.BIN_PACKING, {'kind': 'pair', 'prefix': prefix, 'bin_copies': 'items'},
            t_upstream, load_pair(prefix, Objective.BIN_PACKING, bin_copies='items'))

    if os.path.isdir(ROADEF):
        rng = random.Random(seed)
        by_family: Dict[str, List[str]] = {}
        for r in _rows(os.path.join(DATA, 'boxstacks', 'data_knapsack_roadef2022_2024-04-25.csv')):
            parts = r['Path'].split('/')
            by_family.setdefault(parts[1] + '/' + parts[2], []).append(r['Path'])
        for fam, paths in sorted(by_family.items()):
            for p in sorted(rng.sample(paths, min(roadef_per_family, len(paths)))):
                prefix = os.path.join(os.path.dirname(ROADEF), p)
                if os.path.isfile(prefix + '_items.csv'):
                    add('boxstacks/' + p, 'roadef2022', 'boxstacks', Objective.KNAPSACK, {'kind': 'prefixed', 'prefix': prefix}, t_upstream, load_prefixed(prefix))

    for solver in ['box', 'boxstacks']:
        stacked = solver == 'boxstacks'
        for objective in [Objective.KNAPSACK, Objective.BIN_PACKING]:
            for container in CONTAINERS:
                for n_types in [2, 5, 10, 20, 40]:
                    for fill in [0.6, 0.9, 1.2, 2.0]:
                        # bin packing: enough bins for ~75% packing efficiency plus one spare, as a planner would enter
                        bins = 1 if objective == Objective.KNAPSACK else math.ceil(fill / 0.75) + 1
                        s = seed + n_types * 100 + int(fill * 10)
                        spec = {'kind': 'synthetic', 'seed': s, 'container': container, 'n_types': n_types, 'fill': fill,
                                'stacked': stacked, 'objective': objective.value, 'bins': bins}
                        add(f'{solver}/synthetic/{objective.value}/{container}/t{n_types}/f{fill}', 'synthetic', solver, objective, spec,
                            t_synthetic, synthetic(s, container, n_types, fill, stacked, objective, bins))
            if solver == 'boxstacks' and objective == Objective.KNAPSACK:
                # several bins with more cargo than fits: the multi-bin knapsack path (SVC on every upstream so far)
                for container in CONTAINERS:
                    for n_types in [2, 5, 10, 20]:
                        for fill in [0.9, 1.5, 2.5]:
                            bins = max(2, math.ceil(fill / 0.75) - 1)
                            s2 = seed + 7000 + n_types * 100 + int(fill * 10)
                            spec = {'kind': 'synthetic', 'seed': s2, 'container': container, 'n_types': n_types, 'fill': fill,
                                    'stacked': True, 'objective': objective.value, 'bins': bins}
                            add(f'{solver}/synthetic_multi/{objective.value}/{container}/t{n_types}/f{fill}', 'synthetic_multi', solver, objective, spec,
                                t_synthetic, synthetic(s2, container, n_types, fill, True, objective, bins))
            for scale, types, tag in [(1, 1, 'demo'), (2, 1, 'demo_x2'), (1, 2, 'demo_ten')]:
                bins = 1 if objective == Objective.KNAPSACK else 4
                spec = {'kind': 'demo', 'stacked': stacked, 'objective': objective.value, 'scale': scale, 'types': types, 'bins': bins}
                for rep in range(3):
                    add(f'{solver}/{tag}/{objective.value}/rep{rep}', 'demo', solver, objective, spec, t_synthetic, demo(stacked, objective, scale, types, bins))
    return jobs


def instantiate(source):
    kind = source['kind']
    if kind == 'pair':
        obj = Objective.BIN_PACKING if source.get('bin_copies') == 'items' else Objective.KNAPSACK
        return load_pair(source['prefix'], obj, source.get('bin_copies'))
    if kind == 'prefixed':
        return load_prefixed(source['prefix'])
    if kind == 'synthetic':
        return synthetic(source['seed'], source['container'], source['n_types'], source['fill'], source['stacked'],
                         Objective(source['objective']), source['bins'])
    if kind == 'demo':
        return demo(source['stacked'], Objective(source['objective']), source['scale'], source['types'], source['bins'])
    raise ValueError(kind)


if __name__ == '__main__':
    jobs = build_jobs()
    print(len(jobs), 'jobs')
    from collections import Counter
    print(Counter((j['solver'], j['family'], j['objective'], j['weight']) for j in jobs))
    print(json.dumps(jobs[0], indent=1)[:600])
