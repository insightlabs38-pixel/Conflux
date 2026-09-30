# Completion Rules — Product Depth v3

These rules are stricter than the original DOGFOOD queue because Product Depth v3 explicitly aims to prevent shallow feature closure.

## Task completion

A task may move to `DONE` only after the controller/reviewer confirms all of the following:

1. **Deliverables:** every item in `task.deliverables` exists and behaves as specified.
2. **Invariants:** every item in `task.invariants` still holds.
3. **Verification:** every required item in `task.verification` was actually executed or satisfied with recorded evidence.
4. **Spec contract:** all task-relevant requirements in `spec_refs` are satisfied; a worker cannot close only the literal title while ignoring the subsystem contract.
5. **Primitive reuse:** every item in `reuses` uses the canonical primitive or has an approved escalation/spec amendment.
6. **Design refs:** every required `design_refs` target exists and the implementation preserves its must-preserve hierarchy, density, interaction order, states and responsive intent.
7. **Surface matrix:** task-required surfaces are implemented or explicitly reclassified by an approved contract change; "not relevant" cannot be invented at review time.
8. **Migration/compatibility:** changes to persisted state, API contracts, archives, Event-as-Code, SDKs or extensions have the required migration/compatibility treatment.
9. **Edge states:** applicable loading/empty/error/permission/large-data/mobile/offline/concurrency states are not missing.
10. **Tests are honest:** no test, gate, assertion, fixture, timeout or linter rule was weakened merely to obtain green output.
11. **No hidden bypass:** canonical services, authorization, audit, validation, versioning and state machines were not bypassed for convenience.
12. **Scope:** no unrelated rewrite or parallel representation was introduced.
13. **Integration:** branch is integrated or integration-ready with no unresolved merge/invariant conflict.
14. **Receipt:** a valid task receipt exists with exact verification commands/results, changed paths, limitations and escalations.
15. **Open issues:** no unresolved P0/P1 escalation blocks correctness, security, integrity, migration or intended product behavior.

A worker may set its receipt to `candidate_complete`; only the controller/reviewer transitions the runtime task state to `DONE`.

## What does NOT prove completion

None of these is sufficient by itself:
- code compiles;
- focused tests pass;
- a route/component exists;
- the happy path works;
- a UI control is visible;
- the worker says "done";
- an API returns data;
- a screenshot looks plausible;
- T90/T91 exist later in the batch.

If the task's promised depth is absent, the task remains incomplete.

## Batch completion

A batch may move to `DONE` only when:

1. every task is `DONE`;
2. all batch `depth_contract` items are proven;
3. required T90 verification is complete;
4. required T91 cross-surface integration is complete;
5. any required T95/frontier review is complete;
6. the batch surface matrix is closed;
7. no unresolved escalation applies to the batch;
8. canonical main passes the batch-level verification after integration;
9. queue/spec/design/primitive validators pass;
10. a batch receipt exists at `docs/execution-v3/receipts/batches/<BATCH>.md`;
11. that human batch receipt is **<=25 physical lines**;
12. the batch receipt identifies real limitations instead of hiding them;
13. a coherent integration commit is present and recorded.

## Gate completion

A gate is not a normal feature batch. It must prove the exact integrated scenarios named by the gate contract on canonical integrated state.

A gate may not be weakened because downstream work is waiting.

## Design completion

Visual work does not close because it "matches the vibe." For UI-facing tasks, review must compare against:
- approved local Claude Design references;
- required states;
- realistic data density;
- responsive/mobile behavior;
- keyboard/accessibility behavior;
- the anti-slop rules in the visual/product contract.

## Regression handling

A newly discovered regression caused by the current task is part of the task even if the failing test lies outside the immediate file list.

An unrelated pre-existing defect should be recorded and queued/escalated, not silently absorbed into the task unless it blocks correct implementation.

## Corrections

`CORRECTIONS` is not a completion state. It means review found a specific mismatch. The worker fixes the mismatch, updates verification evidence, and returns to `REVIEW`.
