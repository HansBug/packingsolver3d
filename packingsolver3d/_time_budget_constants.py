"""Fitted constants of :mod:`packingsolver3d.estimate` -- generated, do not edit by hand.

Generated 2026-09-19 by experiments/time_budget/export_constants.py from the campaign described in
experiments/time_budget/README.md: 3158 anytime runs on upstream PackingSolver 2a598481 (bischoff1995, davies1999,
egeblad2009, loh1992, ivancic1989, a ROADEF 2022 sample, synthetic container loads and the Stowly demo).
Reference machine: 11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz, Linux, one solve per core; times rescaled to the idle machine by a per-path calibration on 80 instances (load inflation: TSMS 2.31x, SOR 1.91x, SSK 1.14x, boxstacks SVC 1.12x, others 2.17x)
"""

#: Upstream commit, number of recorded runs, date and CPU of the campaign the constants were fitted on.
REFERENCE = "upstream 2a598481, 3158 runs, 2026-09-19, 11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz"

#: Grid of ``alpha`` values at which the improvement tables are tabulated; values in between are interpolated in log(alpha).
ALPHAS = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]

#: Floor of the predicted first-solution latency, in seconds (below this the bridge overhead dominates).
MIN_LATENCY = 0.2
#: Number of item types from which the TSMS block-generation step is charged (the block cap is reached).
BLOCK_TYPES = 4

#: ``(solver, path)`` -> latency regression ``beta`` (log space: intercept, log size, log types[, overfull]), TSMS ``block`` step,
#: per-path calibration ``scale``, the log-space coverage ``shift`` between the median and the covered latency, and the ``alpha`` tables
#: ``m`` (multiple of the latency) and ``add`` (seconds) of the improvement term.
PATHS = {
    ('box', 'SSK'): {
        'n': 55, 'growth': False, 'coverage': 0.98, 'rmse_log': 1.054,
        'beta': [-7.3358, 1.2766, 1.0847], 'block': 0.000, 'scale': 0.880, 'shift': 2.1819,
        'm': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
        'add': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
    },
    ('box', 'SVC'): {
        'n': 32, 'growth': False, 'coverage': 0.98, 'rmse_log': 0.851,
        'beta': [-3.3192, 0.0, 2.4422], 'block': 0.000, 'scale': 0.461, 'shift': 1.3788,
        'm': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
        'add': {0.25: 0.0, 0.5: 0.0144, 1.0: 0.0609, 1.5: 0.0609, 2.0: 0.0622, 3.0: 0.0622, 4.0: 0.0622, 6.0: 0.0622, 8.0: 0.0622},
    },
    ('box', 'TS'): {
        'n': 80, 'growth': True, 'coverage': 0.9, 'rmse_log': 1.923,
        'beta': [-2.515, 0.0, 0.1722], 'block': 0.000, 'scale': 0.461, 'shift': 3.5826,
        'm': {0.25: 0.1189, 0.5: 0.4173, 1.0: 1.0204, 1.5: 1.0722, 2.0: 1.2646, 3.0: 3.9025, 4.0: 5.67, 6.0: 9.4684, 8.0: 30.7674},
        'add': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
    },
    ('box', 'TSMS'): {
        'n': 1653, 'growth': True, 'coverage': 0.9, 'rmse_log': 0.847,
        'beta': [-8.7532, 1.2677, 0.7096], 'block': 0.965, 'scale': 0.433, 'shift': 0.8696,
        'm': {0.25: 0.0269, 0.5: 0.0841, 1.0: 0.2493, 1.5: 0.4626, 2.0: 0.6754, 3.0: 1.333, 4.0: 2.0543, 6.0: 3.9594, 8.0: 6.6543},
        'add': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
    },
    ('boxstacks', 'SOR'): {
        'n': 49, 'growth': True, 'coverage': 0.9, 'rmse_log': 0.919,
        'beta': [-4.7479, 0.4148, 1.0779, 1.9462], 'block': 0.000, 'scale': 0.524, 'shift': 1.2203,
        'm': {0.25: 0.0149, 0.5: 0.0221, 1.0: 0.7982, 1.5: 1.8468, 2.0: 3.7091, 3.0: 5.8297, 4.0: 6.8614, 6.0: 17.7218, 8.0: 25.4292},
        'add': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
    },
    ('boxstacks', 'SVC'): {
        'n': 32, 'growth': False, 'coverage': 0.98, 'rmse_log': 0.395,
        'beta': [-2.8245, 1.2516, 0.2625], 'block': 0.000, 'scale': 0.895, 'shift': 0.8359,
        'm': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
        'add': {0.25: 0.0, 0.5: 0.0, 1.0: 0.0, 1.5: 0.0, 2.0: 0.0, 3.0: 0.0, 4.0: 0.0, 6.0: 0.0, 8.0: 0.0},
    },
}
