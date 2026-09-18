"""Prototype for the PR comment: recommendations for the demo container variants, and one real solve driven by them."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instances  # noqa: E402
from packingsolver3d import box, boxstacks, recommend_time_budget, algorithm_path  # noqa: E402

print('| instance | solver | objective | path | alpha | latency L | extra | time_limit | after | patience |')
print('|---|---|---|---|---|---|---|---|---|---|')
variants = [('demo 40HQ (1036 items, 5 types)', 1, 1), ('demo x2 (2072 items)', 2, 1), ('demo ten types (1554 items)', 1, 2)]
for name, scale, types in variants:
    for stacked in (False, True):
        for objective, bins in (('knapsack', 1), ('bin-packing', 4)):
            inst = instances.instantiate({'kind': 'demo', 'stacked': stacked, 'objective': objective, 'scale': scale, 'types': types, 'bins': bins})
            solver = 'boxstacks' if stacked else 'box'
            for alpha in (4.0, 8.0):
                b = recommend_time_budget(inst, solver, alpha=alpha)
                print(f'| {name} | {solver} | {objective} | {b.path} | {alpha} | {b.latency:.1f} | {b.improvement:.1f} | {b.time_limit:.1f} | {b.stop_when_unimproved_after:.1f} | {b.stop_when_unimproved_for:.1f} |')

print()
inst = instances.instantiate({'kind': 'demo', 'stacked': False, 'objective': 'knapsack', 'scale': 1, 'types': 1, 'bins': 1})
for solver, module in (('box', box), ('boxstacks', boxstacks)):
    inst = instances.instantiate({'kind': 'demo', 'stacked': solver == 'boxstacks', 'objective': 'knapsack', 'scale': 1, 'types': 1, 'bins': 1})
    budget = recommend_time_budget(inst, solver)
    events = []
    t0 = time.perf_counter()
    result = module.solve(inst, progress_callback=lambda e: events.append((round(e.time, 1), e.number_of_items)) or None, **budget.as_options())
    wall = time.perf_counter() - t0
    print(f'{solver}: budget={budget.as_options()} -> wall={wall:.1f}s items={len(result.placements)}/{sum(i.copies for i in inst.item_types)} stop_reason={result.run.stop_reason} events={events}')
