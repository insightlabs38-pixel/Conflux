# Security

Do not commit credentials. Use local environment variables for secrets and
report vulnerabilities privately to repository maintainers.

## Threat model

Trust boundaries: browser/public internet (in a real deployment), Caddy/
app, DB, worker queue, object storage, webhook destinations, API
credentials/invite tokens.

Critical threats and where each is controlled:

- **Event/workspace RBAC bypass and IDOR** — every organizer/participant/
  judge view resolves its workspace/event/project from the URL server-side
  and scopes every query to it (`events.views.OrganizerView`,
  `participation.views.ParticipantView`, `core.mixins.WorkspaceLookupMixin`,
  and each app's own equivalent); a public_id alone is never enough to
  reach a row outside the caller's own scope.
- **Judge peer-score leakage** — `evaluations.views.BallotListCreateView`
  and `integrations.views.JudgeScoresView` both refuse an explicit
  `?judge=` for anyone but that judge or an organizer/admin; a judge's own
  request defaults to their own ballots only.
- **Deadline bypass/race** — mutations that must not race
  (`select_for_update` around award selection, fulfillment transitions,
  invite redemption, rate limiting, webhook delivery claims) hold a row
  lock for the duration of the check-then-act sequence.
- **Privilege/token escalation** — role grants require an existing
  organizer/admin (`workspaces.views.WorkspaceMembersView`); API
  credentials are scoped to one workspace (optionally one event) and an
  explicit `METHOD:route-name` allowlist (`accounts.authentication
.CookieSessionAuthentication`).
- **Malicious uploads/path/content-type tricks** — object keys are always
  server-generated (UUIDs + a random token, never a client-supplied
  filename); every download forces `Content-Disposition: attachment`, and
  a fixed set of actively-executable content types is rejected outright
  regardless of artifact kind. See `docs/architecture/ARTIFACT_SERVING.md`
  (added by the GSEC-002 finding this gate raised and fixed).
- **Webhook SSRF/signature/replay** — `integrations.webhooks
.validate_destination` requires HTTPS on port 443, resolves the host and
  rejects any non-global address, and the actual delivery connection is
  pinned to the address validated (DNS-rebinding-proof); deliveries are
  HMAC-signed with a timestamp and deduplicated per (subscription,
  domain_event).
- **Community-vote Sybil/ballot stuffing/duplicate identities** — one vote
  per `voter_key` per plan (DB-enforced), DB-backed rate limiting per scope
  (never cache-based, since Valkey is disposable), explainable
  `AbuseSignal` evidence rather than an opaque score.
- **Private submission/artifact leakage** — `artifacts.models
.can_view_artifact` is the single visibility gate (public/organizer/
  judge/participant), checked by every read path including the public
  server-rendered gallery, which additionally requires `status=READY`.
- **Invite reset/token replay** — `TeamInvite` redemption checks and
  increments `use_count` under a row lock; an expired, revoked, or
  exhausted token is rejected explicitly.
- **Cross-event cache key leakage** — there is no application-level cache
  backend; Valkey is disposable Celery broker/result state only
  (`config/settings.py`), never a place tenant data could leak across a
  shared key.

## Verification ownership

This is a single-worker campaign (see AGENTS.md): there is no separate
fuzzing/permutation worker running broad RBAC/malformed-input matrices
continuously. `docs/batches/C-B28.md` records what was reviewed and found
for the Core security gate; `tests/security/` holds the resulting
regression coverage.
