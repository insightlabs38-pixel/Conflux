# Custom taxonomies

Organizer-defined classification labels, workspace-scoped and applied per event to **projects**, **people** (workspace members) or the **event** itself.

- `GET/POST /workspaces/<w>/taxonomies/`, `GET/PATCH/DELETE .../taxonomies/<t>/` — `key` and `applies_to` are immutable; `allows_multiple` cannot be turned off while a subject holds several terms; a term still assigned cannot be removed; a taxonomy with assignments cannot be deleted. Bounds: 20 taxonomies per workspace, 50 terms each.
- `GET/PUT /workspaces/<w>/events/<e>/taxonomy-assignments/` — PUT replaces one subject's terms in one taxonomy (`{taxonomy, subject: {type, id?}, terms: [keys]}`); GET filters by `taxonomy`, `term`, `subject_type`. Archived events are frozen.

Non-authoritative by design: no eligibility, authorization, scoring, award, result or public-page code reads a label, and labels never render publicly. Organizer-only; every change is audited with before/after. Person labels are personal data: they are included in per-subject export and erasure (`docs/operations/RETENTION_PRIVACY.md`). Assignments are not part of v2 final archives (taxonomies are workspace-level).
