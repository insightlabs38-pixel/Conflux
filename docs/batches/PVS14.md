# PVS14 — Workspace cross-event portfolio
## Result
Participants can see their own history across every event in a workspace; organizers get a filterable, paginated cross-event project list and per-person aggregates, all derived read-only from existing records.
## Changes
- New `portfolio` app (no tables): `me/`, `projects/`, `participants/`, `participants/{user}/`.
- Awards are shown only when published; participants never see other people's projects.
- Fixed-cost queries per page (prefetch/aggregate), bounded pagination and validated filters.
## Verification
- `test_portfolio.py` (14): own-only scope, cross-event, award publication gate, workspace isolation, role gates, filters/pagination, hostile params → 400, constant query count.
- OpenAPI + SDKs regenerated and checked.
## Limitations
- No UI yet (PVS-H03); no result ranks or scores in the portfolio (results stay behind their own publication rules).
## Next
PVS15 (narrowly scoped post-event project continuation/follow-up).
