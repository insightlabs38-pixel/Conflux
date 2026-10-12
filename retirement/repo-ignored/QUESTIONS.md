
## 2026-09-30T13:30Z PD-B04-T08 (data_integrity, P1 found and fixed; owner review of one migration choice)
Question: how should unsent judge ballots queued by earlier app versions (localStorage `conflux.judge-outbox.<plan>`, no user in the key) be handled now that the outbox is scoped per account?
Options: A leave untouched and never read (safe, buffer not shown); B adopt for the first account that opens the plan (keeps single-judge buffers, repeats mis-attribution once on shared browsers); C delete (loses ballots).
Conservative default chosen: A. Nothing is deleted or replayed. Details and evidence: docs/execution-v3/escalations/ESC-20260930-001.yaml.

## 2026-09-30T17:10Z PD-F001-B01-T00 (plan_defect, P2)
Question: PD-F001-B01 reuses shared primitives (SCHEMA_EDITOR, QUERY, POLICY_EXPLAIN, ROUTER, ASYNC_JOB) whose owner tasks are sequenced after it, and its owned paths omit events/communications/integrations. Resequence or proceed?
Options: A domain-first without the primitives (plain descriptors/query params/one Reason shape, adopted later); B resequence F002/F071 primitive batches first (rewrites dependency graph); C stop.
Conservative default chosen: A. Additive and reversible. Also: readiness stays advisory (no new hard gate on opening). Details: docs/execution-v3/escalations/ESC-20260930-002.yaml.

## 2026-09-30T22:27Z PD-F001-B02-T01 (product_ambiguity, P3)
Question: which "generated configuration" must include explicit values only when necessary? The batch surface matrix marks event_as_code not_required, yet Event-as-Code export is the only existing config generator.
Options: A new additive generated-configuration document derived from the PD-F001-B01 registry (preset + only values that differ from their baseline; inherited defaults legible as comments), with API and web view; B change the Event-as-Code export to omit defaults (alters a supported, round-tripping format; belongs to PD-S046); C escalate and stop.
Conservative default chosen: A. Additive, no change to the EaC format; EaC minimal export recorded as a limitation/follow-up for PD-S046.

## 2026-09-30T22:42Z PD-F001-B02-T02 (data_integrity, P2)
Question: preset events always carry a published rubric, which is permanent, so draft events and judged stages can never be deleted (the endpoints returned HTTP 500). Allow deleting an unused published rubric with its draft event?
Options: A refuse cleanly with the reason (no invariant change); B sanction deleting an unused rubric (needs a definition of unused); C stop publishing the rubric at creation (undoes T03).
Conservative default chosen: A. Details: docs/execution-v3/escalations/ESC-20260930-003.yaml.

## 2026-09-30T23:06Z PD-F002-B01-T00 (architecture, P2)
Question: migrate existing near-primitives (bulk planner, SavedPublicSearch, four note/comment models) into the new shared primitives, or adopt them and build the primitives beside them in a dependency-free core?
Options: A registry-first in core, adopt existing, migrate nothing; B migrate everything now; C per-domain placement.
Conservative default chosen: A. Additive and reversible. Details: docs/execution-v3/escalations/ESC-20260930-004.yaml.

## 2026-10-01T04:30Z PD-F002-B02-T01 (architecture, P2)
Question: the eight B02 primitives each overlap a near-implementation (two schema validators, two rich-content renderers, artifact inspector, flat audit diffs, three explanation shapes, scattered provenance, extension registries) and the queue has no contract task for the batch. Migrate them into the primitives, or absorb them behind byte-identical behavior?
Options: A absorb by adoption in core, byte-for-byte compatible, contract written under T01; B migrate stored values and public rendering now; C leave beside without adopting.
Conservative default chosen: A (same as ESC-20260930-004). Details: docs/execution-v3/escalations/ESC-20260930-005.yaml.

## 2026-10-01T13:47Z PD-F003-B01-T00 (architecture, P2)
Question: what artifact is the §3 cross-surface completeness contract (a checklist, an executable registry of features and claims with verifiers, or a retrofit of every model), and how does T07 reuse TYPED_CLIENT, whose owner batch is later?
Options: A executable registry in core with claims verified against the live registries, bounded feature set, gaps recorded as planned with an owner; B documentation checklist only; C retrofit all 122 models to all 21 properties now.
Conservative default chosen: A; TYPED_CLIENT = the existing generated SDKs until its batch lands. Additive, no migration. Details: docs/execution-v3/escalations/ESC-20260930-006.yaml.

## 2026-10-06T04:06Z PD-F003-B01-T95 (plan_defect, P3)
Question: T95 asks for an independent frontier review, but this campaign has one agent that implemented the batch. Who reviews?
Options: A run the code-review skill (separate review passes) over the whole batch diff at high effort, fix confirmed findings, record that the review is by the same tooling account and not an outside party; B stop and wait for the owner or another reviewer; C mark T95 not applicable.
Conservative default chosen: A. Reversible and additive; the receipt states the limitation so an owner can still commission a human or second-model review before release. No gate is downgraded.

## 2026-10-06T21:50Z PD-F003-B03-T04 (data_integrity, P2)
Question: immutable version models (forms.FormVersion, evaluations.RubricVersion/AssignmentVersion/NormalizationRun/PairwiseRun, projects.SubmissionVersion, governance.RulesVersion) refuse edits and deletes only in `save()`/`delete()`; a queryset `update`/`delete` bypasses the guard (verified). Add a database-level guard (trigger) for them?
Options: A keep the model-level rule, add a test that no source file bulk-writes these models, record the residual; B add a PostgreSQL trigger migration per table (new migration, SQLite parity unclear); C stop and wait for the owner.
Conservative default chosen: A. Additive and reversible; no migration blast radius; the residual is stated in the T04 receipt, COMPLETENESS.md and spec 003 so an owner can still commission B.

## 2026-10-06T22:40Z PD-F003-B03-T95 (plan_defect, P3)
Question: T95 asks for an independent frontier review of the batch; this campaign has one agent that implemented it, and the review it can run (the code-review skill) is by the same account and model family. Who reviews?
Options: A run the code-review skill at high effort over the whole batch diff, fix confirmed findings with tests, state the same-account limitation in the receipt; B stop and wait for the owner or another reviewer; C mark T95 not applicable.
Conservative default chosen: A (same as PD-F003-B01-T95). Reversible and additive; no gate is downgraded and the owner can still commission a human or second-model review before release.

## 2026-10-06T22:41Z PD-F003-B03-T90 (test_reliability, P3)
Question: tests/e2e/workspace-shell.spec.ts `role navigation organizer` takes 19-30 s of its fixed 30 s budget (nine destinations, each opened, settled and checked for overflow and accessibility) and timed out at 390 on the first full run after a rebuild, twice in this campaign. Raise its budget with the destination count, or leave it?
Options: A leave the fixed 30 s, record the flake, rely on a clean rerun (AGENTS.md: do not hide regressions behind timeouts); B budget = 20 s + 5 s per destination (tried, reverted after review); C split the test per destination (changes test structure, owner decision).
Conservative default chosen: A. B was applied then reverted after the T95 review flagged it against AGENTS.md; the evidence for the batch is a clean run on a warmed stack. The owner may choose B or C.

## 2026-10-07T00:30Z PD-F004-B01-T00 (product, P3)
Question: self-host IBM Plex Sans/Mono and Source Serif 4 (OFL) as font binaries in the repo for v3 typography, or stay on the system stack (design D-007 item 2)?
Options: A keep the stack with Plex named first and ship no binaries until the owner confirms licence packaging and air-gapped needs; B vendor woff2 files plus OFL notices now; C system stack only, drop Plex.
Conservative default chosen: A. Reversible (adding binaries later is additive); typography tasks use the 11-32px scale and metrics that work with both fonts; the limitation is stated in the B01 receipts.

## 2026-10-07T04:10Z PD-F004-B01-T90 (test_reliability, P3) — supersedes the 2026-10-06T22:41Z default
Question: `workspace-shell` "role navigation organizer" (nine destinations, a full-page axe scan each) took 25-31 s of its 30 s budget before this batch and now times out reproducibly at 390 and 768 under `make e2e-fast` (2 of 3 full runs; alone it passes at 25-26 s). Keep waiting for a clean rerun (the earlier default A), raise the budget, or split the walk?
Options: A leave as is and rely on a clean rerun (no longer yields a clean full run); B raise the budget (reviewed against AGENTS.md before: no); C split the organizer walk into one test per destination, keeping every assertion.
Conservative default chosen: C. Test structure only, nothing weakened or removed (same overflow and axe checks per destination, plus the same retention and hidden-module checks in their own test), each test about 4 s, reversible. The owner may still prefer another shape.

## 2026-10-07T07:15Z PD-F004-B02-T08 (product, P3)
Question: the B01 checkpoint asked for a mapping decision before changing the stored hero vocabulary (split, poster, editorial) to none/compact/standard. Replace `hero` or add a second key?
Options: A keep `hero` as the layout and add `hero_size` (compact, none, standard) to `theme_config`, absent means compact; B overload `hero` with all six values and migrate stored themes; C stop and wait for the owner.
Conservative default chosen: A. Additive and reversible: no stored value is rewritten, no migration, both settings stay meaningful. Visible consequence: every event now renders the compact hero unless its organizer picks Standard (stated in UPGRADES.md).

## 2026-10-07T07:40Z PD-F004-B03-T01 (design, P3)
Question: design D-007 item 4 says the immersive hero was intentionally not designed beyond its Advanced entry point, and B03 is design_required. May the immersive size be built from the existing rules (V-HERO-1, D-005, D-012, LATER_DESIGN_PASSES: other surfaces inherit Ledger primitives)?
Options: A build it as an opt-in `hero_size: immersive` that needs a hero image, art as its own full-width strip above a solid title row (never text over art), art capped at 352px desktop and 120px mobile, no new tokens; B stop B03 and wait for a design pass; C skip T01.
Conservative default chosen: A. Opt-in, additive, reversible (one enum value and one CSS block), every V-* rule and the contrast gate still apply; the limitation is stated in the T01 receipt so the owner can commission the design pass and replace the CSS.

## 2026-10-07T08:05Z PD-F004-B03-T05 (security, P2)
Question: organizer-typed links in public page blocks (hero `cta_href`, cta `href`, sponsor and resource `url`) were rendered unchecked on the public site, which shares an origin with the application, so an organizer could store a `javascript:` link. Fix it inside T05 (which adds a block with a link) or leave it?
Options: A validate at save time for the five link fields and drop unsafe values at render time with a template filter (stored values keep working if safe; an unsafe stored value renders as no link); B only validate the new lead block; C stop and wait for the owner.
Conservative default chosen: A. Additive and reversible; relative paths such as the demo's `gallery/` stay valid; the residual is that an already-stored unsafe link now disappears instead of executing. Recorded as a finding in the T05 receipt and the upgrade note.

## 2026-10-07T09:05Z PD-F004-B03-T90 (test_reliability, P3)
Question: `uiv2-surfaces` walks nine surfaces per width in one test (about 13 axe scans of 1.8 s on pages of about 10,000 elements, 21 s alone) and timed out at 30 s under the parallel read-only tier in `make e2e-fast`, at 1024 and 1440, twice. Raise its budget, leave it or split it?
Options: A leave and rely on a clean rerun; B raise the budget (AGENTS.md: do not hide regressions behind timeouts); C split into one test per surface and width, keeping every assertion (same shape as the organizer navigation split, 2026-10-07T04:10Z).
Conservative default chosen: C. Test structure only, nothing weakened; each test about 4-5 s; reversible.

## 2026-10-07T21:40Z PD-F005-B01-T00 (plan_defect, P2)
Question: PD-F005-B01-T01/T03/T05 reuse the ROUTER and COMMANDS primitives, but their owner tasks (PD-F071-B01-T01, PD-F071-B02-T01) are in later batches and PLANNED. Wait for them, move ownership now, or land the first implementation here?
Options: A adopt forward: ROUTER is the existing routes.ts + urlState.ts, COMMANDS is created once by F005-B01-T05 in src/web/lib/commands.ts, and the F071 tasks later formalise those exact modules; B move ownership in PRIMITIVE_REGISTRY/TASKS now; C stop the shell track until F071 is done.
Conservative default chosen: A (ESC-20260930-007). No queue or registry edit; reversible; the F071 owners must adopt, not rebuild.

## 2026-10-07T21:40Z PD-F005-B01-T00 (product, P3)
Question: should shell preferences (theme, favorite events) follow the person across devices (a server-side per-user preference store) or stay on the device?
Options: A device-local in B01 (namespaced by user and workspace, cleared on sign-out, ids revalidated against the server); B add a per-user preference table, API, SDK and feature claims now; C defer to PD-F005-B02/B03 where density and column preferences also need a home.
Conservative default chosen: A. No migration, endpoint or SDK change; B01-T08 and T02 read and write through one `shellPreferences` module so moving to a server store later changes one file.

## 2026-10-07T23:35Z PD-F005-B02-T08 (design, P3)
Question: design D-009 makes Standard (36px rows) the default account density with comfortable 44px and dense 28px; the app's tables today are about 48px (32px controls plus padding). Which should the default be?
Options: A keep today's look as the default ("comfortable") and add compact (about 40px) and high density (about 32px); B make the default the design's 36px Standard, which changes every table; C wait for a design pass on the data surface.
Conservative default chosen: A. No existing table changes unless the person chooses; the three labels follow the research (comfortable, compact, high density) and the heights are measured in the browser spec. Moving the default is one token change.

## 2026-10-08T00:10Z PD-F005-B02-T05 (product and architecture, P2)
Question: "preview as participant, judge or public without unsafe impersonation" could mean a whole-app view of another role's screens, or a read-only server-evaluated preview of what that person would see. Which?
Options: A the PREVIEW_CONTEXT primitive as built - a dialog (account menu and palette, organizers and admins only) that asks the server for the saved application form as that role meets it and, for the public, the public page in a script-less frame; B render the participant or judge workspace for the organizer, which would run those screens as the organizer and show empty or wrong data (the organizer has no team, no judging queue) or need real impersonation; C wait for more registered preview surfaces.
Conservative default chosen: A. No impersonation is possible by construction (a context is request data, the caller stays the actor); the two registered surfaces (form, page) are what can be previewed today and each new surface registered with PREVIEW_CONTEXT appears by adding it to the dialog.

## 2026-10-08T00:30Z PD-F005-B02-T01 (product, P2)
Question: the research lists the event states draft, open, judging, published, archived but the stored status is draft, open, closed, archived. How should judging and published be defined, and where?
Options: A derive them once on the server from what has happened (events/lifecycle.py) and send them as an additive read-only `phase` on the three event lists - published when an award is published, judging when a non-calibration ballot has been submitted, closed when closed with neither, so six words (closed is kept because it is a real stored state); B add judging and published as stored statuses with transitions (a migration and a state machine change); C derive them in the browser from several endpoints (two sources of truth).
Conservative default chosen: A. Deterministic, no clock, no client input, no migration, reversible (one function and one field); the rule is in the module docstring and tests/integration/test_event_phase.py.

## 2026-10-08T02:45Z PD-F005-B03-T03 (design, P2)
Question: design D-009 says wide displays add information, not chrome, and that "Ops mode may add one [second contextual region], undocumented here". What does the second pane of operations mode show?
Options: A one read-only pane beside the page from 1800px that watches a chosen existing server read - what needs attention (the readiness list), the person's own recent actions (audit log) or their inbox - with the live health line; B a second route rendered beside the first (two views at once, two sets of panel state in one URL); C wait for a design pass on Ops mode.
Conservative default chosen: A. No new endpoint or data, no second route model, off by default and a device choice, absent below 1800px. Which panels belong there, and whether a second place should ever render beside the first, is the owner's call; adding a panel is one entry in OperationsPane.tsx.
Resolution (owner, 2026-10-08): decision confirmed - read-only, off by default, very wide layouts only. Adjustment applied: the pane is a contextual utility slot with a panel registry (lib/opsPanels.ts); readiness, recent actions and inbox are the first three registered panels, not a fixed set.

## 2026-10-08T03:45Z PD-F006-B01-T00 (product and architecture, P2)
Question 1: should typed search text be shareable in a URL? Spec 005 forbids typed text in URLs and storage. Options: A transient, shareable only by saving a view; B put it in the URL. Default: A.
Question 2: the research says "pagination or virtualized windowing". Options: A server offset paging only (pages of at most 100 native rows), no client virtualization; B add a windowing layer. Default: A, with a performance escalation if the 5,012-row fixture exceeds 300 ms.
Question 3: the surface matrix requires cli and mcp for B01 but saved-view references and the text query language are B04. Options: A a read-only `entities query` command and `query_entity` tool now (same route and parameters); B nothing until B04. Default: A.

## 2026-10-08T05:20Z PD-F006-B02-T07 (product and privacy, P2)
Question: "URL-encoded shareable transient views" conflicts with the URL rule that typed text and personal data never go in a link. What may a link carry?
Options: A only filters whose every value is structured (an enum choice from the field's own list, a yes or no, a number, a calendar date or time, an emptiness check), encoded and re-checked on open; a filter with text or an id stays out and the person is told to save a view; B encode any filter; C no transient links, only saved views.
Conservative default chosen: A. No new storage or endpoint, free text and ids never reach a URL, history or log, and C remains the existing path for anything else. Numbers and dates are treated as structured, not personal; tightening to enum, yes or no and emptiness only is one function (lib/transientView.ts).

## 2026-10-08T06:20Z PD-F006-B03-T01 (design and product, P3)
Question: the data-surface design only names a List/Board toggle ("Board view is only named, not designed"); a matrix and a calendar are not drawn at all. Which layouts, and how do they look?
Options: A offer a layout only where it means something and is registered for the list (board when a workflow-like field exists, matrix when two fields can be grouped, calendar when a date places rows), built from the Ledger primitives already approved (hairline columns, tables with real headers, tint for the open item, no cards); B only the toggle the design names (list and board); C wait for a design pass on the data surface.
Conservative default chosen: A. Every layout reads the one entity query, so nothing is stored or computed beyond counts; a layout the owner dislikes is removed by deleting its registration (`board_field`, `calendar_fields`) with no migration. A design pass on board cards, matrix cells and the calendar is the owner's call.

## 2026-10-08T06:21Z PD-F006-B03-T01 (architecture, P3)
Question: the inspector used to find its record on the loaded page, so a card on a board, a day's row or a group's row could not open it. How should it find a record?
Options: A one added read, `GET entities/{key}/{row_id}/`, under the list's own base queryset and roles (a record the list would not show is 404); B load a page that happens to contain it; C keep the inspector to the flat list only.
Conservative default chosen: A. It is the same authorization as the list, returns only registered fields, adds no write, and replaces the inspector's second page query. It is also the target the inline edit (T04) writes to.
