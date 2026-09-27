# Canonical archive (v1)

A deterministic JSON export of one event's organizer-authored configuration,
and a validated importer that rebuilds it as a brand-new event. Lets an
organizer clone an event's setup (within a workspace or into another one) or
keep an offline backup of it.

`GET  /api/v1/workspaces/<workspace>/events/<event>/archive/?mode=config|full`
`POST /api/v1/workspaces/<workspace>/archive/import/` — body `{name, slug, archive}`

Both require the organizer/admin role on the workspace. Import always creates
a **new** event — it never overwrites an existing one — starting as an
unpublished `draft`, with the `name`/`slug` the caller supplies (never the
source event's, so cloning within one workspace can't collide on slug).

## `format_version`

The archive's top-level `format_version` (currently `1`) is the compatibility
contract. A build only ever reads the versions it was written to understand:
importing a document with any other `format_version` is an explicit, named
error — never a best-effort reinterpretation. Raising the number is reserved
for a change that isn't purely additive (a field's meaning changes, a
required field is added, a section is restructured). Purely additive changes
(a new optional field or section) do not require a version bump; a reader
must already treat an unknown field as absent.

## References are local and stable, not database identities

Every archived row carries a `ref` (its `public_id` at export time), and
every cross-reference in the document (`track_ref`, `stage_ref`,
`policy_ref`, `from_ref`/`to_ref`, `eligibility_track_ref`) points at one of
those. Import never reuses a source-side `public_id` or primary key for the
rows it creates — it builds a fresh ref → new-row map as it goes and
rewrites every reference through it. This is what makes the document
portable across databases and makes round-tripping (export → import →
export) produce a structurally identical archive.

## What v1 covers

Two modes, `config` (default) and `full`:

- `config`: `event`, `tracks`, `base_prizes`, `stages`, `stage_transitions`,
  `forms` (definitions and their published versions), `policies`,
  `temporal_gates`, `policy_bindings`, `awards` (with their prize
  components). An award using evaluation-sourced selection is exported by
  its evaluation plan's *name*, not a portable definition of the plan
  itself — importing such an award requires a plan with that exact name to
  already exist in the target event, and fails explicitly (ambiguous or
  missing) otherwise.
- `full`: everything in `config`, plus `projects` (name, description, track,
  and the creating user's *username*). Import resolves that username against
  users that already exist in the target deployment and fails explicitly if
  none matches — it never creates a shadow account, which would invent new
  identity semantics outside the frozen architecture.

Every imported row runs through its own model's `full_clean()`, so ordinary
domain invariants (a track must belong to the award's event, a cash prize
needs an amount and currency, the stage graph must stay acyclic, ...) apply
exactly as they would to organizer-authored input. Import is transactional:
a validation failure partway through leaves nothing behind.

## What v1 does not cover (by design, not oversight)

Deliberately out of scope for both modes, to keep this version's contract
honest rather than a shaky partial attempt at deeper fidelity:

- Participant-facing operational history: `Submission`/`SubmissionVersion`,
  `StageEntry` (who is currently where in the stage graph), `FormResponse`/
  `FormAnswer`.
- Anything already decided about who won what: `AwardWinner`,
  `PrizeFulfillment`.
- Evaluation activity (scores, reviews) and community activity (votes,
  comments, fraud-review state).
- `Team` and `ProjectMembership` — `full` mode's `projects` carry a creator
  username only, with no team assignment.
- `ExceptionGrant` (a one-off per-subject override) and the audit/webhook
  event log.
- Any secret material — a re-imported webhook subscription, if this document
  is ever extended to include integrations config, would need its signing
  secret reissued, never carried in the archive itself.

A future version that adds any of these does so as an explicit, documented
`format_version` bump (or a clearly-labeled optional section, if additive),
not a silent change to what `config`/`full` already mean.
