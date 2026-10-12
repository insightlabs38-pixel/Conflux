# Acceptance Checker Analysis

## Exact behavior
The stdlib checker reads `.dogfood.toml`, loads `fixtures.json`, then performs seven HTTP checks:
1. unauthenticated gallery returns 200;
2. raw gallery body contains a known fixture project title;
3. participant POST to the configured submission route is rejected 4xx because fixture event is closed;
4. judge A can read own scores;
5. judge B is denied 401/403 at the configured peer-score URL;
6. participant is denied judge-score URL;
7. organizer CSV export returns 200 with a comma in the first line.

## Consequences
- Do not require browser JS for check #2.
- Seed deterministic acceptance identities/tokens and routes; checker never logs in.
- Deadline rejection must arise from real server semantics, not intentionally malformed JSON.
- Backend/API isolation is mandatory.

## T3/T4 inconsistency
The released script contains no T3/T4 checks. Its `verified` list only includes tiers with checks and the final ladder stops after the first unverified tier. Ask organizer whether T3/T4 are intentionally manual or whether a revised checker is expected. Do not block implementation; internally prove T3/T4 regardless.
