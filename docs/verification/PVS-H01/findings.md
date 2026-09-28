# PVS-H01 audit findings

| #   | Finding                                                                                                                                                                                              | Severity                     | Fix                                                                                                                                                                            | Regression                                |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- |
| 1   | Behind the bundled Caddy every visitor shared one client address, so the 30/hour vote-attempt and email-token IP limits applied to the whole audience at once (load tests bypassed Caddy and hid it) | P1 availability/integrity    | `client_identifier` trusts the first `X-Forwarded-For` entry only when the peer is an internal address                                                                         | `test_session_csrf.py::client_identifier` |
| 2   | Idempotency keys were global: another caller reusing a key and body received the first caller's cached response; a duplicate while the first request ran executed twice; 5xx responses were cached   | P1 confidentiality/integrity | Keys are scoped to caller + method + path; in-flight duplicates get 409; server errors are never cached; oversized keys rejected                                               | `test_idempotency_scope.py`               |
| 3   | Cookie-authenticated writes had no cross-site defence beyond `SameSite=Lax`                                                                                                                          | P2                           | Writes carrying a foreign `Origin` (or `Sec-Fetch-Site: cross-site`) are refused; `DJANGO_CSRF_TRUSTED_ORIGINS` extends the allowlist; scripts/API clients send neither header | `test_session_csrf.py`                    |
| 4   | No throttle on password guessing                                                                                                                                                                     | P2                           | 10 failures per account per 15 minutes returns 429 with `Retry-After`; success resets                                                                                          | `test_session_csrf.py`                    |
| 5   | Session cookie lacked `Max-Age` and `Secure` behind TLS                                                                                                                                              | P3                           | 12 h `Max-Age`; `Secure` when the request is HTTPS or forwarded as such                                                                                                        | `test_session_csrf.py`                    |
| 6   | Non-object JSON bodies (`null`, `[]`, `"x"`, numbers) crashed login and credential issuing with 500                                                                                                  | P3                           | Global `ObjectJSONParser` returns 400                                                                                                                                          | `test_route_sweep.py` adversarial bodies  |
| 7   | Anonymous callers could list an event's finalized project names through voting candidates even when no voting plan existed                                                                           | P3                           | Candidates require a voting plan                                                                                                                                               | route sweep                               |

## Standing sweeps (`tests/security`)

- Every API route and method: anonymous, other-tenant organizer and non-member participant get no data or write; only documented public routes are open.
- Every route as organizer, judge and participant with ten adversarial bodies and hostile query strings: no 5xx.
- Every judge-readable route: no peer ballot content or id appears.
- Real-PostgreSQL races (`tests/integration/concurrency/test_pvs_races.py`): single-slot table placement, concurrent auto-assign, double apply of one plan, stance/finalize, concurrent remediation.

## Reviewed, no change needed

Webhook destinations (HTTPS-only, public addresses, resolved address pinned); artifact object keys (server generated with random suffix; downloads presigned only for viewers); audit/outbox (`record_mutation` refuses to run outside a transaction); model-level immutability of finalized evidence.

## Known limitations

- ~~Session tokens are stored unhashed.~~ **Resolved in PVS-H06:** sessions are stored as keyed SHA-256 digests (see SECURITY.md); migration `accounts.0005` digests existing rows.
- Per-account lockout can be triggered by an attacker against a known username (15 min); an operator can clear `accounts_loginfailure`.
