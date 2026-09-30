# Stage B — Queue Enrichment and Execution-Contract Rewrite

## Status

This is the **Stage B** working set. It replaces the Stage A-generated queue as the preferred Product Depth v3 queue, but it remains **FROZEN** until the remaining execution bundle is built and activation is explicitly approved.

## Result

- **Batches:** 330
- **Tasks:** 3104
- Added **1 design-ingestion batch** with 7 design-contract tasks.
- Added **1 project-story architecture implementation task** so the canonical AST precedes editor work.
- Every research-backed task now has stable subsystem spec references.
- Every task now has explicit `deliverables`, `invariants`, `verification`, `non_goals`, `task_kind`, `executor_class`, `reuses`, `surface_matrix`, and design references where applicable.
- Every research-backed batch now has semantic scope, depth contract, completion evidence and concurrency lock groups.
- Generated **129 subsystem execution contracts** from the research program.
- Tasks with design references: **2496**
- Tasks reusing at least one canonical primitive: **2063**

## Major semantic corrections

1. **Claude Design moves before the visual foundation.** `PD-DESIGN-B00` sits between the product/cross-surface foundation and `PD-F004`. Claude Design may run earlier in parallel, but its approved local handoff must be ingested before the visual system is implemented.
2. **Project stories are architecture-first.** `PD-S015-B01-T00A` establishes the canonical rich-document AST and migration scaffold before Markdown/rich-editor tasks.
3. **§117 scenarios are fixtures over one simulation engine.** Scenario tasks explicitly forbid bespoke calculators.
4. **§130 examples are adapters over one structured explanation model.** They no longer authorize hardcoded explanation strings.
5. **§71 registered-type fragments are rewritten into coherent schema/version/migration/permission/audit contracts.**
6. **Query/saved-view work explicitly reuses the foundation query/data-grid primitives.**
7. **Risk now considers blast radius** for shared primitives, official judging/results and sensitive domains.
8. **Batch names are semantic** rather than generic `slice XX` labels.
9. **T90/T91 now have explicit proof responsibilities** via the subsystem surface matrix and task verification fields.
10. **Model names are no longer the only scheduling signal.** `executor_class` is the durable requirement; a later policy maps it to current agents/models.

## Why the YAML is more specific without becoming the only spec store

The queue remains a practical execution/state index and can be maintained directly with targeted search/edit tooling. Reusable architecture and depth additionally live in:
- `docs/product-depth-v3/specs/*.md`
- `PRIMITIVE_REGISTRY.yaml`
- `EXECUTION_PRINCIPLES.md`
- the Claude Design manifest/handoff.

This prevents `TASKS.yaml` from becoming thousands of independent mini-design documents while still making every task substantially harder to satisfy shallowly.

## Validation

The queue is structurally revalidated after enrichment:
- IDs unique;
- batch/task references resolved;
- batch DAG acyclic;
- every batch task ID resolves to a task in that batch;
- all tasks/batches remain BLOCKED.

## Risk distribution

- `high`: 813
- `low-medium`: 726
- `medium`: 498
- `medium-high`: 1067

## Task-kind distribution

- `domain_capability`: 1548
- `verification`: 337
- `integration`: 316
- `ui_capability`: 297
- `frontier_review`: 160
- `architecture_contract`: 129
- `migration`: 107
- `programmable_surface`: 81
- `gate`: 39
- `security`: 37
- `design_guardrail`: 13
- `audit`: 11
- `scenario_fixture`: 9
- `repair`: 7
- `design_contract`: 7
- `explanation_adapter`: 5
- `architecture_implementation`: 1

## Next bundle stage

Do not activate yet. The remaining bundle work should add:
- controller/orchestrator contract;
- resumable claim/lease/state rules;
- receipt schema;
- escalation schema/protocol;
- checkpoint/handoff format;
- executor-class → current-model policy;
- queue/design/spec lint tooling;
- exact parallelism/lock enforcement;
- activation procedure;
- top-level implementation handoff prompt.

Claude Design can proceed locally now; its approved output will eventually fill `design/DESIGN_MANIFEST.yaml` and satisfy `PD-DESIGN-B00`.


## Execution bundle

The controller/resumability/receipt/escalation/checkpoint/parallelism/activation layer and standard prompts are now included under `docs/execution-v3/` and `prompts/`. The program remains FROZEN.
