# Configuration history contract

New organizer mutations to event settings, stages, policies, and published rubrics record the changed fields in the existing workspace audit event, within the same transaction as the mutation. Each field change carries its before and after value. A new event-scoped, organizer-only history endpoint reads these audit entries newest first and shows the actor, time, resource, action, and field changes. The UI renders structured values as JSON so policy ASTs and rubric criteria remain inspectable.

Earlier audit rows contain action names but no before/after values. The endpoint must never invent historical values for them. It omits rows without captured changes. Audit entries keep their existing public IDs and permissions; there is no parallel history store or replay mechanism. Deletes record the removed fields, and published rubric versions remain immutable.

## Restore configuration

Organizer/admin `POST /api/v1/audit/{workspace}/events/{event}/config-history/{entry}/restore/` restores the captured **before** values for an update or restore entry. Only that entry's fields change; intervening edits to those fields are overwritten. The history panel shows those values and asks for confirmation. Stage, temporal gate, policy, event, track, and prize edits use current edit validation and event-scoped references. Archived events, deleted targets, unsupported entries, missing snapshots, identity fields, and invalid current-state combinations fail closed. The original audit entry is preserved; a new atomic mutation records `restored_from`, the resulting diff, and an outbox event.

Policy `PATCH .../events/{event}/policies/{policy}/` supports name/AST or preset edits and captures their before/after values. History predating captured diffs cannot be restored.

Published form and rubric snapshots remain immutable. These organizer/admin endpoints copy the selected snapshot into the current draft; publish through the existing endpoint to create a new live version:

- `POST /api/v1/workspaces/{workspace}/events/{event}/forms/{form}/versions/{version}/restore/`
- `POST /api/v1/workspaces/{workspace}/events/{event}/stages/{stage}/evaluation-plans/{plan}/rubric-versions/{version}/restore/`

Version IDs must belong to the specified form/plan. Restore does not change responses, ballots, assignments, published results, or the current live snapshot. Form versions expose a Restore to draft control; rubric restore is available through the API using a version ID from published rubric history. Reload an open configuration editor after an immediate history restore.
