# UIV2-B06 — participant event/team/submission experience
Result: DONE; participant flow is task-oriented, not one long panel stack.
Material changes: Overview (team/project/eligibility/deadline status + next action);
Team = Your team / Find teammates; resources = Rules / Sponsor challenges / On-site;
project tasks: story, evidence & checks, forms, submission, eligibility, support, after event;
task switches keep drafts; story editing via existing PATCH; readable signed receipt with
frozen judge-visible evidence, signature/digest/history in native disclosures; drift hides downloads.
API/model: unchanged; server keeps deadline, policy, eligibility and immutable-evidence authority.
Verification: frontend 158 PASS (62 files); typecheck+build PASS; prettier PASS; diff --check PASS.
Playwright (after scripts/demo-reset): participant-workflow, lifecycle, pvs, workspace-shell,
scenes, roles = 55 PASS, 28 duplicate-matrix skips; axe/overflow/keyboard at 390/768/1024/1440.
Note: an initial run failed only because prior-run demo state was consumed; fresh reset passed.
Evidence: docs/verification/UIV2-B06; full matrix in ignored tests/e2e/artifacts.
Commit: this checkpoint; push origin/main.
Limitations: overview deadline derives from configured public event window, not per-stage policy.
Next: UIV2-B07-01 — judge queue, scoring workflow and artifact inspector.
