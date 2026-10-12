# Conflux — DOGFOOD 2026 Post-Spec Product & Architecture Plan v2.2

**Freeze date:** 2026-09-23  
**Implementation window:** 2026-09-25 18:00 UTC → 2026-09-28 18:00 UTC  
**Status:** planning only; no competition implementation code is contained in this package.

This supersedes `DOGFOOD_prebuild_plan_frozen_2026-09-01.zip` as the authoritative product/architecture plan after release of the official spec, checker, and fixture corpus.

## Thesis

Build an adoption-quality, self-hosted competition platform whose **Core is materially above T4**. The tier ladder is an acceptance floor inside Core, not the product boundary. Stretch and Very Stretch work must be additive through stable extension contracts; it must not require schema or architecture rewrites.

## Read order

1. `00_EXECUTIVE_FREEZE.md`
2. `01_OFFICIAL_REQUIREMENTS_AND_DELTAS.md`
3. `02_CORE_SCOPE_AND_PRODUCT_STRATEGY.md`
4. `03_ARCHITECTURE.md`
5. relevant domain file(s)
6. `21_CORE_FEATURE_MATRIX.md`, `22_STRETCH_GOALS.md`, `23_VERY_STRETCH_GOALS.md`
7. execution details live in the separate `Conflux execution-control` pack.

## Official snapshot

`official/` contains the released spec context, exact `run.py`, and exact `fixtures.json` used for this planning pass.

## Non-goal

This package is not a starter repository. It deliberately contains no Conflux project source, generated framework scaffold, Compose configuration, migrations, or application code that would violate the competition's pre-kickoff code restriction.

## Execution v2.2
See `29_EXECUTION_INTERFACE.md`; detailed logistics live in the updated execution-control pack.
