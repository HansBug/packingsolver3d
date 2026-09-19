"""Render the fitted model as packingsolver3d/_time_budget_constants.py."""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import model  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def main(campaign_path, scale, out_path, calib_note):
    recs = analyze.load(campaign_path)
    rows = [a for a in (analyze.analyse(r) for r in recs) if a]
    fit_rows = [r for r in rows if r['family'] != 'roadef2022']
    M = model.fit(fit_rows, scale)
    upstream = subprocess.run(['git', '-C', REPO + '/upstream/packingsolver', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    cpu = [l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')][0]
    lines = ['"""Fitted constants of :mod:`packingsolver3d.estimate` -- generated, do not edit by hand.', '',
             f'Generated {time.strftime("%Y-%m-%d")} by experiments/time_budget/export_constants.py from the campaign described in',
             'experiments/time_budget/README.md: %d anytime runs on upstream PackingSolver %s (bischoff1995, davies1999,' % (len(recs), upstream),
             'egeblad2009, loh1992, ivancic1989, a ROADEF 2022 sample, synthetic container loads and the Stowly demo).',
             f'Reference machine: {cpu}, Linux, one solve per core; {calib_note}', '"""', '',
             '#: Upstream commit, number of recorded runs, date and CPU of the campaign the constants were fitted on.',
             'REFERENCE = ' + json.dumps('upstream %s, %d runs, %s, %s' % (upstream, len(recs), time.strftime('%Y-%m-%d'), cpu)), '',
             '#: Grid of ``alpha`` values at which the improvement tables are tabulated; values in between are interpolated in log(alpha).',
             f'ALPHAS = {json.dumps(sorted(model.ALPHAS))}', '',
             '#: Floor of the predicted first-solution latency, in seconds (below this the bridge overhead dominates).',
             f'MIN_LATENCY = {model.MIN_LATENCY}',
             '#: Number of item types from which the TSMS block-generation step is charged (the block cap is reached).',
             f'BLOCK_TYPES = {model.BLOCK_TYPES}', '',
             '#: ``(solver, path)`` -> latency regression ``beta`` (log space: intercept, log size, log types[, overfull]), TSMS ``block`` step,',
             '#: per-path calibration ``scale``, and the ``alpha`` tables ``m`` (multiple of the latency) and ``add`` (seconds) of the improvement term.',
             'PATHS = {']
    for key, e in sorted(M.items()):
        lines.append(f'    ({key[0]!r}, {key[1]!r}): {{')
        lines.append(f"        'n': {e['n']}, 'growth': {e['growth']}, 'coverage': {e['coverage']}, 'rmse_log': {e['rmse_log']:.3f},")
        lines.append(f"        'beta': {json.dumps([round(b, 4) for b in e['beta']])}, 'block': {e['block']:.3f}, 'scale': {e['scale']:.3f},")
        lines.append(f"        'm': {{{', '.join(f'{a}: {round(v, 4)}' for a, v in sorted(e['m'].items()))}}},")
        lines.append(f"        'add': {{{', '.join(f'{a}: {round(v, 4)}' for a, v in sorted(e['add'].items()))}}},")
        lines.append('    },')
    lines.append('}')
    open(out_path, 'w').write('\n'.join(lines) + '\n')
    print('wrote', out_path)


if __name__ == '__main__':
    scale_arg = json.load(open(sys.argv[2])) if sys.argv[2].endswith('.json') else float(sys.argv[2])
    main(sys.argv[1], scale_arg, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'no load calibration applied')
