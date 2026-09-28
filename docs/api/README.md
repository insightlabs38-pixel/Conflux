# Conflux API v1

The live OpenAPI schema is available at `GET /api/v1/schema/`. The [checked schema](openapi.yaml) is generated from the same Django routes and verified with `make openapi-check`. Paths are versioned under `/api/v1/`; JSON routes end in `/`, and CSV exports end in `.csv`.

Use the [local administration CLI](CLI.md) to create, manage and clone events.

Use the [local API explorer](EXPLORER.md) to browse the live contract and send seeded examples.

See the [generated SDK guide](SDK.md) for TypeScript and Python clients derived from the checked schema.
See the [CSV migration adapter](CSV_MIGRATION.md) for importing external project rows through the canonical archive.

See [webhooks](WEBHOOKS.md) for subscription, signing, retry, and replay behavior.
See [awards](AWARDS.md) for winner selection, publication, typed prizes, and fulfillment.
See [the canonical archive](../architecture/CANONICAL_ARCHIVE.md) for exporting and importing an event's configuration.
See [verifiable records](../architecture/VERIFIABLE_RECORDS.md) for signed event/project/judge records, offline verification, and the embeddable gallery.

## Authenticate

Browser UI calls use the `session` cookie. External clients can ask a workspace organizer to issue a scoped bearer credential. The organizer creates it with a human session:

```sh
curl -X POST "$API_BASE/api/v1/workspaces/$WORKSPACE_ID/api-credentials/" \
  -H 'Content-Type: application/json' \
  -H "Cookie: session=$SESSION_TOKEN" \
  -d '{"name":"Event reader","event":"EVENT_PUBLIC_ID","allowed_actions":["GET:event-detail"],"expires_in_days":30}'
```

Replace `EVENT_PUBLIC_ID` with the actual event UUID. The response contains `token` once; keep it secret. The token is bound to the workspace, this event, and `GET:event-detail`. It cannot list all workspace events, perform a write, or manage credentials. See [credential scopes](CREDENTIALS.md) for expiry and revocation.

## Read an event

```sh
curl "$API_BASE/api/v1/workspaces/$WORKSPACE_ID/events/$EVENT_ID/" \
  -H "Authorization: Bearer $API_TOKEN"
```

The route returns an event JSON object. The bearer credential's owner must retain the organizer role; removing that role removes access immediately. A wrong workspace, event, action, expired token, or revoked token fails closed. Invalid input returns JSON errors; missing scoped resources return 404. See [route conventions](CONVENTIONS.md) and the checked schema for request and response fields.

## Revoke

With an organizer session, call `POST /api/v1/workspaces/{workspace}/api-credentials/{credential}/revoke/`. Bearer credentials cannot call the management route. Issuance and revocation appear in the workspace audit log without the token value.

## Paging public galleries

`GET /api/v1/gallery/` and `GET /api/v1/events/{event}/gallery/` return a JSON array (unchanged) but are bounded: `limit` (1–100, default 50) and `offset` query parameters, `X-Total-Count` for the number of matching projects and `Link` headers with `rel="next"`/`"prev"`. Other values return 400. Results are ordered by name, then ID, so pages never overlap. The event gallery also accepts `q`.
