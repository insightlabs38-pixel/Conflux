# Upgrade and compatibility discipline

What an operator can expect when moving to a newer build of Conflux, and
what stays stable across that move.

## Moving to a build with the shared primitives (PD-F002-B01)

Additive only: migrations `core/0002_saved_views`, `0003_jobs`, `0004_approvals` and `0005_threads` add tables and change nothing that exists, so they apply on the normal startup `migrate` and a rollback to the previous image simply leaves them unused. Two new Celery tasks need the **worker and beat to be restarted on the new image** (`docker compose up -d --build` rebuilds all three services; the `app` container alone does not carry them): `core.tasks.run_job` and the beat entries `sweep-jobs` (every 60 s: fails jobs that stopped reporting, re-sends queued ones that never started) and `sweep-approvals` (every 5 minutes: marks lapsed approvals). Until the worker is updated, a started job (an archive export) stays queued, and the sweep, once beat is current, re-sends it. Approval gates are off for every existing event, so no behavior changes until an organizer turns one on. See [shared primitives](../architecture/SHARED_PRIMITIVES.md).

## Moving to a build with the second shared primitives (PD-F002-B02)

Additive only. One migration, `core/0006_notification_preferences`, adds a table that stays empty until a person changes a notification choice; until then every category keeps its default, so mail goes out exactly as before, and a rollback to the previous image leaves the table unused. No new Celery task or beat entry, so the worker and beat need no restart for this batch. Existing audit rows, job results and configuration history are unchanged (older rows simply have no provenance). New read-only endpoints (rich preview, artifact preview, version history and comparison, notification preferences, extensions) appear in the OpenAPI contract and the generated SDKs. **Startup now runs the extension manifest check**: `manage.py check` (so `migrate` and `runserver`) fails with `core.manifest.<code>` when a source declares something that is not registered, a requirement is unresolved, or a manifest asks for an unsupported `api_version`. A deployment that adds its own registry entries should declare them in a `<app>/manifest.py`; an entry that is registered but not declared is only a warning. See [extensions](EXTENSIONS.md) and [shared primitives](../architecture/SHARED_PRIMITIVES.md).

## Moving to a build with preview contexts (PD-F002-B03)

Additive only: no migration, no new Celery task and no change to an existing endpoint. One new read-only endpoint, `POST /api/v1/workspaces/{id}/preview-as/{surface}/` (organizers and admins), appears in the OpenAPI contract and the generated SDKs; it stores and sends nothing. The extensions inventory gains a `preview_surface` capability, and a deployment that registers its own preview surface must declare it in its `manifest.py` or `manage.py check` fails. See [preview contexts](PREVIEW_CONTEXT.md).

## Application startup: normal migrations, no destructive hacks

`infra/api.Dockerfile`'s entrypoint runs, in order, every time the `app`
container starts:

```
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec uvicorn config.asgi:application ...
```

This is a plain, additive `manage.py migrate` — the same command an
operator would run by hand. Nothing here ever flushes, resets, fakes, or
drops schema on startup; upgrading means pulling a new image and letting
Django's own migration graph bring the schema forward, in the same
dependency order it always resolves migrations in. A newer build's
container simply refuses to start if its migrations can't apply cleanly,
rather than silently reinterpreting or discarding existing data.
`tests/compatibility/test_migration_discipline.py` guards both of these
as a regression: the entrypoint never gains a destructive command, and
every app's migration graph has exactly one leaf (no unmerged branches a
plain `migrate` could apply in an ambiguous order).

## Data migration: backup and restore

Before any upgrade, back up authoritative state:

For quiesced snapshots with integrity manifests and post-restore verification,
see [verified backup checkpoints](BACKUP_CHECKPOINTS.md). The Core commands below
remain available.

```
make backup                    # -> backups/<timestamp>/
make backup DEST=/path/to/dir  # or a caller-chosen destination
```

This covers PostgreSQL (a `pg_dump --format=custom`) and the object
store's raw volume (artifacts, not their metadata, which lives in
Postgres). Valkey is never included — disposable cache/broker state only,
per `config/settings.py`'s own comment on `VALKEY_URL` — restoring it
would be meaningless, and a fresh instance rebuilds it on its own.

Restore the same way:

```
make restore DEST=backups/<timestamp>
```

`make backup-restore-smoke` proves the round trip actually recovers real
state (not just "the commands didn't error"): it seeds a uniquely-named
workspace, backs up, deletes the workspace, restores, and confirms it (and
only it) is back. See `scripts/backup-restore-smoke`.

## Canonical archive (`format_version`)

Exporting/importing an event, saving/instantiating an event template, and
cloning an event all go through the same canonical archive described in
`docs/architecture/CANONICAL_ARCHIVE.md`. Its `format_version` is the
compatibility contract for _that_ document, independent of the database
schema above: a build only ever reads the `format_version` values it was
written to understand, and an archive from an incompatible version is
rejected outright with a named error, never silently reinterpreted.

## API versioning

Every application route lives under `/api/v1/`, per
`docs/api/CONVENTIONS.md`. A breaking change to a route's request/response
shape is a new version prefix, not a silent change to `v1` — nothing in
this codebase does that yet, but the moment it needs to, this is where
that decision gets recorded.

## Prior-schema migration smoke fixture

`demo/release-freeze` (PostgreSQL 17 dump from the 2026-09-27 release rehearsal, checksum in its
`MANIFEST.md`) is the recorded prior released schema. `tests/compatibility/test_prior_schema_migration_smoke.py`
restores it into a scratch database, runs a normal `manage.py migrate` with the current code, checks
`migrate --check` is clean, and asserts the five records named in the manifest (event, project,
submission version, ballot, award) read back exactly once. It runs when `DATABASE_URL` is PostgreSQL
and a `pg_restore` that can read the dump is available (local, else Docker `postgres:17`, override with
`CONFLUX_PG_RESTORE_IMAGE`); otherwise it skips with the reason. A companion test pins the dump's
SHA-256 so the fixture cannot drift silently. When a newer release ships, add its dump next to this one
and extend the test rather than replacing the record of the older release.

## Moving to a build with the completeness contract (PD-F003-B01)

No migration, no new Celery task and no new endpoint beyond one read-only report, `GET /api/v1/workspaces/{id}/completeness/` (organizers and admins), which lists which of fifteen features provides which properties and checks every claim against the running system. See [completeness](COMPLETENESS.md). Four changes are visible outside that page:

- **More changes are audited.** Project, form, evaluation-plan, artifact, submission-draft, application-decision and team writes now write an audit row in their own transaction (`project.created`, `project.updated`, `form.created`, `form.draft_saved`, `evaluation_plan.updated`, `evaluation_plan.deleted`, `artifact.added`, `artifact.upload_started`, `artifact.uploaded`, `artifact.validated`, `submission.draft_saved`, `application.decided`, `team.created`, `team.member_joined`, `team.member_left`, `team.captain_transferred`, `team.invite_created`, `team.invite_revoked`, `team.invite_redeemed`). Rows hold ids and field names, never content, object keys, signed URLs or invite tokens. A submission autosave now adds one row per save.
- **Four creates accept an `Idempotency-Key`**: sending a message, posting an announcement, creating a project and adding an external artifact. It is opt-in: a request without the header behaves as before. The key mechanism itself changed: it is now considered only after authentication and permissions (a replay is never served to someone the view would refuse and a signed-out caller leaves no row), keys belong to the signed-in user rather than to a session cookie, and keys and their stored answers expire after 24 hours. A new beat entry, `sweep-idempotency` (hourly, `core.tasks.sweep_idempotency`), deletes expired keys: **restart beat and the worker on the new image** (`docker compose up -d --build`); until then expired keys are simply treated as new requests and not purged.
- **The OpenAPI document and both SDKs were corrected.** Ten list operations (announcements, artifacts, evaluation plans, events, forms, policies, projects, stages, team invites, tracks) were documented as one record and are now arrays, so a TypeScript or Python client that worked around the wrong type should drop the workaround; the message list documents its `offset`; the award output documents `resources`.
- **An empty-bodied 404 now carries `{"detail": "Not found."}`** (projects, artifacts, judging results and the scoreboard), with the same status.

## Moving to a build with the eight surface properties (PD-F003-B02)

No migration, no new Celery task, no new endpoint and no change to the OpenAPI document or either SDK. The completeness report (`GET /api/v1/workspaces/{id}/completeness/`) now covers sixteen properties instead of eight: the eight surfaces (base and advanced UI, bulk operations, CLI, MCP, Event-as-Code, webhooks and the outbox, archive) each have a claim per feature and a derived fact set, so the response carries more property keys and facts; clients that read only the earlier keys are unaffected. See [completeness](COMPLETENESS.md). Two things are visible outside the page:

- **The CLI reads one table.** `conflux-admin` (`sdks/python/conflux_sdk/cli.py`) now keeps its commands in a `COMMANDS` table that `execute` also reads; commands, options, requests and exit codes are unchanged.
- **Event-as-Code declares its sections.** `integrations.eventascode.SECTION_MODELS` names the model that owns each document section; the document format, the plan digest and the apply behavior are unchanged.

A build that adds a bulk action, an MCP tool, a CLI command, a document section, an audited change or an archive model must now also say what that means for its feature (the claims in `<app>/features.py`); the completeness checks (`manage.py check` for the running claims, `core.features.check_static` in CI) fail until it does.

## Moving to a build with the five platform properties (PD-F003-B03)

No migration, no new Celery task, no new endpoint and no change to the OpenAPI document or either SDK. The completeness report (`GET /api/v1/workspaces/{id}/completeness/`) now covers all 21 properties: analytics dimensions, retention and privacy, extension hooks, version and migration, and test fixtures and scenarios join the sixteen before them, so the response carries five more property keys and their facts and no property is left pending; clients that read only earlier keys are unaffected. See [completeness](COMPLETENESS.md). Nothing a participant or organizer does changes. For people who extend or test the platform:

- **Every person column has a stated fate.** A feature whose model has a user column (a poster, a decider, a creator) must say what becomes of that person's data (`erased`, `retained`, `purged` or `staff`, with a reason where the row is kept), and a new column fails the check until it does.
- **A new version model, counter, comparison source, hook, bulk or privacy bucket must be claimed.** Numbered immutable models, version counters, manifest provides, analytics measures and privacy buckets are derived from the code and must be claimed by exactly one feature or named as outside; `check_static` in CI and `manage.py check` fail otherwise.
- **The demo scenario is claimed per feature.** Nine features appear in the generated demo event; five (announcements, artifacts, forms, messages, policies) are owed by PD-S061-B02-T01 and one (webhook subscriptions) is deliberately not created. A change to what the demo creates must update the claims; the proof counts rows in both directions.
- **Known gaps stated, not hidden:** form answers are in no privacy export or erasure bucket yet (PD-S013-B02-T05); version models are immutable in the model and not in the database, so a bulk queryset write would bypass them (a source scan test guards it).

## Moving to a build with the visual foundation (PD-F004-B01)

No migration, no new endpoint and no change to the OpenAPI document or either SDK; the build is stylesheets, tokens and React components. What an operator or organizer will notice:

- **The default accent is blue** (`#1d55c2`) instead of green, for the application and for public event sites that have not stored an accent. A stored organizer accent (the technical, student and conference presets, or a custom colour) is kept as it is; every accent the old contrast gate accepted is still accepted on the new light and dark backgrounds (proved over a 4,000-colour grid), and the gate message is unchanged.
- **The authenticated shell is denser**: a 44px top bar, a 216px rail with icons, 28 to 32px controls on desktop and 44px controls on touch layouts (below 768px or a coarse pointer), headings at most 20px, no shadows except on the account popover and dialogs, and one filled button per context. The marketing line at the foot of the rail is gone.
- **Public hero titles are smaller** (24 to 32px, fluid) than before; the poster and editorial heroes keep their large monogram until the hero work in PD-F004-B02/B03.
- **A destructive action asks first.** "Delete template" now shows a named confirmation instead of deleting at once; "Delete view" and "Decline" are neutral buttons, and the red filled button appears only as the final confirm.
- **The public presentation payload keeps every existing key** (`--color-accent`, `--color-accent-strong`, ...) and adds the v3 names (`--accent`, `--accent-hover`, `--accent-ink`, `--accent-tint`, `--accent-line`); a client that applies the variables needs no change. The legacy `--color-*` CSS names are aliases to the v3 colour tokens for one release and are removed by the close of PD-F004-B05; custom CSS or embeds that read `--space-*`, `--radius-*`, `--font-size-*`, `--shadow-*` or `--control-height*` must move to `--sp-*`, `--r-*`, `--fs-*`, `--sh-*` and `--h-ctl*` (the values are the same, apart from the new scale: 3/5/8px radii, 11 to 32px type).
- **Fonts**: IBM Plex Sans and Mono are named first, but no font files ship yet; hosts without them use the system font (open question logged for the owner).

## Moving to a build with status, state and hero polish (PD-F004-B02)

No database migration, no new endpoint and no change to either SDK; the build is stylesheets, React components and templates. What an operator or organizer will notice:

- **The public hero is compact by default.** It is a short band (title, status, art or a small lettered lockup) with the description and one action beneath, at most 240px on desktop and 120px on a phone, instead of the large split, poster or editorial block. This applies to every event, including events whose theme was saved earlier (their stored theme has no hero size, which means compact). An organizer who wants more room chooses **Standard**, or **None** for a title and one action, under Event setup, Public page, Appearance, Hero size; the layout choice (split, poster, editorial) is separate and unchanged.
- **Statuses read as icon plus word**, and ordinary labels are plain tags, not coloured chips.
- **Loading shows the grid's header over placeholders; empty states say why and offer the next step; failed loads say whether anything changed and what Try again does** (a failed read changed nothing; a save that failed without a refusal says the change could not be confirmed, check before repeating it).
- **Public presentation payload**: `presentation.hero_size` is added (`compact`, `none`, `standard`); clients that ignore it keep working. A saved theme containing any other value is refused with a 400 naming `hero_size`.
- Advanced sections now share one disclosure look and borders are solid; no behavior or default open state changed.

## Moving to a build with hero art direction, the lead block and the page preview (PD-F004-B03)

One choices-only migration (`presentation 0006`, the allowed block kinds) and one additive OpenAPI and SDK change (the block kind `lead`); nothing stored is rewritten. What an operator or organizer will notice:

- **Hero size gains `immersive`** (a full-width image above the title; needs a hero image URL, refused without one) and **hero image crop** (focal point sliders and an optional phone image) under Event setup, Public page, Appearance, in a closed section. Events that set none of this look as before.
- **A Lead block** (Public page, Content, Add block) replaces the default hero with a title, a short body, up to four facts and one action. It is placed first when added.
- **Preview**: a closed section "Preview at desktop, tablet and mobile widths" draws the public page with the appearance as it is in the form, saved or not, at 1440, 768 and 390px. Nothing is saved.
- **Public page changes for every event**: the hero shows the status and dates (in the event's timezone); on a phone the header is two rows; project pages put their story and evidence above the fold with a small cover tile; project covers, tags and statuses use the same lettered identity, tags and status words as the app.
- **Security hardening (links in page blocks).** Links typed into blocks must be a path or anchor on the site, or an `http(s)` or `mailto` link. Saving anything else is refused with that sentence, and a link already stored that does not meet the rule is no longer rendered as a link (it used to be written into the page as typed, including `javascript:`). Check pages that use unusual schemes (`tel:`, `ftp:`) before upgrading; they now render without a link until changed to an allowed form.
- **Initials**: a name starting with punctuation or an emoji now draws its first letters ("(Open) Data" is OD, not "(D"); only an empty name draws "?".

## Moving to a build with the anti-slop cleanups (PD-F004-B04)

No migration, no endpoint, no SDK change; web only. What an operator or organizer will notice:

- **Page headers carry a title and a short context line**, not a sentence of marketing; the overview and the on-site facts are a strip of figures instead of rows of boxed cards, and the operations sections are separated by hairlines.
- **Fewer repeated headings**: panels under a task tab (Settings, Features, Forms, Policies, Stages) no longer say the tab's name again; the Communications panel is titled "Send a message" and the judging card "Evaluation setup". Browser tests or scripts that find these cards by heading must use the new names.
- **No frame inside a frame**: the public page editor stands on the page, and empty and loading states and tables inside a card lose their own border (error and denied states keep theirs).
- The browser suite has a new read-only gate, `slop-audit`, that fails when a page regains a gradient, a coloured icon tile, a card row, a pill around ordinary text, a nested card, a repeated label or a three-dot menu (docs/operations/VISUAL_FOUNDATION.md).

## Moving to a build with the data guardrails (PD-F004-B05)

No migration, no endpoint, no SDK change. What an organizer will notice:

- **Choosing instead of pasting ids.** Setup > Policies "Check policy" chooses the project (or the team, for joining) from a list by name, with a box to narrow it; Permissions "Test" with a real person chooses them by username. The API calls are unchanged and still receive the record's id, so scripts that post ids keep working. The person list is the workspace's project participants; to test a judge or mentor use the hypothetical-role mode.
- **Registrations and projects are sortable tables**; red now marks only a failure or the final destructive button (bulk apply and rebalance are no longer red).
- The projects query entity gained a read-only `team_id` field (not a default column, not filterable) so a screen can name a team without exposing its id. Saved views and API clients that list the entity's fields will see one more.
- The browser suite's `slop-audit` gate now also fails on boxed records, alarm colours, assistant-like controls, figures with more than two decimals and id-typed inputs; the new `record-picker` spec is in the read-only tier.

## Moving to a build with the application shell (PD-F005-B01)

No migration, no endpoint, no SDK change; web only. Every existing URL keeps working. What an operator, organizer or participant will notice:

- **A new top bar**: an event switcher (current, favorites, recent, other events, and your other workspaces), **Search** (also Ctrl+K or Cmd+K, which opens a palette of commands such as "Go to Judging", "Switch to ...", "Use the dark theme", "Sign out" and, for organizers, a search of the event's projects and applications), a notification bell with the unread count, and the account menu.
- **Navigation changes with the screen**: a 52px icon rail between 1024 and 1439 pixels, the old drawer from 768 to 1023, and on phones a bottom bar of at most five controls with a **More** sheet. Browser tests or scripts that opened the old "Navigation" toggle on a phone must use "More" (the shared helper `goToDestination` already does).
- **Theme**: Account, Theme chooses System, Light or Dark for the app's own screens. It is kept on the device and forgotten at sign-out; public event pages follow the organizer's theme and are never changed by it.
- **Favorites and recent events** are kept on the device too, not on your account, so they do not follow you to another browser.
- **Notification preferences** are one click from the account menu and the bell; they open the profile section directly.
- The browser suite's read-only tier gained `shell-responsive`, `event-switcher`, `account-menu`, `global-search` and `command-palette`, the isolated tier gained `inbox-center`, and `slop-audit` has a `crumbs` rule. `Modal` now returns focus to the control that opened it (a fix for an autofocused field being mistaken for the opener).
- Integrators: a new query entity now needs an entry in `src/web/lib/searchTargets.json` (a test fails otherwise), and the inbox read is shared by `useInbox`.

## Moving to a build with the second slice of the application shell (PD-F005-B02)

No migration. Two small additive API changes (OpenAPI and both SDKs regenerated): the three event lists (organizer, judge, participant) gained a read-only `phase` object (`key`, `label`, `reason`), and `GET /audit/{workspace}/` accepts optional `mine` and `limit` (1 to 200, newest first) and answers exactly as before without them. What people will notice:

- **The event's phase** (Draft, Open, Closed, Judging, Published, Archived) beside its name in the event switcher; hover for the reason. Judging means a judge has submitted a ballot (practice ballots do not count), Published means an award is published.
- **Account menu**: Viewing as (only if you hold several roles; the default is now your most privileged role, a link with as chooses another), Preview as participant, judge or public (organizers and admins; read-only, nothing is saved or sent), Theme, Table density (comfortable, the long-standing look, compact, high density) and Keyboard shortcuts.
- **Keyboard**: ? shows the shortcuts, / opens the palette, G then a letter goes to a place (G then J for Judging); single-key shortcuts can be turned off in the help, Ctrl or Cmd K always works.
- **Palette**: pinned views first (pin one in a list's view bar), your latest actions from the audit log, views you opened lately, View as and Preview as commands.
- **Lists**: every list has a Details button that opens the record in an inspector beside the list (a sheet below 1024px); a link with row_<entity> reopens it.
- **On a phone** the brand word hides so the event switcher keeps its room; the browser suite's `goToDestination` is unchanged.
- Integrators: scripts that read the event lists will now see `phase`; clients that list a person's memberships may see several rows for one workspace (one per role), as before.

## Moving to a build with the second slice of the data grid (PD-F006-B02)

No migration. Two more additive optional parameters on the entity query (`group`, `subgroup`, with `groupable` in the catalogue; OpenAPI and both SDKs regenerated), carried by the CLI and the MCP tool.

- **Narrow screens**: on a phone the header becomes a bar above the rows (Select page, sort buttons); from 641 to 1023px a wide list keeps its select box and name column while it scrolls sideways.
- **Filters**: nested groups (Add group), operators worded and entered by type (date and number boxes, ranges as two boxes, several enum values as checkboxes); a filter with a refused value is explained beside its condition.
- **Saved views**: Reset, who can see a view, pinned views first in the picker, a conflict reloads the view; views may carry a grouping.
- **Links**: a filter whose values are all structured is in the address (`f_<entity>`) and opens the same list; a filter with text is not, and the page says to save a view.
- **Group by** (and Then by): collapsible groups with counts, each opening its rows; selection and bulk actions are in the flat list.
- Integrators: older builds ignore `group_`, `then_` and `f_` params; a view saved with `group` is refused by a build that does not know it.

## Moving to a build with the first slice of the data grid (PD-F006-B01)

No migration. One additive API parameter (`search` on the entity query, with `search_fields` in the catalogue; OpenAPI and both SDKs regenerated) and one new CLI command group and MCP tool that call existing routes.

- **Lists**: a search box above lists that can be searched; sort by clicking a header, Shift-click adds a second and third key (the order is numbered and kept in the address); the active filter is read back as a sentence with Clear filter, and a value the server refuses is explained beside its condition; rows per page (25, 50, 100), First and Last, Page X of Y; a selection is only of the rows in view and has a Clear selection button; the bulk bar shows one primary action and says why one is unavailable; the column picker counts and can show all.
- **Links** carry the sort, page and rows per page (`sort_`, `page_`, `size_`); search text is never in a link, save a view to share it.
- **CLI and agents**: `conflux-admin entities list|query` and the MCP tool `query_entity` run the same query, read-only.
- Integrators: empty values now sort last in both directions on every database; saved views may carry `search`, stored only when used.

## Moving to a build with the third slice of the application shell (PD-F005-B03)

No migration and no API change. New device-local keys (versioned `conflux:v1:`): remembered columns, kept tabs, operations mode and live operations; they are cleared at sign-out. Unsaved edits in tabs are memory only.

- **Columns**: the picker's choice for a list is remembered on this device; Reset columns forgets it. A saved view's own columns still win while it is open.
- **Links**: lists put their sort and page in the address, and "Copy link to this view" (palette) copies exactly the view you are looking at, without the invite token or anything typed.
- **Tabs**: "Keep this place open in a tab" (palette) keeps a place under the header; a place with unsaved changes (the event appearance form first) stays marked while you work elsewhere. Closing it or signing out asks first; a reload warns.
- **Selected rows**: with rows selected, the palette offers commands for them, such as "Move 2 projects to <track>" which opens the usual preview.
- **Live operations**: a button in a list's tools (or the palette) refreshes the list every 15 s and shows connection health and the age of the data; offline, row actions wait.
- **Operations mode**: Account menu, or the palette, adds a second pane beside the page on displays 1800px wide or more (needs attention, recent actions, inbox).
- Integrators: the browser suite gained `share-link`, `column-preferences`, `live-operations`, `workspace-tabs`, `operations-mode` (read-only) and `selection-commands` (isolated).
