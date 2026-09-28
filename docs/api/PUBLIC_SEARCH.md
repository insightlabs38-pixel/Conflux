# Advanced public search

`GET /api/v1/events/{event}/search/` returns `count`, `next_offset` and up to
50 `items`. Offset defaults to zero. Only projects with finalized submissions
in a public, opened (or closed/archived) event are searchable. Filters combine
with AND:

- `q`: at most 200 characters and 10 terms, matching public project name and
  description. PostgreSQL uses native plain full-text search with the `simple`
  dictionary (all tokens required, no stemming). SQLite development uses
  case-insensitive substring matching for each whitespace-separated term.
- `tags`: repeated ASCII slug values, at most 10, normalized to lowercase;
  every supplied tag must match.
- `artifact_kind`: a real artifact kind; only ready, public artifacts match.
  Private, pending, uploaded and rejected artifacts cannot affect this filter
  or the returned artifact-kind list. Artifact contents/titles are not indexed.
- `stage`, `track`: UUID associations; a stage match requires a finalized
  submission in that same stage. Unmatched associations return no results.
- `offset`: integer from zero through 1,000,000. Results sort by project name
  then public ID, with one result per project.

Public text is plain text and must be escaped when displayed. Responses contain
public tags, artifact kinds and existing gallery metadata, without storage keys,
private artifacts, participant identities or draft answer fields.

Project members manage at most 10 public tags with GET/PUT on
`/api/v1/workspaces/{workspace}/events/{event}/projects/{project}/tags/`:
`{"tags":["education","ai"]}`. Replacement is transactional and audited;
archived events reject changes. Tags are public metadata when the project is
publicly listed, not an extension to private submission answers.

Workspace members save private views with POST to the event's
`saved-searches/` path: `{"name":"AI repos","filters":{"tags":["ai"],"artifact_kind":"repository"}}`.
GET lists the caller's views (maximum 50). GET `{view}/` reruns the saved filters
against current public data, accepting only `offset`; DELETE removes that view.
Names must be unique per caller/event. Another member cannot read, run or delete
the view, and making the event private prevents its execution. No results are
snapshotted. Change a view by deleting and saving it again.

The additive API, generated SDKs and API explorer expose advanced search; the
existing gallery layout and its name search remain. PostgreSQL currently computes
search vectors at query time; there is no external search service, relevance
ranking, language-specific stemming or full-text index of uploaded artifacts.
