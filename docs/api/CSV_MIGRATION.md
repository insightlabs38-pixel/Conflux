# CSV project migration adapter

The adapter converts an external project CSV plus a Conflux `config` archive into a `full` archive. An organizer reviews that file, then imports it through the existing workspace archive endpoint. This creates a new draft event and runs the canonical archive's transaction and model validation. The adapter never creates users, teams, submission versions, judging evidence, or winners.

The mapping file names CSV columns for `name` and `created_by_username`, plus optional `description`, `track`, and `external_id`. Creator usernames must already exist in the target deployment. Track names must exactly match one track in the config archive; blank means no track. External IDs identify rows within the CSV and become deterministic archive refs. If omitted, refs derive from row position and content. Duplicate IDs, unknown tracks, empty required values, malformed CSV, and non-config input fail before output is written.

Conversion does not change the source CSV or archive and will not overwrite an output file. It is safe to preview the generated JSON before using `POST /api/v1/workspaces/{workspace}/archive/import/` with `{name, slug, archive}`. The importer is responsible for final user resolution and event creation.

Export the source event's config archive from `GET /api/v1/workspaces/{workspace}/events/{event}/archive/`. A mapping for columns named `Project Title`, `Summary`, `Category`, `Owner Username`, and `Submission ID` is:

```json
{
  "name": "Project Title",
  "description": "Summary",
  "track": "Category",
  "created_by_username": "Owner Username",
  "external_id": "Submission ID"
}
```

Run:

```sh
python scripts/convert_project_csv.py --archive config.json --csv projects.csv --mapping mapping.json --output full.json
```

The command accepts UTF-8 CSV (including a BOM), up to 5 MB and 10,000 project rows. Every mapped column must exist. The converter's output is the value for the import request's `archive` field; the request's `name` and `slug` name the new event. See [the canonical archive contract](../architecture/CANONICAL_ARCHIVE.md) for the import endpoint and its identity rules.
