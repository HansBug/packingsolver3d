"""Turn campaign records into per-instance quality curves, time-to-quality ladders and F-alpha optima."""
import json
import os
import math
import sys
from typing import Dict, List, Optional

LEVELS = [0.5, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 1.0]
ALPHAS = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
TAU = 60.0  # seconds; human patience scale of the speed score


def load(path: str) -> List[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def curve(rec: dict):
    """Monotone improvement curve [(t, value)] in the direction of the objective (bigger = better internally)."""
    minimize = rec['objective'] != 'knapsack'
    pts = []
    best = None
    for t, items, bins, profit, cost, label in rec['events']:
        v = -bins if minimize else profit
        if best is None or v > best:
            best = v
            pts.append((t, v))
    return pts, minimize


def quality_at(pts, t, ref):
    """Relative quality reached at wall time t (0 before the first solution)."""
    v = None
    for pt, pv in pts:
        if pt <= t:
            v = pv
        else:
            break
    if v is None:
        return 0.0
    if ref < 0:  # minimization stored negated: q = ref/v with both negative
        return ref / v if v != 0 else 1.0
    return v / ref if ref else 1.0


def analyse(rec: dict) -> Optional[dict]:
    if rec.get('error') or not rec.get('events'):
        return None
    pts, minimize = curve(rec)
    final = pts[-1][1]
    ref_run = final
    bks = rec.get('bks')
    ref_abs = None
    if bks is not None and not minimize:
        ref_abs = max(bks, final)
    elif minimize and rec.get('bound') is not None:
        ref_abs = -rec['bound'] if rec['bound'] else None  # lower bound on bins, negated
    t_ref = rec['t_ref']
    end = rec['solve_time'] if rec.get('solve_time') and rec['solve_time'] < t_ref else t_ref
    self_terminated = rec.get('solve_time') is not None and rec['solve_time'] < t_ref - 0.5
    ladder = {}
    for lvl in LEVELS:
        t_hit = None
        for t, v in pts:
            if quality_at([(t, v)], t, ref_run) >= lvl - 1e-12:
                t_hit = t
                break
        ladder[lvl] = t_hit
    # F-alpha optimum over candidate budgets = event times (plus the end of the run)
    candidates = sorted({t for t, _ in pts} | {end})
    opt = {}
    for a in ALPHAS:
        best_f, best_t = -1, None
        for T in candidates:
            used = min(T, end)
            q = quality_at(pts, T, ref_run)
            s = 1.0 / (1.0 + used / TAU)
            f = (1 + a * a) * s * q / (a * a * s + q) if (a * a * s + q) > 0 else 0
            if f > best_f + 1e-12:
                best_f, best_t = f, T
        opt[a] = best_t
    gaps = [b[0] - a_[0] for a_, b in zip(pts, pts[1:])]
    return {
        'id': rec['id'], 'family': rec['family'], 'solver': rec['solver'], 'objective': rec['objective'],
        'features': rec['features'], 'weight': rec['weight'], 't_ref': t_ref, 'end': end, 'self_terminated': self_terminated,
        'status': rec.get('status'), 'cores': rec['cpu'] / rec['wall'] if rec.get('wall') else None,
        'n_events': len(rec['events']), 'n_improvements': len(pts), 't_first': pts[0][0], 't_last': pts[-1][0],
        'final': final, 'q_abs_final': (None if ref_abs is None else quality_at(pts, t_ref, ref_abs)),
        'ladder': ladder, 'opt': opt, 'max_gap': max(gaps) if gaps else 0.0, 'pts': pts, 'ref_run': ref_run,
    }


def summarize(rows: List[dict], key=lambda r: (r['solver'], r['family'], r['objective'])):
    groups: Dict = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)

    def pct(xs, p):
        xs = sorted(x for x in xs if x is not None)
        if not xs:
            return None
        return xs[min(len(xs) - 1, int(math.ceil(p * len(xs))) - 1)]

    print(f"{'group':52s} {'n':>4s} {'self%':>5s} {'first50':>7s} {'T95 p50/p90':>13s} {'T99 p50/p90':>13s} {'T100 p50/p90':>13s} {'qabs p50':>8s} {'T*a1 p50':>8s} {'T*a2 p50':>8s} {'T*a4 p50':>8s}")
    for g, rs in sorted(groups.items()):
        n = len(rs)
        selfp = 100 * sum(r['self_terminated'] for r in rs) / n
        f50 = pct([r['t_first'] for r in rs], 0.5)
        def lad(l, p):
            v = pct([r['ladder'][l] for r in rs], p)
            return '-' if v is None else f'{v:.1f}'
        qabs = pct([r['q_abs_final'] for r in rs], 0.5)
        line = f"{'/'.join(g):52s} {n:4d} {selfp:5.0f} {f50:7.2f} {lad(0.95,.5):>6s}/{lad(0.95,.9):<6s} {lad(0.99,.5):>6s}/{lad(0.99,.9):<6s} {lad(1.0,.5):>6s}/{lad(1.0,.9):<6s} {('-' if qabs is None else f'{qabs:.4f}'):>8s}"
        for a in (1.0, 2.0, 4.0):
            v = pct([r['opt'][a] for r in rs], 0.5)
            line += f" {v:8.1f}"
        print(line)


if __name__ == '__main__':
    recs = load(sys.argv[1])
    rows = [a for a in (analyse(r) for r in recs) if a]
    errs = [r for r in recs if r.get('error')]
    print(len(recs), 'records,', len(rows), 'analysed,', len(errs), 'errors')
    for e in errs[:5]:
        print('ERR', e['id'], e['error'][:200])
    summarize(rows)
