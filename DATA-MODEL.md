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

`accounts.Session` stores `token_digest` (keyed SHA-256) and never the raw
cookie value; API credentials store `token_digest` likewise. `Event` and
`Workspace` public IDs are ordinary UUIDs everywhere except generated demo
scenarios, where they are derived from the scenario and seed so links survive a
reset (`integrations.demo_scenarios.demo_public_ids`); primary keys are still
never exposed.
