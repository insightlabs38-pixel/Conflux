# Verifiable records (REC-001..003)

A signed, publicly verifiable record for an event, a project, or a judge's
participation in it. Every field comes from the event's own real
configuration/data at issuance time — there is no fixed certificate
template to fill in.

## Issue a record (organizer, authenticated)

```
POST /api/v1/workspaces/<workspace>/events/<event>/records/event/
POST /api/v1/workspaces/<workspace>/events/<event>/records/project/   {"project": "<project public_id>"}
POST /api/v1/workspaces/<workspace>/events/<event>/records/judge/     {"user": "<user public_id>"}
```

Each returns `{"token": "<jwt>", "claims": {...}}`. A judge record requires
the user to actually be a pool member for that event (`evaluations.PoolMembership`);
otherwise the request fails with a 400 naming the problem, not a record for
a fact that isn't true.

## Verify a record (nobody needs an account)

The token is a JWT signed with Ed25519 (`alg: EdDSA`, `iss: conflux`). It is
**verifiable entirely offline**: fetch the public key once, then check the
signature yourself with any standard JWT library. This server is never in
the loop for verification, and no lookup or database record backs a
token — the signature alone is the proof.

```
GET /api/v1/records/verification-key/
=> {"issuer": "conflux", "algorithm": "EdDSA", "public_key_pem": "-----BEGIN PUBLIC KEY-----..."}
```

```python
import jwt
public_key_pem = ...  # fetched once, above
claims = jwt.decode(token, public_key_pem, algorithms=["EdDSA"], issuer="conflux")
```

```js
// npm i jose
import { importSPKI, jwtVerify } from "jose";
const key = await importSPKI(publicKeyPem, "EdDSA");
const { payload } = await jwtVerify(token, key, { issuer: "conflux" });
```

For anyone without tooling handy, `POST /api/v1/records/verify/
{"token": "..."}` and the page at `/e/verify/?token=...` run the identical
check server-side — a convenience, not a requirement. **No hosted verifier
is needed**: the local check above is the primary, permanent path, and it
keeps working even if this deployment disappears, as long as the public key
was saved.

## Compatibility

- The keypair is derived deterministically from `RECORD_SIGNING_KEY_SEED`
  (see `presentation/keys.py`); there is no rotation or multi-key support in
  v1 — rotating the seed invalidates every previously issued record.
- A record is a stateless, self-contained claim (nothing is persisted per
  issuance); there is no revocation. Re-verifying always re-checks the
  underlying fact only at issuance time, not at verification time.
- `kind` is one of `event`, `project`, `judge`. A reader should ignore
  unknown future `kind` values rather than reject the whole token, the same
  additive-compatibility stance as the canonical archive
  (see [CANONICAL_ARCHIVE.md](CANONICAL_ARCHIVE.md)).

## The embeddable gallery (EMB-001/002)

`GET /api/v1/events/<event>/gallery/` is a small, unauthenticated,
dependency-light JSON read of the same public gallery the server-rendered
site shows (name, description, track, team, and a link to the project's
public page). It exists for external consumers like the
`<conflux-gallery>` Web Component in `src/embed` — see
[docs/embed/README.md](../embed/README.md) and
[examples/embed.html](../../examples/embed.html) for self-host usage.
