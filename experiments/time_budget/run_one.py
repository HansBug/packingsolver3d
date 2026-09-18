"""Solve one job for its reference time and print a JSON record with the improvement curve."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instances  # noqa: E402
import packingsolver3d as ps  # noqa: E402
from packingsolver3d import OptimizationMode  # noqa: E402

job = json.loads(sys.argv[1])
instance = instances.instantiate(job['source'])
module = ps.boxstacks if job['solver'] == 'boxstacks' else ps.box
events = []
t0 = time.perf_counter()
c0 = time.process_time()
error = None
try:
    result = module.solve(instance, time_limit=job['t_ref'], optimization_mode=OptimizationMode.ANYTIME,
                          progress_callback=lambda e: events.append((e.time, e.number_of_items, e.number_of_bins, e.profit, e.cost, e.label)) or None)
except Exception as exc:  # record, do not crash the campaign
    result = None
    error = repr(exc)
wall = time.perf_counter() - t0
cpu = time.process_time() - c0
record = dict(job)
record.update({
    'wall': wall, 'cpu': cpu, 'events': events, 'error': error,
    'value': None if result is None else result.value,
    'bound': None if result is None else result.bound,
    'status': None if result is None else result.status.value,
    'items': None if result is None else len(result.placements),
    'bins_used': None if result is None else result.number_of_bins,
    'solve_time': None if result is None else result.solve_time,
    'proven_optimal': None if result is None else result.is_proven_optimal,
})
print(json.dumps(record))
