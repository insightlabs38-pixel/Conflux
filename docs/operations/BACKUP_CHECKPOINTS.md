# Verified backup checkpoints

`scripts/backup-checkpoint create backups/<new-name>` creates a quiesced snapshot
of PostgreSQL and the default RustFS raw volume. Run it from the operator host
with Python 3.11+, Docker Compose and the existing `conflux-api:latest` helper
image. Compose project/file environment overrides are respected. The directory
must not exist. This is additive to the Core `scripts/backup`/`scripts/restore`.

Creation stops currently running app/worker/beat/objectstore services, records
every public database table's row count, dumps PostgreSQL, archives the object
volume, then resumes those same services. Stop external writers beforehand;
the tool cannot quiesce SQL clients or another application sharing the volume.
Traffic and direct S3 uploads are unavailable during this maintenance interval.

`manifest.json` records the snapshot interval, checkout revision, PostgreSQL
version, objectstore image digest, file sizes/SHA-256 hashes, table counts and a
digest of object paths/types/modes/content. No credentials are recorded. Preserve
the complete directory privately: database dumps and raw objects contain private
data. Checksums detect corruption; they do not authenticate an untrusted backup.
The checkout revision identifies the operator's checkout, not a deployed-image
attestation. A missing manifest denotes an incomplete backup; retain it for
diagnosis and use a new directory for another attempt.

Run `scripts/backup-checkpoint verify <directory>` anywhere with Python to check
the manifest, hashes, dump header and safe object inventory without contacting
Docker. Keep the directory immutable during verification/restore. Links,
devices, duplicate paths and archive traversal are rejected.

`scripts/backup-checkpoint restore <directory>` replaces the selected Compose
project's database and object volume. Before stopping services it checks integrity,
the PostgreSQL major version, exact objectstore image digest and `pg_restore --list`.
Restore uses an atomic, error-stopping PostgreSQL transaction and then replaces the
object volume. It compares all table counts and the complete object inventory
before resuming the services that were running at invocation. Success emits JSON
with `verified: true`, checkpoint time and restore time; retain that output as
operator evidence. Table counts supplement the dump's checksums, not row-level
content attestations.

Failure after services stop leaves them stopped. Resolve the reported error and
retry the restore while only the database is running. A successful retry preserves
the stopped state; explicitly start app/worker/beat/objectstore after inspecting
the verification output. Failed database and object-volume restore operations
cannot roll back together. Use a disposable project for rehearsal first.

`scripts/backup-checkpoint-smoke` creates its own isolated, egress-free Compose
project, seeds a real database value and object-volume file, creates/verifies a
checkpoint, deletes both, restores, and checks the original value/bytes. It removes
only its own containers and volumes. Existing images must already be present.

This is snapshot recovery at the recorded interval, not continuous PostgreSQL WAL
archival or recovery to an arbitrary timestamp. No cross-provider raw-volume
restore is supported; use canonical archives and artifact portability for that.
