# Stage, Policy, Gate and Advancement Model

## Stage graph
Acyclic graph; deterministic validation; branches/merges; stage-specific participant/team/project rules. Templates provide defaults, not semantics.

## Advancement strategies
Core registry includes manual, everyone, top-N, threshold, percentile, top-N-per-track, pass/fail and external-result/API strategies. Decisions are explicit/audited.

## Team lifecycle
Stages may be individual-only, team-formation, team-locked or otherwise constrained. Stable user/project identity survives transitions.

## Policy AST
Safe typed JSON/AST with bounded depth/operators and explicit facts. No eval/JS/Python/SQL. Unknown facts/operators fail closed for protected actions.

## Temporal gates
Open/close windows are distinct from stages. Server time is authoritative. DST/user display is presentation only; persisted canonical timestamps are UTC.

## Scoped exceptions
ExceptionGrant names subject, action/gate, scope, expiry/reason/granter. It cannot widen unrelated permissions.

## Explanations
Core returns decision evidence suitable for simple organizer/user explanations. Stretch upgrades this to a full policy debugger/trace UI.
