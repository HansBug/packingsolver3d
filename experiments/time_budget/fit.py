"""Fit alpha-parameterised time-budget formulas on the analysed curves and evaluate them.

Per instance i we have the improvement curve q_i(t) (relative to the end of the long run) and the end time e_i
(self-termination or t_ref). For a budget T the time actually spent is u = min(T, e_i).
Speed score S(u) = 1 / (1 + u / TAU); F_alpha = (1 + a^2) S q / (a^2 S + q): alpha -> 0 favours speed, alpha -> inf favours quality.
T*_i(alpha) = argmax_T F_alpha. We then regress log T* on log features per stratum and evaluate the formula on every instance.
"""
import json
import os
import math
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402

FEATURES = ['log_items', 'log_types', 'log_stacks', 'log_mipb', 'fill', 'log_bins', 'multi']


def design(rows):
    X = []
    for r in rows:
        f = r['features']
        X.append([1.0, math.log(f['n_items']), math.log(f['n_types']), math.log(max(1, f['n_stacks'])),
                  math.log(f['mean_items_per_bin']), min(f['fill_ratio'], 5.0), math.log(f['n_bins']), 1.0 if f['n_bins'] > 1 else 0.0])
    return np.array(X)


def stratum(r):
    return (r['solver'], 'multi' if r['features']['n_bins'] > 1 else 'single')


def _ols(rows, y, coverage):
    X = design(rows)
    keep = [j for j in range(X.shape[1]) if j == 0 or np.ptp(X[:, j]) > 1e-9]
    beta, *_ = np.linalg.lstsq(X[:, keep], y, rcond=None)
    resid = y - X[:, keep] @ beta
    full = np.zeros(X.shape[1])
    full[keep] = beta
    full[0] += float(np.quantile(resid, coverage))
    return {'beta': full, 'n': len(rows), 'rmse': float(np.sqrt(np.mean(resid ** 2))), 'shift': float(np.quantile(resid, coverage))}


LATENCY_COVERAGE = 0.95  # never recommend less than the time to get any solution, for 95% of instances
D_EPS = 0.1


def fit_alpha(rows, alpha, coverage=0.8):
    """Two-part model per stratum: T = t_first_pred (coverage 0.95) + D_pred(alpha) (coverage `coverage`), both log-linear in the features.

    T*_i(alpha) sits at an improvement time, so D*_i = T*_i - t_first_i >= 0 is the extra time worth waiting beyond the first solution.
    """
    models = {}
    for key in sorted({stratum(r) for r in rows}):
        rs = [r for r in rows if stratum(r) == key and r['opt'][alpha] is not None]
        if len(rs) < 8:
            continue
        lat = _ols(rs, np.array([math.log(max(r['t_first'], 1e-3)) for r in rs]), LATENCY_COVERAGE)
        imp = _ols(rs, np.array([math.log(max(r['opt'][alpha] - r['t_first'], 0.0) + D_EPS) for r in rs]), coverage)
        models[key] = {'latency': lat, 'improve': imp, 'n': len(rs), 'rmse': imp['rmse'], 'rmse_latency': lat['rmse'], 'beta': imp['beta'], 'beta_latency': lat['beta']}
    return models


def predict(models, r):
    m = models.get(stratum(r))
    if m is None:
        return None
    x = design([r])[0]
    return float(math.exp(x @ m['latency']['beta']) + max(math.exp(x @ m['improve']['beta']) - D_EPS, 0.0))


def evaluate(rows, models, floor=1.0, cap=600.0):
    out = []
    for r in rows:
        T = predict(models, r)
        if T is None:
            continue
        T = min(max(T, floor), cap)
        used = min(T, r['end'])
        q = analyze.quality_at(r['pts'], T, r['ref_run'])
        out.append({'id': r['id'], 'family': r['family'], 'solver': r['solver'], 'T': T, 'used': used, 'q': q,
                    'q_first': analyze.quality_at(r['pts'], r['t_first'], r['ref_run']), 't_last': r['t_last'], 'end': r['end']})
    return out


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)] if xs else float('nan')


def report(rows, alphas=analyze.ALPHAS, coverage=0.8):
    print(f"{'alpha':>5s} {'n':>5s} {'q p10':>6s} {'q p50':>6s} {'q<0.99':>7s} {'q<0.95':>7s} {'used p50':>8s} {'used p90':>8s} {'T p50':>6s} {'T p90':>6s} {'waste p50':>9s}")
    for a in alphas:
        models = fit_alpha(rows, a, coverage)
        ev = evaluate(rows, models)
        if not ev:
            continue
        qs = [e['q'] for e in ev]
        used = [e['used'] for e in ev]
        waste = [e['used'] / max(e['t_last'], 0.05) for e in ev]
        print(f"{a:5.2f} {len(ev):5d} {pct(qs, .1):6.4f} {pct(qs, .5):6.4f} {100 * sum(q < 0.99 for q in qs) / len(qs):6.1f}% {100 * sum(q < 0.95 for q in qs) / len(qs):6.1f}% "
              f"{pct(used, .5):8.1f} {pct(used, .9):8.1f} {pct([e['T'] for e in ev], .5):6.1f} {pct([e['T'] for e in ev], .9):6.1f} {pct(waste, .5):9.2f}")
    return models


if __name__ == '__main__':
    recs = analyze.load(sys.argv[1])
    rows = [a for a in (analyze.analyse(r) for r in recs) if a]
    print(len(rows), 'instances')
    models = report(rows)
    for key, m in models.items():
        print(key, 'n', m['n'], 'rmse', round(m['rmse'], 3), 'beta', np.round(m['beta'], 3))
