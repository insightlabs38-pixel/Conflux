# Legacy DOGFOOD Execution Files — Integration Policy

The original DOGFOOD execution artifacts are useful context and should generally be preserved/merged into the cohesive repository documentation rather than discarded.

## Why keep them

They contain:
- historical implementation decisions and batch receipts;
- evidence about what actually shipped;
- prior verification commands/results;
- useful operating conventions;
- limitations and lessons that explain current architecture.

The old files are therefore **historical/context authority for the work they describe**.

## Authority boundary

For future Product Depth v3 execution:
- `TASKS.yaml` / `BATCHES.yaml` from Product Depth v3 define the new program;
- `docs/execution-v3/**` defines current execution-control semantics;
- `docs/product-depth-v3/**` defines current product/depth/design contracts.

Old DOGFOOD queue/status files must not create a second active scheduler or override Product Depth v3 runtime state.

## Merge guidance

A merge agent should:
1. retain historical receipts, batch reports, architecture docs and useful old execution context;
2. relocate or clearly label old queue/control files as historical where necessary;
3. preserve links/references used by current docs when practical;
4. avoid duplicating two active `TASKS.yaml` / `BATCHES.yaml` authorities;
5. add a short lineage/index explaining which files are historical versus active;
6. preserve old evidence verbatim where rewriting would weaken provenance.

The old and new systems are not radically incompatible. The new system is primarily a stricter, more resumable evolution of the earlier approach, so a cohesive combined bundle is preferable to deleting historical context.
