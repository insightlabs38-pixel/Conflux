# Execution Decision Register

- X001 only three human-visible control lanes: Claude, Codex, Freebuff orchestrator.
- X002 Freebuff simultaneous writers use isolated CLI worker processes/worktrees; orchestrator is control plane.
- X003 one canonical shared application runtime from green main.
- X004 Freebuff owns most fuzz/property/permutation breadth; frontier models protect semantics and gates.
- X005 canonical queue state updated by orchestrator/integration control only; workers emit receipts.
- X006 main should remain green/demonstrable.
- X007 frontier escalation is human-approved; Freebuff cannot autonomously consume Claude/Codex allowance.
- X008 related escalations are batched when context overlaps.
- X009 Core/Stretch/Very Stretch are scheduling tiers; valuable features may be promoted whenever gates support it.
- X010 no Dogfood project code/Git commits before official kickoff.
- X011 (2026-09-27, owner-approved) C-B12's public gallery/event/project pages
  (GAL-001/GAL-002) are plain Django server-rendered templates
  (src/api/presentation/templates), not the React SPA: the official checker
  (run.py) does a raw urllib GET and substring-matches the response body
  with no JS execution, so a client-rendered shell would fail it. Search/
  filter is plain GET query params/forms. React stays for the organizer-
  authenticated page-builder editing UI only. Both CSS reuse the same
  src/web/styles tokens via a shared STATICFILES_DIRS.
- X012 (2026-09-27, owner-directed) Project.track is the canonical track
  association (not Team): the official fixture format itself carries
  `"track"` on each project object, not on the team, so this matches the
  spec rather than inventing a new shape. Nullable FK, same-event enforced
  in Project.clean(). Fixes GAL-001 gallery filtering and JDG-007 track-fit,
  both of which had silently degraded to no-ops (see ATTENTION.md). Landed
  as a corrective prerequisite before C-B15, not as part of it.
- X013 (2026-09-27, C-B25) communications.audiences are computed live, never
  persisted as saved "mailing lists": a stale audience definition that no
  longer matches current participation/judging state would be a worse
  organizer-facing bug than the cost of recomputing on every send/preview.
  Email delivery defaults to Django's console backend (no network, matches
  the offline-first architecture); a real deployment opts in to SMTP via
  `DJANGO_EMAIL_BACKEND`/`EMAIL_HOST`/etc. The in-app `MessageRecipient` row
  is the durable record regardless of email outcome.
- X014 (2026-09-27, C-B28 security gate, GSEC-002) found and fixed a real
  P1: `infra/Caddyfile` reverse-proxies the object store under the app's
  own origin, so a `file`/`document`/`dataset`-kind artifact upload (no
  content-type check before this fix) or an `image`-kind upload claiming
  `image/svg+xml` (passes a naive `image/*` prefix check) could reach a
  project's public-gallery link and execute script same-origin. Fixed with
  two independent controls: every presigned download now forces
  `Content-Disposition: attachment`, and validation rejects
  `text/html`/`application/xhtml+xml`/`image/svg+xml` outright for every
  artifact kind. See docs/architecture/ARTIFACT_SERVING.md and
  tests/security/test_stored_xss_hardening.py.
- X015 (2026-09-27, owner-approved) STRETCH-GATE promoted: the owner
  reviewed the completed S01-S24 code directly and explicitly authorized
  continuing sequentially into Very Stretch (VS01 -> VS02 -> ... -> VS50)
  in this same single-worker session. Not self-promoted by the worker.
