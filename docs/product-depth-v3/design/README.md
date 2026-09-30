# Conflux v3 design handoff (r2.1 · frozen for implementation)
Start here: `DESIGN_MANIFEST.yaml` → `system/README.md` → `decisions/` → `references/<x>/README.md` (+ `screenshots/`, `html/`). QA: `reviews/R2_1_BOARD_QA.md` (all 45 boards opened in the r2.1 session). Owner reviews: `reviews/CONFLUX_R1_DESIGN_REVIEW.md` (drove r2), `reviews/CONFLUX_R2_SIGNOFF_REVIEW.md` (drove r2.1). Later design passes: `LATER_DESIGN_PASSES.md`.
- `exports/r2.1/canvas/project/` is the native Claude Design project (`Main.dc.html`, `canvas.json`, 45 boards). `exports/r2.1/tools/build-exports.mjs --shots` regenerates standalone HTML + screenshots (`sync-canvas.py` keeps canvas.json in step).
- `exports/r2/` preserves r2 (native canvas, index, QA reports, `published/` r2 HTML + screenshots as delivered); `exports/r1/` preserves r1 the same way.
- `prompts/` holds the exact prompts that produced each pass.
Implementation agents: follow must-preserve intent; do not copy prototype CSS verbatim; map components via `system/component-mapping.md`. Foundation design is frozen: remaining questions in `decisions/007-open-questions.md` are non-blocking.
