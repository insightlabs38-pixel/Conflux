# CLAUDE DESIGN SECOND PASS — Conflux v3 r2 Refinement

You are the product-design lead responsible for the **second-pass refinement of the existing Conflux v3 foundation design**.

This is a new chat/session. Do not redesign Conflux from scratch.

The current approved-candidate direction is **Ledger**, revision r1. Your job is to inspect the existing local design handoff, preserve the parts that are working, and produce a stronger **r2** that fixes concrete composition gaps and closes several missing reference states before production implementation starts.

Use **Claude Opus 5.5** for this design pass. High thinking is appropriate for the initial audit, pairwise judging, responsive-system decisions, and dark-mode reconciliation; Medium is acceptable for iterative visual corrections after the decisions are stable.

Production implementation remains a separate later task.

## 1. Read the existing r1 package first

From the repository root, inspect:

```bash
sed -n '1,320p' docs/product-depth-v3/design/reviews/R1_OWNER_REVIEW_AND_R2_PLAN.md
sed -n '1,320p' docs/product-depth-v3/design/DESIGN_MANIFEST.yaml
sed -n '1,320p' docs/product-depth-v3/design/system/README.md
sed -n '1,320p' docs/product-depth-v3/design/system/component-mapping.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/001-direction-ledger.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/002-shell-inspector-routing.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/003-data-grid-contract.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/004-status-color-a11y.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/005-public-hero-versions.md
sed -n '1,320p' docs/product-depth-v3/design/decisions/007-open-questions.md
```

Use `rg`, `grep`, `sed -n`, targeted file reads, and the existing rebuild tooling freely. The YAML size is not an issue when inspected surgically.

Inspect the current canvas/export structure:

```bash
find docs/product-depth-v3/design -maxdepth 5 -type f | sort | sed -n '1,360p'
```

## 2. Preserve the successful r1 direction

Do **not** replace Ledger with a new visual language unless you discover a concrete usability failure that cannot be corrected within it.

Preserve:

- light neutral hairline structure;
- one restrained blue action/selection accent;
- compact type and geometry;
- table-first operator UX;
- organizer rail + right inspector;
- top-bar-only participant/judge shell;
- compact public hero default;
- visible frequent actions;
- one primary action per context;
- status = icon + word;
- dense grid + saved views + query + frozen bulk plan;
- long-form public project reading treatment;
- living vs as-judged project versions;
- source/split/rich story editor over one canonical model;
- deliberation sensitivity/coverage/explanation model;
- task-specific mobile layouts.

The r1 organizer data surface, organizer overview, deliberation, event builder, split story editor, public project, and mobile My Event are strong references. Refine them only where the audit finds a real issue.

## 3. First task: manually review all existing boards

Do not rely only on the prior overflow script.

Open and visually inspect **every r1 screenshot/artboard at full resolution**.

You may create contact sheets for orientation, but each final board must receive an individual visual check.

For every board inspect:

- unused/accidental blank regions;
- fixture realism;
- alignment/rhythm;
- clipping/overflow;
- truncated labels;
- card nesting;
- border/radius consistency;
- hierarchy;
- primary action clarity;
- pane/inspector balance;
- text size/readability;
- status semantics;
- mobile target sizing;
- whether the composition looks like mature production software at a glance.

Record a concise QA ledger under:

`docs/product-depth-v3/design/reviews/R2_BOARD_QA.md`

Do not create dozens of prose pages; a compact table is fine.

## 4. Correct fixture-induced whitespace

The owner specifically wants the large unused regions corrected.

The important distinction is:

> do not make the UI busier merely to occupy pixels; make the reference fixture realistic enough that the design demonstrates how the product normally uses its workspace.

Use this remedy order:

1. choose a realistic target viewport;
2. use a larger realistic fixture where that workflow normally has more data/content;
3. expose only genuinely useful enabled-event modules;
4. preserve intentional reading whitespace where it improves comprehension.

### Required corrections

#### `Shell-Participant`
The r1 board leaves roughly the lower half of the desktop artboard unused.

Replace the sparse shell-only composition with a realistic participant view, or use a more appropriate desktop viewport. The board must still demonstrate the D2 shell contract, but it should not teach implementation agents that a normal participant screen is mostly blank canvas.

Reuse the successful D4 My Event patterns rather than inventing filler cards.

#### `Shell-Judge`
The queue/overview content is too sparse relative to the main working area.

Use a realistic judge workload:
- more upcoming assignments;
- route/room context when enabled;
- pacing/deadline state;
- drafts/to-do;
- conflict/recusal state;
- only workflow-relevant summary information.

Do not convert it into KPI-card dashboard clutter.

#### `MyEvent` desktop
The content itself is good, but the 1280×1380 artboard extends substantially past the useful page.

Either:
- normalize the reference to a realistic desktop viewport such as ~1280×900/1000; or
- add naturally enabled content that would actually belong in the participant hub.

Do not add arbitrary modules solely to fill the bottom.

#### `Story-Rich`
Use a longer realistic technical-document fixture so the editing area demonstrates continued rich content below the first benchmark/equation block.

Include at least one additional meaningful technical block such as:
- figure + caption;
- code;
- architecture block;
- results section;
- citation-heavy paragraph.

Keep the comments/suggestions behavior.

#### `Judge-Review`
Use a longer realistic evidence/story fixture so the center pane demonstrates real review scrolling instead of ending high in the viewport while the rubric continues.

Show enough technical evidence to prove:
- position preservation;
- artifact switching;
- long-form reading;
- scoring while evidence scrolls.

Do not alter the strong queue/evidence/rubric three-pane model.

### General desktop reference rule

For normal app-screen reference boards, standardize around realistic viewport classes rather than arbitrary tall artboards.

If a screen genuinely has less content than one viewport, blank space is acceptable. If the emptiness comes from a toy fixture or oversized artboard, fix the fixture/artboard.

## 5. Add representative dark mode, not a duplicate design set

The r1 tokens already define dark mode. r2 must **prove it visually** on a representative subset.

Do not redraw every page.

Required dark references:

1. **D1 dark foundations/components**
   - neutrals;
   - semantic states;
   - inputs;
   - table rows;
   - selection;
   - focus;
   - status;
   - overlays.

2. **Organizer shell + dense data surface**
   - rail/top bar;
   - inspector;
   - selected rows;
   - nested filters/query;
   - job/bulk state.

3. **Judge review**
   - evidence;
   - rubric;
   - warning state;
   - autosave;
   - disabled submit.

4. **Participant My Event**
   - choose desktop or mobile;
   - include warning/action-needed and ready/success semantics.

5. **One overlay/dialog/state-matrix sample**
   - prove layering/elevation/focus in dark mode.

### Dark-mode semantics

For authenticated app surfaces define:
- `system`;
- `light`;
- `dark`;

as a user preference.

Public event/project presentation is organizer-theme-controlled and should not be silently overridden by the logged-in user's app theme. A base dark public preset may be shown if useful, but keep this authority boundary explicit.

Validate contrast again after actual dark comps, including semantic tints and borders.

## 6. Close the intermediate + wide responsive gap

r1 proves mobile and desktop but not the difficult middle or ultra-wide operator case.

Add at least:

### 1024px organizer/tablet reference
Show:
- rail behavior;
- inspector transition;
- data table/grid strategy;
- toolbars/filters;
- whether inspector becomes sheet/detail.

### ~768px narrow-tablet reference
Use a high-density workflow such as:
- judge review;
- organizer data surface;
- event builder.

Make the transition rules concrete. Do not simply scale down desktop.

### 1920×1080 wide operator reference
Use the organizer data surface or operations center.

Prove that additional width creates useful density through:
- appropriate additional columns;
- wider readable values;
- inspector;
- optional second contextual region only if genuinely useful;
- dense-mode behavior.

Do not allow 1920px to become giant empty columns or stretched cards.

Document the density recommendation for wide displays.

## 7. Fully design pairwise judging

Pairwise judging is the highest-value unresolved interaction in r1 and must receive a real board before implementation.

Create a dedicated reference, preferably more than one state.

Required behavior:

- project A vs project B evidence;
- frozen revision labels;
- enough technical evidence to compare meaningfully;
- assignment/progress context;
- select A / select B / tie or abstain only if the configured method permits it;
- recusal/conflict;
- keyboard path;
- optional criterion/anchor context without turning pairwise into two full rubrics;
- pairwise history/progress;
- narrow-screen fallback;
- hybrid event behavior where pairwise is a tiebreaker after rubric scoring.

The design must make direct comparison faster than opening two project pages manually.

Do not leave this as “split the center pane.”

Add the reference to the judge-review README and manifest.

## 8. Add one large-realistic-fixture stress test

Create at least one reference showing a genuinely large event state, for example:

- 5,000 participants;
- 1,000+ projects;
- many tracks;
- mixed warnings/eligibility/check-in states;
- realistic long names;
- enough rows to imply virtualization.

This can reuse the 1920 organizer board.

The point is to prove the system still looks intentional under production-scale data and not only under curated ten-row fixtures.

## 9. Fix manifest / artifact-quality issues

Correct the r1 manifest issue where the system state coverage accidentally split:

`dark tokens (defined, not comped per surface)`

into multiple YAML list entries.

Update manifest schema/content cleanly for r2.

The design revision should become **r2**.

Preserve r1 artifacts under `exports/r1/`; create r2 under `exports/r2/` rather than destroying the prior revision.

Update each changed reference README with:
- new board names;
- must-preserve rules;
- responsive/dark additions;
- known limitations.

## 10. Font/prototype handling

IBM Plex and Source Serif 4 are suitable open-source/self-hostable choices; keep the typography unless the actual rendering reveals a design problem.

Do not spend this pass reselecting fonts.

The prototype should remain understandable if external Google Font loading fails.

Do not package unrelated dependencies/caches/secrets into the handoff.

Production font packaging/licence notices belong to implementation/release work, not this design pass.

## 11. What remains intentionally deferred

Do not expand r2 into another massive product-design project.

These may remain deferred:

- final logo/brand mark;
- immersive hero beyond its existing advanced entry point;
- full wallet-pass internals;
- live collaborative cursors/co-editing;
- exhaustive RTL/localization;
- every later Product Depth v3 surface.

Record them cleanly.

## 12. Identify later design-first surfaces

In the r2 handoff, create/update a short planning note identifying which later Product Depth v3 systems deserve a dedicated design pass before their implementation batch.

At minimum assess:

- assignment optimization/rebalance/dropout simulation;
- Event Doctor + what-if simulator;
- Event-as-Code drift/field ownership/conflicts;
- audit/provenance/replay/evidence graph;
- floorplan/spatial placement + judge routing;
- RTL/localization stress test.

Do not design all of these now unless a tiny supporting sketch is needed to validate the foundation.

## 13. Rebuild and QA

Use the existing export tooling as the base:

`docs/product-depth-v3/design/exports/r1/tools/build-exports.mjs`

Create the r2 equivalent under `exports/r2/tools/`.

Rebuild all changed HTML/screenshots.

Run the overflow/dimension checks.

Then manually open and inspect **every r2 screenshot**.

A script saying “no overflow” does not constitute visual approval.

Do not mark references `APPROVED` until that manual review is complete.

## 14. Record this prompt

For provenance, ensure the exact prompt for this pass is stored at:

`docs/product-depth-v3/design/prompts/CLAUDE_DESIGN_R2_REFINEMENT_PROMPT.md`

Do not overwrite the r1 review.

## 15. Required r2 package

Before your final report, package the complete design handoff into:

`conflux_v3_claude_design_handoff_r2.zip`

The ZIP must include:

- complete `docs/product-depth-v3/design/` tree;
- r1 history;
- r2 canvas/native design source;
- updated manifest;
- r2 HTML exports;
- r2 screenshots;
- system tokens/readmes;
- decisions;
- r1 review;
- r2 QA ledger;
- this r2 prompt;
- later-design planning note.

Exclude:
- `node_modules`;
- caches;
- secrets;
- unrelated build output;
- the whole source repository.

Verify archive contents after packaging:

```bash
unzip -l conflux_v3_claude_design_handoff_r2.zip | sed -n '1,260p'
```

If ZIP tools are unavailable, use Python `zipfile` and verify the member list.

Print the exact absolute archive path:

```bash
python - <<'PY'
from pathlib import Path
print(Path("conflux_v3_claude_design_handoff_r2.zip").resolve())
PY
```

## 16. Final report — <=25 physical lines

Report only:

- design revision;
- number of boards/artboards;
- whitespace/density corrections;
- dark references created;
- responsive/wide references created;
- pairwise reference created;
- QA status;
- manifest path;
- unresolved design questions;
- exact absolute ZIP path.

Do not re-explain the whole design system in the final report.
