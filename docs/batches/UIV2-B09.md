# UIV2-B09 — remaining visible surfaces
Result: DONE; developer, builder and operations surfaces use the v2 system.
Material changes: API explorer (searchable list, method chips, endpoint/auth bar, formatted JSON
response); setup task tabs; page builder (outline + single editor, save state, confirmed removal,
brand/style/layout groups, accent preview, preview link); operations card grid; shared responsive
raw-form layout; communications field pairs; collapsible event creation/templates.
API/model: unchanged; constrained page customization architecture preserved.
Verification: frontend 167 PASS (+PageBuilder workflow, explorer format tests); typecheck/build PASS.
Playwright via `make e2e-fast` after rebuild + demo-reset: 125 PASS (37+48+40); new uiv2-surfaces tour
passes axe/overflow at 390/768/1024/1440; overflow helper now names the first offending element.
Fix: e2e discovery ignores artifacts/ (race between concurrent groups).
Evidence: docs/verification/UIV2-B09; matrix in ignored tests/e2e/artifacts.
Commit: this checkpoint; push origin/main.
Limitations: Form/Policy/Stage builders and webhooks gain structure/spacing, not new preview
features; no analytics page exists in the product to restyle; judge directory unchanged beyond forms.
Next: UIV2-B10-01 — final visual/accessibility/regression gate.
