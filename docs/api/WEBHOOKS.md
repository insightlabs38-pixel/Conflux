# Webhooks

Workspace organizers manage subscriptions at `GET/POST /api/v1/workspaces/{workspace}/webhooks/`. A subscription can cover the workspace or one event. `event_types` is a nonempty list of exact dotted domain event names, such as `event.status_changed`. Event scoped subscriptions receive only outbox records whose `data.event` matches that event ID. Create requires a public HTTPS destination on port 443. The response contains the signing secret once; later reads omit it.

The worker stages matching committed outbox events and sends a JSON envelope:

```json
{"version":"1","id":"EVENT_UUID","type":"event.status_changed","created_at":"2026-09-27T06:00:00+00:00","workspace":"WORKSPACE_UUID","data":{"event":"EVENT_UUID","status":"open"}}
```

Each POST has `X-Conflux-Event-Id`, `X-Conflux-Timestamp` (Unix seconds), and `X-Conflux-Signature: v1=HEX`. Verify the HMAC-SHA256 of the exact received body prefixed by `timestamp + "."`, using the issued secret as UTF-8 bytes. Compare signatures in constant time and reject old timestamps. Deduplicate by event ID: delivery is at least once, including after worker interruption or manual replay. Redirects are never followed. The destination is resolved and checked again for every attempt.

Success requires HTTP 2xx. Failures retry with bounded exponential backoff and become dead after five attempts. `GET /api/v1/workspaces/{workspace}/webhooks/{subscription}/deliveries/` returns the newest 100 delivery records; use `?offset=` for older records. Organizers can replay a completed delivery at `POST .../deliveries/{delivery}/replay/` after enabling its subscription. Disable or enable with `PATCH /api/v1/workspaces/{workspace}/webhooks/{subscription}/` and `{ "enabled": false }` or `true`.
