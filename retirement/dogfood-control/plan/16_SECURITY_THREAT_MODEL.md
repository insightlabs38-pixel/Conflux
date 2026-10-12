# Security and Threat Model

## Trust boundaries
Browser/public Internet (during real deployment), Caddy/app, DB, worker queue, object storage, webhook destinations, API credentials/invite tokens.

## Critical threats
- event/workspace RBAC bypass and IDOR
- judge peer-score leakage
- deadline bypass/race
- privilege/token escalation
- malicious uploads/path/content-type tricks
- webhook SSRF/signature/replay issues
- community-vote Sybil/ballot stuffing/duplicate identities
- organizer/judge collusion evidence gaps
- private submission/artifact leakage
- invite reset/token replay
- cross-event cache key/data leakage

## Controls
Server-side authorization, event scoping, DB constraints, short-lived/scoped tokens, bounded uploads, safe content handling, rate limiting, idempotency, secure defaults, audit evidence, webhook allow/deny policy and signing.

## Verification ownership
Bulk verification lanes (Freebuff/Luna) run broad RBAC permutations, malformed HTTP, property/fuzz and abuse matrices continuously. Claude/Sol review large security gates, architecture invariants and weird/high-severity findings.
