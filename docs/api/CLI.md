# Local administration CLI

Run `scripts/conflux-admin` from a checkout, or install `sdks/python` and use
`conflux-admin`. Both use the generated Python SDK and the canonical API;
no direct database access or external service is needed. Python 3.12+ is required.

Set the API origin and exactly one credential through the environment:

```sh
export CONFLUX_BASE_URL=https://conflux.example
export CONFLUX_SESSION_TOKEN=YOUR_SESSION_TOKEN
scripts/conflux-admin whoami
export CONFLUX_WORKSPACE=WORKSPACE_PUBLIC_UUID
```

A scoped bearer token can instead use `CONFLUX_BEARER_TOKEN`; unset the session
token first. Credentials are never command-line arguments or stored in a CLI
configuration file. Workspace/event arguments must be public UUIDs. Global
options (`--base-url`, `--workspace`, `--timeout`) precede the command.
HTTP is accepted only on loopback for local development; remote origins require
verified HTTPS. Redirects are rejected and network requests time out after
30 seconds by default (maximum configurable timeout: 300 seconds).

```sh
scripts/conflux-admin events list
scripts/conflux-admin events create --name "Local hackathon" --slug local-hackathon
scripts/conflux-admin events get EVENT_PUBLIC_UUID
scripts/conflux-admin events update EVENT_PUBLIC_UUID --input changed-fields.json
scripts/conflux-admin events status EVENT_PUBLIC_UUID --status open
```

Create makes a private draft with UTC timezone unless `--timezone` specifies
another IANA zone. `--description` is optional. Update reads a nonempty JSON
object of changed event fields, for example:

```json
{
  "description": "Updated description",
  "starts_at": "2026-10-01T09:00:00Z",
  "ends_at": "2026-10-02T18:00:00Z"
}
```

Use the status command for `open`, `closed` or `archived`. The server still
enforces valid transitions, dates, authorization and mutability. Errors use
nonzero exit status and stderr; success returns JSON on stdout. Credential
values are redacted from error output. Do not capture private success responses
in public logs.

## Portable archives

```sh
scripts/conflux-admin events export EVENT_PUBLIC_UUID --output event.json
scripts/conflux-admin events export EVENT_PUBLIC_UUID --mode full --output full-event.json
scripts/conflux-admin events import --input event.json --name "New event" --slug new-event
scripts/conflux-admin events import --input event.json --name "New event" --slug new-event --apply
```

Export defaults to configuration; full mode includes the canonical archive's
additional project/evidence sections. A file export is published atomically,
has owner-only permissions (0600), and never overwrites an existing destination.
`--output -` writes the archive to stdout for an intentional pipe.

Import previews by default and leaves no new event. `--apply` uses the same
validated importer to create a new unpublished draft with fresh identities;
it never overwrites an existing event. Preview does not reserve the slug, so
apply can fail if another operator has taken it. See the
[archive contract](../architecture/CANONICAL_ARCHIVE.md) for included sections,
reference rewriting and import limits. Object bytes, live identities and
in-flight runtime state are not restored by this configuration import.

This CLI handles plain canonical archives, not signed envelopes or arbitrary
API requests. Use the API/SDK for signed archive workflows and other domains.
A timeout is an unknown write outcome: inspect server state before retrying.
