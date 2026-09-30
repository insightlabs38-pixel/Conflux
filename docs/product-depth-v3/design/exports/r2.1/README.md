# r2.1 (current)
`canvas/project/` is the native Claude Design project (45 boards, `canvas.json`, `v3.css`). `html/Main.html` + `screenshots/Main.png` are the index board; every other board is exported into `references/`, `states/` and `system/prototypes/`. `qa/dimension-report.json` is the overflow/dimension first filter from the final build.
Rebuild (from repo root): `python3 docs/product-depth-v3/design/exports/r2.1/tools/sync-canvas.py && node docs/product-depth-v3/design/exports/r2.1/tools/build-exports.mjs --shots`
History: `../r1/` (r1 as delivered), `../r2/` (r2 native project + `published/` r2 outputs as they were before r2.1).
