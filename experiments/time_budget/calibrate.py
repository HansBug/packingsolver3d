"""Compare the same instances solved under campaign load and on the idle machine; output the inflation factor per path."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

camp = {}
for l in open(os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'campaign.jsonl')):
    r = json.loads(l)
    camp[r['id']] = r
cal = [json.loads(l) for l in open(os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'calib.jsonl'))]


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)] if xs else float('nan')


rows = []
for c in cal:
    r = camp.get(c['id'])
    if not r or not c.get('events') or not r.get('events'):
        continue
    path = paths.path(r['solver'], r['objective'], r['features'])
    tf_ratio = r['events'][0][0] / max(c['events'][0][0], 1e-3)
    # time to reach 99% of the (campaign) final value in both runs, when both reached it
    def t99(rec, ref):
        best = None
        for t, items, bins, profit, cost, label in rec['events']:
            v = -bins if rec['objective'] != 'knapsack' else profit
            if best is None or v > best:
                best = v
            if (ref < 0 and ref / best >= 0.99) or (ref > 0 and best / ref >= 0.99):
                return t
        return None
    minimize = r['objective'] != 'knapsack'
    finals = []
    for rec in (r, c):
        vals = [(-e[2] if minimize else e[3]) for e in rec['events']]
        finals.append(max(vals))
    ref = min(finals) if not minimize else max(finals)  # the weaker final so that both runs reached it
    a, b = t99(r, ref), t99(c, ref)
    rows.append({'id': c['id'], 'path': r['solver'] + '/' + path, 'tf_camp': r['events'][0][0], 'tf_idle': c['events'][0][0], 'tf_ratio': tf_ratio,
                 't99_camp': a, 't99_idle': b, 't99_ratio': (a / max(b, 1e-3)) if a is not None and b is not None and b > 0.05 else None,
                 'cores': c['cpu'] / c['wall']})
lines = ['| solver/path | n | first-solution ratio load/idle p25 / p50 / p75 | time-to-99% ratio p50 (n) | idle cores per solve p50 |', '|---|---|---|---|---|']
by = {}
for x in rows:
    by.setdefault(x['path'], []).append(x)
overall = [x['tf_ratio'] for x in rows if x['tf_idle'] > 0.05]
for k, xs in sorted(by.items()):
    tf = [x['tf_ratio'] for x in xs if x['tf_idle'] > 0.05]   # sub-50 ms first solutions are noise
    t9 = [x['t99_ratio'] for x in xs if x['t99_ratio'] is not None]
    lines.append(f"| {k} | {len(xs)} | {q(tf, .25):.2f} / {q(tf, .5):.2f} / {q(tf, .75):.2f} | {q(t9, .5) if t9 else float('nan'):.2f} ({len(t9)}) | {q([x['cores'] for x in xs], .5):.1f} |")
lines.append(f"| all (first solution > 50 ms) | {len(overall)} | {q(overall, .25):.2f} / {q(overall, .5):.2f} / {q(overall, .75):.2f} | | |")
md = '# Load calibration: 80 instances rerun on the idle machine (2 slots)\n\n' + '\n'.join(lines) + '\n'
open(os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'calibration.md'), 'w').write(md)
print(md)
global_scale = 1 / q(overall, .5)
scale = {'default': global_scale}
for k, xs in sorted(by.items()):
    tf = [x['tf_ratio'] for x in xs if x['tf_idle'] > 0.05]
    if len(tf) >= 5:
        scale[k] = 1 / q(tf, .5)
json.dump(scale, open(os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'scale.json'), 'w'), indent=1)
print('scale.json (idle seconds per campaign second):', {k: round(v, 3) for k, v in scale.items()})
