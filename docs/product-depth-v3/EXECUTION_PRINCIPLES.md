# Product Depth v3 — Execution Principles

## Purpose

This program is intended to turn Conflux into an unusually advanced and customizable hackathon / technical-competition operating system **without making the base product complicated or turning feature count into an end in itself**.

The queue is frozen until the full execution bundle is approved.

## Non-negotiable product rules

1. **Base-state excellence:** normal events must remain straightforward with sane defaults and progressive disclosure.
2. **Depth over checkbox breadth:** a capability is not complete because a field, endpoint, or settings toggle exists. The real workflow, edge cases, diagnostics, migration, permissions, testing and appropriate surfaces must exist.
3. **One canonical operation:** UI, API, SDK, CLI, MCP and Event-as-Code are interfaces over canonical domain semantics, not separate products with divergent rules.
4. **Reuse before duplication:** shared primitives in `PRIMITIVE_REGISTRY.yaml` are mandatory reuse points unless a documented escalation proves the abstraction is wrong.
5. **Design is a contract:** UI-facing work uses the approved Conflux v3 design manifest. Legacy styling is context, not the visual target.
6. **No shallow closure:** tests passing does not close a task when required UX states, migrations, edge cases or integration surfaces are missing.
7. **No strange capability inflation:** include features with recognizable user/operator value. Do not add verification recursion, ornamental cryptography, surveillance, purposeless gamification, or full clones of generic external products.
8. **Deterministic authority:** LLM/AI assistance may draft, summarize or propose; official scores, permissions, deadlines, policy, assignment constraints and winner state remain deterministic and reviewable.
9. **Sensitive state is least-privilege:** safety, consent, accommodation, dietary, recruiting and similar data receives explicit visibility/retention rules.
10. **Official results are reproducible:** judging/result algorithms use frozen, versioned inputs and do not silently rewrite historical results.
11. **Migration is part of implementation:** changing existing persisted state or an external contract requires an explicit compatibility/migration path.
12. **Recovery is repository-backed:** task/batch state, specs, receipts, design refs and escalations must allow a replacement controller/agent to resume without one long-lived process.

## Task closure

A task closes only when:
- its `deliverables` exist;
- `invariants` hold;
- `verification` is executed with real evidence;
- applicable `design_refs` are satisfied;
- required `surface_matrix` entries are closed or explicitly reclassified by an approved spec change;
- `non_goals` were not violated;
- a receipt records commands/results, changed paths, migrations, deviations and limitations.

## Batch closure

A batch closes only when every task is DONE **and** its subsystem spec/depth contract is satisfied. T90/T91 tasks are not paperwork: they must prove the explicit verification and cross-surface matrix.

## Research tiers are not implementation order

`BASE`, `ADV`, `EXPERT`, `PROG`, and `OPTIONAL` describe product exposure/depth. Architecture prerequisites may need to be implemented earlier than an “EXPERT” capability that depends on them. The project-story AST is the canonical example.

## UI timing

Claude Design foundation work may begin while stabilization/frontend architecture work is underway. The approved local handoff must be ingested by `PD-DESIGN-B00` before the visual foundation proceeds. Domain-specific Claude Design refinement should then run just-in-time before major UI-heavy subsystem batches rather than waiting for one late “massive UI” phase.
