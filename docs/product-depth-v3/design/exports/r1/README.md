# r1 (preserved)
r1 as delivered: `canvas/project/` (native), `html/Main.html` + `screenshots/Main.png` (index), `published/` (r1 reference HTML + screenshots as they were before r2). Do not run `tools/build-exports.mjs` from here — it writes into `references/`, `states/` and `system/` and would overwrite r2 outputs; use `../r2/tools/`.
