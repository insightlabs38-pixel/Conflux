# PVS-H05 — Demo evidence

Screenshots (1280×800 desktop, deterministic seed 7, reduced motion) captured by `tests/e2e/scenes.spec.ts` against a fresh `make demo-reset`: landing, gallery, results, agenda, expo map, organizer/judge/participant workspaces, API explorer, sign-in. Per-scene `video.webm` clips are regenerated with `make demo-e2e` (kept in `tests/e2e/artifacts/`, not committed).

Final re-verification on the finished tree: SQLite 1340 passed/23 skipped, PostgreSQL 1358 passed/5 skipped, Playwright 37/37, official acceptance 7/7 (T1 T2 verified), ruff/prettier/tsc/OpenAPI/SDK gates clean, image rebuilt and demo reset from scratch.
