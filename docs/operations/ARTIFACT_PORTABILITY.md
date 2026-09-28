# Copy event artifacts between S3 backends

The host-side Django command copies one event's completed stored artifacts from
the configured S3 backend to another RustFS or SeaweedFS backend. It preserves
keys, content type, all object metadata and artifact identity. External URLs and
unfinished uploads with no committed object key are excluded. No application
records, visibility, validation statuses or backend settings change.

Configure the source using the normal application S3 environment. Supply
destination credentials in `CONFLUX_COPY_DEST_ACCESS_KEY` and
`CONFLUX_COPY_DEST_SECRET_KEY`; they are not command-line arguments or report
fields. Preview first:

```sh
uv run --frozen python src/api/manage.py copy_event_artifacts EVENT_UUID \
  --destination-endpoint http://destination:8333 \
  --destination-bucket conflux-artifacts
```

Add `--execute` to copy. Preview reads and hashes source/existing destination
objects but creates no bucket and writes nothing. Execution creates the bucket
if needed. Output is JSON listing artifact identity, object key, byte count,
SHA-256 and `would_copy`, `copied` or `verified_existing` status. Objects spool to
local temporary disk with bounded reads; allow disk space for the largest file.

Source size/type/artifact metadata and any recorded SHA-256 must agree with the
database. Existing destination objects must match metadata and bytes exactly;
conflicts fail without overwriting. New writes use S3 `If-None-Match: *` to protect
objects arriving after the existence check. Unsupported conditional writes fail
closed. Each copy is downloaded again to verify metadata and SHA-256 before it
is reported successful. Verified existing copies are skipped on retry.

Copy failure can leave already copied objects or a partially verified destination
object. Sources are never deleted. Retry verifies existing objects; a conflicting
object requires operator investigation before another attempt. No automatic
cleanup deletes uncertain data. A backend outage produces a nonzero command exit.

This is an operator maintenance command, not an API or automatic cutover. Quiesce
application/external writers for a stable inventory, copy every required event,
resolve outstanding uploads, retain reports, then separately decide whether to
change S3 settings. Signed download URLs must be reissued against the new public
endpoint. Source and destination credentials need only their intended bucket
permissions. Treat reports as private operational artifacts.

`scripts/verify-artifact-portability` starts two disposable Compose storage
services, tests real RustFS→SeaweedFS and reverse copies plus conditional-write
collision protection, and removes its own resources. Images must already exist.
Without those endpoint variables, the ordinary focused suite explicitly skips
the real-backend case. No shared runtime is stopped or reconfigured.
