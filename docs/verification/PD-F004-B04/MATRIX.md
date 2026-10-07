# PD-F004-B04 verification matrix — the anti-slop guardrails

Every capability is a rule of the live audit (`tests/e2e/slop.ts`, `slopProblems`) run by `tests/e2e/slop-audit.spec.ts` (read-only tier, seed 7) on every destination and task tab of the organizer, participant and judge roles and on the three public pages, at 390 and 1440 (65 page tests). Contract: design `V-SLOP-1..8`. Each rule has a self-test that injects a violation and expects the finding, so the gate is proven able to fail.

| Task | Rule (V-SLOP)      | Positive proof (page is clean)                      | Negative proof (the gate fails)                                                    | Product change                                                                                              |
| ---- | ------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| T01  | gradient (1)       | all audit pages; stylesheet and web-source ratchets | self-test "a gradient and an icon in a coloured square"                            | none; no organizer option can produce one                                                                   |
| T02  | iconTile (2)       | all audit pages                                     | same self-test                                                                     | none (B01/B02 already removed the tiles)                                                                    |
| T03  | kpiCards (3, 14)   | all audit pages                                     | self-test "a row of cards"                                                         | overview, on-site facts and operations sections became one summary strip each; per-figure loading and retry |
| T04  | operatorCopy (6)   | all audit pages                                     | self-test "oversized and tagline copy"                                             | 43 page taglines removed; shell text held to 20px                                                           |
| T05  | pills (5)          | all audit pages                                     | self-test "a pill around words and two tags in one row"                            | none (Status and Tag from B02)                                                                              |
| T06  | nestedCards (4)    | all audit pages and every task tab                  | self-test "a card inside a card"                                                   | page editor stands on the page; empty, loading and table states lose their inner frame                      |
| T07  | repeatedLabels (7) | all audit pages and every task tab                  | self-test "a label said twice and a crumb that repeats the title"                  | task-tab headings removed; Communications and Judging cards renamed                                         |
| T08  | hiddenActions (8)  | all audit pages and every task tab                  | self-test "actions hidden behind three dots" (glyph, menu trigger, icon-only More) | none; no menu existed                                                                                       |

## State and viewport coverage

- Normal and dense: seed 7 has the full demo event (stages, forms, policies, 10-page organizer destinations). Narrow: every rule runs at 390.
- Loading, empty and error states are exercised by existing specs that stay green (`visual-foundation` states, `uiv2-gate`, `uiv2-final-states`); error and denied states keep their border because it carries meaning (T06).
- Authorization and lifecycle: no endpoint, model or lifecycle changed in this batch; server-side authorization is untouched. The audit is read-only and runs on the shared stack.

## Defects found by this batch's verification (fixed in the product, nothing relaxed)

- 43 pages carried a tagline under the title (T04); four cases of a card inside a card (T06); headings repeating the tab or page title on six panels (T07); three card rows (T03).

## Commands

`T90-e2e-fast.log` (full `make e2e-fast`, clean on the first run: read-only 264 passed, every isolated spec and the canary chain ok) and `T90-verify-fast.log` (`make verify-fast`, 2940 pytest and 701 vitest passed) in this folder.
