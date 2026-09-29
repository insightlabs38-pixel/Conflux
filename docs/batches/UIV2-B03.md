# UIV2-B03 — event themes and public shell
Result: DONE; constrained event brand/layout settings and coherent public presentation.
Material changes: real appearance editor, active public navigation/footer, responsive
hero treatments, schedule/resources/FAQ/announcements; Django and React share resolved settings.
Schema: optional Page.theme_config; safe HTTP(S) image URLs, typed presets and accent contrast.
Three repeatable demo themes differ in typography, hero, density, width and corner treatment.
v1/Event-as-Code portability retained; final v4 carries themes and reads frozen v2/v3 contracts.
Verification: frontend 146 tests PASS; typecheck/build/format/diff PASS; SDK/schema check PASS.
Verification: public/theme/final-archive/Event-as-Code suite 56 PASS;
seed/theme/audit suite 42 PASS; theme/accessibility/conformance suite 44 PASS; Ruff PASS.
Verification: existing Playwright public/theme matrix 32 PASS, 16 intentional viewport skips.
Rendered Django and React: 390/768/1024/1440 × technical/student/conference/dark;
axe/overflow PASS, keyboard public skip-link PASS. Scoped React dark contrast defect fixed.
Evidence: docs/verification/UIV2-B03; full matrix in ignored e2e artifacts.
Demo events: seeds 81 technical, 82 student, 83 conference (synthetic published workflows).
Commit: this checkpoint; push origin/main.
Limitations: project/gallery/result storytelling and profile attribution belong to B04/B05.
Next: UIV2-B04-01 READY — reusable identity model/API and profile/person presentation.
