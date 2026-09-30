# Event base experience (PD-F001-B01)

The day-one path is small: name an event, pick a format, answer a few questions. Everything else is derived from the format, stays collapsed until needed, and is queryable. Contract and decisions: [spec 001](../product-depth-v3/specs/001-base-experience-must-remain-smaller-than-the-platform.md); proofs: [matrix](../verification/PD-F001-B01/MATRIX.md).

## For organizers

- **Create event** (Setup): a name, a format (hackathon, science fair, grant program, demo day, pitch competition, or no format), and optionally start date and time zone, registration mode, team size range and whether the event page is public. The form shows what the format starts with and what is still yours to add (judges, prize amounts, dates). The web address is derived from the name unless you open **Web address**.
- A format gives real values: stages and flow, end date from the format's duration, a registration row, evidence requirements, a **published** rubric, tracks only when the format has them. Nothing is a placeholder, so the event is complete except for what only you know.
- **Features** turns optional modules on (eligibility review, on-site, integrations, community voting, mentorship, public page). A module that is off has no navigation entry or tab; opening its link explains and offers to turn it on. A module with content cannot be turned off. Deliberation is always on.
- **Readiness** (overview and Setup) is the one list of what is missing before launch, each item with a link to fix it. It is advisory: opening an event is never blocked, and the unresolved items are recorded when you open.
- **Stages** shows whether the stages and judging still follow the format. Edit anything; only what changed is listed as custom, nothing is reset, and changing it back restores "Follows the format".
- **Defaults and overrides** (advanced) lists every setting with its value, where it comes from (format, changed, default, derived), what it started as and why it is locked if it is.

## For automation

All endpoints are organizer/admin only, workspace-scoped and in the OpenAPI document and SDKs.

| Need                                                      | Call                                                                                                                                                                                        |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Formats                                                   | `GET /workspaces/{w}/event-templates/library/`                                                                                                                                              |
| Create from a format                                      | `POST /workspaces/{w}/event-templates/library/{key}/instantiate/` with `name`; optional `slug`, `is_public`, `starts_at`, `timezone`, `registration_mode`, `min_team_size`, `max_team_size` |
| Create blank                                              | `POST /workspaces/{w}/events/` with `name`; `slug` is optional                                                                                                                              |
| Modules                                                   | `GET /workspaces/{w}/modules/?event={e}`, `PATCH /workspaces/{w}/events/{e}/modules/{key}/` with `{"enabled": bool}`                                                                        |
| Readiness                                                 | `GET /workspaces/{w}/events/{e}/readiness/`                                                                                                                                                 |
| Every setting, baseline, source, lock and how to write it | `GET /workspaces/{w}/events/{e}/configuration/?module=&tier=&source=&key=`                                                                                                                  |
| Preset or custom                                          | `GET /workspaces/{w}/events/{e}/workflow/` (`source`: `preset`, `custom`, `none`; named `differences`)                                                                                      |

The address is derived as the slugified name, suffixed `-2`, `-3` on a clash; a chosen address that is taken is a 400 on `slug`. Each configuration entry names the existing endpoint, field and body kind that changes it, so nothing is reverse-engineered from the UI.

## For operators and developers

- **Audit.** Creation records `event_template.library_instantiated` with the preset version; its domain event payload (webhooks) adds `slug_derived` and `chosen`. Module changes record `event.module_enabled|disabled`; registration changes record `registration.settings_updated` with before/after (previously unaudited).
- **Formats** live only in `eventconfig/presets.py`; raise a preset's `version` to change it. Events record the `(key, version)` they started from (`EventProfile`), which is the baseline for "Changed" and for the workflow comparison. Readiness rules live only in `eventconfig/readiness.py`; the older launch checklist and dashboard checks are projections of them.
- **Compatibility.** Additive tables only (`EventProfile`, `EventModuleSetting`); no backfill. Events without a profile behave as before: modules derive from content, configuration has no baseline, workflow is `none`, and reading creates nothing. `slug` became optional on event creation and library instantiation; clients that send it are unaffected. Organizer navigation now hides optional modules that are neither enabled nor in use, so scripted browser flows that open those views must enable the module first. New tables are not in the event archive (recorded in the spec); a cloned event derives module use from its cloned rows.
- **Not here.** Weekend, online and internal formats, consequence previews, participant/judge navigation, and multi-instance settings in the registry (judging, stage, award) are later work.
