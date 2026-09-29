# UIV2-B07 — judge workflow and scoring
Result: DONE; judge desk optimizes throughput with intentional desktop/mobile layouts.
Material changes: overview summary (assigned/remaining/next/recused/route); progress meter;
queue list with Next/status; evidence | rubric split; criterion cards (weight, anchors);
autosave state; previous/next; recuse/conflict action; Submit and continue; sticky mobile
actions; route as numbered stops with next-stop emphasis; assignment rows; polished inspector.
Safety: inspector renders inspected static content only; no participant content executed.
API/model: unchanged; judging semantics, normalization, eligibility, peer isolation untouched.
Verification: frontend 160 PASS (added JudgeDesk tests); typecheck/build/prettier/diff PASS.
Playwright (fresh demo-reset, app image rebuilt): uiv2-judge 4 PASS (axe/overflow/keyboard at
390/768/1024/1440); lifecycle judges+publish 4 PASS; pvs/roles/workspace-shell/scenes/participant 49 PASS.
Evidence: docs/verification/UIV2-B07; full matrix in ignored tests/e2e/artifacts.
Commit: this checkpoint; push origin/main.
Limitations: demo seed has no assignment rows/shared artifacts, so those states are unit-tested,
not rendered; "Recuse" reuses Decline (no new COI API added).
Next: UIV2-B08-01 — organizer overview, eligibility queue, logistics, deliberation, publication, onsite.
