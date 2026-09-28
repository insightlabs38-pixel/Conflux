# Event funnel analytics

GET `/api/v1/workspaces/{workspace}/events/{event}/operations/analytics/` as an
organizer or administrator. This read-only API returns live aggregate metrics,
including for archived events, through the SDKs and API explorer. It does not
expose voter keys, application notes, judge comments or participant identities.

Every reported rate includes `numerator`, `denominator` and `ratio`. An empty
denominator returns `null`; unavailable judging expectations return `completion:
null`. The domains use different units; these rates do not describe one
person-by-person conversion chain.

| Metric                     | Numerator                                                                                | Denominator                         |
| -------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------- |
| Registration approval      | Approved event applications                                                              | All event applications              |
| Approved applicants teamed | Approved applicants in this event's teams                                                | Approved event applications         |
| Team project creation      | Event teams with at least one event project                                              | Event teams                         |
| Projects with submissions  | Distinct event projects with any stage submission                                        | Event projects                      |
| Finalized projects         | Distinct projects currently finalized with a durable receipt in at least one event stage | Event projects                      |
| Rubric completion          | Current rubric's live, applicable judge/project ballots                                  | Currently applicable expected pairs |
| Voting project engagement  | Distinct event projects with an event voting-plan vote                                   | Event projects                      |

Registration counts use event applications rather than workspace memberships.
Team counts distinguish empty teams. Submission metrics also report current
draft/finalized records and immutable historical receipt counts; a reopened
draft's old receipt does not make it currently finalized. Multiple stages,
team members, or votes do not multiply distinct project/team counts.

Judging metrics use current eligible candidates, pool membership and conflicts.
Assigned-subset completion uses the active assignment; all-judges completion
uses the eligible judge/candidate matrix minus conflicts. Calibration ballots,
prior rubrics and inactive assignments do not count as current completion.
Pairwise plans report applicable comparisons and participating judges, with no
invented rubric completion denominator.

The judging section contains at most 50 plans, with `plan_count`, `offset` and
`next_offset`. Request further pages with `plan_offset`; other metrics retain
their event-wide scope. Metrics are live reads across domains, not a quiesced
checkpoint or historical cohort report. Each conversion's population counts
are aggregated together; activity may still change other metrics during the
response. `generated_at` records the end of computation.
