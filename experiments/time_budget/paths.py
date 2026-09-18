"""Replicate upstream's automatic algorithm selection (box/optimize.cpp, boxstacks/optimize.cpp) from instance features.

Upstream picks the algorithm from three quantities: the number of bins, ``mean_items_per_bin`` = largest bin volume /
mean item volume (integer), and ``mean_type_copies`` = items / item types, with thresholds 16 / 64 and factor 1.
"""
MANY_ITEMS_IN_BINS = 16
MANY_ITEMS_IN_BINS_2 = 64
MANY_COPIES_FACTOR = 1.0


def box_path(objective, n_bins, mean_items_per_bin, mean_type_copies):
    mipb = int(mean_items_per_bin)
    if n_bins <= 1:
        if objective in ('knapsack', 'feasibility') and mipb > MANY_ITEMS_IN_BINS_2:
            return 'TSMS'
        return 'TS'
    copies_heavy = mean_type_copies > MANY_COPIES_FACTOR * mipb
    if copies_heavy:
        return 'SSK' if mipb > MANY_ITEMS_IN_BINS else 'SVC'
    if mipb > MANY_ITEMS_IN_BINS_2:
        return 'SSK'
    if objective in ('bin-packing', 'bin-packing-with-leftovers') and mipb > MANY_ITEMS_IN_BINS:
        return 'TS'
    return 'TS'  # tree search (+ column generation; bin packing adds SVC): multi-bin tree search


def boxstacks_path(n_bins):
    return 'SOR' if n_bins <= 1 else 'SVC'


def path(solver, objective, features):
    if solver == 'boxstacks':
        return boxstacks_path(features['n_bins'])
    return box_path(objective, features['n_bins'], features['mean_items_per_bin'], features['mean_copies'])


LABEL_PREFIX = {'TSMS': 'TSMS', 'TS ': 'TS', 'SSK': 'SSK', 'SVC': 'SVC', 'CG': 'CG', 'SOR': 'SOR', 'iteration': 'SVC', 'DS': 'DS'}


def observed(rec):
    """Algorithms that actually reported solutions, from the event labels."""
    seen = set()
    for ev in rec['events']:
        label = ev[5]
        for prefix, name in LABEL_PREFIX.items():
            if label.startswith(prefix):
                seen.add(name)
                break
        else:
            seen.add(label.split()[0])
    return seen


if __name__ == '__main__':
    import json
    import sys
    from collections import Counter
    recs = [json.loads(l) for l in open(sys.argv[1])]
    agree = Counter()
    mismatch = Counter()
    for r in recs:
        if not r.get('events'):
            continue
        p = path(r['solver'], r['objective'], r['features'])
        obs = observed(r)
        key = (r['solver'], r['family'], r['objective'], p, tuple(sorted(obs)))
        if p in obs or (p == 'TS' and obs <= {'TS', 'CG', 'SVC'}) or (p == 'SVC' and obs <= {'SVC', 'CG'}):
            agree[key] += 1
        else:
            mismatch[key] += 1
    print('agree', sum(agree.values()), 'mismatch', sum(mismatch.values()))
    for k, v in sorted(mismatch.items(), key=lambda kv: -kv[1])[:12]:
        print('  MISMATCH', v, k)
    print('paths by family:')
    for k, v in sorted(Counter((r['solver'], r['family'], r['objective'], path(r['solver'], r['objective'], r['features'])) for r in recs if r.get('events')).items()):
        print('  ', v, k)
