#!/usr/bin/env python3
from pathlib import Path
import argparse, yaml, subprocess, datetime, sys

ROOT=Path(__file__).resolve().parents[2]
state_dir=ROOT/"docs/execution-v3/state"

def load(p):
    with p.open(encoding="utf-8") as f: return yaml.load(f, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
def save(p,d):
    p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True), encoding="utf-8")

ap=argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--confirm", default="")
args=ap.parse_args()

program=load(state_dir/"PROGRAM_STATE.yaml")
if program["state"]!="FROZEN":
    raise SystemExit(f"refusing: program state is {program['state']}, expected FROZEN")

commit=subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
print("Would activate Product Depth v3")
print(f"canonical commit: {commit}")
print("initial batch: PD-R00")
print("initial task promotion: dependency-satisfied entry task(s) in PD-R00")

if not args.apply:
    print("DRY RUN only. Use --apply --confirm PRODUCT-DEPTH-V3")
    raise SystemExit(0)
if args.confirm!="PRODUCT-DEPTH-V3":
    raise SystemExit("confirmation mismatch")

bd=load(ROOT/"BATCHES.yaml")
td=load(ROOT/"TASKS.yaml")
b0=next(b for b in bd["batches"] if b["id"]=="PD-R00")
task_map={t["id"]:t for t in td["tasks"]}

bstate=load(state_dir/"BATCH_STATE.yaml")
tstate=load(state_dir/"TASK_STATE.yaml")

bstate.setdefault("batches",{})["PD-R00"]="IN_PROGRESS"
for tid in b0["task_ids"]:
    t=task_map[tid]
    if not t["task_dependencies"] and not t["batch_dependencies"]:
        tstate.setdefault("tasks",{})[tid]="READY"

program["state"]="ACTIVE"
program["controller_epoch"]=int(program.get("controller_epoch",0))+1
program["activated_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
program["canonical_commit_at_activation"]=commit

save(state_dir/"PROGRAM_STATE.yaml",program)
save(state_dir/"BATCH_STATE.yaml",bstate)
save(state_dir/"TASK_STATE.yaml",tstate)
print("ACTIVATED")
