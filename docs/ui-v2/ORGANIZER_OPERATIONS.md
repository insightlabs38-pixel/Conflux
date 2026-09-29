# Organizer operations

**Overview** derives a "Needs action" list and five metric cards (registrations,
eligibility workload, judging progress, results/publication, on-site readiness) from
existing read endpoints. Each card loads independently and shows its own error/retry;
event dates are shown in UTC.

**Task tabs.** Multi-panel destinations use retained-draft tabs (WorkflowSections):
Participants (Registration / Teams / Mentors), Eligibility (Review queue / Deadline
exceptions), Judging (Rubrics / Workload / Logistics / Community voting), Results
(Deliberation / Publication / Awards), Operations (Operations / Continuations /
Configuration history / Permissions).

**Eligibility** is a filterable queue (per-status counts), selected-row detail with
findings, team responses and organizer decisions, request-changes and decision forms.

**Logistics** adds assignment-health tiles and a simulate-then-apply rebalance using the
existing dropout-simulation and rebalance endpoints (explicit confirmation; a new
assignment version is frozen; submitted ballots keep their pairings).

**Deliberation** shows a four-step progress, evidence tiles (ballots, judges, candidates,
conflicts excluded), a combined finalist table (raw, normalized, disagreement bar, panel
tally, close-call/recommended/also-wins-another-award flags), selection summary with
override-reason warning, and an immutable finalized banner with winner names.

**Publication** shows a pipeline (calculated, approval when required, published) and the
result version derived from correction history. No "scheduled" step exists in the API.

**On-site** has a large check-in desk, progress, searchable/filterable attendance with
touch-size actions, and unchanged layout/auto-assign controls.

Unchanged: RBAC, approval semantics, COI exclusion, normalization, immutability.
