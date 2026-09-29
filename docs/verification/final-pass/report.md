# Final targeted Conflux pass

Implementation source: `d7c6d87` (full SHA in the extended receipt).

The PVS-H06 release remains closed. This pass fixes pairwise evaluation
awards and sponsor-resource portability, adds independent evidence and
refreshes the demo/README. The vendor checker remains byte-identical:
`aa98963841bc8e18e8e5d76f0499697c093dd3c0055f9d73a459f592f4dcf09d`.

## Changes proven

- Evaluation-sourced awards select from the published run matching the plan
  mode. Pairwise evidence records `pairwise_run`; weighted rubric evidence
  retains `normalization_run`. Track ranking, allowed ranks, reasoned
  overrides, event scope, stacking and authorization retain their boundaries.
- Canonical final archive v3 carries all five sponsor resource kinds,
  creator attribution and ordering (including tied positions), and rewrites
  pairwise winner references. Restored comparison pairs respect their fresh
  primary-key order. v2 imports retain exact source/provenance and upgrade
  explicitly; v3 cannot silently omit its new table. v1 config/full and
  Event-as-Code remain narrower, documented formats.
- Conflux claims T1–T4 under the organizer clarification. The official
  checker automates T1/T2 only; T3/T4 are manually judged. Its actual note
  “claimed but not verified: T3 T4” is preserved and explained in the README.
- Screenshot-only polish: route panels show the count of unplaced projects;
  deliberation avoids invented expected coverage when no assignment count
  exists. Both preserve API semantics and existing workspace structure.

## Regression receipts

| Gate                                                          | Result                                                                                                      |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Initial targeted awards/pairwise/archive compatibility        | 50 passed                                                                                                   |
| Final archive + acceptance consistency                        | 18 passed                                                                                                   |
| Full PostgreSQL 17 suite                                      | 1391 passed, 5 skipped                                                                                      |
| Affected PostgreSQL suites after resource ordering refinement | 70 passed                                                                                                   |
| Final `make verify-fast`                                      | 1373 backend passed, 23 skipped; 137 web + 8 embed passed; format/lint/build/OpenAPI/SDK/block-schema clean |
| Untouched official acceptance                                 | 7/7; claims T1–T4, verifies T1/T2                                                                           |
| Conflux extended verifier                                     | PASS; 320 regression tests, OpenAPI/SDK and live embed; exact sources linked below                          |
| Submitted Playwright suite                                    | 60 passed, 11 desktop-only mobile skips                                                                     |
| Final lifecycle with uploaded brief and safe inspector        | 6/6 passed                                                                                                  |
| Published Playwright suite                                    | 39/39 passed                                                                                                |

The full PostgreSQL receipt precedes the final tied-position refinement;
the affected PostgreSQL and final full fast suites cover that refinement.
The final lifecycle browser run covers the added brief upload and inspector;
published browser checks cover the final screenshot scene selection using
the public/roles/scenes/signin/embed set. Stateful PVS workflows and their
role accessibility/overflow scans are covered at the submitted checkpoint.
Transient screenshot-selector failures and a rebuild-interrupted mobile
sign-in run were corrected/rerun. No failed-run media is in the handoff.

[Extended tier/capability report](../dogfood-extended.txt) reruns voting,
comments/moderation, hidden results, ballot order and abuse controls; signed
records, webhooks/retries/replay, archive round-trips; normalization proof,
pairwise awards, isolation, CLI/SDK, judging replay, Event-as-Code, capsule,
OIDC, MCP, hybrid/on-site, governance and portfolio. It also runs validated
OpenAPI/SDK commands and a live embed browser check.

## Media and handoff

Deterministic seed 7, submitted and published checkpoints; raw successful
Playwright clips, 19 selected screenshots and 12 videos. Four losslessly
optimized PNGs in `docs/assets/readme/` are committed. Browser views were
inspected for loading placeholders, errors, overflow, identifying local data
and redundant content. Demo identities/content are synthetic.

Run `scripts/package-demo-media --zip` after collecting both checkpoint runs.
The ignored handoff is `artifacts/conflux-final-demo-media.zip`, with a scene
index, README and SHA-256 manifest. No videos, traces, database dumps or ZIP
are committed.

## Prior evidence and remaining limits

[PVS-H06](../PVS-H06/report.md) retains Dex OIDC 18/18, cold/offline startup,
backup/restore, chaos, artifact portability and load receipts (zero 5xx,
zero race/integrity violations). Those expensive checks are referenced,
not reported as rerun in this pass.

[Known limits](../README.md#remaining-limits) include manual tier judging,
identity/normalization assumptions, API/CLI-first operator capabilities and
the need to re-open a project after upload to refresh its submission picker.
