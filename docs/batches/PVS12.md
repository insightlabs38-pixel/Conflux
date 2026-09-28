# PVS12 — Optional generic OIDC/SSO
## Result
Operators can enable standards-based OpenID Connect sign-in by environment variables; built-in password login, offline startup and existing session semantics are unchanged.
## Changes
- `accounts.oidc`: discovery, PKCE authorization request, token exchange, ID-token verification against JWKS; `ExternalIdentity` (issuer+subject) and single-use `OidcLoginState` (bound to the starting browser).
- Auto-create, email-domain allowlist, opt-in link-by-verified-email and default-workspace participant membership are configurable; nothing elevated is ever granted automatically.
## Verification
- `test_oidc.py` (28, fake provider): PKCE/state/nonce, replay, cross-browser, expiry, 9 malformed-token cases, allowlist, linking, disabled account, open-redirect, off-by-default, config never touches the network.
- `manage.py check` with an unreachable issuer configured → clean; full suite 1239 passed/23 skipped; route sweep, OpenAPI and SDK checks clean.
## Limitations
- No logout propagation, refresh tokens or claim→role mapping; no UI button yet (PVS-H03 can read `oidc/config/`).
## Next
PVS13 (permissioned MCP adapter).
