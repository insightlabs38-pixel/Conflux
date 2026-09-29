# Authoritative sequential execution queue

`BATCHES.yaml` and `TASKS.yaml` are the existing DOGFOOD v2 queue, relocated
from `/home/insightlabs38/DOGFOOD_EXECUTION_CONTROL_v2_2026-09-23` on 2026-09-29.
The old paths are forwarding symlinks, not a second queue. Historical YAML
entries are preserved verbatim. Their stale statuses must be interpreted with
committed `docs/batches/` receipts and `docs/IMPLEMENTATION_CHECKPOINT.md`:
VS38–VS50 and PVS through H06 were implemented after the external VS37 snapshot.
No historical unfinished task is silently promoted by this migration.

UI-v2 is authorized by the owner as a new sequential implementation campaign.
The previous release closure is historical, not an active freeze on this phase.
One worker owns canonical main, queue updates, verification and runtime for this
campaign; old pool, leases and integration-owner rules do not schedule UI-v2.
Never reset existing work or change backend semantics for visual convenience.

Batch statuses: IN_PROGRESS, BLOCKED, DONE. Exactly one batch may be IN_PROGRESS.
Task lifecycle remains BLOCKED → READY → CLAIMED → ACTIVE → REVIEW → DONE;
ACTIVE represents in-progress implementation. Later batches depend on predecessor.
Receipts follow RECEIPT_SCHEMA.yaml and `docs/batches/UIV2-Bxx.md` (<=25 lines).
Verify, update status, commit and push each coherent batch before the next.
B00 begins ACTIVE; B01 becomes eligible only after census/media/queue validation.
No UI-v2 completion marker is written until B10's visual and regression gates pass.
