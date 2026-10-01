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

## Adding an action (extension seam)

The five actions above are registered in `communications/bulk.py` like any other. An app adds its own without editing the planner: `bulk.register_action(BulkAction(key, label, handler, params=SomeSerializer))`. `handler(event, actor, op)` does the domain work with its normal validation and audit, runs inside the planner's transaction (DB only, never external delivery) and returns `(effect, impact)`: a JSON description of exactly what changed and how many records it touched. A registered action is sent as `{"action": "<key>", "params": {...}}` and its `params` are validated by its serializer; the built-in actions keep their flat fields (a built-in given `params`, or a registered action given flat fields, is refused). Preview, the signed token, drift detection, atomic apply, per-action audit, receipts, replay by token and every limit apply to a registered action unchanged. The OpenAPI `action` enum documents the five built-ins; registered keys are accepted at runtime.

## Receipts

`GET .../operations/bulk/receipts/` lists what was applied in the event, newest first (`public_id`, `actor`, `created_at`, `actions`; `limit` 1-100 and `offset`, total in `X-Total-Count`), and `GET .../operations/bulk/receipts/{id}/` adds the exact `effects`. Organizer/admin only, scoped to the event.

## Rollback and compensation

Rollback is whole-batch and automatic: a failure at any step, a stale preview or an audit failure changes nothing. **Compensation after a successful apply is not generic**: undoing an applied batch is a new, deliberate operation using the domain's own inverse (move the projects back, extend the gates back), previewed and receipted like any other. The planner does not offer a one-click undo.

## In the web

Select projects in the Projects list (Participants > Projects), pick a track and **Preview move**. The dialog states the exact effects ("Move 3 projects to Hardware (1 from no track, 2 from Software)"), applies on an explicit button, shows the receipt, asks for a new preview when the old one is stale, and on a lost connection offers a retry of the same preview (a replay never applies twice). The reusable pieces are `lib/bulk.ts` and `components/BulkPlanner.tsx`.

## Approvals

When an event has turned on an approval gate for an action (today: `send`, see [APPROVALS.md](../operations/APPROVALS.md)), a preview lists it under `approvals` and applying without an approval answers **409 `approval_required`** with the pending request; nothing is applied. After another person approves it, send the same apply again with the same preview token. This 409 is not a stale preview.
