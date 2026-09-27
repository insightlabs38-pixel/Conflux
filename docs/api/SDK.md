# Generated SDK contract

`docs/api/openapi.yaml` is the checked source for the TypeScript and Python SDKs. Regeneration must be deterministic and fail if the checked schema contains an operation or schema shape the generator cannot represent. The generated files are committed, and a check command compares them with fresh output.

Each client exposes an operation ID based `call` method. A call supplies path values, optional query values, and an optional JSON body. It returns the schema's JSON response, text for CSV or other text responses, and `null`/`None` for no-content responses. Both clients support bearer credentials and session cookies, encode path values, and raise an error with the HTTP status and response body for non-success responses. They never retry writes automatically.

Generated TypeScript operation types include request and response shapes; generated Python schema types use `TypedDict`. Runtime code is small and hand maintained. Client calls still pass through server-side authorization and validation. The SDKs do not embed credentials or select a workspace implicitly.
