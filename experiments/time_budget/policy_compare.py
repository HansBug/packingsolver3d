"""Replay three stopping policies on every recorded curve, also under a mis-estimated machine speed.

A(alpha)  : fixed time limit from the formula only.
B(P)      : stagnation only -- stop when no improvement for P seconds (clock from start unless `after` given), cap 600 s.
B_L(P)    : stagnation with the model's latency as the earliest stop (after = L), cap 600 s.
C(alpha)  : the PR rule -- T from the formula, after = max(L, T/2), patience = max(2, (T-L)/2).
Speed factor k: the real machine is k times slower than assumed (curve times multiplied by k); policy parameters unchanged.
"""
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import model  # noqa: E402
import paths  # noqa: E402

WORK = os.environ.get('TB_WORK', '/tmp/tb')
recs = analyze.load(os.path.join(WORK, 'results', 'campaign.jsonl'))
rows = [a for a in (analyze.analyse(r) for r in recs) if a]
scale = json.load(open(os.path.join(WORK, 'results', 'scale.json')))
fit_rows = [r for r in rows if r['family'] != 'roadef2022']
M = model.fit(fit_rows, scale)
for r in rows:
    r['path'] = paths.path(r['solver'], r['objective'], r['features'])
    r['sc'] = model.scale_of(scale, (r['solver'], r['path']))
CAP = 600.0


def replay(r, k, policy, param):
    """Return (stop time in idle seconds, quality). Curve times converted to idle seconds then slowed by k."""
    pts = [(t * r['sc'] * k, v) for t, v in r['pts']]
    end = r['end'] * r['sc'] * k          # self-termination also scales with the machine
    p = model.predict(M, r['solver'], r['objective'], r['features'], param if policy in ('A', 'C') else 4.0)
    if policy == 'A':
        T = min(max(p['time_limit'], 1.0), CAP)
        stop = min(T, end)
    elif policy == 'B':
        stop = model.stall_stop(pts, end, CAP, 0.0, param)
    elif policy == 'B_L':
        stop = model.stall_stop(pts, end, CAP, p['latency'], param)
    elif policy == 'C':
        T = min(max(p['time_limit'], 1.0), CAP)
        stop = model.stall_stop(pts, end, T, max(p['latency'], T / 2), max(2.0, p['extra'] / 2))
    else:
        raise ValueError(policy)
    q = analyze.quality_at(pts, stop, r['ref_run'])
    return stop, q


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)] if xs else float('nan')


POLICIES = [('A', 4.0, 'A: time limit only, alpha=4'), ('A', 8.0, 'A: time limit only, alpha=8'),
            ('B', 3.0, 'B: stagnation only, patience 3 s'), ('B', 5.0, 'B: stagnation only, patience 5 s'), ('B', 10.0, 'B: stagnation only, patience 10 s'),
            ('B_L', 5.0, 'B_L: patience 5 s, not before predicted first solution'), ('B_L', 10.0, 'B_L: patience 10 s, not before predicted first solution'),
            ('C', 4.0, 'C: PR rule, alpha=4'), ('C', 8.0, 'C: PR rule, alpha=8')]
GROUPS = [('box/TSMS', lambda r: r['solver'] == 'box' and r['path'] == 'TSMS'),
          ('box/TS', lambda r: r['solver'] == 'box' and r['path'] == 'TS'),
          ('boxstacks/SOR (Stowly-like)', lambda r: r['solver'] == 'boxstacks' and r['path'] == 'SOR' and r['family'] != 'roadef2022'),
          ('box/SSK', lambda r: r['solver'] == 'box' and r['path'] == 'SSK'),
          ('boxstacks/SVC', lambda r: r['solver'] == 'boxstacks' and r['path'] == 'SVC'),
          ('Stowly-like all (demo+synthetic)', lambda r: r['family'] in ('demo', 'synthetic'))]
out = []
for k in (1.0, 2.0, 0.5):
    out.append(f'\n## machine {k:g}x slower than assumed' if k != 1.0 else '\n## machine speed as assumed (k = 1)')
    for gname, sel in GROUPS:
        rs = [r for r in rows if sel(r)]
        out.append(f'\n### {gname}  n={len(rs)}\n')
        out.append('| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 | ran to cap |')
        out.append('|---|---|---|---|---|---|---|---|')
        for pol, par, label in POLICIES:
            res = [replay(r, k, pol, par) for r in rs]
            qs = [q for _, q in res]
            used = [s for s, _ in res]
            waste = [s / max(r['t_last'] * r['sc'] * k, 0.05) for (s, _), r in zip(res, rs)]
            capped = sum(1 for (s, _), r in zip(res, rs) if s >= min(CAP, r['end'] * r['sc'] * k) - 1e-9 and r['end'] >= r['t_ref'] - 0.5)
            out.append(f'| {label} | {pct(qs, .1):.4f} | {100 * sum(q < 0.99 for q in qs) / len(qs):.1f}% | {100 * sum(q < 0.95 for q in qs) / len(qs):.1f}% | '
                       f'{100 * sum(q == 0 for q in qs) / len(qs):.1f}% | {pct(used, .5):.1f} / {pct(used, .9):.1f} | {pct(waste, .5):.2f} | {100 * capped / len(rs):.0f}% |')
md = '\n'.join(out)
open(os.path.join(WORK, 'results', 'policy_compare.md'), 'w').write(md)
print(md)


# ---------------------------------------------------------------- D: adaptive stagnation, patience relative to the OBSERVED first solution
def replay_D(r, k, alpha, kappa, cap_alpha):
    pts = [(t * r['sc'] * k, v) for t, v in r['pts']]
    end = r['end'] * r['sc'] * k
    p = model.predict(M, r['solver'], r['objective'], r['features'], alpha)
    pc = model.predict(M, r['solver'], r['objective'], r['features'], cap_alpha)
    T = min(max(pc['time_limit'], 1.0), CAP)
    t_first = pts[0][0]
    patience = max(2.0, kappa * t_first)
    stop = model.stall_stop(pts, end, T, p['latency'], patience)
    return stop, analyze.quality_at(pts, stop, r['ref_run'])


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'D':
    out = []
    for k in (1.0, 2.0, 0.5):
        out.append(f'\n## D (adaptive patience = max(2 s, kappa x observed first-solution time), after = L, cap = T(alpha)); machine k={k:g}')
        for gname, sel in GROUPS[:3] + GROUPS[5:]:
            rs = [r for r in rows if sel(r)]
            out.append(f'\n### {gname}  n={len(rs)}\n')
            out.append('| policy | q p10 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | used ÷ last improvement p50 |')
            out.append('|---|---|---|---|---|---|---|')
            for label, fn in [('C: PR rule, alpha=4', lambda r: replay(r, k, 'C', 4.0)), ('C: PR rule, alpha=8', lambda r: replay(r, k, 'C', 8.0)),
                              ('D: kappa=1, cap T(4)', lambda r: replay_D(r, k, 4.0, 1.0, 4.0)), ('D: kappa=2, cap T(4)', lambda r: replay_D(r, k, 4.0, 2.0, 4.0)),
                              ('D: kappa=2, cap T(8)', lambda r: replay_D(r, k, 4.0, 2.0, 8.0)), ('D: kappa=4, cap T(8)', lambda r: replay_D(r, k, 4.0, 4.0, 8.0)),
                              ('D: kappa=8, cap T(8)', lambda r: replay_D(r, k, 4.0, 8.0, 8.0))]:
                res = [fn(r) for r in rs]
                qs = [q for _, q in res]; used = [s for s, _ in res]
                waste = [s / max(r['t_last'] * r['sc'] * k, 0.05) for (s, _), r in zip(res, rs)]
                out.append(f'| {label} | {pct(qs, .1):.4f} | {100 * sum(q < 0.99 for q in qs) / len(qs):.1f}% | {100 * sum(q < 0.95 for q in qs) / len(qs):.1f}% | '
                           f'{100 * sum(q == 0 for q in qs) / len(qs):.1f}% | {pct(used, .5):.1f} / {pct(used, .9):.1f} | {pct(waste, .5):.2f} |')
    md = '\n'.join(out)
    open(os.path.join(WORK, 'results', 'policy_compare_D.md'), 'w').write(md)
    print(md)
