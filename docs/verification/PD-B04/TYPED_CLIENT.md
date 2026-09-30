# PD-B04-T03 — generated typed client as the default transport

One seam: `src/web/lib/api.ts`. The app talks to the network only through it (ratchet: `lib/transport.test.ts`).

| Entry point                 | Use                                                                                                                                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apiCall(operation, args)`  | Preferred for new code: `sdks/typescript` `ConfluxClient.call`, so path, method, path/query parameters, body and response are checked against the OpenAPI contract at compile time.            |
| `apiRequest(url, opts)`     | URL-based callers (panels build URLs from bases). `resolveOperation(method, path)` matches the URL against the generated `operations` catalog; a documented request is sent through `apiCall`. |
| fallback (same function)    | A URL, query parameter or body the contract does not document is sent by a plain `fetch` with the identical policy (credentials, JSON, signal, `ApiError`). Free-form tools still work.        |
| `apiJson`, `problemText`    | Panel convention (`field: message` errors) over `apiRequest`; replaces ten copies of a hand-written `request()`.                                                                               |
| `orNull(promise, ...codes)` | An expected 403/404 becomes `null`.                                                                                                                                                            |

Path parameters are bound by name from the template (the catalog lists them alphabetically, not in URL order); a literal segment beats a parameter (`/rules/acknowledgements/` vs `/rules/{number}/`). Same-origin relative URLs and `credentials: "include"` are unchanged, so cookies, CSRF-free JSON sessions and the Caddy gateway see the same requests as before.

## Raw `fetch` that remains (allowlisted in `transport.test.ts`)

- `ApiExplorer`: public schema read with credentials omitted, and the free-form "try it" request (any URL by design).
- `ArtifactPanel`: presigned uploads to object storage, which must not receive application credentials.

## Contract defects found by making the typed client the default

- 18 GET operations are documented with no response body although the server returns JSON (e.g. `result-publication-requests/`, `rules/`, `mentors/`). The SDK client returned `null` for them. Fixed in `sdks/typescript/client.ts`: a documented-empty response that carries a body is parsed, never discarded (204 stays `null`). The schema itself (missing serializer annotations) is a backend follow-up; static types for those operations still say `null`.
- `apiRequest` resolves path parameters by template order, not the catalog's alphabetical `path_params`; a first version bound them wrongly and unit tests caught it.

## Measured

- Static app URLs: 48 `/api/v1/...` string literals in non-test sources resolve to documented operations; the 7 others are base prefixes concatenated later, docs text or the explorer root.
- Bundle: main chunk 570.7 kB to 710.0 kB (gzip 161.6 to 170.2) from the generated operation catalog and client; splitting it out is a later optimisation, not a correctness issue.
- Behaviour kept: `useLoad` failures show at once with the panel's Try again (no silent backoff), matching prior states and the loading/error browser gate.
