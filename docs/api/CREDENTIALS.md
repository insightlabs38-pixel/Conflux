# Scoped API credentials

An organizer or workspace admin creates a credential with a cookie-authenticated `POST /api/v1/workspaces/{workspace}/api-credentials/`. Supply a name, `allowed_actions`, optional event public ID, and optional `expires_in_days` (1–90, default 30). For example, `GET:event-list` permits only GET on the named event-list route; `GET:event-detail` permits GET on an event detail route. Actions are the HTTP method and route name, separated by `:`. The token appears only in the creation response. Store it as a secret.

Send `Authorization: Bearer <token>` on workspace-nested API routes. The server checks the token's workspace, optional event, exact action, expiry, revocation, and the owner's current role. An invalid bearer header does not fall back to a browser cookie. Event-bound credentials cannot call routes without the event ID in the path. Credential management requires a human session; a bearer token cannot issue or revoke credentials.

`GET /api/v1/workspaces/{workspace}/api-credentials/` lists metadata without token values. `POST /api/v1/workspaces/{workspace}/api-credentials/{credential}/revoke/` revokes immediately. Issuance and revocation are recorded in workspace audit history without the secret.
