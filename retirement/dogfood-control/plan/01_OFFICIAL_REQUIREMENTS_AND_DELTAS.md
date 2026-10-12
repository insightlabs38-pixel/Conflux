# Official Requirements and Final Spec Delta

## Tier ladder

### T1 Core acceptance
- authentication and sessions
- visitor/participant/judge/organizer/admin role model
- events with configurable dates, tracks, prizes
- team formation by invite
- draft/edit submission until deadline
- server-enforced deadline
- public searchable/filterable gallery

### T2 Judging
- judge invitation/assignment
- configurable weighted rubric
- backend role isolation; judges cannot read peer scores
- live progress dashboard
- documented cross-judge normalization
- CSV export

### T3 Public
- configurable community-voting identity modes
- comments
- hidden results during voting
- randomized ballot ordering
- rate limits, duplicate detection, readable audit

### T4 Stretch tier
- REST API + webhooks
- certificates/records
- signed publicly verifiable judge participation records
- embeddable gallery
- bulk import/export

## Score

- Tier Completion & Correctness: 40%
- Judging Integrity: 25%
- Adoptability & Operability: 20%
- Code Quality & Innovation: 15%

Correctness outranks breadth. Core is therefore protected by permanent gates while expansion continues in parallel.

## Bonus correction from the pre-spec pack

The old plan modeled bonuses as +5/+3 score additions. The released spec says they **do not change the 0–5 score**. They break ties and determine the Best Judging Engine prize.

New classification:
- Normalization Proof — Core output.
- API First — Core output.
- Threat Model — Core output.
- Pairwise/Bradley–Terry — Stretch #1.

## Checker-specific findings

The official checker issues seven requests and exercises only T1/T2 behavior. It does not execute browser JavaScript when checking gallery content. Therefore the configured gallery route must return at least one fixture project title in the raw HTTP response body.

The released checker contains no T3/T4 assertions. Its tier-verification loop only considers tiers for which checks exist, so a T3/T4 claim cannot be mechanically verified by this exact script. Treat T3/T4 as internally proven/manual-judging surfaces unless the organizer clarifies or publishes a replacement checker.

## Repository deliverables

The final public repository must provide the exact expected root artifacts (`.dogfood.toml`, `acceptance-report.txt`, `docker-compose.yml`, README, ARCHITECTURE, DATA-MODEL, JUDGING, OSI license, `src/`, `tests/`). The post-kickoff repository layout is designed around those names.
