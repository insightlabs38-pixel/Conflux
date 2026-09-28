# Optional OpenID Connect sign-in (PVS12)

Built-in username/password authentication is always available and is the only mode needed offline. Setting `OIDC_ISSUER` and `OIDC_CLIENT_ID` additionally offers authorization-code + PKCE sign-in with any standards-compliant provider. The provider is contacted only while someone signs in — never at startup — so the stack still boots with no network.

Register `https://<host>/api/v1/accounts/oidc/callback/` (or `OIDC_REDIRECT_URI`) at the provider.

| Variable | Meaning |
|---|---|
| `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` | Provider and client. The secret is optional (public PKCE client) and sent as HTTP Basic. |
| `OIDC_SCOPES` | Default `openid email profile`. |
| `OIDC_ALLOWED_EMAIL_DOMAINS` | Comma list; requires a *verified* email in an allowed domain. |
| `OIDC_AUTO_CREATE_USERS` | Default `1`. When `0`, only already-linked identities can sign in. |
| `OIDC_LINK_BY_VERIFIED_EMAIL` | Default `0`. When `1`, a first sign-in links to the single local account with that verified email. Enable only if the provider verifies addresses. |
| `OIDC_DEFAULT_WORKSPACE_SLUG` | New accounts join this workspace as **participant** (elevated roles are never granted automatically). |
| `OIDC_ALLOW_INSECURE_HTTP` | Development only; otherwise the provider must use https. |

Routes: `GET accounts/oidc/config/` (is SSO offered), `GET accounts/oidc/login/?next=/path`, `GET accounts/oidc/callback/`. Identities are keyed by (issuer, subject), never by email. New accounts have no usable password. Sign-ins produce the same session cookie as password login and an `auth.oidc_login` audit event.

Checks on every sign-in: single-use `state` bound to the initiating browser by a short-lived cookie, `nonce`, PKCE S256, asymmetric signature verified against the provider's JWKS (`none`/HMAC refused), `iss`/`aud`/`exp`/`iat`/`sub` required, `azp` for multi-audience tokens, same-site `next` only, no redirects followed when talking to the provider.

Limitations: no logout propagation or refresh tokens; group/role claims are not mapped to roles.
