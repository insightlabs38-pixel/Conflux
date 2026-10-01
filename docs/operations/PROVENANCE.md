# Provenance (AUDIT_PROVENANCE)

An audit row says that something happened. A provenance **envelope** says what the result was made from, by whom and under which rules, so a person can trace it later. Code: `core/provenance.py`; it lives where results already live, in `AuditEvent.metadata["provenance"]` and in a job's `result`, with no new table and no new endpoint. Web: `lib/provenance.ts` and `components/ProvenanceView.tsx`. Adopters: the archive export job (job result and its `job.succeeded` audit row) and configuration restore (`*.restored` audit rows, shown in Operations > Configuration history).

## The envelope

```
{version: 1, by: {public_id, username} | null, at: ISO time,
 source: {kind, id},
 inputs: {digest: sha256 | null, refs: [{kind, id, label?}]},
 rules: {name, version} | null,
 output: {name, bytes, sha256} | null,
 summary: "One sentence.",
 changes: {total, added, removed, changed, moved} | null}
```

- `by` is the person (or `null` for the system); `at` the time; `source` is the thing that produced the result (`archive_export` with the job id, `config_history` with the change that was restored).
- `inputs.refs` name what was used, by kind and id and a short label, never content. `inputs.digest` is the SHA-256 of the canonical JSON of an `inputs` value **only when the caller passes one** (a re-checkable parameter set); most results carry references only.
- `rules` is the named, versioned logic that produced it (`event_archive` at the archive format version, `restore_before_values` at 1).
- `output` is the checkable fact of a file someone downloads: name, size and SHA-256 of the exact bytes. This is the one digest the platform keeps by default, because it enables a real check later: `sha256sum file` against the record, or the "Check a downloaded file" control, which hashes the file in the browser and uploads nothing.
- `changes` counts what a restore changed, read from `core.version_diff` ([VERSION_DIFF.md](VERSION_DIFF.md)).

## What it is not

It adds **no signature layer**: nothing here proves who wrote an audit row and it never claims to (a signed archive keeps its own signature). It stores no content, no secrets and no free text beyond the one summary sentence (300 characters; 20 references; labels 120). Canonical JSON is sorted keys, compact separators, UTF-8 and no NaN, so a digest is the same on every machine.

## Using it

```python
from core import provenance
made = provenance.envelope(
    by=actor, source_kind="my_export", source_id=job.public_id, summary="Weekly report.",
    refs=[{"kind": "event", "id": event.public_id, "label": event.name}],
    rules=("weekly_report", 3), output=provenance.describe_output(name, body))
record_mutation(..., metadata=provenance.attach({"kind": "weekly"}, made))   # or return it in a job result
provenance.verify_output(made, downloaded_bytes)   # True when the file is exactly the recorded one
provenance.problems(read_back)                     # [] when an envelope read from storage is well formed
```

A job handler that returns `{"provenance": envelope, ...}` has it kept on the job and copied onto the `job.succeeded` audit row; a kind that returns none is unchanged.

## Compatibility

Additive and stateless: no table, no migration. Existing audit rows have no envelope and keep working (`provenance` is `null` in the configuration history, which now returns it per entry). Restore, export, archive digests and signed archives behave as before.

## Verification

`tests/integration/test_provenance.py`: canonical JSON and a known digest vector, key-order independence, bounds, no content stored, the system actor, `verify_output` and `problems`, an independent feature recording its own audit row, the export (the downloaded file equals the digest, the audit row carries the same envelope, a signed export is described by the bytes that were downloaded, a kind without provenance is unchanged) and a restore (source, rules, refs and change counts). The browser spec runs a real export and restore at 390 and 1440 and checks a downloaded file, and an altered one, against the record.
