#!/usr/bin/env python3
"""PD-B03-T01 evidence: wall time of `demo_scenario create` by size/checkpoint and under concurrency.

Uses the shared stack through `docker compose exec` (each call includes ~1 s of exec+Django
start-up). Probe seeds 93xx are purged afterwards.
"""
import subprocess, time
from concurrent.futures import ThreadPoolExecutor

def manage(*a):
    t = time.monotonic()
    r = subprocess.run(["docker","compose","exec","-T","app","python","manage.py",*a],capture_output=True,text=True)
    return r.returncode, time.monotonic()-t

def create(seed, p, j, live, cp):
    args = ["demo_scenario","create","--seed",str(seed),"--participants",str(p),"--judges",str(j),"--password","x-probe-pw","--checkpoint",cp]
    if live is not None: args += ["--live",str(live)]
    return manage(*args)

seeds=[]
def run(label, seed, p, j, live, cp):
    seeds.append(seed); rc, s = create(seed,p,j,live,cp)
    print(f"{label:<34} rc={rc} {s:5.1f}s", flush=True); return rc, s

rc, s = manage("check"); print(f"{'manage.py check (exec+boot baseline)':<34} rc={rc} {s:5.1f}s")
run("4p/2j submitted", 9301, 4, 2, 2, "submitted")
run("4p/2j judged", 9302, 4, 2, 2, "judged")
run("4p/2j published", 9303, 4, 2, 0, "published")
run("8p/4j submitted", 9304, 8, 4, 2, "submitted")
run("24p/6j submitted (demo-sized)", 9305, 24, 6, 2, "submitted")
for n in (2, 4):
    t = time.monotonic()
    with ThreadPoolExecutor(n) as ex:
        res = list(ex.map(lambda i: create(9310 + n * 10 + i, 4, 2, 2, "submitted"), range(n)))
        seeds += [9310 + n * 10 + i for i in range(n)]
    print(f"{n} concurrent 4p/2j submitted     rc={[r for r,_ in res]} wall {time.monotonic()-t:5.1f}s (each {[round(s,1) for _,s in res]})", flush=True)
for seed in seeds:
    manage("demo_scenario","purge",f"demo-hackathon-{seed}")
print("purged", len(seeds), "probe seeds")
