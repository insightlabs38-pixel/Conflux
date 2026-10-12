# CLAUDE DESIGN r2.1 MICRO-POLISH / FINAL SIGN-OFF PASS

You are responsible for the **final micro-polish and QA pass** on the existing Conflux v3 Ledger foundation design.

This is **not a redesign**.

Current state:
- r1 established Ledger.
- r2 fixed fixture-induced whitespace, added dark mode, 768/1024/1920 responsive references, large-data stress coverage, and full pairwise judging.
- The owner considers the direction substantially correct.
- Your task is to remove the remaining small inconsistencies and produce a trustworthy final implementation handoff.

Use Claude Opus 5.5 Medium by default. High thinking is unnecessary unless you encounter an actual design-system contradiction.

## 1. Read first

```bash
sed -n '1,320p' docs/product-depth-v3/design/DESIGN_MANIFEST.yaml
sed -n '1,320p' docs/product-depth-v3/design/reviews/R2_BOARD_QA.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/007-open-questions.md
sed -n '1,260p' docs/product-depth-v3/design/decisions/008-dark-mode.md
sed -n '1,260p' docs/product-depth-v3/design/decisions/009-responsive-and-wide.md
sed -n '1,280p' docs/product-depth-v3/design/decisions/010-pairwise-judging.md
sed -n '1,360p' docs/product-depth-v3/design/reviews/R2_SIGNOFF_REVIEW.md 2>/dev/null || true
```

Use targeted `rg`, `grep`, `sed -n`, exact files and the existing rebuild scripts.

Do not redesign Ledger or revisit settled product hierarchy without a concrete defect.

## 2. Perform a genuinely complete manual board QA

Open **all 45 current r2 boards at full resolution in this session**, including byte-identical inherited boards.

Do not rely on claims about what was manually inspected during r1.

Update:

`docs/product-depth-v3/design/reviews/R2_1_BOARD_QA.md`

For each board record only:
- PASS / FIXED / BLOCKED;
- one concise note where useful.

Check:
- alignment;
- whitespace;
- clipping;
- action hierarchy;
- control baselines;
- fixture realism;
- pane balance;
- text truncation;
- responsive composition;
- dark tokens;
- status semantics.

The ledger must truthfully describe what you actually opened.

## 3. Correct current-revision labels

Historical files under `exports/r1/**` remain untouched and continue to say r1.

Current reference/system/state outputs must identify the current revision consistently.

At minimum inspect/fix the current equivalents of:
- Sys-Foundations;
- Sys-Components;
- States-1;
- States-2.

Use `r2.1` or an explicit current label such as `r2.1 · content inherited from r1`; do not falsely rewrite historical provenance.

Search all current non-history design outputs for stale revision labels before finishing.

## 4. Remove the “Error by horizon” ambiguity

In normal successful project/evidence references, **“Error by horizon” means statistical forecast error**, not a render error, but the striped placeholder makes it look broken.

For normal successful states:

- rename the figure title/caption to **“Forecast MAE by horizon”**;
- replace the striped Figure 2 placeholder with a simple real inline SVG/static chart using the existing fixture values for h=1, h=6 and h=24;
- use the same semantic figure treatment in the story editor, judge evidence, public project, responsive judge and pairwise/mobile references where that figure appears.

Do not create a visualization library. This is a design fixture.

Keep the intentionally broken-media state in the state matrix, but make the distinction obvious:

- failure label: `Figure 2 failed to load`;
- retained caption/title: `Forecast MAE by horizon`;
- retry + long-description behavior remains visible.

If practical, replace the normal striped architecture placeholder with one compact real architecture diagram as well. Do not expand the task if that becomes time-consuming.

## 5. Fix the known Data-Surface polish issues

Fix:
- stray hairline fragment at the selected/cursor row → inspector boundary;
- overly tight `Changed` column at 1440.

Do not reduce useful data density or change the established table/inspector contract.

Regenerate light, dark and wide derivatives affected by the shared fix.

## 6. Button/control alignment sweep

There is no evidence of a system-wide `.btn` sizing failure; `.btn` already uses fixed control height + inline-flex centering.

Audit the visible mixed action rows and fix only actual visual misalignment:

- Story editor top controls;
- Builder-Plan top action group;
- Deliberation-Finalize approval/footer row;
- My Event event-pass/help actions;
- Resp-768 evidence/footer actions;
- Pairwise-Narrow decision bars;
- dialogs and overlays;
- dark equivalents where affected.

Distinguish:
- outlined button;
- ghost button;
- text link;
- status/tag;
- segmented control.

Do not make unlike controls identical just to force a common box.

## 7. Resolve the outlined-button border question

Adopt the stronger **line-3** border for normal outlined interactive buttons in light and dark mode.

Keep:
- primary buttons filled;
- ghost/text actions borderless;
- panel/table hairlines at their existing lighter strength;
- disabled styling visibly distinct.

Check that the stronger button line does not make dense toolbars noisy. If one toolbar genuinely becomes too heavy, use an explicitly documented compact/toolbar variant rather than reverting the entire system.

Update D-008 and remove this item from open questions.

## 8. Close the density and public-dark decisions

Treat these as owner-approved:

### Density
- Standard is the default.
- Dense is an explicit user option/suggestion on ≈1800px+ operator displays.
- Never automatically change a user's density simply because viewport width changes.

Update D-009/open questions accordingly.

### Public dark preset
- Keep an optional organizer-selectable **Dark base** public theme preset.
- It is independent from authenticated app light/dark/system preference.
- Do not add another full public-page design set; existing theme rules are sufficient.

Update D-008/open questions accordingly.

## 9. Move pairwise product-policy questions out of design blocking

The following are not required to close foundation design:
- default tie-share cap;
- whether strength-of-preference ships.

Keep the UI/config model capable of reflecting configured behavior, but record these as judging/product-spec decisions rather than unresolved foundation-design defects.

Do not invent the final policy here.

## 10. Whitespace rule

Do one final whitespace review but do not manufacture content.

Remaining intentional examples are acceptable:
- long-form reading whitespace;
- inspector growth space;
- state-matrix cells;
- short frozen snapshots;
- modest bottom slack inside normal panels.

Only fix blank areas caused by:
- wrong artboard height;
- missing realistic fixture content;
- accidental layout constraints.

## 11. Rebuild and verify

Create r2.1 exports under:

`docs/product-depth-v3/design/exports/r2.1/`

Preserve:
- `exports/r1/`
- `exports/r2/`

Regenerate affected HTML/PNG output.

Run existing dimension/overflow checks.

Then re-open every final r2.1 board manually at full resolution.

Check that all manifest paths resolve.

## 12. Manifest / status

Update:
- design revision → `r2.1`;
- QA ledger path;
- changed references;
- resolved open questions;
- known limitations.

Do not mark a reference APPROVED until its final r2.1 screenshot was actually inspected.

## 13. Record this exact prompt

Store this prompt at:

`docs/product-depth-v3/design/prompts/CLAUDE_DESIGN_R2_1_POLISH_PROMPT.md`

## 14. Package final handoff

Create:

`conflux_v3_claude_design_handoff_r2_1.zip`

Include the complete design tree and r1/r2 history.

Do not include:
- node_modules;
- caches;
- secrets;
- unrelated repository source/build output.

Verify the ZIP member list and report its exact absolute path.

## 15. Final report — <=25 physical lines

Report:
- revision;
- boards manually inspected / total;
- boards changed;
- figure-placeholder correction;
- data-grid correction;
- button/control alignment corrections;
- resolved design decisions;
- remaining non-blocking questions;
- manifest path;
- exact ZIP path.

After this pass, the default assumption is that the foundation design is **frozen for implementation**. Do not propose another broad foundation pass unless you find a genuine blocking design-system contradiction.
