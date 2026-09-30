#!/usr/bin/env python3
from pathlib import Path
import sys, yaml

if len(sys.argv)!=2:
    raise SystemExit("usage: lint_receipt.py PATH")
p=Path(sys.argv[1])
if not p.exists(): raise SystemExit(f"missing {p}")

if p.suffix.lower()==".md":
    lines=p.read_text(encoding="utf-8").splitlines()
    if len(lines)>25:
        raise SystemExit(f"FAIL: {p} has {len(lines)} physical lines; max 25")
    print(f"PASS: {p} has {len(lines)} lines")
    raise SystemExit(0)

d=yaml.load(p.read_text(encoding="utf-8"), Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
required={"version","task","batch","status","executor","git","changed_paths","deliverables","invariants","verification","design_refs","surface_matrix","migrations","findings","escalations","limitations","next"}
miss=required-set(d or {})
if miss: raise SystemExit(f"FAIL: missing fields {sorted(miss)}")
if d["status"] not in {"candidate_complete","blocked","failed","corrections"}:
    raise SystemExit(f"FAIL: bad status {d['status']}")
for v in d["verification"]:
    if v.get("result") not in {"pass","fail","skipped"}:
        raise SystemExit(f"FAIL: bad verification result {v}")
if d["status"]=="candidate_complete":
    bad=[x for x in d["deliverables"]+d["invariants"] if x.get("result")=="fail"]
    bad += [x for x in d["verification"] if x.get("result")=="fail"]
    if bad: raise SystemExit("FAIL: candidate_complete receipt contains failing required evidence")
print("PASS")
