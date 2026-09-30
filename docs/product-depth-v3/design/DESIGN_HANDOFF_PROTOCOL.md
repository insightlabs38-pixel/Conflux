# Claude Design → Conflux v3 Handoff Protocol

## Timing decision

Do **not** wait until the end for one giant UI design pass.

Use a two-level design cadence:

### 1. Foundation design — early

Claude Design work can begin immediately from the current codebase, UI census and Product Depth v3 direction while correctness/test/frontend-architecture stabilization continues.

Before Conflux begins the visual foundation (`PD-F004` onward), `PD-DESIGN-B00` must freeze:
- the Conflux v3 design system;
- application shell;
- dense organizer pattern;
- participant My Event;
- project editor;
- judge workspace;
- deliberation/results;
- public event/project;
- builder/configuration pattern;
- onsite/mobile pattern;
- canonical state matrix.

This avoids implementing shared components, layout, navigation and data surfaces against the legacy look and then rewriting them later.

### 2. Domain refinement — just in time

Before a major UI-heavy subsystem begins, Claude Design can refine the already-approved system using the now-stable domain contract and real data/state requirements. This is especially useful for unusual surfaces such as judging logistics, Event-as-Code planning, incident operations, simulator results or sponsor workflows.

The refinement may add a reference surface/state, but it must not silently replace the v3 system or domain invariants.

## Local CLI workflow

The user intends to run Claude Design through the CLI so artifacts remain available locally. The execution bundle should treat the **committed local export** as authoritative.

Recommended local capture:

```text
docs/product-depth-v3/design/
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
  exports/
    <revision>/
  decisions/
```

Capture, when available:
- Claude Design project/export bundle;
- standalone HTML prototype;
- canonical screenshots at named viewports/states;
- design-system/tokens guidance;
- component/reference mapping;
- README/handoff context;
- concise design decisions.

Do not make implementation depend on a hosted Claude conversation being available.

## Using the current Conflux codebase

Treat current code as **functional/product context**:
- roles and workflows;
- data density;
- accessibility semantics;
- existing domain terminology;
- functional component inventory;
- current failure/empty/loading states.

Do **not** treat current styling as aesthetic authority:
- card usage;
- spacing;
- typography;
- hero scale;
- shell layout;
- density;
- visual hierarchy.

The v3 direction is professional, clean, compact and deliberate. A compact hero is the default where a hero is useful; authenticated operator screens should prioritize task/data density over marketing presentation.

## Handoff quality gate

A reference surface is acceptable only if a coding agent can implement it without inventing:
- hierarchy;
- dominant task/action;
- density;
- navigation relationship;
- interaction order;
- empty/loading/error handling;
- mobile behavior;
- high-impact confirmation behavior.

Pixel-perfect copying is not required. Must-preserve intent and adaptable implementation details must be distinguished.

## Source references

Current Anthropic documentation confirms Claude Design can work from codebases/design systems, run from Claude Code/terminal workflows, export local artifacts, and hand off to local coding agents. Re-check current Anthropic documentation when the design pass begins because the product is evolving quickly.
