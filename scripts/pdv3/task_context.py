#!/usr/bin/env python3
from pathlib import Path
import sys, yaml

ROOT=Path(__file__).resolve().parents[2]
if len(sys.argv)!=2:
    raise SystemExit("usage: task_context.py TASK-ID")
task_id=sys.argv[1]

def load(p):
    with p.open(encoding="utf-8") as f: return yaml.load(f, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))

td=load(ROOT/"TASKS.yaml"); bd=load(ROOT/"BATCHES.yaml")
tasks={t["id"]:t for t in td["tasks"]}
batches={b["id"]:b for b in bd["batches"]}
if task_id not in tasks:
    raise SystemExit(f"unknown task: {task_id}")
t=tasks[task_id]; b=batches[t["batch"]]

print("# TASK")
print(yaml.safe_dump(t, sort_keys=False, allow_unicode=True, width=110).rstrip())
print("\n# BATCH")
summary={k:b.get(k) for k in ["id","title","phase","dependencies","owned_paths","spec_refs","design_refs","surface_matrix","scope_summary","depth_contract","completion_evidence","lock_groups"]}
print(yaml.safe_dump(summary, sort_keys=False, allow_unicode=True, width=110).rstrip())

print("\n# REFERENCED SPEC HEADERS")
for ref in t.get("spec_refs",[]):
    p=ROOT/ref
    print(f"\n## {ref}")
    if not p.exists():
        print("MISSING")
        continue
    lines=p.read_text(encoding="utf-8").splitlines()
    # bounded preview; worker can use sed for more
    for line in lines[:120]:
        print(line)
    if len(lines)>120:
        print(f"... ({len(lines)-120} more lines; use sed -n on exact ranges)")
