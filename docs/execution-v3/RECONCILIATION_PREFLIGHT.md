# Product Depth v3 — Pre-Implementation Reconciliation Contract

`PD-R00` is the first executable batch after activation.

Its purpose is to prove that the repository and execution bundle are coherent **after the legacy DOGFOOD materials and Product Depth v3 materials have been combined**, before product implementation starts.

It is deliberately narrower than `PD-B00`. `PD-R00` reconciles execution authority and repository state; `PD-B00` then performs the substantive current-product baseline and defect census.

## Required outcomes

1. **One active authority**
   - Product Depth v3 `TASKS.yaml` / `BATCHES.yaml` are the active future-work queue.
   - `docs/execution-v3/**` is the active execution-control system.
   - legacy DOGFOOD execution files remain useful historical evidence/context but are clearly non-active.
   - no second controller/runtime-state mechanism can be mistaken for current authority.

2. **Cohesive old/new documentation**
   - historical receipts, batch reports, architecture decisions and verification evidence remain reachable;
   - conflicting duplicate instructions are either reconciled or explicitly labeled historical;
   - links/references used by active Product Depth v3 material resolve.

3. **Known Git/runtime state**
   - canonical branch and HEAD are recorded;
   - working tree/worktrees are understood;
   - stale claims/controller state from prior experiments are not mistaken for live Product Depth work;
   - no unexplained merge markers or abandoned active-control artifacts remain.

4. **Valid execution bundle**
   - queue/spec/primitive/design-reference validation passes;
   - controller scripts compile and their frozen-state behavior is correct;
   - required-reading references resolve;
   - activation still targets this reconciliation batch first.

5. **Plan/repository assumption check**
   - obvious cases where the current repository already implements functionality named by future tasks are recorded for later `PD-B00` audit;
   - this preflight does **not** mark those future tasks DONE;
   - obvious cases where paths/modules named by the queue no longer exist are recorded/fixed so later workers receive valid context.

6. **Claude Design lane ready**
   - the local Claude Design prompt/handoff protocol/manifest exist and are internally coherent;
   - Claude Design may continue in parallel and remains gated at `PD-DESIGN-B00`, not at this preflight.

## Non-goals

- Do not perform the full product defect census; that is `PD-B00`.
- Do not implement future features.
- Do not mass-rewrite historical receipts merely for formatting consistency.
- Do not discard historical DOGFOOD evidence unless it is a generated duplicate with a preserved canonical copy.
- Do not mark a future Product Depth task complete merely because related code already exists; `PD-B00` and the relevant subsystem contract must determine whether the existing implementation satisfies v3 depth.
