#!/usr/bin/env python3
from pathlib import Path
import yaml, subprocess

ROOT=Path(__file__).resolve().parents[2]
execdir=ROOT/"docs/execution-v3"

def load(p):
    with p.open(encoding="utf-8") as f: return yaml.load(f, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))

print("# PROGRAM")
print(yaml.safe_dump(load(execdir/"state/PROGRAM_STATE.yaml"), sort_keys=False).rstrip())

claims=list((execdir/"claims").glob("*.yaml"))
print(f"\n# CLAIMS {len(claims)}")
for p in sorted(claims):
    d=load(p)
    print(f"{p.name}\t{d.get('state')}\t{d.get('task')}\t{d.get('branch')}\t{d.get('last_heartbeat')}")

esc=list((execdir/"escalations").glob("*.yaml"))
open_esc=[]
for p in esc:
    d=load(p)
    if d.get("status")=="OPEN": open_esc.append((p,d))
print(f"\n# OPEN_ESCALATIONS {len(open_esc)}")
for p,d in open_esc:
    print(f"{p.name}\t{d.get('severity')}\t{d.get('task')}\t{d.get('summary')}")

handoffs=list((execdir/"handoffs").glob("*.yaml"))
print(f"\n# HANDOFFS {len(handoffs)}")
for p in sorted(handoffs):
    d=load(p)
    print(f"{p.name}\t{d.get('task')}\t{d.get('branch')}\t{d.get('head_commit')}")

try:
    out=subprocess.check_output(["git","status","--short"], cwd=ROOT, text=True)
    print("\n# GIT_STATUS")
    print(out.rstrip() or "clean")
except Exception as e:
    print(f"\n# GIT_STATUS unavailable: {e}")
