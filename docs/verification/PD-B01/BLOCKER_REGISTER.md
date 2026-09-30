# PD-B01 — Current-state blocker register (closed)

**No known P0/P1 correctness, security, integrity or migration blocker remains.** None existed at the PD-B00 baseline; this batch repaired every repairable P2/P3 correctness/integration finding and records the rest as non-blocking limitations owned by later batches. PD-B00's `DEFECT_REGISTER.md` stays as the baseline record; this file holds final states.

## Repaired (verified)

| ID               | Sev | Repair                                                                                                                          | Evidence                                                                                                        |
| ---------------- | --- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| D-09             | P3  | `JudgeWorkspace` ignores re-selection of the current event/stage (root cause: loading flag set without a re-running effect)     | vitest regression (failed pre-fix), Playwright probe on rebuilt stack, `logs/T05-d09-browser-probe.spec.ts.txt` |
| D-04             | P2  | Real prior-release upgrade smoke test from `demo/release-freeze` (51→101 migrations, 5 known records intact) + fixture hash pin | PG suite 1420 passed/4 skipped; negative case fails loudly                                                      |
| D-01             | P3  | `lifecycle` canary fails in ≤10 s with an actionable "run scripts/demo-reset submitted" message                                 | `logs/T03-lifecycle-guard-no-reset.log`                                                                         |
| D-06             | P3  | S3 storage contract verified against the running RustFS (3 passed); two-endpoint portability stays a release script             | `logs/T05-s3-contract.log`                                                                                      |
| D-14             | P3  | Not reproduced: 2-worker throughput varies 101–148 req/s run to run on this host; closed as measurement variance                | `logs/T05-h02-workers2-rerun{1,2}.log`                                                                          |
| D-02, D-07, D-11 | P3  | Docs corrected in PD-B00-T06; runbooks updated in B01-T04                                                                       | —                                                                                                               |

## Remaining, non-blocking limitations (owned elsewhere)

| ID   | Sev  | Limitation                                                                | Owner                |
| ---- | ---- | ------------------------------------------------------------------------- | -------------------- |
| D-03 | P3   | ~7.7 s per-xdist-worker DB setup dominates backend wall time              | PD-B02               |
| D-05 | P3   | No isolated per-test event fixtures; single mutable demo event            | PD-B03               |
| D-08 | P3   | Deep link to a view the role lacks silently falls back to Overview        | PD-B04 / spec 122    |
| D-10 | P3   | Signed-out shell logs an expected-but-noisy 401 console error             | PD-B04               |
| D-12 | P2   | No webhook/API-credential load coverage                                   | spec 051/055 batches |
| D-13 | P3   | k6 scenarios need a hand-built profile (none committed)                   | spec 055/061 batches |
| —    | P3   | Artifact picker does not live-update after upload (Refresh button exists) | spec 015/017 batches |
| —    | info | Legacy `freebuff` process still idle in `freebuff-lane` worktree          | owner discretion     |
