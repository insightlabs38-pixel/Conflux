# PD-DESIGN-B00 — Conflux v3 design-system and reference-surface handoff gate
## Result
All 7 tasks DONE (T01-T07; this batch has no T90/T91/T95). The r2.1 Claude Design handoff is committed, reviewed against the shipped system and frozen for implementation. No application code, route, migration, OpenAPI or SDK change.
## Changes
- `exports/r2.1/SOURCE.md` (revision, archive sha256, zero-diff check), `system/VISUAL_CONTRACT.md` (rules V-*, anti-slop V-SLOP-1..15), `states/STATE_MATRIX.md` (rules S-*, 9 surfaces x 11 classes), `reviews/B00_APPROVAL.md` (approval, findings F-1..F-8, obligations O-1..O-4), `IMPLEMENTATION_HANDOFF.md`, manifest pointers.
- Decisions D-011 (organizer rail size, 11px floor) and D-012 (44px touch hit area `--h-touch`, hero budget is the band); tokens corrected (contrast comments, revision r2.1, `--h-touch`).
## Verification
- `uv run --frozen pytest tests/test_design_manifest.py` 21 passed: manifest and artifact paths resolve, css equals json, contrast of every token pair in both themes, scales, board must-preserve markers, state matrix completeness, every `Role` reviewed, queue design refs in manifest.
- Chromium measurements at 1440 and 390 (geometry, fonts, hero bands, touch heights, landmarks); screenshots of 12 boards opened at full resolution; `validate_queue.py` valid (331 batches, 3110 tasks, 0 errors).
## Findings
- Resolved by decisions: rail size, 10px avatar text, 40px mobile controls, hero heights read literally. Planned: sponsor board (just-in-time), assignment/Event Doctor/drift/floorplan/audit/RTL passes (`LATER_DESIGN_PASSES.md`).
- Obligations for PD-F004: shipped DataGrid lacks J/K/X/E/V/F and `aria-sort`; state components lack kept-data, retry-scope, error-ref and reason fields.
## Limitations
- Approval is by the single implementing agent (same-account), on top of the owner's direction sign-off (`reviews/CONFLUX_R2_SIGNOFF_REVIEW.md`); static comps leave hover, focus, axe and motion to implementation QA.
## Next
PD-F004-B01 (visual direction spec 004). Checkpoint: `checkpoints/CP-PD-DESIGN-B00.yaml`.
