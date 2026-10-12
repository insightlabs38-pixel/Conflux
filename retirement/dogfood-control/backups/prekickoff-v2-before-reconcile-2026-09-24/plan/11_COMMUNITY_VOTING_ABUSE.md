# Community Voting, Comments and Abuse Controls

## Modes
Support authenticated, email-gated/token-link and organizer-configured participation. Identity mode is explicit per voting plan.

## Window/privacy
Voting opens/closes server-side. Results/aggregate counts remain hidden according to policy until publication.

## Ballots
Candidate ordering is randomized with auditable/deterministic seed semantics where appropriate; no UI-only hiding.

## Anti-abuse
Rate limits, duplicate-vote constraints/signals, token replay prevention, suspicious identity/IP/device-ish evidence only where privacy-appropriate, and readable AuditEvents. Avoid opaque fraud scores.

## Fraud review
Core includes organizer-facing signals and evidence rather than storing abuse data nobody can inspect.

## Comments
Event-configurable permissions/moderation; comments are audit/moderation subjects and cannot expose private judging data.
