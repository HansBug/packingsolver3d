"""Replay stall-stop rules on every recorded curve: the 0.0.3 rule C, a relative patience E (after = L) and the guarded relative patience E2 shipped since 0.0.4 (never before the first solution).

Usage: TB_WORK=/tmp/tb python stall_policy_replay.py [campaign_merged.jsonl]
"""
import json, math, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get('TB_WORK', '/tmp/tb')
import analyze, model, paths

recs = analyze.load(os.path.join(WORK, 'results', sys.argv[1] if len(sys.argv) > 1 else 'campaign.jsonl'))
rows = [a for a in (analyze.analyse(r) for r in recs) if a]
scale = json.load(open(os.path.join(WORK, 'results', 'scale.json')))
M = model.fit([r for r in rows if r['family'] != 'roadef2022'], scale)
for r in rows:
    r['path'] = paths.path(r['solver'], r['objective'], r['features'])
    r['sc'] = model.scale_of(scale, (r['solver'], r['path']))
CAP = 600.0

def stall_rel(pts, end, T, after, rho, pmin):
    prev = 0.0
    for t, _ in pts:
        fire = max(after, prev + max(pmin, rho * prev))
        if fire < t and fire <= min(T, end):
            return fire
        prev = t
    return min(T, end, max(after, prev + max(pmin, rho * prev)))

def stall_rel_guarded(pts, end, T, after, rho, pmin):
    """Relative patience that never fires before the first solution (the shipped rule's shape)."""
    if not pts:
        return min(T, end)
    prev = pts[0][0]
    for t, _ in pts[1:]:
        fire = max(after, prev + max(pmin, rho * prev))
        if fire < t and fire <= min(T, end):
            return fire
        prev = t
    return min(T, end, max(after, prev + max(pmin, rho * prev)))


def replay(r, alpha, policy, **kw):
    p = model.predict(M, r['solver'], r['objective'], r['features'], alpha)
    sc = r['sc']
    T = min(max(p['time_limit'], 1.0), CAP) / sc          # campaign seconds
    L = p['latency'] / sc
    end = r['end']
    if policy == 'A':
        stop = min(T, end)
    elif policy == 'C':
        stop = model.stall_stop(r['pts'], end, T, max(L, T / 2), max(2.0, p['extra'] / 2) / sc)
    elif policy == 'E':
        stop = stall_rel(r['pts'], end, T, L if kw.get('after', 'L') == 'L' else 0.0, kw['rho'], kw['pmin'] / sc)
    elif policy == 'E2':
        stop = stall_rel_guarded(r['pts'], end, T, L, kw['rho'], kw['pmin'] / sc)
    q = analyze.quality_at(r['pts'], stop, r['ref_run'])
    return stop * sc, T * sc, q, r['t_last'] * sc

def pct(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)] if xs else float('nan')

GROUPS = [('box/TSMS', lambda r: r['solver'] == 'box' and r['path'] == 'TSMS'),
          ('boxstacks/SOR (Stowly-like)', lambda r: r['solver'] == 'boxstacks' and r['path'] == 'SOR' and r['family'] != 'roadef2022'),
          ('box/TS', lambda r: r['solver'] == 'box' and r['path'] == 'TS'),
          ('Stowly-like all', lambda r: r['family'] in ('demo', 'synthetic'))]
POLICIES = [('A: time limit only', 'A', {}), ('C: shipped (after=max(L,T/2), patience=(T-L)/2)', 'C', {}),
            ('E: after=L, patience=max(2 s, 0.5*t_last)', 'E', dict(rho=0.5, pmin=2)),
            ('E: after=L, patience=max(2 s, 1.0*t_last)', 'E', dict(rho=1.0, pmin=2)),
            ('E: after=L, patience=max(5 s, 1.0*t_last)', 'E', dict(rho=1.0, pmin=5)),
            ('E: after=L, patience=max(2 s, 1.5*t_last)', 'E', dict(rho=1.5, pmin=2)),
            ('E: after=L, patience=max(2 s, 2.0*t_last)', 'E', dict(rho=2.0, pmin=2))] + \
    [(f'E2: >=1 solution, patience=max({pm} s, {rho}*t_last)', 'E2', dict(rho=rho, pmin=pm)) for pm in (2, 5) for rho in (1.0, 1.5, 2.0, 3.0, 4.0)]
for alpha in (4.0, 8.0):
    print(f'\n## alpha = {alpha}')
    for gname, sel in GROUPS:
        rs = [r for r in rows if sel(r)]
        print(f'\n### {gname}  n={len(rs)}\n')
        print('| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ T p50 / p90 | used ÷ last improvement p50 |')
        print('|---|---|---|---|---|---|---|---|')
        for label, pol, kw in POLICIES:
            res = [replay(r, alpha, pol, **kw) for r in rs]
            qs = [x[2] for x in res]; used = [x[0] for x in res]; ratio = [x[0] / x[1] for x in res]; waste = [x[0] / max(x[3], 0.05) for x in res]
            print(f"| {label} | {pct(qs, .1):.4f} | {100 * sum(q < 0.99 for q in qs) / len(qs):.1f}% | {100 * sum(q < 0.95 for q in qs) / len(qs):.1f}% | {100 * sum(q == 0 for q in qs) / len(qs):.1f}% | {pct(used, .5):.1f} / {pct(used, .9):.1f} | {pct(ratio, .5):.2f} / {pct(ratio, .9):.2f} | {pct(waste, .5):.2f} |")
