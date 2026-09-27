# External qualifier import (EXTQ-001/002)

Lets an API credential or organizer report the outcome of a qualifying
round run _outside_ this platform — a partner site, a manual review, an
earlier season — as a direct entry into one of this event's stages.

`POST /api/v1/workspaces/<workspace>/events/<event>/stages/<stage>/external-qualifiers/`
`GET` the same path lists past import receipts for that stage.

Body: `{"entries": [{"external_ref": "<opaque string>", "project": "<uuid, optional>"}]}`.
Reachable by an organizer's browser session or a scoped API credential
(`POST:external-qualifier-import` in its `allowed_actions`) — the same
`CookieSessionAuthentication` class already supports both, so no new
authentication surface exists for this.

Only stages whose `participation_mode` expects a team subject are
supported (`team_formation`/`team_locked`); an individual-mode stage is
rejected explicitly.

## Identity continuity, not a new identity

`external_ref` never becomes a new kind of participant identity. The first
call for a given `external_ref` must supply `project` (an existing
Project's `public_id` in this event); that pairing is recorded once as an
`ExternalQualifierBinding` and every later call for the same `external_ref`
resolves to that same Project without the caller ever needing to learn our
internal id. A call that supplies a _different_ `project` for an
already-bound `external_ref` is rejected outright — the binding is never
silently reassigned.

Each project's team is entered into the target stage via
`StageEntry.objects.enter` directly (not `advance_stage`, which requires an
existing entry in a _from_ stage — external qualifiers by definition have
no local stage history to advance from). A project whose team already
holds an active entry in that stage is left alone: re-running the same
import call twice never creates a duplicate entry.

## Worked example

```
# Round one: the partner site's own id "region-1:team-42" qualifies,
# and we tell it which local project that is.
curl -X POST .../stages/<finals>/external-qualifiers/ \
  -d '{"entries": [{"external_ref": "region-1:team-42", "project": "<project-uuid>"}]}'
# -> 201, entries: [{"external_ref": "region-1:team-42", "project": "<project-uuid>", "advanced": true}]

# Round two: the partner site re-sends its qualifier list. It only ever
# knows its own id, never ours -- and still lands on the same project,
# with no duplicate stage entry.
curl -X POST .../stages/<finals>/external-qualifiers/ \
  -d '{"entries": [{"external_ref": "region-1:team-42"}]}'
# -> 201, entries: [{"external_ref": "region-1:team-42", "project": "<project-uuid>", "advanced": false}]
```

See `tests/integration/test_external_qualifiers.py` for this exact
sequence (and the rejection cases) as a regression test.
