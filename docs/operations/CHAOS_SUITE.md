# Interruption verification

Run `scripts/verify-chaos` from an installed checkout. It uses pytest's disposable
database and Happy DOM; it never stops containers or modifies the application
runtime. Do not point test configuration at a production database.

| Boundary                  | Injected failure                          | Recovery assertion                                                           |
| ------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------- |
| Outbox staging / database | Database error after delivery creation    | Entire transaction rolls back; next poll creates exactly one delivery        |
| Delivery worker           | Process exit after receiver acceptance    | Claim delays retry for ten minutes; retry retains event ID and body          |
| Webhook receiver          | Timeout or HTTP 503                       | Pending work survives; retry starts at backoff expiry and clears error       |
| Object storage            | HEAD timeout after multipart completion   | No ready artifact; retry verifies completed object before committing         |
| Upload database           | Database error after artifact update      | Intent and artifact roll back together; completed object remains recoverable |
| Judge browser             | Unmount/reopen with queued offline ballot | Local ballot survives reopening and syncs on reconnection                    |

Recovery rejects mismatched size/type/artifact identity and propagates storage
errors other than `NoSuchUpload`. That specific response permits a HEAD check,
not automatic acceptance. Normal intent expiration, membership and part checks
still apply. Uploaded artifacts still require validation before becoming ready.

Webhook delivery remains at least once: receivers must deduplicate by event ID.
The tests inject failures at real service boundaries; they do not demonstrate
physical process termination, PostgreSQL failover, broker durability, real browser
crashes, or provider outages. Existing concurrency and S3 contract suites remain
separate verification for real infrastructure. No shared runtime chaos is enabled.
