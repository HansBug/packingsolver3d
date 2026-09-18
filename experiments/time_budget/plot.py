"""Figures for the PR comment: per-family curves, demo curves with the recommended budgets, latency fit, T*(alpha), formula evaluation."""
import json
import math
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import model  # noqa: E402
import paths  # noqa: E402

WORK = os.environ.get('TB_WORK', '/tmp/tb')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'results', 'figures')
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'figure.dpi': 110})

recs = analyze.load(os.path.join(WORK, 'results', 'campaign.jsonl'))
rows = [a for a in (analyze.analyse(r) for r in recs) if a]
scale = json.load(open(os.path.join(WORK, 'results', 'scale.json')))
fit_rows = [r for r in rows if r['family'] != 'roadef2022']
M = model.fit(fit_rows, scale)
for r in rows:
    r['path'] = paths.path(r['solver'], r['objective'], r['features'])
    r['key'] = f"{r['solver']}/{r['path']}"
    r['sc'] = model.scale_of(scale, (r['solver'], r['path']))


def q_curve(r, grid):
    return np.array([analyze.quality_at(r['pts'], t, r['ref_run']) for t in grid])


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)] if xs else float('nan')


# ---------------------------------------------------------------- F1: per-family quality curves
groups = defaultdict(list)
for r in rows:
    groups[(r['solver'], r['family'], r['objective'])].append(r)
keys = sorted(groups)
fig, axes = plt.subplots(4, 4, figsize=(15, 12), sharey=True)
for ax, g in zip(axes.flat, keys):
    rs = groups[g]
    t_ref = rs[0]['t_ref']
    grid = np.logspace(-2, math.log10(t_ref), 160)
    Q = np.array([q_curve(r, grid) for r in rs])
    ax.fill_between(grid, np.percentile(Q, 10, axis=0), np.percentile(Q, 90, axis=0), color='tab:blue', alpha=0.2, label='p10-p90')
    ax.plot(grid, np.median(Q, axis=0), color='tab:blue', lw=2, label='median')
    ax.plot(grid, np.percentile(Q, 25, axis=0), color='tab:blue', lw=0.8, ls=':', label='p25')
    for a, color in ((4.0, 'tab:orange'), (8.0, 'tab:red')):
        Ts = []
        for r in rs:
            p = model.predict(M, r['solver'], r['objective'], r['features'], a)
            if p:
                Ts.append(min(max(p['time_limit'], 1.0), 600.0) / r['sc'])   # back to campaign seconds
        if Ts:
            ax.axvline(pct(Ts, .5), color=color, lw=1.5, label=f'formula T, alpha={a:g} (median)')
    ax.set_xscale('log')
    ax.set_xlim(0.01, 160)
    ax.set_ylim(0, 1.02)
    ax.set_title(f"{'/'.join(g)}  n={len(rs)}", fontsize=8.5)
    ax.grid(True, which='both', alpha=0.25)
for ax in axes[-1]:
    ax.set_xlabel('time since start (s, campaign machine, log)')
for ax in axes[:, 0]:
    ax.set_ylabel('value / value at end of run')
for ax in axes.flat[len(keys):]:
    ax.axis('off')
axes.flat[0].legend(loc='lower right', fontsize=7)
fig.suptitle('F1. Relative quality vs time per family (band = 10th-90th percentile over instances); vertical lines = median recommended time_limit', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(os.path.join(OUT, 'f1_family_curves.png'))
plt.close(fig)

# ---------------------------------------------------------------- F1b: same, zoomed on the last 10 %
fig, axes = plt.subplots(4, 4, figsize=(15, 12), sharey=True)
for ax, g in zip(axes.flat, keys):
    rs = groups[g]
    t_ref = rs[0]['t_ref']
    grid = np.logspace(-2, math.log10(t_ref), 160)
    Q = np.array([q_curve(r, grid) for r in rs])
    ax.fill_between(grid, np.percentile(Q, 10, axis=0), np.percentile(Q, 90, axis=0), color='tab:blue', alpha=0.2, label='p10-p90')
    ax.plot(grid, np.median(Q, axis=0), color='tab:blue', lw=2, label='median')
    ax.plot(grid, np.percentile(Q, 25, axis=0), color='tab:blue', lw=0.8, ls=':', label='p25')
    for a, color in ((4.0, 'tab:orange'), (8.0, 'tab:red')):
        Ts = [min(max(model.predict(M, r['solver'], r['objective'], r['features'], a)['time_limit'], 1.0), 600.0) / r['sc'] for r in rs]
        ax.axvline(pct(Ts, .5), color=color, lw=1.5, label=f'formula T, alpha={a:g} (median)')
        ax.axvline(pct(Ts, .9), color=color, lw=1, ls='--', label=f'formula T, alpha={a:g} (p90)')
    ax.axhline(0.99, color='k', lw=0.6, ls=':')
    ax.set_xscale('log')
    ax.set_xlim(0.01, 160)
    ax.set_ylim(0.9, 1.003)
    ax.set_title(f"{'/'.join(g)}  n={len(rs)}", fontsize=8.5)
    ax.grid(True, which='both', alpha=0.25)
for ax in axes[-1]:
    ax.set_xlabel('time since start (s, campaign machine, log)')
for ax in axes[:, 0]:
    ax.set_ylabel('value / value at end of run')
for ax in axes.flat[len(keys):]:
    ax.axis('off')
axes.flat[0].legend(loc='lower right', fontsize=7)
fig.suptitle('F1b. Same curves, zoomed on the last 10 % (dotted line = 99 %); vertical lines = recommended time_limit, median (solid) and p90 (dashed)', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(os.path.join(OUT, 'f1b_family_curves_zoom.png'))
plt.close(fig)

# ---------------------------------------------------------------- F2: demo container curves with recommended budgets and stall stop
demo = [r for r in rows if r['family'] == 'demo']
variants = [('demo', 'x1: 1036 items, 5 types'), ('demo_x2', 'x2: 2072 items, 5 types'), ('demo_ten', 'ten types: 1554 items')]
fig, axes = plt.subplots(2, 3, figsize=(15, 7.5), sharey='row')
for row_i, solver in enumerate(('box', 'boxstacks')):
    for col_i, (tag, label) in enumerate(variants):
        ax = axes[row_i, col_i]
        rs = [r for r in demo if r['solver'] == solver and r['objective'] == 'knapsack' and r['id'].startswith(f'{solver}/{tag}/')]
        for k, r in enumerate(rs):
            ts = [0.0] + [t for t, _ in r['pts']] + [r['t_ref']]
            vs = [0.0] + [analyze.quality_at(r['pts'], t, r['ref_run']) for t, _ in r['pts']] + [1.0]
            ax.step(ts, vs, where='post', color='tab:blue', alpha=0.7, lw=1.2, label='recorded runs (3 repeats)' if k == 0 else None)
        r0 = rs[0]
        for a, color in ((4.0, 'tab:orange'), (8.0, 'tab:red')):
            p = model.predict(M, r0['solver'], r0['objective'], r0['features'], a)
            T = min(max(p['time_limit'], 1.0), 600.0) / r0['sc']
            ax.axvline(T, color=color, lw=1.8, label=f"time_limit alpha={a:g}: {p['time_limit']:.0f} s idle ({T:.0f} s here)")
            ax.axvline(p['latency'] / r0['sc'], color=color, lw=1, ls='--', label=f'predicted first solution L alpha={a:g}' if a == 4.0 else None)
            after = max(p['latency'], p['time_limit'] / 2) / r0['sc']
            patience = max(2.0, p['extra'] / 2) / r0['sc']
            stops = [model.stall_stop(r['pts'], r['end'], T, after, patience) for r in rs]
            ax.scatter(stops, [analyze.quality_at(r['pts'], s, r['ref_run']) for r, s in zip(rs, stops)], color=color, marker='x', s=60, zorder=5,
                       label=f'stall-stop point alpha={a:g}')
        ax.set_xscale('log')
        ax.set_xlim(0.1, 160)
        ax.set_ylim(0.5, 1.01)
        ax.grid(True, which='both', alpha=0.25)
        ax.set_title(f'{solver} knapsack, {label}')
        if row_i == 1:
            ax.set_xlabel('time since start (s, campaign machine, log)')
        if col_i == 0:
            ax.set_ylabel('value / value at 150 s')
        ax.legend(fontsize=6.5, loc='lower right')
fig.suptitle("F2. Stowly demo 40' HQ container: recorded curves, predicted first solution, recommended time_limit and where the stall stop would end the run", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(os.path.join(OUT, 'f2_demo_budgets.png'))
plt.close(fig)

# ---------------------------------------------------------------- F3: latency fit per path (idle seconds)
fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
for ax, key in zip(axes.flat, sorted(M)):
    rs = [r for r in rows if (r['solver'], r['path']) == key]
    e = M[key]
    xs = [r['t_first'] * r['sc'] for r in rs]
    ys = [model._latency(e, key[0], key[1], r['features']) for r in rs]
    colors = ['tab:gray' if r['family'] == 'roadef2022' else ('tab:red' if r['family'] in ('demo', 'synthetic') else 'tab:blue') for r in rs]
    ax.scatter(xs, ys, c=colors, s=10, alpha=0.6)
    lo, hi = 1e-3, 1000
    ax.plot([lo, hi], [lo, hi], 'k-', lw=1, label='predicted = measured')
    ax.plot([lo, hi], [lo * 2, hi * 2], 'k:', lw=0.8, label='x2')
    ax.plot([lo, hi], [lo / 2, hi / 2], 'k:', lw=0.8)
    covered = np.mean([y >= x for x, y in zip(xs, ys)]) if xs else float('nan')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlim(1e-3, 1000); ax.set_ylim(1e-1, 1000)
    ax.set_title(f"{key[0]}/{key[1]}  n={len(rs)}  target coverage {e['coverage']:.0%}, achieved {covered:.0%}\n{'growth: T = L(1+m)' if e['growth'] else 'single pass: T = L + c'}", fontsize=8.5)
    ax.set_xlabel('measured first-solution time (s, idle-machine scale)')
    ax.set_ylabel('predicted latency L (s)')
    ax.grid(True, which='both', alpha=0.25)
axes.flat[0].scatter([], [], c='tab:blue', label='upstream families'); axes.flat[0].scatter([], [], c='tab:red', label='synthetic + demo'); axes.flat[0].scatter([], [], c='tab:gray', label='ROADEF (not fitted)')
axes.flat[0].legend(fontsize=7, loc='upper left')
fig.suptitle('F3. First-solution latency: measured vs predicted per algorithm path (points above the diagonal are covered by the budget)', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(os.path.join(OUT, 'f3_latency_fit.png'))
plt.close(fig)

# ---------------------------------------------------------------- F4: T*(alpha) per path vs formula
fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
for ax, key in zip(axes, [('box', 'TSMS'), ('box', 'TS'), ('boxstacks', 'SOR')]):
    rs = [r for r in rows if (r['solver'], r['path']) == key and r['family'] != 'roadef2022']
    alphas = analyze.ALPHAS
    for p, ls, lab in ((0.5, '-', 'T* median'), (0.8, '--', 'T* p80'), (0.9, ':', 'T* p90')):
        ax.plot(alphas, [pct([r['opt'][a] * r['sc'] for r in rs], p) for a in alphas], color='tab:blue', ls=ls, marker='o', ms=3, label=lab)
    ax.plot(alphas, [pct([min(max(model.predict(M, r['solver'], r['objective'], r['features'], a)['time_limit'], 1), 600) for r in rs], .5) for a in alphas],
            color='tab:orange', marker='s', ms=4, label='formula T median')
    ax.plot(alphas, [pct([r['t_first'] * r['sc'] for r in rs], .5) for _ in alphas], color='tab:gray', ls='-.', label='first solution median')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xticks(alphas); ax.set_xticklabels([f'{a:g}' for a in alphas])
    ax.set_xlabel('alpha'); ax.set_ylabel('seconds (idle machine)')
    ax.set_title(f"{key[0]}/{key[1]}  n={len(rs)} (non-ROADEF)")
    ax.grid(True, which='both', alpha=0.25)
    ax.legend(fontsize=7)
fig.suptitle('F4. How alpha moves the per-instance optimum T* (F-alpha maximiser) and the fitted formula, growth paths', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(os.path.join(OUT, 'f4_alpha_tstar.png'))
plt.close(fig)

# ---------------------------------------------------------------- F5: quality achieved with the formula (CDF) and time used
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for col, key in enumerate([('box', 'TSMS'), ('box', 'TS'), ('boxstacks', 'SOR')]):
    rs = [r for r in rows if (r['solver'], r['path']) == key and r['family'] != 'roadef2022']
    ax_q, ax_t = axes[0, col], axes[1, col]
    for a, color in ((4.0, 'tab:orange'), (8.0, 'tab:red')):
        for kappa, ls, lab in ((None, '-', 'time limit only'), (0.5, '--', '+ stall stop')):
            ev = model.evaluate(rs, M, a, scale, kappa=kappa)
            qs = np.sort([e['q'] for e in ev])
            ax_q.step(qs, np.linspace(0, 1, len(qs)), where='post', color=color, ls=ls, label=f'alpha={a:g}, {lab}')
            used = np.sort([e['used'] for e in ev])
            ax_t.step(used, np.linspace(0, 1, len(used)), where='post', color=color, ls=ls, label=f'alpha={a:g}, {lab}')
    tl = np.sort([r['t_last'] * r['sc'] for r in rs])
    ax_t.step(tl, np.linspace(0, 1, len(tl)), where='post', color='tab:gray', ls='-.', label='time of last improvement (reference run)')
    ax_q.set_xlim(0.9, 1.001); ax_q.set_xlabel('quality reached / reference'); ax_q.set_ylabel('share of instances (CDF)')
    ax_q.set_title(f"{key[0]}/{key[1]}  n={len(rs)}"); ax_q.grid(True, alpha=0.25); ax_q.legend(fontsize=6.5, loc='upper left')
    ax_t.set_xscale('log'); ax_t.set_xlabel('time used (s, idle machine)'); ax_t.set_ylabel('share of instances (CDF)'); ax_t.grid(True, which='both', alpha=0.25); ax_t.legend(fontsize=6.5, loc='lower right')
fig.suptitle('F5. Replaying the recommendation on every recorded curve: quality reached (top) and time spent (bottom), alpha 4 vs 8, with and without the stall stop', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(os.path.join(OUT, 'f5_formula_eval.png'))
plt.close(fig)

# ---------------------------------------------------------------- F6: formula T vs per-instance optimum T* (looseness)
fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
for ax, a in zip(axes, (4.0, 8.0)):
    for key, color in ((('box', 'TSMS'), 'tab:blue'), (('box', 'TS'), 'tab:green'), (('boxstacks', 'SOR'), 'tab:purple'), (('box', 'SSK'), 'tab:brown'), (('boxstacks', 'SVC'), 'tab:pink')):
        rs = [r for r in rows if (r['solver'], r['path']) == key and r['family'] != 'roadef2022']
        xs = [max(r['opt'][a] * r['sc'], 0.05) for r in rs]
        ys = [min(max(model.predict(M, r['solver'], r['objective'], r['features'], a)['time_limit'], 1), 600) for r in rs]
        ax.scatter(xs, ys, s=9, alpha=0.55, color=color, label=f"{key[0]}/{key[1]} (n={len(rs)})")
    ax.plot([0.05, 600], [0.05, 600], 'k-', lw=1); ax.plot([0.05, 600], [0.15, 1800], 'k:', lw=0.8, label='x3')
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(0.05, 600); ax.set_ylim(0.5, 700)
    ax.set_xlabel(f'per-instance optimum T*(alpha={a:g}) (s)'); ax.set_ylabel('recommended time_limit (s)')
    ax.set_title(f'alpha = {a:g}'); ax.grid(True, which='both', alpha=0.25); ax.legend(fontsize=7, loc='upper left')
fig.suptitle('F6. How loose the upper bound is: recommended time_limit vs the budget each instance actually deserved', fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(os.path.join(OUT, 'f6_looseness.png'))
plt.close(fig)
print('figures written to', OUT, sorted(os.listdir(OUT)))
