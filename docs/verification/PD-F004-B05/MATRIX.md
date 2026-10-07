# PD-F004-B05 verification matrix — the data guardrails

Every capability is a rule of the live audit (`tests/e2e/slop.ts`, `slopProblems`) run by `tests/e2e/slop-audit.spec.ts` (read-only tier, seed 7) on every destination and task tab of the organizer, participant and judge roles and on the three public pages, at 390 and 1440. Contract: design `V-SLOP-9..12`, `V-SLOP-14`. Each rule has a self-test that injects a violation and expects the finding, so the gate is proven able to fail.

| Task | Rule (V-SLOP)    | Positive proof (page is clean)                   | Negative proof (the gate fails)                                                                | Product change                                                                                                                         |
| ---- | ---------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| T01  | recordGrids (14) | registrations and projects pages at 390 and 1440 | self-test "boxed records laid out three across"; "rows of a sortable table" specs              | registrations and projects are sortable tables                                                                                         |
| T02  | alarmColors (9)  | all audit pages                                  | self-test "red outside a failure and a page of alarms"                                         | red kept for a failure and a final destructive button; bulk apply and rebalance no longer red                                          |
| T03  | fakeAi (10)      | all audit pages                                  | self-test "an assistant look on a deterministic workflow"                                      | none; no assistant affordance existed                                                                                                  |
| T04  | precision (11)   | all audit pages                                  | self-test "a figure with false precision"                                                      | none; no surface showed more than two decimals                                                                                         |
| T05  | opaqueIds (12)   | all audit pages (Policies failed before the fix) | self-test "a box that asks for an opaque id"; live Policies page failed against the old bundle | policy check and permissions dry run choose a project, team or person by name (`RecordPicker`); `team_id` field on the projects entity |

## Behavior proofs for the one product change (T05)

- Unit: `RecordPicker.test.tsx` (names not ids, teams listed once, no-match and "showing N of M" states, participants source), `PolicyDebugger.interaction.test.tsx` (the chosen project's id is what the API receives).
- Integration: `tests/integration/test_entity_pickers.py` (team found through its project with its id, null teams excluded, `team_id` hidden by default and unfilterable, judge refused on the projects entity and on participants); `test_feature_search` and `test_extension_manifest` keep the registry claims honest.
- Browser: `tests/e2e/record-picker.spec.ts` at 1440 and 390 on live seed data: project and team chosen by name, policy check returns a result.

## State and viewport coverage

- Normal and dense: seed 7 is the full demo event. Narrow: every rule runs at 390.
- Loading, empty, error and long-list: the picker shows "Loading…", "Could not load X", "No X matches" and "Showing N of M; type to narrow" (unit-tested). The other states stay covered by `visual-foundation`, `uiv2-gate`, `uiv2-final-states` in the same green run.
- Authorization: the picker reads only sources that already enforce organizer/admin (projects entity, portfolio participants); a judge gets 403 on both (integration test). Policy-debug still 404s a subject outside the event.
- Migration/lifecycle: no persisted state changed; the new field is read-only derived data and the API payloads for policy-debug and authz-dry-run are unchanged.

## Defects found by this batch's verification (fixed in the product, nothing relaxed)

- Setup > Policies asked for a typed "Project ID" / "Team ID" (T05); the Permissions dry run asked for a "User public ID" (T05); boxed record rows on registrations and projects (T01); alarm-red on bulk apply and rebalance (T02).
- Tried and backed out: new `teams` and `people` query entities. Every registered entity must be claimed by a feature, a manifest and a search contract, and 17 inventory tests said so; teams are searched through projects by contract, so the picker reads the existing sources.

## Commands

`T90-e2e-fast.log` (`make e2e-fast`, run alone: read-only, isolated-mutation and canary ok) and `T90-verify-fast.log` (`make verify-fast`: format, ruff, 2943 pytest passed, 704 vitest, build, openapi, sdk checks) in this folder. An earlier run with both in parallel failed one vitest (`useRealtime`) and one 30 s canary timeout (`uiv2-organizer` at 390) from CPU contention; both passed alone and are not related to this batch.
