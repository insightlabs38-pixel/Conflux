# Reference extensions

After Django setup, import `extensions.examples`. These maintained examples
cover the six families currently supported by [SDK v1](../docs/architecture/EXTENSION_SDK.md).
Importing them does not install strategies or page blocks. They are deployment
source code, never organizer-supplied code.

| Family             | Reference                                                             | Use and boundary                                                                                                                                                                                                                                                                                                      |
| ------------------ | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Artifact validator | `inspect_pdf(artifact, storage)`                                      | Additional PDF-only inspection after canonical metadata/content checks. This is a preflight, not persisted readiness evidence. Never register it as a replacement validator: it delegates to `inspect_artifact`. New kinds still need the complete domain integration described by the SDK.                           |
| Advancement        | `register_scored_threshold()`                                         | Explicitly registers `example_scored_threshold`; duplicate registration fails. Includes only finite, present scores at or above `minimum`, retaining `(subject_type, subject_id)`. Invoke through `advance_stage` for audited transitions.                                                                            |
| Assignment         | `ordered_assignment(plan, coverage=3)`                                | Positive integer coverage; canonical conflict/connectivity computation with stable judge/project output order. Returns pairings without writes. Activation remains owned by the domain assignment services.                                                                                                           |
| Page block         | `NOTICE_BLOCK`                                                        | Plain notice with bounded required text and integer priority, using the actual supported schema subset. In tests, explicitly install `BLOCK_TYPES["example_notice"] = NOTICE_BLOCK` and call `clean_config`. Persisted kinds also require model/migration/UI integration; render message as escaped text, never HTML. |
| Archive converter  | [`scripts/convert_project_csv.py`](../scripts/convert_project_csv.py) | Existing maintained `convert(archive, csv_text, mapping)` example maps project CSV into canonical v1 without database writes. Unknown columns/tracks, duplicate IDs and unsupported versions fail.                                                                                                                    |
| Import/export      | `export_configuration`, `import_private_copy`                         | Configuration-only export; canonical import in an atomic transaction with new identities and private draft visibility. Caller must authorize the workspace and record mutation audit. Use `preview_archive_import` before committing a copy.                                                                          |

Run the converter from the repository root:

```sh
python scripts/convert_project_csv.py --archive config.json --csv projects.csv \
  --mapping mapping.json --output converted.json
```

For columns `Title,Owner`, `mapping.json` is
`{"name":"Title","created_by_username":"Owner"}`. Creators must already exist
when importing the converted archive; conversion does not create accounts.

The larger frozen architecture family list describes domain boundaries, not
additional SDK registrations. This batch adds no runtime loader, new persisted
kind or public renderer. Preserve versioned archive semantics and the SDK's
domain validation, authorization and audit requirements when adapting examples.

Verification: `tests/integration/test_extension_examples.py`,
`test_extension_sdk.py`, `test_csv_migration_adapter.py` and the affected artifact,
assignment, advancement and canonical archive suites. No recorded surface changes.
