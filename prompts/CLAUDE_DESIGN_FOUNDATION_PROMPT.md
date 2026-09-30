# CLAUDE DESIGN FOUNDATION PROMPT — Conflux v3

You are the **product-design lead responsible for the Conflux v3 foundation design pass**.

You are running as Claude Opus 5.5 for this design task. Use High thinking for the initial system-level direction and the hardest reference surfaces when available; Medium is acceptable for iterative variants and refinement once the design language is stable.

Your output will be consumed later by separate production implementation agents. Do not implement the production frontend in this task. Your responsibility is to leave those agents a concrete, versioned, high-quality design system and reference-state handoff that removes ambiguity from implementation.

## Mission

Design the concrete v3 product language and reference experiences for Conflux: a self-hostable operating system for hackathons and technical competitions with unusually deep judging, submissions, customization, onsite operations, Event-as-Code, API/CLI/MCP and extensibility.

The design must make an extremely capable product feel **professional, clean, coherent and highly usable in its base state**.

This is not a superficial reskin and not a landing-page exercise.

## Critical context

The existing Conflux application is functionally broad and already has:
- participant, judge, mentor, volunteer and organizer workspaces;
- registration/teams/projects/submissions;
- sophisticated judging/normalization/pairwise/deliberation;
- eligibility/remediation;
- page/theme customization;
- onsite/check-in/logistics;
- sponsor/mentor systems;
- Event-as-Code;
- API/CLI/MCP;
- audit/provenance.

However, the visual/product UI was built under hackathon time pressure. Treat the current UI as **legacy visual implementation**.

### Existing code IS authoritative for:
- domain behavior;
- role/workflow meaning;
- accessibility semantics;
- current feature inventory;
- real data density/edge cases;
- useful component functionality.

### Existing code is NOT authoritative for:
- current visual styling;
- current card usage;
- current typography/spacing;
- current shell/layout appearance;
- current hero proportions;
- current information hierarchy where it feels scaffold-like;
- current density choices.

Do not merely "polish the existing UI." Establish the new Conflux v3 system.

## Read first

From repo root, use targeted inspection rather than dumping huge files.

Start with:

```bash
sed -n '1,240p' docs/product-depth-v3/design/DESIGN_HANDOFF_PROTOCOL.md
sed -n '1,260p' docs/product-depth-v3/EXECUTION_PRINCIPLES.md
sed -n '1,260p' docs/product-depth-v3/specs/004-visual-direction-professional-clean-compact-deliberate.md
sed -n '1,260p' docs/product-depth-v3/specs/005-professional-application-shell-depth.md
sed -n '1,320p' docs/product-depth-v3/specs/006-universal-data-grid-and-saved-view-system.md
sed -n '1,360p' docs/product-depth-v3/specs/015-project-authoring-and-technical-story.md
sed -n '1,320p' docs/product-depth-v3/specs/027-judge-workspace-ux.md
sed -n '1,320p' docs/product-depth-v3/specs/029-deliberation-and-winner-finalization.md
sed -n '1,320p' docs/product-depth-v3/specs/063-organizer-operations-center.md
sed -n '1,360p' docs/product-depth-v3/specs/073-personalized-participant-event-pass-my-event-hub.md
```

Then inspect focused frontend source using `rg`, `grep`, `sed`, and exact paths. At minimum locate:
- app shell/navigation;
- design tokens/styles;
- foundation components;
- participant workspace;
- judge workspace;
- organizer workspace;
- public event/project surfaces;
- page/theme builder.

Use `rg`, `grep`, `sed -n`, and other targeted reads for `TASKS.yaml` / `BATCHES.yaml` when queue context is useful. Their size is not a problem when accessed surgically; avoid only dumping large irrelevant ranges into the working context.

## Design-system import strategy

Use Claude Design/Claude Code `/design-sync` against the focused existing frontend/component system when it helps you understand or reuse functional components.

But do not let imported legacy styling become the target. If the imported design system fights the v3 direction, create a **new v3 design system** while mapping which existing functional components can be migrated.

## Visual/product direction

The default should be:

- professional rather than flashy;
- clean rather than empty;
- compact/content-first rather than oversized;
- dense where operators need density;
- calm neutral structure with restrained semantic color;
- strong typography and hierarchy;
- modest radii/elevation;
- excellent tables/forms/inspectors;
- obvious interaction state;
- accessible;
- fast to scan;
- appropriate for serious technical competitions.

### Hero rule

No giant generic SaaS hero.

For public event pages:
- `none`, `compact`, and `standard` are valid;
- **compact is the default**;
- immersive/art-heavy treatment is optional;
- project content should appear near the fold.

Authenticated operator workflows should generally have no marketing hero.

### Avoid AI/SaaS slop

Do not default to:
- gradients everywhere;
- icons in colored rounded squares beside every heading;
- huge KPI cards where a table/strip is better;
- excessive pills/badges;
- nested cards;
- oversized whitespace;
- giant page titles;
- random glassmorphism;
- decorative animation;
- every action hidden in kebab menus;
- three-column card dashboards when the workflow needs a dense data surface.

The application should plausibly look like mature production software in any random screenshot.

## Information architecture principle

Conflux can have enormous capability without exposing enormous complexity at once.

Use:
- progressive disclosure;
- enabled-feature-aware navigation;
- task-oriented overview;
- saved views;
- search/command palette;
- contextual inspectors;
- dense tables;
- good defaults;
- advanced mode only when needed.

Do not "simplify" by removing the feature depth. Organize it.

## Required foundation deliverables

Create a coherent interactive design set for these references.

### D1 — `design/system-v3`
Define:
- typography;
- spacing;
- density;
- color;
- borders/elevation;
- radii;
- icon policy;
- buttons/actions;
- form controls;
- table/data-grid grammar;
- status treatment;
- navigation;
- tabs;
- drawers/dialogs;
- tooltips;
- loading/empty/error;
- motion;
- focus/keyboard behavior;
- responsive rules;
- public-vs-operator distinction;
- compact hero rules;
- anti-slop rules.

### D2 — `design/app-shell`
Show:
- organizer desktop shell;
- participant/judge shell;
- workspace/event context;
- navigation;
- account;
- global search/command entry;
- notifications;
- mobile navigation;
- high-density state.

### D3 — `design/organizer-data-surface`
Use a realistic operations workflow, not toy cards.

Must show:
- dense data grid;
- filters;
- nested filter affordance;
- saved view;
- grouping/columns;
- selection;
- bulk action;
- split inspector;
- inline status/action;
- async job/progress;
- keyboard-friendly workflow;
- hundreds-of-records feel.

This becomes the reference pattern for many organizer pages.

### D4 — `design/participant-my-event`
Show a participant's real next-action hub:
- acceptance/RSVP/readiness;
- team;
- project/submission;
- deadline;
- eligibility issue if present;
- event QR/pass;
- personalized schedule;
- venue/table;
- mentor/support status;
- "ready" state;
- mobile.

It should make Conflux's depth feel simple.

### D5 — `design/project-story-editor`
Show a serious technical-project authoring experience:
- project metadata;
- Markdown/source mode;
- rich/WYSIWYM mode;
- live preview;
- code;
- math/LaTeX;
- figures/media;
- structured technical sections;
- bibliography/citations;
- preflight/lint;
- draft autosave;
- comments/suggestions;
- history/diff;
- exact judge/public preview;
- frozen judged revision vs living post-event story.

Do not make this look like a generic blog editor.

### D6 — `design/judge-review`
Show:
- assignment/review queue;
- selected project evidence;
- artifact preview;
- technical story;
- rubric;
- autosave state;
- conflict/recusal;
- flag/escalate;
- progress;
- keyboard path;
- optional physical route context;
- narrow/mobile mode.

Optimize for judge speed and mistake prevention.

### D7 — `design/deliberation-awards`
Show:
- finalists table;
- side-by-side comparison;
- raw vs normalized;
- coverage;
- disagreement/close-call state;
- award eligibility;
- notes;
- recusal;
- override reason;
- approval;
- publication preview/finalization.

It should look like a serious decision room, not an admin form.

### D8 — `design/public-event`
Show:
- compact event identity;
- dates/status/primary action;
- schedule/challenges/tracks/resources;
- project gallery;
- sponsor treatment;
- results;
- no-artwork default;
- tasteful organizer-customized theme example;
- mobile.

### D9 — `design/public-project`
Show:
- permanent technical project page;
- strong typography;
- code/math/figures;
- repository/demo/dataset/paper metadata;
- team;
- awards;
- exact "as judged" snapshot vs post-event living version;
- accessible responsive media.

### D10 — `design/event-builder`
Show:
- event setup;
- forms/policies/stages;
- page/theme builder;
- progressive advanced options;
- validation diagnostics;
- preview;
- plan/apply/change impact;
- schema-driven extension config.

Do not make advanced configuration an enormous flat settings page.

### D11 — `design/onsite-mobile`
Show task-specific mobile:
- QR check-in;
- volunteer desk;
- judge route/current stop;
- participant pass;
- mentor/help queue;
- pitch/demo queue.

This is not "desktop squeezed onto a phone."

### D12 — `design/state-matrix`
For representative major surfaces, show:
- normal;
- loading;
- empty;
- partial;
- error;
- permission denied;
- validation failure;
- large/dense data;
- destructive/high-impact confirmation;
- mobile;
- offline/degraded where relevant.

## Exploration expectation

For the design system/app shell and at least two critical surfaces, create **2–3 materially distinct design directions first**.

Compare them against:
- professional credibility;
- operator density;
- participant clarity;
- extensibility/customization;
- accessibility;
- resistance to visual slop;
- ability to scale to many features.

Then converge on one system. Do not produce ten barely different color variations.

## Realistic content requirement

Use realistic Conflux data density and terminology.

Avoid lorem ipsum and four-row toy tables as the only example.

Design for:
- large participant/project sets;
- multiple tracks/stages;
- meaningful status mixtures;
- long project names;
- warnings/partial states;
- enough rows/cards to prove density.

## Accessibility

Review:
- contrast;
- focus;
- keyboard paths;
- heading structure;
- control labels;
- responsive text;
- status not color-only;
- reduced motion;
- data-grid usability;
- technical math/code readability.

Do not trade accessibility for aesthetics.

## Deliverables on disk

Keep all of your design work local and versionable.

Update/create under:

`docs/product-depth-v3/design/`

At minimum:

```text
DESIGN_MANIFEST.yaml
system/
references/
  app-shell/
  organizer-data-surface/
  participant-my-event/
  project-story-editor/
  judge-review/
  deliberation-awards/
  public-event/
  public-project/
  event-builder/
  onsite-mobile/
states/
decisions/
exports/
```

Preserve whatever native Claude Design project/export artifacts are useful.

Also export, when supported:
- standalone HTML prototypes;
- canonical screenshots;
- design-system/tokens summary;
- component mapping;
- README/handoff context.

Critical decisions must be written to repository-readable files, not only left in the Claude conversation.

## Manifest update

Update `docs/product-depth-v3/design/DESIGN_MANIFEST.yaml` with:
- each reference id;
- status;
- artifact paths;
- approved viewport/state coverage;
- design revision;
- must-preserve intent;
- known adaptable implementation details;
- known limitations.

Do not mark a reference APPROVED if it is only a rough concept.

## Production-code boundary

This pass is design/prototyping and handoff.

Do not perform the full production UI rewrite in `src/web/**`; that belongs to later Sonnet 5 High implementation workers.

Small temporary prototype/export files belong under the design directory. If `/design-sync` needs to inspect real components, inspection is fine. The later implementation agents will migrate production code against the approved design contract.

## Final quality test

Before calling the foundation design complete, ask:

> If I showed a random major Conflux screen to someone without context, would it plausibly look like mature production software rather than a hackathon scaffold or AI-generated SaaS mockup?

and:

> Can an organizer run a 5,000-person event efficiently without the interface becoming a sea of cards, clicks, or hidden settings?

and:

> Can a first-time weekend-hackathon organizer still understand the base product without learning every advanced subsystem?

Iterate until the answers are convincingly yes.


## Final packaging — mandatory ZIP handoff

Before your final report, package **all design artifacts produced by this task** into one self-contained ZIP.

The ZIP must include, at minimum:
- the complete `docs/product-depth-v3/design/` tree;
- the updated `DESIGN_MANIFEST.yaml`;
- design-system/tokens guidance;
- all approved reference surfaces and state matrices;
- canonical screenshots;
- standalone HTML/prototype exports where available;
- design decisions/component mappings/handoff README;
- any native Claude Design export/project artifacts that are useful for later implementation.

Do not include unrelated repository build artifacts, dependency directories, caches, secrets, or the entire source repository.

Create the archive at the repository root with this stable name:

`conflux_v3_claude_design_handoff.zip`

If an older archive exists, replace it only after the new design artifacts are safely written.

Verify the archive contents after creation, for example with:

```bash
unzip -l conflux_v3_claude_design_handoff.zip | sed -n '1,220p'
```

If `zip`/`unzip` is unavailable, use Python's standard `zipfile` module and verify the member list programmatically.

Then resolve and record the absolute path, for example:

```bash
python - <<'PY'
from pathlib import Path
print(Path("conflux_v3_claude_design_handoff.zip").resolve())
PY
```

Your final report must include the **exact absolute ZIP path** on its own line so the user can retrieve it immediately.

## Final report

Keep the final terminal/controller-facing report concise (<=25 physical lines):
- design revision;
- surfaces completed;
- files/exports created;
- major system decisions;
- unresolved design questions;
- exact manifest path;
- exact absolute ZIP path.

Do not spend the final report re-describing the entire design.
