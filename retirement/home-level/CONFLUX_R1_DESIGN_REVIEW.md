# Conflux v3 Design r1 — Owner Review / r2 Plan

**Reviewed artifact:** `conflux_v3_claude_design_handoff.zip`  
**Revision reviewed:** r1  
**Disposition:** Keep the Ledger direction. Perform a targeted r2 refinement pass before treating the design handoff as final implementation authority.

## Overall assessment

The r1 foundation is a major improvement over the hackathon-era UI. The strongest parts are the operator-heavy surfaces: organizer overview, data grid + inspector, deliberation, event builder, project-story split editor, public project page, and mobile My Event. These now look like a coherent technical-operations product rather than generic card-based SaaS.

The second pass should **not redesign the system**. It should fix under-filled reference boards, prove dark mode and intermediate/wide responsiveness, finish pairwise judging, and manually review every board at full resolution.

## What should remain stable

- Ledger: light neutral structure, one restrained blue accent, hairline hierarchy, compact type and geometry.
- Table-first operator UX and right inspector pattern.
- Participant/judge top-bar shell distinction from organizer rail.
- Compact public hero as the default.
- One primary action per context.
- Status = icon + text, never color alone.
- Saved views / query / frozen bulk plan pattern.
- Public project living vs as-judged version model.
- Story source/split/rich modes over one canonical document model.
- Deliberation: normalized/raw/coverage/spread/sensitivity + deterministic explanation.
- Mobile task-specific layouts rather than desktop compression.

## Whitespace / fixture audit

The major problem is not excessive spacing tokens. It is **reference boards whose fixture does not use the available working area**, which can teach implementation agents the wrong composition.

A simple pixel/background heuristic corroborated the visual review:

| Board | Approx. unused lower artboard | Review |
|---|---:|---|
| `Shell-Participant` | ~44% | Clear outlier. Replace shell-only placeholder composition with realistic participant content or a more appropriate viewport. |
| `MyEvent` desktop | ~24% | Content is good, but the 1280×1380 artboard extends far beyond it. Use a normal desktop viewport or add genuinely useful enabled-event content. |
| `Story-Rich` | ~6% bottom, plus large internal editor void | Use a longer realistic technical document fixture and show continued editing content below the first benchmark block. |
| `Shell-Judge` | bottom metric is small because the conflict panel reaches low, but the main area is visually under-filled | Use a realistic workload fixture: more upcoming reviews/route context/alerts or reuse a fuller judge overview composition. |
| `Judge-Review` | overall frame is occupied, but the evidence pane ends early | Use a longer story/evidence fixture so the three-pane review demonstrates realistic scrolling and density. |

Do **not** solve blank space by adding arbitrary cards. Preferred remedies, in order:
1. use a realistic target viewport;
2. use realistic larger fixtures for surfaces that normally contain more work/data;
3. add only workflow-relevant enabled modules;
4. leave intentional reading whitespace where it improves long-form content.

The dense operator surfaces (`Data-Surface`, `Shell-Organizer`, `Deliberation`, `Builder-*`) should not be made denser merely for consistency; their current balance is good.

## Dark mode

The token system already contains a coherent dark palette. A local contrast calculation over primary/secondary/tertiary and semantic inks against dark surfaces found the lowest tested pair at about **6.69:1**, so the base tokens are a strong starting point.

r2 should design **representative dark references**, not duplicate all 34 boards.

Required dark proofs:
- system/component grammar;
- organizer shell + dense data surface (including inspector, selected rows, bulk/job state);
- judge review (rubric, warnings, autosave, evidence);
- one participant surface (`My Event` desktop or mobile);
- one overlay/dialog or state-matrix sample.

Public event themes should remain conceptually separate from the authenticated user's light/dark preference. A base dark public preset may be demonstrated if useful, but organizer theme ownership must remain clear.

## Responsive coverage gap

r1 mostly proves 390 mobile and 1280–1440 desktop. That leaves the difficult middle unspecified.

r2 should add:
- one **~1024px/tablet organizer** reference showing rail/inspector transition;
- one **~768px/narrow tablet** reference for a high-density workflow;
- one **1920×1080 wide operator** reference proving that more width increases useful information density rather than producing huge empty columns.

The 1920 board should test the design-system question about dense mode on wide displays.

## Pairwise judging

This is the clearest missing high-value surface. It should be designed before the pairwise/adaptive judging implementation batches.

Required pairwise board:
- A/B evidence comparison;
- frozen evidence/version labels;
- judge progress and assignment context;
- decision/abstain/recusal behavior;
- optional rubric context without overwhelming comparison;
- keyboard path;
- narrow-screen fallback;
- transition between pairwise and ordinary rubric review where the event uses a hybrid method.

Do not represent pairwise as a vague “split the middle pane” note.

## Manual visual QA

Only a subset of r1 boards was manually inspected. r2 must manually inspect **every exported reference board** at full resolution after regeneration.

For each board check:
- unintended blank regions;
- clipped/overflowing content;
- alignment rhythm;
- truncated labels;
- accidental card nesting;
- inconsistent radii/borders;
- unrealistic toy fixtures;
- overly small text;
- unclear primary action;
- inspector/pane imbalance;
- mobile target sizes;
- status/color misuse;
- visual hierarchy at a glance.

Scripted overflow checks remain useful but are not sufficient.

## Small cleanup findings

- In `DESIGN_MANIFEST.yaml`, the `design/system-v3` `state_coverage` entry accidentally splits `dark tokens (defined, not comped per surface)` into two list items. Fix this in r2.
- The r1 hosted prototypes depend on Google Fonts. Production should self-host fonts, and exports should remain understandable if external fonts fail.
- The placeholder `C` mark is acceptable for implementation until actual branding exists; do not block r2 on logo design.
- Immersive hero can remain deferred.
- Wallet pass detail can remain deferred.
- Live collaborative cursor UX can remain deferred until the feature is near implementation.
- RTL/localization does not need to block r2, but should receive its own stress-test design before the i18n/RTL implementation phase.

## Additional complex surfaces worth design-first treatment later

These do not all belong in r2, but they are unusual enough that a targeted Claude Design pass before implementation is valuable:

1. assignment optimization / rebalance / dropout simulation;
2. Event Doctor + what-if simulator;
3. Event-as-Code drift / field ownership / conflict resolution beyond the current plan view;
4. audit/provenance/replay/evidence-graph explorer;
5. floorplan/spatial placement + physical judge-route operations;
6. pairwise/adaptive judging (promoted to r2 because it is already an explicit r1 gap);
7. RTL/localization stress test before the internationalization phase.

Most other Product Depth v3 surfaces can inherit the existing Ledger primitives without a bespoke design project.

## Font-license note

IBM Plex and Source Serif 4 are both distributed under the SIL Open Font License 1.1 in their upstream ecosystems. Self-hosting them with the application is compatible with that licensing model when the required license notices are included. Production should still preserve the applicable OFL license text and avoid reserved-name issues if fonts are modified.

## r2 completion bar

r2 is ready for owner approval when:
- Ledger remains recognizably the same system;
- the under-filled boards are corrected without ornamental filler;
- representative dark mode is proven;
- 768/1024/1920 behavior is concrete;
- pairwise judging has a real reference;
- all exported boards are manually inspected;
- manifest/readmes reflect the new revision accurately;
- the entire r2 handoff is packaged into one verified ZIP with its exact path reported.
