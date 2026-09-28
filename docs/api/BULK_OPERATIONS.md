# Bulk organizer operations

POST `/api/v1/workspaces/{workspace}/events/{event}/operations/bulk/` as an
organizer or administrator. Bearer credentials use the existing workspace
scope and role rules. Targets must belong to the event; archived events reject
both preview and apply.

Send `{"operations": [...]}` to preview. Operations run in order, including
their normal validation, in a rolled-back transaction. The response contains
`effects`, `preview_token` and `expires_in` (600 seconds). No domain, audit,
outbox or inbox records survive a preview. PostgreSQL sequences may advance.

Review the effects, then resend exactly the same operations with the returned
`preview_token`. Apply revalidates and compares exact effects; changed effects,
tampering, expiration, or another actor/event/request produce HTTP 409.
Unavailable or invalid targets produce HTTP 400. Every action and the overall
batch are audited in the same transaction. Any failure rolls back the whole
batch. Reusing an applied token during its validity returns the saved result
without repeating assignments, advancement, extensions or messages. A fresh
preview represents a new intent and can deliberately repeat work.

| Action    | Required fields                    | Behavior                                                                                                                       |
| --------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `assign`  | `plan`, `coverage`                 | Freeze the existing heuristic assignment; expose exact pairs and coverage/conflict/connectivity evidence.                      |
| `advance` | `stage`, `to_stage`, `entries`     | Advance selected active entry UUIDs through an existing transition, preserving participation mode checks.                      |
| `extend`  | `gates`, `seconds`                 | Add positive seconds to bounded temporal gates; expose before/after schedule changes.                                          |
| `move`    | `projects`, `track`                | Move projects to an event track; expose prior and destination track UUIDs.                                                     |
| `send`    | `subject`, `body`, `audience_kind` | Resolve the live audience and create durable inbox delivery; optional `audience_params` uses the existing audience parameters. |

Limits: 20 operations, 100 explicit targets per operation, 1,000 aggregate
assignment pairs/advanced entries/gates/projects/recipients. Assignment matrix
size (candidates × judges) and each dimension must also be at most 1,000.
Coverage is 1–100; extensions are 1 second–366 days. A plan can be assigned once
per batch. Duplicate target UUIDs and unknown/irrelevant fields are rejected.

Bulk send uses the inbox only; use the existing message API for best-effort
email. There is no new bulk editor; this additive API is available through the
generated SDKs and the API explorer. The event and selected records are locked
on PostgreSQL; normal domain uniqueness constraints remain authoritative.
