# PD-B00 — Current-state baseline and defect census

## Result

Product baseline `e1888de` is green and reproducible; no P0/P1 found. 14 findings (0 P1, 2 P2, rest P3) routed to PD-B01–B04.

## Measured

- Backend: `pytest -n auto` 1400 passed/23 skipped (78 s); PostgreSQL 17: 1418 passed/5 skipped (97 s).
- Frontend: web 168 + embed 8 pass; format/lint/build/OpenAPI/SDK/block-schema/i18n pass.
- Browser: `e2e-fast` 144 passed/91 mobile skips/0 failed (3m48s); UI census 81 captures, 0 axe violations, 0 overflow.
- Load (H02, PG17): 147.6 req/s @2 workers, 222.7 @4; 0 5xx; 8/8 integrity checks each.

## Limitations

- S3 contract tests and k6 scenarios not run; webhook/API load not covered; single load run per config.

## Next

PD-B01 triage: D-09, D-04, D-12, D-06/D-13. Evidence: `BASELINE_RESULTS.md`, `DEFECT_REGISTER.md`, `ui-census/`, `logs/`.
