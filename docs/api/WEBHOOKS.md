# Webhooks

Workspace organizers manage subscriptions at `GET/POST /api/v1/workspaces/{workspace}/webhooks/`. A subscription can cover the workspace or one event. `event_types` is a nonempty list of exact dotted domain event names, such as `event.status_changed`. Event scoped subscriptions receive only outbox records whose `data.event` matches that event ID. Create requires a public HTTPS destination on port 443. The response contains the signing secret once; later reads omit it.

The worker stages matching committed outbox events and sends a JSON envelope:

```json
{
  "version": "1",
  "id": "EVENT_UUID",
  "type": "event.status_changed",
  "created_at": "2026-09-27T06:00:00+00:00",
  "workspace": "WORKSPACE_UUID",
  "data": { "event": "EVENT_UUID", "status": "open" }
}
```

Each POST has `X-Conflux-Event-Id`, `X-Conflux-Timestamp` (Unix seconds), and `X-Conflux-Signature: v1=HEX`. Verify the HMAC-SHA256 of the exact received body prefixed by `timestamp + "."`, using the issued secret as UTF-8 bytes. Compare signatures in constant time and reject old timestamps. Deduplicate by event ID: delivery is at least once, including after worker interruption or manual replay. Redirects are never followed. The destination is resolved and checked again for every attempt.

Success requires HTTP 2xx. Failures retry with bounded exponential backoff and become dead after five attempts. `GET /api/v1/workspaces/{workspace}/webhooks/{subscription}/deliveries/` returns the newest 100 delivery records; use `?offset=` for older records. Organizers can replay a completed delivery at `POST .../deliveries/{delivery}/replay/` after enabling its subscription. Disable or enable with `PATCH /api/v1/workspaces/{workspace}/webhooks/{subscription}/` and `{ "enabled": false }` or `true`.

## Inspector and destination changes

`GET .../deliveries/{delivery}/` previews the next attempt's exact UTF-8 body,
SHA-256 digest, current destination and signature scheme without sending it.
`history` contains the newest 100 persisted attempts; `?offset=100` retrieves
older attempts and `history_has_more` indicates another page. Each attempt
retains its actual destination, body, signed headers, start/completion times,
HTTP status and bounded error. The signing secret is never returned by inspection.
Verify saved signatures against the saved body and timestamp, not a reformatted
JSON document. Generic and chat-format deliveries use the same signing contract.

History is captured from VS32 onward; older deliveries have no reconstructed
attempts. An interrupted attempt without completion has an unknown outcome,
including possible remote acceptance. Replay resets the current retry budget,
preserves attempt history and keeps the domain event ID. A late result from an
expired claim cannot overwrite a newer attempt's result.

Organizers can change the subscription destination with
`PATCH .../webhooks/{subscription}/` and `{ "url": "https://receiver.example/hook" }`.
The same public HTTPS/DNS checks apply at update and at every send. This changes
future attempts and replays; an already claimed attempt keeps its original URL.
No ad-hoc or unvalidated replay destinations are supported. The inspector,
destination updates and replay require an organizer/admin human session in the
subscription's workspace; bearer credentials alone cannot access them.
