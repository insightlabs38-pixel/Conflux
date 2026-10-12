# Conflux v3 r2 — Sign-off Review

## Disposition

**Design direction: approved.**
**Implementation handoff: one small r2.1 polish/QA pass recommended before final sign-off.**

Do not redesign Ledger. The remaining work is correction/provenance polish.

## What is already strong

- Organizer data surfaces and Wide-1920 are production-like and appropriately dense.
- Dark mode is coherent and exposed real token defects rather than merely recoloring the light UI.
- 768/1024 responsive rules are concrete.
- Pairwise judging is now sufficiently designed to guide implementation.
- My Event, judge review, event builder, deliberation and public project all provide useful implementation authority.
- Remaining whitespace is mostly intentional reading/panel growth space rather than the fixture-induced voids from r1.

## Why r2.1 is still worthwhile

### 1. QA provenance is inconsistent

`reviews/R2_BOARD_QA.md` says:

> Manual review of every r2 screenshot at full resolution

but then says 19 byte-identical boards were accepted because they had been inspected in the r1 audit.

The owner-provided r1 completion report said only about ten of the 34 r1 boards were opened manually; the rest were checked only by the overflow script.

Therefore r2.1 must actually open **all 45 current boards in the new session** and make the QA ledger truthful.

### 2. Some current boards still visually identify themselves as r1

Current r2 HTML still contains revision labels such as:
- `Sys-Foundations`: `design/system-v3 · r1`
- `Sys-Components`: `design/system-v3 · r1`
- `States-1`: `design/state-matrix · r1`
- `States-2`: `design/state-matrix · r1`

Historical r1 source should stay r1, but current r2/r2.1 reference exports should identify the current revision or explicitly say the content is inherited.

### 3. “Error by horizon” is not a rendering error, but it looks like one

The normal story/judge/public references use striped placeholder art with text such as:

`Figure 2 · Error by horizon`

This means *forecast error as a function of prediction horizon*. It is not a browser/rendering failure.

The actual failed-media state is separate and intentionally says `Figure 2 failed to load`.

Still, the combination of the word “Error” and striped placeholder art is visually ambiguous. For final implementation authority:
- rename the normal figure to **“Forecast MAE by horizon”**;
- preferably render a tiny real inline SVG/static chart from the fixture values rather than striped placeholder art;
- keep the explicit failed-media specimen only in the state matrix.

The architecture placeholder can likewise become a simple inline architecture diagram if this can be done without expanding the pass.

### 4. One known data-grid defect remains

The r2 QA ledger itself records:
- a stray hairline fragment on the selected/cursor row at the inspector boundary;
- a tight `Changed` column at 1440.

These are small but worth fixing because `Data-Surface` is one of the highest-reuse implementation references.

### 5. Button alignment is not a systemic component bug

The base rule is sound:

`.btn { display:inline-flex; align-items:center; justify-content:center; height:var(--h-ctl); ... }`

Most button groups in the screenshots are aligned correctly.

A final visual sweep should still inspect mixed action rows where buttons sit next to tags, text actions, segmented controls or status elements:
- story-editor top toolbar;
- Builder-Plan top actions;
- Deliberation-Finalize approval/footer actions;
- My Event pass/help actions;
- Resp-768 asset/action bar;
- pairwise narrow decision bars;
- dialogs/overlays.

Only fix real visual offsets. Do not standardize unlike controls into identical-looking buttons.

## Owner decisions recommended for r2.1

### Outlined button border
Use the stronger **line-3** border for normal outlined interactive buttons.

Rationale:
- it gives a clearer affordance in both light and dark;
- the design remains restrained enough to tolerate the stronger line;
- inputs already rely on stronger control boundaries;
- ghost/text actions remain available where a border would be too heavy.

Do not apply line-3 to every panel/table divider.

### Density
Approve D-009:
- **Standard remains the default**;
- Dense is an explicit option/suggestion on very wide (≈1800+) operator displays;
- never auto-switch density simply because the viewport changes.

### Public Dark base preset
Keep it as an **optional organizer-selectable public preset**, separate from the authenticated user's app theme.

This is useful, inexpensive given the completed dark token system, and already consistent with D-008.

### Pairwise tie-share / strength of preference
Not a design blocker.
Move the default tie-share cap and whether strength-of-preference ships to the judging/product specification. The UI should remain parameterized for configured tie behavior.

## ZIP size

The larger r2 archive does not contain suspicious dependency/build bloat.

Observed:
- r1 reviewed ZIP: about **5.6 MiB**
- r2 ZIP: about **14 MiB**
- extracted r2 design tree: about **17 MiB**
- `exports/r1/published/` alone: about **6.1 MiB**
- total exact duplicate file payload inside the extracted tree: about **3.54 MiB**
- no `node_modules`, `.git`, build cache or similar heavyweight directory is present.

The size increase is mostly intentional:
1. r1 published HTML/screenshots are now preserved inside r2;
2. current references also retain copies of unchanged outputs;
3. r2 adds dark/responsive/pairwise boards and PNGs;
4. ZIP compression does not deduplicate identical files stored at different paths.

At ~14 MiB this is not worth optimizing. Keep the full-history handoff unless archive size becomes materially larger later.

## Final recommendation

Run one **r2.1 micro-polish pass**, then freeze the foundation design and begin implementation.

Do not schedule a third broad foundation-design pass after r2.1. Future Claude Design work should be just-in-time for the specialized systems already listed in `LATER_DESIGN_PASSES.md`.
