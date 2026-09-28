# Sponsor fulfillment export

`GET /api/v1/workspaces/<w>/events/<e>/awards/fulfillment-export/` (JSON `{rows}`) and `.../fulfillment-export.csv`.

Rows cover **published** awards only, one per prize component per winning project, ordered by award, component and project: `handoff_reference` (the fulfillment id), award, component, kind, quantity, amount, currency, project, team, state, updated_at. Optional `state` filter.

Minimal by default. Opt-in extras are organizer-only (sponsors get 403 if they ask):

- `include_notes=true` adds the organizer/sponsor fulfillment note.
- `include_recipients=true` adds project members' usernames and emails, for the actual handoff.

Sponsors see only awards they are tagged on and never receive contacts or notes. Every export writes an `award.fulfillment_exported` audit event recording row count and the options used, never the data. CSV cells that start with `=`, `+`, `-`, `@`, tab or CR are prefixed with `'` so spreadsheets do not execute them.
