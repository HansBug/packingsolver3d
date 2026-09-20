"""Interpretable time-budget model, one small formula per upstream algorithm path.

    T(alpha) = L_hat * (1 + m_P(alpha)) + c_P(alpha)

* L_hat = exp(a_P) * size^b_P * types^c_P  -- the first-solution latency: the cost of one full pass of the algorithm
  (block generation + first beam pass for TSMS, the g=1 SOR pass, the first SVC/SSK iteration over all bins). Fitted by
  least squares in log space, intercept shifted so that L_hat covers LATENCY_COVERAGE of the instances of the path.
  size = items for box, stacks for boxstacks (SOR / SVC work on stacks).
* m_P(alpha): for "growth" paths whose queue doubles between passes (TSMS, TS, SOR) the time worth waiting after the
  first solution is a multiple of the first pass: reaching level k costs L * (2^k - 1). m_P(alpha) is the
  IMPROVE_COVERAGE quantile of (T*(alpha) - t_first) / t_first over the path. Single-pass paths (SSK, box SVC,
  boxstacks SVC) have m = 0: their first complete solution is essentially final (it usually proves optimality).
* c_P(alpha): an additive floor for the extra time (IMPROVE_COVERAGE quantile of the absolute extra time), needed where
  the first solution is nearly instantaneous (TS on small instances) so that a multiple of ~0 s means nothing.
"""
import json
import os
import math
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import paths  # noqa: E402

LATENCY_COVERAGE = 0.9
IMPROVE_COVERAGE = 0.8
GROWTH_PATHS = {'TSMS', 'TS', 'SOR'}
MIN_LATENCY = 0.2      # seconds; below this the bridge overhead dominates
ALPHAS = analyze.ALPHAS


def size_of(r):
    return r['features']['n_stacks'] if r['solver'] == 'boxstacks' else r['features']['n_items']


def key_of(r):
    return (r['solver'], paths.path(r['solver'], r['objective'], r['features']))


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)] if xs else float('nan')


SINGLE_PASS_COVERAGE = 0.98   # SSK / SVC: the first complete solution is final, and the run ends by itself, so a generous cap is free
BLOCK_TYPES = 4               # TSMS: block generation hits its 10000-block cap from about this many item types on


def latency_design(solver, path, features):
    """Feature vector of the latency regression for one path (see module docstring)."""
    size = features['n_stacks'] if solver == 'boxstacks' else features['n_items']
    over = 1.0 if features['fill_ratio'] > 1.0 else 0.0
    if path == 'TSMS':
        return [1.0, math.log(size), math.log(features['n_types'])]          # pass term only; the block step is separate
    if path == 'SOR':
        return [1.0, math.log(size), math.log(features['n_types']), over]     # overfull cargo makes the 1D selection stage slow
    return [1.0, math.log(size), math.log(features['n_types'])]


def _quantile_shift_fit(X, y, coverage):
    X = np.array(X)
    y = np.array(y)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    beta[1:] = np.maximum(beta[1:], 0.0)   # a bigger / more heterogeneous / overfull instance never gets a smaller latency
    beta[0] = float(np.mean(y - X[:, 1:] @ beta[1:]))
    resid = y - X @ beta
    return beta, resid


def scale_of(scale, key):
    """`scale` is a float, or a dict {'solver/path': factor, 'default': factor} from calibrate.py."""
    if isinstance(scale, dict):
        return scale.get(f'{key[0]}/{key[1]}', scale['default'])
    return scale


def fit(rows, scale=1.0):
    """`scale` multiplies every measured time (calibration: idle-machine seconds per campaign second), per path or global."""
    model = {}
    groups = defaultdict(list)
    for r in rows:
        groups[key_of(r)].append(r)
    for key, rs in sorted(groups.items()):
        if len(rs) < 8:
            continue
        solver, path = key
        scale_all = scale
        scale = scale_of(scale_all, key)
        growth = path in GROWTH_PATHS
        coverage = LATENCY_COVERAGE if growth else SINGLE_PASS_COVERAGE
        entry = {'n': len(rs), 'growth': growth, 'coverage': coverage, 'block': 0.0, 'm': {}, 'add': {}}
        if path == 'TSMS':
            # block generation step: median first-solution time of small instances with >= BLOCK_TYPES types
            blk = [r['t_first'] * scale for r in rs if r['features']['n_types'] >= BLOCK_TYPES and r['features']['n_items'] <= 300]
            entry['block'] = float(np.median(blk)) if blk else 0.0
            # pass term: fitted on instances where it is visible (first solution clearly above the block step)
            sel = [r for r in rs if (r['t_first'] * scale - (entry['block'] if r['features']['n_types'] >= BLOCK_TYPES else 0.0)) > 0.3 * scale]
            X = [latency_design(solver, path, r['features']) for r in sel]
            y = [math.log(r['t_first'] * scale - (entry['block'] if r['features']['n_types'] >= BLOCK_TYPES else 0.0)) for r in sel]
            beta, resid = _quantile_shift_fit(X, y, coverage)
            # coverage is enforced where the pass term matters (large instances); the block step already covers the small ones
            entry['shift'] = float(np.quantile(resid, coverage))   # log-space distance between the median and the covered prediction
            beta[0] += entry['shift']
            entry['beta'] = beta.tolist()
            entry['rmse_log'] = float(np.sqrt(np.mean(resid ** 2)))
            entry['n_pass_fit'] = len(sel)
        else:
            X = [latency_design(solver, path, r['features']) for r in rs]
            y = [math.log(max(r['t_first'] * scale, 1e-3)) for r in rs]
            beta, resid = _quantile_shift_fit(X, y, coverage)
            entry['shift'] = float(np.quantile(resid, coverage))
            beta[0] += entry['shift']
            entry['beta'] = beta.tolist()
            entry['rmse_log'] = float(np.sqrt(np.mean(resid ** 2)))
        for a in ALPHAS:
            extra = [max(r['opt'][a] - r['t_first'], 0.0) * scale for r in rs if r['opt'][a] is not None]
            if growth:
                ratio = [e / max(r['t_first'] * scale, MIN_LATENCY) for e, r in zip(extra, rs)]
                entry['m'][a] = float(q(ratio, IMPROVE_COVERAGE))
                entry['add'][a] = 0.0
            else:
                entry['m'][a] = 0.0
                entry['add'][a] = float(q(extra, IMPROVE_COVERAGE))
        entry['scale'] = scale
        model[key] = entry
        scale = scale_all
    return model


def _latency(entry, solver, path, features):
    x = np.array(latency_design(solver, path, features))
    lat = math.exp(float(x @ np.array(entry['beta'])))
    if path == 'TSMS' and features['n_types'] >= BLOCK_TYPES:
        lat += entry['block']
    return max(lat, MIN_LATENCY)


def predict(model, solver, objective, features, alpha):
    key = (solver, paths.path(solver, objective, features))
    e = model.get(key)
    if e is None:
        return None
    latency = _latency(e, solver, key[1], features)
    m, add = _interp(e['m'], alpha), _interp(e['add'], alpha)
    extra = latency * m + add
    return {'path': key[1], 'latency': latency, 'extra': extra, 'time_limit': latency + extra}


def _interp(table, alpha):
    xs = sorted(table)
    if alpha <= xs[0]:
        return table[xs[0]]
    if alpha >= xs[-1]:
        return table[xs[-1]]
    for lo, hi in zip(xs, xs[1:]):
        if lo <= alpha <= hi:
            w = (math.log(alpha) - math.log(lo)) / (math.log(hi) - math.log(lo))
            return table[lo] + w * (table[hi] - table[lo])


def stall_stop_relative(pts, end, T, after, ratio, patience):
    """When the shipped watchdog ends a run capped at T: never before the first solution, then once the run has been
    silent for max(patience, ratio x time of the last improvement), and not before `after`."""
    if not pts:
        return min(T, end)
    prev = pts[0][0]
    for t, _ in pts[1:]:
        fire = max(after, prev + max(patience, ratio * prev))
        if fire < t and fire <= min(T, end):
            return fire
        prev = t
    return min(T, end, max(after, prev + max(patience, ratio * prev)))


def stall_stop(pts, end, T, after, patience):
    """When the watchdog (stop_when_unimproved_for=patience, _after=after) would end a run capped at T."""
    last = 0.0
    for t, _ in pts:
        fire = max(after, last + patience)
        if fire < t and fire <= min(T, end):
            return fire
        last = t
    return min(T, end, max(after, last + patience))


def evaluate(rows, model, alpha, scale=1.0, kappa=None, floor=1.0, cap=600.0):
    out = []
    for r in rows:
        p = predict(model, r['solver'], r['objective'], r['features'], alpha)
        if p is None:
            continue
        sc = scale_of(scale, (r['solver'], p['path']))
        T = min(max(p['time_limit'], floor), cap) / sc  # back to campaign seconds for replay
        end = r['end']
        if kappa is None:
            stop = min(T, end)
        else:
            # the shipped rule: floor 5 s, ratio alpha / 2 clamped to 1 ... 4, not before the covered latency
            ratio = min(max(alpha / 2.0, 1.0), 4.0)
            stop = stall_stop_relative(r['pts'], end, T, p['latency'] / sc, ratio, 5.0 / sc)
        qv = analyze.quality_at(r['pts'], stop, r['ref_run'])
        out.append({'id': r['id'], 'family': r['family'], 'solver': r['solver'], 'path': p['path'], 'T': T * sc, 'used': stop * sc, 'q': qv,
                    't_last': r['t_last'] * sc, 'tstar': (r['opt'][alpha] or 0) * sc})
    return out


def table(ev, by):
    groups = defaultdict(list)
    for e in ev:
        groups[by(e)].append(e)
    lines = ['| group | n | q p10 | q p50 | q<0.99 | q<0.95 | no solution | used p50 / p90 (s) | T p50 / p90 (s) | T* p50 (s) | used ÷ last improvement p50 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for g, es in sorted(groups.items()):
        qs = [e['q'] for e in es]
        lines.append(f"| {g} | {len(es)} | {q(qs, .1):.4f} | {q(qs, .5):.4f} | {100 * sum(x < 0.99 for x in qs) / len(qs):.1f}% | {100 * sum(x < 0.95 for x in qs) / len(qs):.1f}% | "
                     f"{100 * sum(x == 0 for x in qs) / len(qs):.1f}% | {q([e['used'] for e in es], .5):.1f} / {q([e['used'] for e in es], .9):.1f} | "
                     f"{q([e['T'] for e in es], .5):.1f} / {q([e['T'] for e in es], .9):.1f} | {q([e['tstar'] for e in es], .5):.1f} | {q([e['used'] / max(e['t_last'], 0.05) for e in es], .5):.2f} |")
    return '\n'.join(lines)


def constants_table(model):
    lines = ['| solver / path | n | growth | coverage | latency formula (s) | rmse(log) | m(4) | add(4) | m(8) | add(8) | example L / T(4) / T(8): size 1000, 10 types, overfull |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for key, e in sorted(model.items()):
        b = e['beta']
        names = ['log size', 'log types', 'overfull'][:len(b) - 1]
        formula = ' + '.join([f'{b[0]:+.2f}'] + [f'{v:+.2f}·{n}' for v, n in zip(b[1:], names)])
        if key[1] == 'TSMS':
            formula = f"{e['block']:.2f} s·[types>={BLOCK_TYPES}] + exp({formula})"
        else:
            formula = f'exp({formula})'
        f = {'n_items': 1000, 'n_stacks': 1000, 'n_types': 10, 'fill_ratio': 1.5}
        L = _latency(e, key[0], key[1], f)
        T4 = L * (1 + e['m'][4.0]) + e['add'][4.0]
        T8 = L * (1 + e['m'][8.0]) + e['add'][8.0]
        lines.append(f"| {key[0]}/{key[1]} | {e['n']} | {'yes' if e['growth'] else 'no'} | {e['coverage']:.2f} | {formula} | {e['rmse_log']:.2f} | {e['m'][4.0]:.2f} | {e['add'][4.0]:.1f} | {e['m'][8.0]:.2f} | {e['add'][8.0]:.1f} | {L:.1f} / {T4:.1f} / {T8:.1f} |")
    return '\n'.join(lines)


if __name__ == '__main__':
    recs = analyze.load(sys.argv[1])
    scale = 1.0
    if len(sys.argv) > 2:
        scale = json.load(open(sys.argv[2])) if sys.argv[2].endswith('.json') else float(sys.argv[2])
    rows = [a for a in (analyze.analyse(r) for r in recs) if a]
    # ROADEF instances are tiny and all finish in < 1 s: they are evaluated but not fitted (they would swamp the SOR path)
    fit_rows = [r for r in rows if r['family'] != 'roadef2022']
    model = fit(fit_rows, scale)
    md = ['## Constants per path (idle-machine seconds; per-path load calibration %s; fitted without ROADEF)\n' % (json.dumps({k: round(v, 3) for k, v in scale.items()}) if isinstance(scale, dict) else scale), constants_table(model)]
    nosol = [r for r in recs if not r.get('error') and not r.get('events')]
    md += ['\n## Instances with no solution within t_ref, and the latency the model predicts for them\n', '| id | items | stacks | types | bins | t_ref | predicted L |', '|---|---|---|---|---|---|---|']
    for r in nosol:
        pr = predict(model, r['solver'], r['objective'], r['features'], 4.0)
        md.append(f"| {r['id']} | {r['features']['n_items']} | {r['features']['n_stacks']} | {r['features']['n_types']} | {r['features']['n_bins']} | {r['t_ref']} | {pr['latency'] if pr else float('nan'):.0f} |")
    for a in (4.0, 8.0):
        ev = evaluate(rows, model, a, scale)
        md += [f'\n## alpha = {a}: time limit only\n', table(ev, lambda e: e['solver'] + '/' + e['path'] + ('' if e['family'] != 'roadef2022' else ' (ROADEF)')), '', table(ev, lambda e: e['solver'] + '/' + e['family'])]
        for kappa in (0.5,):
            evk = evaluate(rows, model, a, scale, kappa=kappa)
            md += [f'\n### alpha = {a}, with the shipped stall stop: not before the first solution nor L, patience = max(5 s, clamp(alpha/2, 1, 4) × t_last)\n', table(evk, lambda e: e['solver'] + '/' + e['path'] + ('' if e['family'] != 'roadef2022' else ' (ROADEF)'))]
    out = '\n'.join(md)
    open(os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'model_report.md'), 'w').write(out + '\n')
    json.dump({f'{k[0]}/{k[1]}': v for k, v in model.items()}, open(os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'model_constants.json'), 'w'), indent=1)
    print(out)
