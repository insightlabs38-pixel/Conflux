# UIV2-B10 — final visual, accessibility and regression gate
Result: DONE; campaign gate passes. Audit: docs/ui-v2/FINAL_AUDIT.md; media: docs/ui-v2/AFTER_MEDIA.md.
Gate found and fixed (an integration test also caught my map template dropping the 'Table T1' label; kept the test): skip-link contrast; focus hidden by sticky judge bar (2.4.11); submitted ballot shown as
empty scores; contradictory assignments copy; deliberation flags/table wrapping; public agenda + expo map never
restyled; foundations dark spec forcing an impossible state.
New specs: uiv2-gate (states, long content, focus, themes, landmarks), uiv2-final-states (finalized/published/
submitted, 6 widths). axe now includes WCAG 2.2 AA (target-size). Overflow helper names the offender.
Verification: make verify-fast exit 0 (pytest 1400 passed/23 skipped, ruff, frontend 168, build, SDK, block schema).
Playwright via make e2e-fast after image rebuild + demo-reset: 144 PASS, 0 failed, all 18 spec files, ~4 min
(serial run ~6+ min); baseline scenes re-recorded (25 stills, hashes in AFTER_MEDIA.md).
Evidence: docs/verification/UIV2-B10; clips remain in ignored artifacts/e2e-fast.
Commit: this checkpoint; push origin/main.
Limitations: no screen-reader pass; organizer/participant tours not at 360/1920; no user theme control in the app;
API-absent features (pairwise, scheduled publish, timeline) intentionally not shown. See FINAL_AUDIT.md.
Next: none; UI-v2 campaign complete.
