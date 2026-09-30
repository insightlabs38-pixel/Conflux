#!/usr/bin/env python3
from pathlib import Path
import sys, yaml, json

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "TASKS.yaml"
BATCHES = ROOT / "BATCHES.yaml"
SPEC_INDEX = ROOT / "docs/product-depth-v3/SPEC_INDEX.yaml"
PRIMS = ROOT / "docs/product-depth-v3/PRIMITIVE_REGISTRY.yaml"
DESIGN = ROOT / "docs/product-depth-v3/design/DESIGN_MANIFEST.yaml"

def load(path):
    with path.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))

errors=[]
td=load(TASKS); bd=load(BATCHES)
tasks=td["tasks"]; batches=bd["batches"]
task_ids=[x["id"] for x in tasks]; batch_ids=[x["id"] for x in batches]
tset=set(task_ids); bset=set(batch_ids)

if len(tset)!=len(task_ids): errors.append("duplicate task IDs")
if len(bset)!=len(batch_ids): errors.append("duplicate batch IDs")

req_task={"id","batch","phase","title","status","batch_dependencies","task_dependencies","goal","preferred_executor","freebuff_eligible","risk","owned_paths","required_reading","acceptance","escalate_if","task_kind","executor_class","spec_refs","design_refs","reuses","deliverables","invariants","verification","non_goals","surface_matrix"}
req_batch={"id","title","phase","preferred_executor","dependencies","owned_paths","task_ids","completion_rule","status","spec_refs","design_refs","surface_matrix","scope_summary","depth_contract","completion_evidence","lock_groups"}

tb={x["id"]:x for x in tasks}
bb={x["id"]:x for x in batches}

for t in tasks:
    miss=req_task-set(t)
    if miss: errors.append(f"{t['id']}: missing task fields {sorted(miss)}")
    if t["batch"] not in bset: errors.append(f"{t['id']}: unknown batch {t['batch']}")
    for d in t["task_dependencies"]:
        if d not in tset: errors.append(f"{t['id']}: unknown task dependency {d}")
    for d in t["batch_dependencies"]:
        if d not in bset: errors.append(f"{t['id']}: unknown batch dependency {d}")

for b in batches:
    miss=req_batch-set(b)
    if miss: errors.append(f"{b['id']}: missing batch fields {sorted(miss)}")
    for d in b["dependencies"]:
        if d not in bset: errors.append(f"{b['id']}: unknown batch dependency {d}")
    for tid in b["task_ids"]:
        if tid not in tset: errors.append(f"{b['id']}: unknown task {tid}")
        elif tb[tid]["batch"] != b["id"]: errors.append(f"{b['id']}: task {tid} belongs to {tb[tid]['batch']}")

# DAG
visiting=set(); visited=set()
def dfs(n):
    if n in visiting:
        raise RuntimeError(f"batch dependency cycle at {n}")
    if n in visited: return
    visiting.add(n)
    for d in bb[n]["dependencies"]: dfs(d)
    visiting.remove(n); visited.add(n)
try:
    for n in batch_ids: dfs(n)
except RuntimeError as e:
    errors.append(str(e))

# referenced files
for obj in list(tasks)+list(batches):
    for ref in obj.get("spec_refs",[]):
        p=ROOT/ref
        if not p.exists(): errors.append(f"{obj['id']}: missing spec ref {ref}")

# required-reading files that are concrete repository paths
for t in tasks:
    for ref in t.get("required_reading", []):
        candidate=ref.split("#",1)[0]
        if candidate.endswith((".md",".yaml",".yml",".json")):
            if not (ROOT/candidate).exists():
                errors.append(f"{t['id']}: missing required reading {candidate}")

# primitive ids
prim_doc=load(PRIMS)
pids={p["id"] for p in prim_doc.get("primitives",[])}
for t in tasks:
    for p in t.get("reuses",[]):
        if p not in pids: errors.append(f"{t['id']}: unknown primitive {p}")

# design ids may be pending but must be declared
design_doc=load(DESIGN)
dids={d["id"] for d in design_doc.get("references",[])}
for obj in list(tasks)+list(batches):
    for d in obj.get("design_refs",[]):
        if d not in dids: errors.append(f"{obj['id']}: unknown design ref {d}")

result={"valid":not errors,"batches":len(batches),"tasks":len(tasks),"errors":errors}
print(json.dumps(result, indent=2))
sys.exit(0 if not errors else 1)
