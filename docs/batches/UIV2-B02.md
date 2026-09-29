# UIV2-B02 — authenticated shell and navigation
Result: DONE; persistent role-aware destinations replace the long-column root experience.
Material changes: desktop sidebar, mobile disclosure, context/title hierarchy,
active links, account menu and role-specific workspace groups; advanced organizer tools retained.
Native links support history/new tabs; inactive destinations retain drafts and offline state.
Authentication, RBAC dispatch, scoring, submission and publication APIs are unchanged.
Verification: frontend 145 tests PASS; typecheck/build PASS; diff/format review PASS.
Verification: stable existing Playwright role/shell/scenes 30 PASS, 13 intentional skips.
Verification: final compact mobile shell/menu/logout 4 PASS.
Verification: fresh seeded lifecycle/PVS 21 PASS, 11 intentional mobile duplicate skips.
Role destinations checked with axe/overflow at 390/768/1024/1440; keyboard/menu focus PASS.
Evidence: docs/verification/UIV2-B02; full matrix in ignored e2e artifacts.
React skill review: stable mounted workflow identity, native navigation, cleaned-up history listener.
Commit: this checkpoint; push origin/main.
Limitations: workflow internals are redesigned in B06–B09; this gate covers structural navigation.
Next: UIV2-B03-01 READY — constrained themes and public event shell.
