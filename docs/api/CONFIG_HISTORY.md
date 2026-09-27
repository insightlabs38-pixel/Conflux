# Configuration history contract

New organizer mutations to event settings, stages, policies, and published rubrics record the changed fields in the existing workspace audit event, within the same transaction as the mutation. Each field change carries its before and after value. A new event-scoped, organizer-only history endpoint reads these audit entries newest first and shows the actor, time, resource, action, and field changes. The UI renders structured values as JSON so policy ASTs and rubric criteria remain inspectable.

Earlier audit rows contain action names but no before/after values. The endpoint must never invent historical values for them. It omits rows without captured changes. Audit entries keep their existing public IDs and permissions; there is no parallel history store or replay mechanism. Deletes record the removed fields, and published rubric versions remain immutable.
