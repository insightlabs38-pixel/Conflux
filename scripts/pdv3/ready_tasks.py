#!/usr/bin/env python3
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]
def load(p):
    with p.open(encoding="utf-8") as f: return yaml.load(f, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))

tasks=load(ROOT/"TASKS.yaml")["tasks"]
batches=load(ROOT/"BATCHES.yaml")["batches"]
tstate=load(ROOT/"docs/execution-v3/state/TASK_STATE.yaml").get("tasks",{})
bstate=load(ROOT/"docs/execution-v3/state/BATCH_STATE.yaml").get("batches",{})
program=load(ROOT/"docs/execution-v3/state/PROGRAM_STATE.yaml")

tb={t["id"]:t for t in tasks}; bb={b["id"]:b for b in batches}
def ts(i): return tstate.get(i, tb[i]["status"])
def bs(i): return bstate.get(i, bb[i]["status"])

if program["state"] not in {"ACTIVE","PAUSED"}:
    print(f"program={program['state']}; no executable READY set while frozen")
    raise SystemExit(0)

ready=[]
for t in tasks:
    if ts(t["id"]) not in {"BLOCKED","READY"}:
        continue
    if any(bs(d)!="DONE" for d in t["batch_dependencies"]):
        continue
    if any(ts(d)!="DONE" for d in t["task_dependencies"]):
        continue
    batch_status=bs(t["batch"])
    if batch_status not in {"READY","IN_PROGRESS"}:
        continue
    ready.append(t)

for t in ready:
    print(f"{t['id']}\t{t['batch']}\t{t['risk']}\t{t['executor_class']}\t{t['title']}")
print(f"# ready={len(ready)}")
