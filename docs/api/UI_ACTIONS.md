# UI action coverage

The web client sends persisted actions through the same `/api/v1/` routes available to external clients. Editing a form, rubric, stage graph, or page block may use local draft state; publish/save actions call the API, where validation and authorization run.

| UI feature                    | API route family                                          | Persisted actions                                             |
| ----------------------------- | --------------------------------------------------------- | ------------------------------------------------------------- |
| Workspace and event dashboard | `workspaces/`, `workspaces/{workspace}/events/`           | Create and update workspace, event, tracks, prizes            |
| Team workspace                | `workspaces/{workspace}/participant-events/`, team routes | Join, invite, redeem, leave, transfer                         |
| Project and submissions       | project, submission, artifact routes                      | Save responses, upload, validate, finalize                    |
| Forms and page builder        | form and page block routes                                | Publish versions and update blocks                            |
| Stages and policies           | stage and policy routes                                   | Update graph, bindings, gates, grants                         |
| Judging                       | evaluation plan, ballot, assignment, result routes        | Publish rubrics, assign judges, save ballots, publish results |
| Community voting              | voting and comment routes                                 | Vote, request link, comment, moderate, publish                |
| Voting review                 | voting plan abuse and audit routes                        | Resolve signals and read audit evidence                       |

Direct object storage upload follows an API-issued upload intent and API completion step. The browser does not decide readiness, eligibility, ballot validity, or result publication.
