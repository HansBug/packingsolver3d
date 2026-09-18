"""Markdown tables for the chat / PR comment plus CSV/JSON exports for the gist."""
import csv
import json
import os
import math
import sys
from collections import defaultdict

import numpy as np

RECS = []

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import fit  # noqa: E402


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x)))
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)]


def f(v, d=1):
    return '-' if v is None else f'{v:.{d}f}'


def family_table(rows, recs):
    no_sol = defaultdict(int)
    for r in recs:
        if not r.get('error') and not r.get('events'):
            no_sol[(r['solver'], r['family'], r['objective'])] += 1
    groups = defaultdict(list)
    for r in rows:
        groups[(r['solver'], r['family'], r['objective'])].append(r)
    lines = ['| solver / family / objective | n | no solution | self-ended | items p50 | first p50 / p90 | T95 p50 / p90 | T99 p50 / p90 | T100 p50 / p90 | q vs BKS p50 / p10 | improvements p50 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for g, rs in sorted(groups.items()):
        n = len(rs)
        lad = lambda l, p: f(pct([r['ladder'][l] for r in rs], p))
        qa = [r['q_abs_final'] for r in rs if r['q_abs_final'] is not None]
        lines.append(f"| {'/'.join(g)} | {n} | {no_sol.get(g, 0)} | {100 * sum(r['self_terminated'] for r in rs) / n:.0f}% | {pct([r['features']['n_items'] for r in rs], .5)} | "
                     f"{f(pct([r['t_first'] for r in rs], .5), 2)} / {f(pct([r['t_first'] for r in rs], .9), 2)} | {lad(0.95, .5)} / {lad(0.95, .9)} | {lad(0.99, .5)} / {lad(0.99, .9)} | "
                     f"{lad(1.0, .5)} / {lad(1.0, .9)} | {f(pct(qa, .5), 4) if qa else '-'} / {f(pct(qa, .1), 4) if qa else '-'} | {pct([r['n_improvements'] for r in rs], .5)} |")
    return '\n'.join(lines)


ROADEF_FIT_SAMPLE = 120


def fit_rows(rows, seed=3):
    """Rows used for fitting: everything, but ROADEF subsampled (1239 trivial single-truck instances would swamp boxstacks)."""
    import random
    rng = random.Random(seed)
    ro = [r for r in rows if r['family'] == 'roadef2022']
    keep = set(id(r) for r in rng.sample(ro, min(ROADEF_FIT_SAMPLE, len(ro))))
    return [r for r in rows if r['family'] != 'roadef2022' or id(r) in keep]


def alpha_table(rows, coverage=0.8, group=None, label='all'):
    """Evaluate the fitted formula per alpha on `group(rows)` (default: all fit rows)."""
    frows = fit_rows(rows)
    lines = [f'| alpha | n | q p10 | q p50 | share q<0.99 | share q<0.95 | share no solution | used p50 / p90 (s) | T p50 / p90 (s) | used ÷ time-of-last-improvement p50 | T* p50 (s) |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for a in analyze.ALPHAS:
        models = fit.fit_alpha(frows, a, coverage)
        target = [r for r in frows if group is None or group(r)]
        ev = fit.evaluate(target, models)
        if not ev:
            continue
        qs = [e['q'] for e in ev]
        used = [e['used'] for e in ev]
        waste = [e['used'] / max(e['t_last'], 0.05) for e in ev]
        tstar = [r['opt'][a] for r in target if r['opt'][a] is not None]
        lines.append(f"| {a} | {len(ev)} | {pct(qs, .1):.4f} | {pct(qs, .5):.4f} | {100 * sum(q < 0.99 for q in qs) / len(qs):.1f}% | {100 * sum(q < 0.95 for q in qs) / len(qs):.1f}% | "
                     f"{100 * sum(q == 0 for q in qs) / len(qs):.1f}% | {pct(used, .5):.1f} / {pct(used, .9):.1f} | {pct([e['T'] for e in ev], .5):.1f} / {pct([e['T'] for e in ev], .9):.1f} | {pct(waste, .5):.2f} | {f(pct(tstar, .5))} |")
    return '\n'.join(lines)


def tau_table(rows, alphas=(2.0, 4.0, 8.0), taus=(30.0, 60.0, 120.0)):
    """Sensitivity of the recommended budget to the patience scale TAU (box/single stratum, BR + demo)."""
    saved = analyze.TAU
    lines = ['| TAU (s) | alpha | box/single T* p50 / p90 | boxstacks/single T* p50 / p90 (non-ROADEF) | q p10 box/single |', '|---|---|---|---|---|']
    for tau in taus:
        analyze.TAU = tau
        rrows = [analyze.analyse(r) for r in RECS]
        rrows = [r for r in rrows if r]
        for a in alphas:
            bs = [r['opt'][a] for r in rrows if fit.stratum(r) == ('box', 'single') and r['opt'][a] is not None]
            ss = [r['opt'][a] for r in rrows if fit.stratum(r) == ('boxstacks', 'single') and r['family'] != 'roadef2022' and r['opt'][a] is not None]
            frows = fit_rows(rrows)
            models = fit.fit_alpha(frows, a)
            ev = fit.evaluate([r for r in frows if fit.stratum(r) == ('box', 'single')], models)
            lines.append(f"| {tau:.0f} | {a} | {f(pct(bs, .5))} / {f(pct(bs, .9))} | {f(pct(ss, .5))} / {f(pct(ss, .9))} | {pct([e['q'] for e in ev], .1):.4f} |")
    analyze.TAU = saved
    return '\n'.join(lines)


def tstar_by_stratum(rows):
    strata = sorted({fit.stratum(r) for r in rows})
    lines = ['| alpha | ' + ' | '.join('/'.join(s) + ' T* p50 / p90' for s in strata) + ' |', '|---|' + '---|' * len(strata)]
    for a in analyze.ALPHAS:
        cells = []
        for s in strata:
            v = [r['opt'][a] for r in rows if fit.stratum(r) == s and r['opt'][a] is not None]
            cells.append(f'{f(pct(v, .5))} / {f(pct(v, .9))}')
        lines.append(f'| {a} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def coefficient_table(rows, coverage=0.8):
    names = ['intercept'] + fit.FEATURES
    out = []
    for a in analyze.ALPHAS:
        models = fit.fit_alpha(fit_rows(rows), a, coverage)
        for key, m in sorted(models.items()):
            out.append(f"| {a} | {'/'.join(key)} | {m['n']} | {m['rmse_latency']:.2f} / {m['rmse']:.2f} | " + ' | '.join(f'{b:+.2f}' for b in m['beta_latency']) + ' | ' + ' | '.join(f'{b:+.2f}' for b in m['beta']) + ' |')
    return ('| alpha | stratum | n | rmse(log) latency / improve | ' + ' | '.join('L:' + n for n in names) + ' | ' + ' | '.join('D:' + n for n in names) + ' |\n|---|---|---|---|' + '---|' * (2 * len(names)) + '\n' + '\n'.join(out))


def family_prediction_table(rows, alphas=(2.0, 4.0, 8.0), coverage=0.8):
    """Per family: what the fitted formula would recommend vs the per-instance optimum and the first-solution time."""
    frows = fit_rows(rows)
    groups = defaultdict(list)
    for r in frows:
        groups[(r['solver'], r['family'], r['objective'])].append(r)
    head = '| solver / family / objective | n | t_first p50 / p90 | ' + ' | '.join(f'a={a}: T* p50 · T pred p50 / p90 · q p10 · no-sol' for a in alphas) + ' |'
    lines = [head, '|---|---|---|' + '---|' * len(alphas)]
    models = {a: fit.fit_alpha(frows, a, coverage) for a in alphas}
    for g, rs in sorted(groups.items()):
        cells = []
        for a in alphas:
            ev = fit.evaluate(rs, models[a])
            if not ev:
                cells.append('-')
                continue
            qs = [e['q'] for e in ev]
            cells.append(f"{f(pct([r['opt'][a] for r in rs], .5))} · {pct([e['T'] for e in ev], .5):.1f} / {pct([e['T'] for e in ev], .9):.1f} · {pct(qs, .1):.3f} · {100 * sum(q == 0 for q in qs) / len(qs):.0f}%")
        lines.append(f"| {'/'.join(g)} | {len(rs)} | {f(pct([r['t_first'] for r in rs], .5), 2)} / {f(pct([r['t_first'] for r in rs], .9), 2)} | " + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def export(rows, recs, out_dir):
    with open(f'{out_dir}/instances.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['id', 'solver', 'family', 'objective', 'n_items', 'n_types', 'n_bins', 'n_stacks', 'fill_ratio', 'mean_items_per_bin', 'mean_rotations', 'weight_ratio',
                    't_ref', 'end', 'self_terminated', 'status', 'cores', 'n_improvements', 't_first', 't_last', 'final', 'q_abs_final']
                   + [f'T{int(l * 1000)}' for l in analyze.LEVELS] + [f'Tstar_a{a}' for a in analyze.ALPHAS])
        for r in rows:
            fe = r['features']
            w.writerow([r['id'], r['solver'], r['family'], r['objective'], fe['n_items'], fe['n_types'], fe['n_bins'], fe['n_stacks'], round(fe['fill_ratio'], 4), round(fe['mean_items_per_bin'], 2),
                        round(fe['mean_rotations'], 2), round(fe['weight_ratio'], 4), r['t_ref'], round(r['end'], 3), r['self_terminated'], r['status'], round(r['cores'] or 0, 2),
                        r['n_improvements'], round(r['t_first'], 4), round(r['t_last'], 4), r['final'], r['q_abs_final']]
                       + [r['ladder'][l] for l in analyze.LEVELS] + [r['opt'][a] for a in analyze.ALPHAS])
    with open(f'{out_dir}/curves.json', 'w') as fh:
        json.dump({r['id']: r['pts'] for r in rows}, fh)
    with open(f'{out_dir}/no_solution.txt', 'w') as fh:
        for r in recs:
            if not r.get('error') and not r.get('events'):
                fh.write(f"{r['id']}\titems={r['features']['n_items']}\tbins={r['features']['n_bins']}\tt_ref={r['t_ref']}\n")


if __name__ == '__main__':
    recs = analyze.load(sys.argv[1])
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results')
    rows = [a for a in (analyze.analyse(r) for r in recs) if a]
    RECS = recs
    strata = sorted({fit.stratum(r) for r in rows})
    md = [f'# Time-budget campaign — {len(recs)} runs, {len(rows)} with at least one solution\n',
          '## A. Per-family curve statistics (seconds; q relative to the end of the long run; BKS where upstream publishes one)\n', family_table(rows, recs),
          f'\n## B. Per-alpha evaluation (TAU = {analyze.TAU:.0f} s, coverage 0.8, formula fitted per solver × single/multi-bin on all rows with ROADEF subsampled to {ROADEF_FIT_SAMPLE}, T floored at 1 s, capped at 600 s)\n',
          '\n### B0. All fit rows\n', alpha_table(rows)]
    for st in strata:
        md += [f'\n### B. Stratum {"/".join(st)}\n', alpha_table(rows, group=lambda r, st=st: fit.stratum(r) == st)]
    md += ['\n### B. Stowly-like only (demo + synthetic, both solvers)\n', alpha_table(rows, group=lambda r: r['family'] in ('demo', 'synthetic')),
           '\n## B2. Per family: recommended T vs per-instance optimum (fit rows)\n', family_prediction_table(rows),
           '\n## C. Per-instance optimal budget T*(alpha) by stratum (all rows)\n', tstar_by_stratum(rows),
           '\n## C2. TAU sensitivity\n', tau_table(rows),
          '\n## D. Fitted coefficients. T = exp(L·x) + exp(D·x) - 0.1: L = first-solution latency (intercept shifted to 95% coverage), D = extra time worth waiting for alpha (80% coverage)\n', coefficient_table(rows)]
    open(f'{out_dir}/report.md', 'w').write('\n'.join(md) + '\n')
    export(rows, recs, out_dir)
    print('\n'.join(md))
