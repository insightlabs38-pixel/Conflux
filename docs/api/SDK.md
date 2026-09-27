# Generated SDK contract

`docs/api/openapi.yaml` is the checked source for the TypeScript and Python SDKs. Regeneration must be deterministic and fail if the checked schema contains an operation or schema shape the generator cannot represent. The generated files are committed, and a check command compares them with fresh output.

Each client exposes an operation ID based `call` method. A call supplies path values, optional query values, and an optional JSON body. It returns the schema's JSON response, text for CSV or other text responses, and `null`/`None` for no-content responses. Both clients support bearer credentials and session cookies, encode path values, and raise an error with the HTTP status and response body for non-success responses. They never retry writes automatically.

Generated TypeScript operation types include request and response shapes; generated Python schema types use `TypedDict`. Runtime code is small and hand maintained. Client calls still pass through server-side authorization and validation. The SDKs do not embed credentials or select a workspace implicitly.

## Use

Build the TypeScript package with `pnpm --filter @conflux/sdk build`. Import `ConfluxClient` from `@conflux/sdk`, create it with the API origin and optional `bearerToken`, then call an OpenAPI operation ID such as `client.call("get_api_v1_accounts_me", {})`. Browser session calls send existing cookies with `credentials: "include"`.

Install the Python package with `pip install ./sdks/python`. Create `ConfluxClient("https://your-conflux-host", bearer_token="...")` or pass `session_token`, then call `client.call("get_api_v1_accounts_me")`. Python schema types live in `conflux_sdk.generated`.

Run `make sdk-generate` after changing the checked OpenAPI artifact. `make sdk-check` verifies OpenAPI freshness, deterministic SDK output, and the TypeScript package build. Operation IDs and schemas are generated; transport behavior is covered by focused Python and TypeScript tests.
