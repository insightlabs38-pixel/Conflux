# CSV project migration adapter

The adapter converts an external project CSV plus a Conflux `config` archive into a `full` archive. An organizer reviews that file, then imports it through the existing workspace archive endpoint. This creates a new draft event and runs the canonical archive's transaction and model validation. The adapter never creates users, teams, submission versions, judging evidence, or winners.

The mapping file names CSV columns for `name` and `created_by_username`, plus optional `description`, `track`, and `external_id`. Creator usernames must already exist in the target deployment. Track names must exactly match one track in the config archive; blank means no track. External IDs identify rows within the CSV and become deterministic archive refs. If omitted, refs derive from row position and content. Duplicate IDs, unknown tracks, empty required values, malformed CSV, and non-config input fail before output is written.

Conversion does not change the source CSV or archive and will not overwrite an output file. It is safe to preview the generated JSON before using `POST /api/v1/workspaces/{workspace}/archive/import/` with `{name, slug, archive}`. The importer is responsible for final user resolution and event creation.
