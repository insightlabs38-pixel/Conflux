# PD-F004 — Visual direction: professional, clean, compact, deliberate

**Status:** Product Depth v3 execution contract  
**Research source:** `conflux_deep_product_feature_research_v2.md` §4  
**Queue batches:** PD-F004-B01, PD-F004-B02, PD-F004-B03, PD-F004-B04, PD-F004-B05

## Completion interpretation

This specification is the canonical depth contract for §4. Research bullets describe required product behavior, but completion also requires the architecture, migration, edge-state, verification and integration rules below.

A capability is not complete because a model field, endpoint, settings toggle or placeholder screen exists.

## Architecture / implementation contract

- Establish or reuse one canonical source of truth.
- Server-side authorization and validation remain authoritative.
- Persist only state that has real lifecycle meaning; derive display-only state where practical.
- Reuse registered shared primitives instead of creating local near-duplicates.
- Existing supported state/API behavior requires an explicit migration/compatibility decision before incompatible change.
- Advanced/expert capability must remain progressively disclosed and must not degrade the base experience.

### Section-specific architecture decisions

- Claude Design v3 output is the visual source of truth. Current repository styling is legacy context, not an aesthetic constraint.
- Anti-slop rules are persistent design/gate criteria; they are not one-time feature tasks.

## Canonical primitive reuse

- `ARTIFACT_PREVIEW`
- `ASYNC_JOB`
- `AUDIT_PROVENANCE`
- `DATA_GRID`
- `POLICY_EXPLAIN`
- `PREVIEW_CONTEXT`

## Required surface matrix

| Surface | Requirement |
|---|---|
| `web` | required |
| `api` | not_required |
| `sdk` | not_required |
| `cli` | not_required |
| `mcp` | not_required |
| `event_as_code` | not_required |
| `audit` | not_required |
| `webhook` | not_required |
| `archive` | not_required |
| `analytics` | not_required |
| `search` | not_required |
| `docs` | required |

## Approved-design references

- `design/state-matrix`
- `design/system-v3`

These references must resolve to approved local design artifacts before UI-facing tasks close.

## Minimum verification contract

For the subsystem as a whole:
- realistic happy-path data;
- malformed/boundary behavior with useful diagnostics;
- authorization/visibility boundaries;
- lifecycle and migration/compatibility behavior;
- retry/idempotency/concurrency for shared-state mutations;
- required browser states for UI-facing flows;
- no regression of canonical existing behavior;
- exact commands/results recorded in receipts.

## Non-goals / restraint

- No duplicate source of truth solely for a new surface.
- No redundant hash/signature/proof layer unless it enables a real portability, offline-verification or external-trust workflow.
- No LLM/AI decision authority for deterministic official state such as scores, permissions, deadlines, policy or winner selection.
- No participant surveillance or engagement gamification without a concrete event purpose.
- No replacement of a mature generic external product category when a bounded integration solves the event-specific need.

## Product requirements from research

Conflux should explicitly reject several common low-quality SaaS/AI-generated UI patterns.

### Default visual language

- BASE: neutral, content-first application shell.
- BASE: modest border radii; avoid turning every region into a giant rounded card.
- BASE: controlled use of elevation; borders and spacing should establish most hierarchy.
- BASE: strong typography scale with fewer arbitrary font sizes.
- BASE: consistent spacing tokens and optical alignment.
- BASE: one primary action per local context; secondary actions remain visibly subordinate.
- BASE: iconography used where it improves recognition, not as decoration.
- BASE: muted color for structure; saturated color reserved for status and action.
- BASE: semantic status colors have icon/text redundancy and accessible contrast.
- BASE: motion communicates state transition; no ambient motion added merely for “polish.”
- BASE: skeletons only where layout is predictable; otherwise clear progress indicators.
- BASE: empty states tell the user the next useful action.
- BASE: error states explain whether data was preserved and what can be retried.
- BASE: “advanced” never means visually chaotic.

### Hero policy

- BASE: **compact hero is the default**, not a viewport-consuming marketing hero.
- BASE: organizer can choose `none`, `compact`, or `standard`.
- ADV: “immersive” / artwork-heavy hero is opt-in for events that deliberately want it.
- BASE: compact hero should usually fit event identity, date/status and one primary action in roughly 160–280 px on desktop.
- BASE: on project pages, project content should begin above or near the fold; avoid a decorative hero that pushes evidence down.
- BASE: on mobile, hero height should collapse aggressively.
- ADV: hero can be replaced with an event-specific lead block.
- ADV: image focal point/crop and responsive art direction.
- ADV: organizer preview at desktop/tablet/mobile.
- BASE: fallback identity should still look intentional when no artwork exists.

### Anti-slop rules

- Do not use gradients by default.
- Do not put icons in colored squares next to every heading.
- Do not use giant KPI cards when a compact summary strip or table is better.
- Do not use oversized marketing copy inside authenticated operator workflows.
- Do not overuse pills/badges for ordinary text.
- Do not make every section a card inside another card.
- Do not repeat the same label in heading, breadcrumb and card title.
- Do not hide frequently used actions behind three-dot menus merely to appear clean.
- Do not use a 3-column dashboard where the organizer needs a sortable data table.
- Do not make destructive operations red until the action itself; avoid a page covered in alarm colors.
- Do not add fake “AI” affordances to ordinary deterministic workflows.
- Do not display unhelpful decimals/precision just because the backend has them.
- Do not make advanced capabilities depend on memorizing opaque IDs.

## Batch scope

### PD-F004-B01 — Visual direction: professional, clean, compact, deliberate — neutral, content-first application shell → muted color for structure; saturated co…

- neutral, content-first application shell
- modest border radii; avoid turning every region into a giant rounded card
- controlled use of elevation; borders and spacing should establish most hierarchy
- strong typography scale with fewer arbitrary font sizes
- consistent spacing tokens and optical alignment
- one primary action per local context; secondary actions remain visibly subordinate
- iconography used where it improves recognition, not as decoration
- muted color for structure; saturated color reserved for status and action

### PD-F004-B02 — Visual direction: professional, clean, compact, deliberate — semantic status colors have icon/text r… → organizer can choose none, compact, or…

- semantic status colors have icon/text redundancy and accessible contrast
- motion communicates state transition; no ambient motion added merely for “polish
- skeletons only where layout is predictable; otherwise clear progress indicators
- empty states tell the user the next useful action
- error states explain whether data was preserved and what can be retried
- advanced” never means visually chaotic
- compact hero is the default, not a viewport-consuming marketing hero
- organizer can choose `none`, `compact`, or `standard`

### PD-F004-B03 — Visual direction: professional, clean, compact, deliberate — immersive” / artwork-heavy hero is opt-… → fallback identity should still look int…

- immersive” / artwork-heavy hero is opt-in for events that deliberately want it
- compact hero should usually fit event identity, date/status and one primary action in roughly 160–280 px on desktop
- on project pages, project content should begin above or near the fold; avoid a decorative hero that pushes evidence down
- on mobile, hero height should collapse aggressively
- hero can be replaced with an event-specific lead block
- image focal point/crop and responsive art direction
- organizer preview at desktop/tablet/mobile
- fallback identity should still look intentional when no artwork exists

### PD-F004-B04 — Visual direction: professional, clean, compact, deliberate — avoid use gradients by default → avoid hide frequently used actions behi…

- Visual guardrail: avoid use gradients by default
- Visual guardrail: avoid put icons in colored squares next to every heading
- Visual guardrail: avoid use giant KPI cards when a compact summary strip or table is better
- Visual guardrail: avoid use oversized marketing copy inside authenticated operator workflows
- Visual guardrail: avoid overuse pills/badges for ordinary text
- Visual guardrail: avoid make every section a card inside another card
- Visual guardrail: avoid repeat the same label in heading, breadcrumb and card title
- Visual guardrail: avoid hide frequently used actions behind three-dot menus merely to appear clean

### PD-F004-B05 — Visual direction: professional, clean, compact, deliberate — avoid use a 3-column dashboard where th… → avoid make advanced capabilities depend…

- Visual guardrail: avoid use a 3-column dashboard where the organizer needs a sortable data table
- Visual guardrail: avoid make destructive operations red until the action itself; avoid a page covered in alarm colors
- Visual guardrail: avoid add fake “AI” affordances to ordinary deterministic workflows
- Visual guardrail: avoid display unhelpful decimals/precision just because the backend has them
- Visual guardrail: avoid make advanced capabilities depend on memorizing opaque IDs


## PD-F004-B01 canonical contract

Written by PD-F004-B01-T00 against the committed design authority (`design/system-v3`, `design/state-matrix`; rules `V-*` in `design/system/VISUAL_CONTRACT.md`, `S-*` in `design/states/STATE_MATRIX.md`, decisions D-001..D-012, obligations in `design/IMPLEMENTATION_HANDOFF.md`).

### What exists (reuse, do not rebuild)

- One token layer, `src/web/styles/tokens.css`, is loaded by the React app (`main.css`) and by the server-rendered public templates (`presentation/base.html` via `{% static 'tokens.css' %}`), so a value change reaches both. `components.css` (2,801 lines) and `presentation.css` (774) are already token-driven: no hex literal beyond one, no gradient, `font-size` through `var(...)`, radii through `--radius-*`.
- `Button`, `Badge`, `Card`, `EmptyState`, `ErrorState`, `LoadingState`, `DeniedState`, `AppShell`, `WorkspaceNavigation`, `Foundation`, `DataGrid` exist (152 / 75 / 38 uses of Button / Badge / Card). `presentation/accessibility.py THEME_COLORS` hand-mirrors the palette for the organizer-theme contrast gate. The dark values exist only as the public-site preset `:root[data-theme="dark"]`.

### Canonical source of truth and names

- Values are defined once, in `src/web/styles/tokens.css`, under the **v3 names** (`--bg`, `--surface`, `--line*`, `--ink*`, `--accent*`, `--ok/warn/err/info/mute` with `-tint` and `-line`, `--fs-*`, `--sp-*`, `--r-*`, `--h-*`, `--sh-*`, `--t-*`, `--focus`) and the v3 dark set under `[data-theme="dark"]`. `design/system/tokens.json` is the approved reference; a test fails when the web tokens differ from it (after normalising rem to px).
- The legacy names (`--color-*`, `--space-*`, `--radius-*`, `--font-size-*`, `--shadow-*`, `--control-height*`) stay for one release as **aliases to the v3 names** (never a second value), so `components.css` keeps working while tasks move it over. A ratchet test counts legacy-name uses and may only fall; the aliases are deleted when the count is zero, no later than the close of PD-F004-B05. New and edited CSS uses v3 names only.
- Sizes are authored in `rem` equal to the design's px at a 16px root (`--fs-14: 0.875rem`), so a user's browser font-size still scales the UI; density row heights and touch targets stay px. The parity test compares the px equivalents.
- `THEME_COLORS` stays a mirror, now proved not trusted: the existing `test_fixed_theme_audit_tracks_shared_css_tokens` (parses `tokens.css`, asserts the mirror equals it) is re-pointed at the v3 names in the colour task. Organizer accents stored today (`#126454`, `#a32918`, `#363636` and any custom value) are re-checked against the new light and dark backgrounds by the existing gate; a stored accent that fails is reported by the migration check below, never silently rewritten.

### Lifecycle, state and authority

- B01 persists nothing and adds no API field: it is CSS, tokens and React components. Per-user theme preference (system / light / dark) is owned by PD-F005-B01-T08, density by PD-F005-B02-T08, event theme modes by PD-S010-B01-T08. B01 ships the dark token set and the theme root rule (re-declare `color` and `background-color`, D-008) and honours an existing `data-theme` attribute; it adds no toggle.
- Official scoring, permissions, deadlines and publication are untouched. A component never decides eligibility, role or deadline state; it renders what the server returned (S-DENY, S-ERR).

### Migration and compatibility

- Stored `theme_config` values (`hero` split / poster / editorial, `density`, `typography`, `personality`, `width`, `background`, `project_card`) stay valid and keep their meaning; the hero vocabulary (none / compact / standard / immersive) is PD-F004-B02/B03 and needs its own mapping decision there.
- The change is visual and structural in the React shell. Server-rendered public pages receive the new palette through the shared tokens, so the public e2e and accessibility gates (`public.spec`, `event-themes.spec`, `uiv2-*`) must stay green at 390 and 1440 without being weakened; `public.spec` expects `system-ui` in the body font stack, which the stack keeps.
- No database migration, no OpenAPI or SDK change, no URL change. A release note goes in `docs/operations/UPGRADES.md` when the palette lands (default accent moves from green to blue; stored organizer accents are untouched).

### Reuse and forbidden duplicates

- Status (icon plus word) and Tag replace the colour-only `Badge` variants; there is one `Button` with one primary per context; one icon component; one set of state components extended with the S- fields. No per-feature copy of any of them, no second token file, no inline style literals for colour, size, radius or shadow.
- `ASYNC_JOB` (the declared reuse) is the only source for the "slow, keep working, cancel" state (S-LOAD, after 8s): a component shows a job's real progress and cancel, it does not invent one.

### Decisions taken here (conservative defaults, reversible)

- Fonts: B01 keeps the font stack (`"IBM Plex Sans"` first, then the system stack) and ships no font binaries. Self-hosting Plex needs the owner's answer on licence packaging and air-gapped installs (design D-007 item 2); until then installs without Plex use the system fallback. Logged in `.claude-supervisor/QUESTIONS.md`.
- Icons: a small first-party inline-SVG `Icon` component with the subset in use (16px, `currentColor`, Lucide-compatible shapes), not a new npm dependency.
- Task order inside the batch (all depend only on T00): T08 colour and token layer, T04 typography, T05 spacing, T02 radii, T03 elevation, T06 primary action, T07 icons, T01 shell last, because it consumes the rest.

### Test strategy

- Python: token parity with the design JSON, `THEME_COLORS` mirror, contrast of every token pair (extends `tests/test_design_manifest.py`).
- Vitest: legacy-name and literal ratchets over `src/web` (hex, px font sizes, radii outside the scale, gradients, shadows outside floating layers), component tests per primitive.
- Playwright (`tests/e2e/visual-foundation.spec.ts`, isolated fixture): computed geometry at 1440 and 390 (top bar 44px, rail 216px, row heights 28/36/44, 44px touch hit areas), focus ring, no horizontal overflow, axe, on organizer, participant and judge shells and one public page, plus the existing gates unchanged.
- Escalation conditions: a stored organizer accent that fails the new gate; a component that needs a second source of truth; a server-rendered template that cannot take the shared tokens.

## PD-F004-B02 canonical contract

Recorded at the close of PD-F004-B02 from what was built (T01-T08), against design `V-*`, `S-*`, D-005 and D-012.

- **Status and tags.** `Status` (icon plus word, one tone) and `Tag` (ordinary text) replace the colour-chip `Badge`; a ratchet fails a colour-only status, a pill status and a reintroduced `Badge`.
- **Motion.** Transitions of 120-180ms for state changes only; one allowed animation (`cx-spin`); `prefers-reduced-motion` collapses everything globally. No ambient motion.
- **Loading, empty, error.** A grid keeps its header over placeholders; elsewhere a spinner; after 8s a slow note and Cancel only when the caller can stop the work. Every `EmptyState` says why and offers the one next action. Every `ErrorState` with a retry says what is known about the data (a failed read changed nothing; a write the server refused was not saved; a write that failed without a refusal says it could not be confirmed) and what Retry does; there is no reassurance without a basis. `DeniedState` renders the server's POLICY_EXPLAIN explanation and never composes a reason. The server sends no request reference yet (follow-up for observability work); `ErrorState` shows one when it is supplied.
- **Advanced is not chaotic.** One disclosure look (`components.css` "Disclosure"): hairline, medium summary, one chevron that turns open; borders are solid hairlines (`dashed` and `dotted` are banned).
- **Hero vocabulary (resolves the B01 mapping question).** Size and layout are two settings. `hero` (split, poster, editorial) stays the layout. `hero_size` is new: `compact` (default), `none`, `standard`, in the page's `theme_config`, validated with the other presentation enums in `presentation/themes.py`. A theme without the key means compact, so nothing is migrated. `immersive` is ADV and is not offered until it is designed. The band (lockup or art, title, status) is 160-240px on desktop (no floor), at most 360px for standard and at most 120px on mobile; the description and the one primary action sit under the band; text never sits over art.
- **Surfaces.** web and docs only. The public presentation payload gains `hero_size` (additive; `theme_config` is free JSON in OpenAPI, so no operation or schema changed). No audit, webhook, archive, search or analytics change: `hero_size` travels inside `theme_config` with Event-as-Code and the archive.

## PD-F004-B03 canonical contract

Recorded at the close of PD-F004-B03 from what was built (T01-T08), against design `V-HERO-1`, D-005 and D-012.

- **One size setting.** `hero_size` in the page's `theme_config` is `compact` (default), `none`, `standard` or `immersive`; `hero` (split, poster, editorial) stays the separate layout. `immersive` is opt-in and needs a hero image (the server refuses it without one and refuses removing the image while it is set). Immersive was not designed beyond its Advanced entry point (D-007 item 4); it is built from V-HERO-1 and D-005: the art is its own full-width strip above the title row, never behind text, at most 352px on a desktop and 120px on a phone (QUESTIONS.md 2026-10-07T07:40Z, default A).
- **Hero content.** The band is lockup or art, title, and one facts line (status and dates in the event's timezone, server-formatted); the description and the one primary action sit beneath. The hero never grows to carry more content. A very long title wraps; it is not cut.
- **Lead block.** The block kind `lead` (title, body up to 600 characters, up to four label and value facts, one action) replaces the default hero: it is placed first when added, the page keeps exactly one h1, and the accessibility audit counts hero and lead together. It has no art.
- **Block links.** Links organizers type into blocks (hero, lead, call-to-action, sponsor and resource URLs) are a relative path, an anchor, or an `http(s)` or `mailto` link: refused at save time and dropped at render time (`presentation/blocks.py safe_href`), because the public site shares an origin with the application.
- **Art direction.** `banner_focus_x` and `banner_focus_y` (whole percents, 50 is the centre and is stored as nothing) set the crop's `object-position` through `--hero-focus-x/y` in the presentation variables; `banner_mobile_url` is an optional alternative picture for a phone, drawn with `<picture>` so the browser loads one image. Both live in a disclosure.
- **Preview.** The appearance form has a closed disclosure that previews the public page at 1440, 768 and 390px with the form's draft appearance over the saved blocks. It is the `page` surface of PREVIEW_CONTEXT (`presentation/preview.py`) on the existing endpoint: the same template and `site_views.landing_context` as the visitor's page, the draft validated by `clean_theme_config`, nothing stored, scripts stripped, shown in a frame with `sandbox=""`. Unsaved block edits are not previewed.
- **Project pages and mobile.** The project cover is a small tile beside the title (a capped strip with art, absent when it is only initials on a phone), so the story and the evidence begin above the fold. The public header is two rows on a phone and each public page puts its title in the top 30% of the screen.
- **Fallback identity.** With no artwork the hero and every project cover draw the same lettered lockup (initials in the accent, hairline frame, type-scale size). One rule produces the letters (`presentation/showcase.py initials`, `web/lib/initials.ts`, shared fixture `tests/fixtures/initials_cases.json`).
- **Migration and compatibility.** `presentation 0006` changes only the allowed values of `PageBlock.kind`. Every new theme key is optional and absent means the old behaviour; no stored value is rewritten. Surfaces: web and docs; the block kind enum gained `lead` in OpenAPI and both SDKs (regenerated, checked); the page preview reuses the existing preview-as endpoint.

## PD-F004-B04 canonical contract

Recorded at the close of PD-F004-B04 from what was built (T01-T08), against design `V-SLOP-1..8`.

- **The guardrails are a measured gate.** `slopProblems` (`tests/e2e/slop.ts`) implements eight rules on the rendered page: `gradient`, `iconTile`, `kpiCards`, `operatorCopy`, `pills`, `nestedCards`, `repeatedLabels`, `hiddenActions`. `slop-audit.spec.ts` runs them on every destination and task tab of the three reference roles and the three public pages at 390 and 1440, and each rule has a self-test that injects a violation. Static ratchets from B01 (stylesheet) and T01 (web sources and templates) remain for gradients.
- **Summary, not KPI cards.** The overview is one strip of at most six figures, each the link to its records; the on-site and deliberation facts share the strip style and the operations sections are hairline-separated rows; each overview figure loads and fails on its own (Loading, or "could not load" with Retry).
- **Operator copy.** Application text is at most 20px; a page header is a title plus context of at most ten words.
- **Labels.** A heading, selected task tab and breadcrumb never say the same thing twice inside the page; the rail may match the page title because it names where you are.
- **Cards.** A box with its own border or a filled padded surface never sits inside another; inside a card the empty and loading states and tables are unframed, error and denied states keep their border because it carries meaning.
- **Actions.** Every frequent action is a labelled button where it is used; a menu popup or dots-glyph trigger fails the audit. Labelled disclosures (Advanced) are allowed.
- **Surfaces.** web and docs only; no endpoint, model, SDK, audit, webhook, archive or Event-as-Code change. Limitation: dialogs, open disclosures and per-record detail views are not walked.

## PD-F004-B05 canonical contract

Recorded at the close of PD-F004-B05 from what was built (T01-T05), against design `V-SLOP-9..12` and `V-SLOP-14`.

- **Five more audit rules** in `slopProblems`: `recordGrids`, `alarmColors`, `fakeAi`, `precision`, `opaqueIds`, each with a self-test and run on the same pages and widths as B04.
- **A list of records is a table.** Registrations and projects are sortable tables (the entity grid); three or more boxed siblings in a row fail the audit.
- **Red is for failure.** Red appears only on the failing item and on a final destructive button; a page with several red marks fails.
- **Deterministic flows do not look like an assistant.** No sparkle, "AI", copilot, magic (other than "magic link") or smart-suggest control; scoring, eligibility and publication stay unlabeled as intelligent.
- **Precision.** A shown figure has at most two decimals; `data-raw` marks an exact value on purpose. Dates in the event timezone with a relative hint are not audited by this rule.
- **No opaque ids as input.** A record is chosen by name (`RecordPicker`): a project or team from the projects entity (a team through its project, via the read-only `team_id` field), a person from the organizer-only participants list. A key the author invents (a form field's id) is `data-authored-key`.
- **Surfaces.** web and docs. The only server change is one derived, non-default `team_id` field on the projects entity (the feature search claim lists it); no model, migration, endpoint payload, SDK, audit, webhook, archive or Event-as-Code change. Registering new query entities was tried and rejected: each must be claimed by a feature, manifest and search contract.
- **Limitations.** Dialogs, open disclosures and per-record detail views are not walked; the person list omits people with no project; a team with no project is not offered.

