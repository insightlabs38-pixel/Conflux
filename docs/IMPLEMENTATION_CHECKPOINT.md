# Conflux — current implementation checkpoint

UI-v2 is active on canonical `main`; authoritative [queue](execution/README.md)
and [surface census](ui-v2/SURFACE_CENSUS.md). One sequential worker; B00–B02 complete; B03 event theming/public shell is next. PVS-H06 remains a completed historical release.

PVS-H06 is complete on `main`; the prior release campaign is closed. Its final
targeted pass closes the pairwise-to-awards and sponsor-resource portability
gaps and refreshes presentation/evidence. UI-v2 extends this completed baseline without changing its integrity guarantees.

## Current state

- Session tokens are stored only as keyed digests; gallery pagination is complete.
- Human-facing PVS workflows are integrated in organizer, judge, participant,
  mentor and volunteer workspaces; [UI map](operations/PVS_UI.md).
- Real-provider Dex OIDC smoke completed: 18/18. Supervisor files and tests
  are committed; obsolete instructions to preserve uncommitted supervisor
  files no longer apply.
- Evaluation awards consume published normalization or pairwise runs according
  to plan mode, preserving track ranking, overrides and run-specific evidence.
- Canonical final archive v3 restores AwardResource content and creator
  attribution, rewrites pairwise award references, and remains able to read
  the frozen v2 contract. Use `mode=final` for sponsor-content portability.
- Conflux claims T1–T4 under the organizer clarification: the unchanged official
  checker automatically verifies T1/T2; T3/T4 are manually judged and backed
  by [Conflux's extended verifier](verification/dogfood-extended.txt).

## Evidence

Current PostgreSQL, fast-gate, browser/media and extended-check results are
in [the final targeted report](verification/final-pass/report.md).
[PVS-H06 release evidence](verification/PVS-H06/report.md) records successful
cold/offline startup, backup/restore, chaos, artifact portability and load
runs (zero server errors or integrity violations), plus Dex interoperability.
These prior expensive checks are labeled as prior receipts, not silently
reported as rerun here.

## Remaining limits / handoff

[Known limitations](verification/README.md#remaining-limits) retain the honest
OIDC, statistical and API/CLI-first boundaries. Sponsor resources travel in
final archives; v1 config/full and Event-as-Code keep their narrower scope.
The owner still records the final video using [the demo runbook](operations/DEMO.md)
and the generated `artifacts/conflux-final-demo-media.zip` handoff.
