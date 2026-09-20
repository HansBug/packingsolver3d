# Time-budget campaign

The data and the fit behind `packingsolver3d.estimate.recommend_time_budget`. Everything here is reproducible; the raw results (about 8 MB of JSON/CSV) are kept in a gist linked from the pull request that introduced the estimator, not in the repository.

## Question

PackingSolver's anytime modes run until their time limit, so the caller must choose one. We want a recommendation `T(instance, alpha)` that is a loose upper bound (the solve usually ends earlier through `stop_when_unimproved_*`), interpretable, and tunable by a single quality-versus-waiting dial `alpha`.

## Protocol

1. **Instances** (`instances.py`): upstream's `box` knapsack families bischoff1995 (700), davies1999 (900), egeblad2009 (60), loh1992 (15); ivancic1989 as multi-bin bin packing (47, bins = items); a stratified sample of the ROADEF 2022 single-truck `boxstacks` knapsack derivation (8 per truck family, 1240; download with upstream's `scripts/download_data.py --data roadef2022_2024-04-25_kp` into `$TB_WORK/data`); 160 synthetic container loads (20' GP and 40' HQ, 2/5/10/20/40 item types, 0.6/0.9/1.2/2.0 bin volumes of cargo, knapsack and bin packing, `box` and `boxstacks`; bin packing gets `ceil(fill/0.75)+1` bins as a planner would enter); the Stowly demo 40' HQ container in three variants (x1, x2, ten types), three repeats each. 3158 jobs.
2. **One long anytime run per instance** (`run_one.py`, `campaign.py`): `optimization_mode=ANYTIME`, `time_limit` 60 s for upstream families and 150 s for container loads, every `progress_callback` event recorded. Each solve is its own process; the scheduler weights jobs by the threads upstream uses (box tree search 6, single-bin TSMS/SOR 1) and ran 13 slots on a 16-core i7-11700. A calibration subset of 80 instances was rerun on the idle machine (2 slots) to measure the contention inflation; the fitted constants are rescaled by it.
3. **Curves** (`analyze.py`): the improvement curve `q(t)` relative to the value at the end of the run (bins reversed for bin packing), time to 50/80/90/95/98/99/99.5/99.9/100 % of it, and the per-instance optimum `T*(alpha)` of `F_alpha = (1+alpha^2) S q / (alpha^2 S + q)` with `S = 1/(1 + t/60 s)`, for alpha in 0.25 ... 8. `report.py` renders the per-family and per-alpha tables and exports `instances.csv` / `curves.json`.
4. **Algorithm path** (`paths.py`): replicates upstream's automatic algorithm selection (`box/optimize.cpp`, `boxstacks/optimize.cpp`) from the instance features; it agreed with the event labels of all 3140 runs that produced a solution.
5. **Model** (`model.py`): per path `T(alpha) = L (1 + m(alpha)) + c(alpha)`. `L` is a log-linear power law in size (items for box, stacks for boxstacks) and item types with non-negative exponents, plus a constant block-generation step for TSMS (types >= 4) and an overfull multiplier for SOR; its intercept is shifted to the 90 % (growth paths TSMS/TS/SOR) or 98 % (single-pass paths SSK/SVC) coverage quantile. `m(alpha)` is the 80 % quantile of `(T* - t_first) / t_first` on growth paths and 0 on single-pass paths; `c(alpha)` the 80 % quantile of `T* - t_first` on single-pass paths. ROADEF instances are evaluated but not fitted (41 items median, all done in under a second). The stall-stop rule `after = max(L, T/2)`, `patience = max(2 s, (T - L)/2)` was chosen by replaying alternatives on the curves.
6. **Export** (`export_constants.py`): renders `packingsolver3d/_time_budget_constants.py` with the reference machine, upstream commit and calibration factor.

## Re-measurement on upstream d10db9d7 and the relative stall stop (2026-09-20)

Upstream `9bfb9431` gave multi-bin `boxstacks` bin packing a sequential single knapsack path (`SSK`) next to the sequential value correction (`SVC`) it had before, and `63ed7915` / `d10db9d7` fixed the timer of the pricing subproblem and enabled a pairing heuristic. `paths.boxstacks_path` mirrors the new selection (bin packing: `SSK` above the same 16 / 64 mean-items-per-bin thresholds as `box`, `SVC` below; knapsack and variable-sized bin packing: `SVC`). Because the multi-bin path changed, every non-ROADEF `boxstacks` job of the campaign was re-run on the new build (`campaign.py --only boxstacks/synthetic` and `--only boxstacks/demo`, same 150 s limit, same 12-slot contention regime, results in `campaign_d10db9d7.jsonl`), plus 24 new multi-bin knapsack loads (`synthetic_multi`, 2 to 3 bins with 0.9 to 2.5 bin volumes of cargo) so that the `SVC` path is fitted on the objective it now serves. The `box` paths and the ROADEF sample were kept from the `2a598481` campaign; the merged file is `campaign_merged.jsonl`. `SSK` has no calibration factor of its own and uses the campaign-wide default.

The stall rule shipped with the estimator changed at the same time. The 0.0.3 rule (`after = max(L, T/2)`, `patience = (T - L)/2`) ended solves at 0.5-0.85 of the limit; the anytime searches double their queues between passes, so the wait for the next pass equals the time already spent and a fixed patience is the wrong shape. `stall_policy_replay` (the `E2` variants) replays a *relative* patience -- never before the first solution, `patience = max(floor, ratio × time of the last improvement)` -- for ratios 1 to 4 and floors 2 and 5 s; the shipped choice is floor 5 s and `ratio = alpha / 2` clamped to 1 ... 4, evaluated in `model.py` through `stall_stop_relative`.

## Reproduce

```bash
export TB_WORK=/tmp/tb                       # scratch directory for data and results
python experiments/time_budget/campaign.py --t-upstream 60 --t-synthetic 150 --capacity 12   # hours
python experiments/time_budget/campaign.py --ids-file calib_ids.txt --capacity 2 --out $TB_WORK/results/calib.jsonl
python experiments/time_budget/report.py $TB_WORK/results/campaign.jsonl $TB_WORK/results   # tables A-D
python experiments/time_budget/model.py $TB_WORK/results/campaign.jsonl <scale>              # constants + evaluation
python experiments/time_budget/export_constants.py $TB_WORK/results/campaign.jsonl <scale> packingsolver3d/_time_budget_constants.py "<calibration note>"
```

`campaign.py` is resumable (it skips ids already in the output file) and kills a job that overruns its time limit by 90 s.

## Files

- `instances.py` -- loaders for the upstream CSV layouts, the ROADEF prefixed layout, the synthetic generator, instance features, the job list.
- `run_one.py`, `campaign.py` -- one solve per subprocess; weighted, resumable scheduler.
- `analyze.py`, `report.py`, `fit.py` -- curves, ladders, F-alpha optima, per-family and per-alpha tables (`fit.py` is the earlier pooled log-linear fit kept for comparison).
- `paths.py` -- upstream algorithm-path classifier and its validation against event labels.
- `model.py`, `export_constants.py` -- the per-path model, its evaluation with and without stall stop, and the constants export.
- `calibrate.py`, `calibration.md` -- the idle-machine rerun of 80 instances and the resulting per-path load factors (first-solution ratio load/idle: TSMS 2.31, SOR 1.91, SSK 1.14, boxstacks SVC 1.12, all 2.17).
- `policy_compare.py`, `policy_compare.md`, `policy_compare_D.md` -- replay of stopping policies on every curve (fixed time limit only, stagnation only with fixed patience, stagnation guarded by the predicted latency, the PR rule, and an adaptive patience relative to the observed first solution), each under a machine 1x / 2x slower / 2x faster than assumed.
- `plot.py`, `figures/` -- the figures posted on the pull request (per-family curves, demo budgets, latency fit, alpha vs optimum, formula evaluation, looseness).
- `report.md`, `model_report.md` -- the tables as generated for the pull request (`model_report.md` is in idle-machine seconds; `report.md` in campaign seconds).
