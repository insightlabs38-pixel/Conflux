# UIV2-B04 — reusable identity and profile
Result: DONE; real profile editing/visibility, reusable person UI and scoped history.
Schema: UserProfile on existing users; name/avatar/bio/location/links, reusable tags,
private/member/public visibility; authenticated edit and privacy-aware person read APIs.
Material changes: profile destinations for all supported roles, person pages/links,
roster/marketplace/judge identity, safe URL/tag validation and deterministic avatar fallback.
Existing matching, availability, expertise, mentoring and portfolio records remain their sources.
Account tags copy into an event draft only by explicit action; matching semantics unchanged.
Audit writes are atomic; sessions/RBAC/SSO/ballot/publication APIs unchanged.
Verification: frontend 151 tests PASS; typecheck/build/format/diff PASS; SDK/schema PASS.
Verification: identity/team/marketplace/judge/auth/session/demo suite 62 PASS; Ruff PASS.
Verification: demo/archive regression suite 39 PASS; migration recorded/confirmed PASS.
Verification: existing Playwright profiles/roles/shell 27 PASS, 15 intentional matrix skips.
Profile edits/public views at 390/1440; every role destination at 390/768/1024/1440;
axe/overflow, keyboard, draft retention, new-tab navigation and logout PASS.
Evidence: docs/verification/UIV2-B04 plus ignored e2e matrix artifacts.
React skill review: lazy initial load with retained drafts; cleanup and response errors contained.
Commit: this checkpoint; push origin/main.
Limitations: public identity does not publish private history or judge expertise; avatars use safe URLs.
Next: UIV2-B05-01 READY — gallery/project/results presentation and attribution.
