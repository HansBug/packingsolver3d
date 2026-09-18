"""Run all jobs with a weighted process pool; resumable (skips ids already in the results file)."""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instances  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--out', default=os.path.join(os.environ.get('TB_WORK', '/tmp/tb'), 'results', 'campaign.jsonl'))
ap.add_argument('--capacity', type=int, default=12)
ap.add_argument('--pilot', action='store_true')
ap.add_argument('--t-upstream', type=float, default=60.0)
ap.add_argument('--t-synthetic', type=float, default=120.0)
ap.add_argument('--only', default=None, help='substring filter on job id')
ap.add_argument('--ids-file', default=None, help='run only the job ids listed in this file (one per line)')
args = ap.parse_args()

jobs = instances.build_jobs(t_upstream=args.t_upstream, t_synthetic=args.t_synthetic)
if args.only:
    jobs = [j for j in jobs if args.only in j['id']]
if args.ids_file:
    wanted = {l.strip() for l in open(args.ids_file) if l.strip()}
    jobs = [j for j in jobs if j['id'] in wanted]
if args.pilot:
    picked, seen = [], {}
    for j in jobs:
        key = (j['solver'], j['family'], j['objective'], j['weight'])
        if seen.get(key, 0) < 2:
            seen[key] = seen.get(key, 0) + 1
            picked.append(j)
    jobs = picked
os.makedirs(os.path.dirname(args.out), exist_ok=True)
done = set()
if os.path.exists(args.out):
    with open(args.out) as f:
        for line in f:
            try:
                done.add(json.loads(line)['id'])
            except Exception:
                pass
todo = [j for j in jobs if j['id'] not in done]
# heavy (multi-thread) jobs first so that they overlap with the long tail of light ones
todo.sort(key=lambda j: (-j['weight'], j['id']))
print(f'{len(jobs)} jobs, {len(done)} done, {len(todo)} to run, capacity {args.capacity}', flush=True)

running = []  # (proc, job, start)
used = 0
out = open(args.out, 'a')
log = open(args.out + '.log', 'a')
started = time.time()
finished = 0
while todo or running:
    while todo:
        # greedy backfill: take the first queued job that fits in the remaining capacity (or anything if idle)
        idx = next((k for k, j in enumerate(todo) if used + j['weight'] <= args.capacity), None)
        if idx is None:
            if running:
                break
            idx = 0
        job = todo.pop(idx)
        proc = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_one.py'), json.dumps(job)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        running.append((proc, job, time.time()))
        used += job['weight']
    time.sleep(0.5)
    still = []
    for proc, job, t_start in running:
        if proc.poll() is None:
            if time.time() - t_start > job['t_ref'] + 90:
                proc.kill()
                proc.wait()
                log.write(f"KILLED {job['id']} after {time.time() - t_start:.0f}s\n")
                out.write(json.dumps(dict(job, error='killed: hung', events=[], value=None)) + '\n')
                out.flush()
                used -= job['weight']
                finished += 1
            else:
                still.append((proc, job, t_start))
            continue
        stdout, stderr = proc.communicate()
        used -= job['weight']
        finished += 1
        if proc.returncode == 0 and stdout.strip():
            out.write(stdout.strip().splitlines()[-1] + '\n')
        else:
            log.write(f"FAILED {job['id']} rc={proc.returncode}\n{stderr[-2000:]}\n")
            out.write(json.dumps(dict(job, error=f'rc={proc.returncode}: {stderr[-500:]}', events=[], value=None)) + '\n')
        out.flush()
        log.flush()
        if finished % 10 == 0 or not todo:
            elapsed = time.time() - started
            log.write(f'{time.strftime("%H:%M:%S")} finished {finished}/{len(jobs) - len(done)} running {len(running)} used {used} elapsed {elapsed:.0f}s\n')
            log.flush()
    running = still
log.write(f'DONE {time.strftime("%H:%M:%S")} total {time.time() - started:.0f}s\n')
log.close()
out.close()
print('done', flush=True)
