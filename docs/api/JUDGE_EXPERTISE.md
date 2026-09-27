# Judge expertise profiles

A workspace judge can read or replace their own expertise tags at
`GET/PUT /api/v1/workspaces/{workspace}/my-judge-expertise/`.
An organizer can read or replace a workspace judge's profile at
`GET/PUT /api/v1/workspaces/{workspace}/judge-expertise/{judge}/`.
The PUT body is `{"tags":["ai","hardware"]}`. Up to 20 unique tags are accepted,
each at most 80 characters. Tags are trimmed, case-folded, sorted, and replace the
previous set. An empty list clears the profile.

An expertise tag matches an event track when their full names match after
trimming and case-folding. Matching adds that track to the judge's assignment
fit for every event in the workspace. Explicit track expertise on an event
pool membership remains effective and combines with profile matches.
Matching is a soft assignment preference; it does not override conflicts,
coverage, workload balancing, or event-pool eligibility. Tags that do not
match a track have no assignment effect.
