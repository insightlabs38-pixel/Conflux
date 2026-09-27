# Data model

Core records are scoped to a Workspace and Event. Membership grants a user a
workspace role. Events own stages, entries, projects, submission versions,
forms, artifacts, evaluation plans, ballots, normalization runs, awards, and
publication state. Policy and temporal gates control when mutations are
allowed; audit and outbox records preserve their effects.

Public IDs are the API boundary. Database primary keys remain internal. The
[canonical archive](docs/architecture/CANONICAL_ARCHIVE.md) describes portable
event configuration and its explicit exclusions; [Judging](JUDGING.md)
describes score and normalization evidence.
