# Product Depth v3 Task and Batch Schema

The original Conflux v2 required fields remain valid and are preserved. Product Depth v3 adds metadata that makes a large autonomous execution queue resistant to shallow implementation.

## Batch — required legacy fields

`id`, `title`, `phase`, `preferred_executor`, `dependencies`, `owned_paths`, `task_ids`, `completion_rule`.

## Batch — Product Depth v3 fields

- `status`
- `research_section` when research-backed
- `spec_refs`
- `design_refs`
- `design_required`
- `surface_matrix`
- `scope_summary`
- `depth_contract`
- `completion_evidence`
- `lock_groups`

`owned_paths` describes likely code ownership. `lock_groups` is the safer concurrency boundary and must be enforced by the future controller when overlapping work is active.

## Task — required legacy fields

`id`, `batch`, `phase`, `title`, `status`, `batch_dependencies`, `task_dependencies`, `goal`, `preferred_executor`, `freebuff_eligible`, `risk`, `owned_paths`, `required_reading`, `acceptance`, `escalate_if`.

## Task — Product Depth v3 fields

- `task_kind`
- `executor_class`
- `research_section`
- `product_tier`
- `spec_refs`
- `design_refs`
- `reuses`
- `deliverables`
- `invariants`
- `verification`
- `non_goals`
- `surface_matrix`

## Task kinds

- `architecture_contract`
- `architecture_implementation`
- `domain_capability`
- `ui_capability`
- `programmable_surface`
- `migration`
- `security`
- `scenario_fixture`
- `explanation_adapter`
- `design_guardrail`
- `design_contract`
- `audit`
- `repair`
- `verification`
- `integration`
- `frontier_review`
- `gate`

Examples/guardrails are not allowed to masquerade as standalone product features. A scenario task must prove a reusable engine; a design guardrail belongs to the persistent design contract/gate.

## Executor classes

Executor classes describe required capability, not a permanently hard-coded model vendor:
- `frontier-architecture`
- `architecture`
- `implementation`
- `ui-implementation`
- `platform-implementation`
- `high-integrity-implementation`
- `migration-implementation`
- `security-review`
- `verification`
- `independent-frontier-review`
- `design-review`

The future execution bundle maps these classes to the best currently available agents/models.

## Surface matrix

Possible surfaces:
`web`, `api`, `sdk`, `cli`, `mcp`, `event_as_code`, `audit`, `webhook`, `archive`, `analytics`, `search`, `docs`.

A value of `required` means T91/batch completion must prove the surface is implemented or explicitly revise the subsystem spec. `not_required` means the subsystem does not need that surface by default; an individual task may still require it.

## Status lifecycle

Task lifecycle remains:

`BLOCKED → READY → CLAIMED → ACTIVE → REVIEW → DONE`

with `CORRECTIONS` looping to review and `ESCALATED` as a side state.

The Stage B queue remains frozen. No task is READY until the final execution bundle activates it.
