# Stored artifact serving (GSEC-002)

`infra/Caddyfile` reverse-proxies the object store under the _same origin_
as the application (`/{{S3_BUCKET_NAME}}/*` on the same host:port as
`/api/v1/*`), so that a plain `<a href>` in the server-rendered public
gallery (`presentation/templates/presentation/project_detail.html`) can
link straight to a project's artifacts without a second, separately-
configured public endpoint. That convenience comes with one obligation:
an uploader's claimed `content_type` can never be trusted enough to let a
browser render a stored object inline, because a same-origin response is
indistinguishable from the application's own pages to anything that reads
`document.cookie`, forges a same-origin `fetch`, or simply impersonates
the real login form.

Two independent controls close this (defense in depth — either one alone
would already stop the attack this document describes):

1. **Every presigned download forces `Content-Disposition: attachment`.**
   `artifacts.storage.S3Storage.presign_get(key, download_filename=...)`
   sets `ResponseContentDisposition` on the GetObject request, so a
   browser always offers the object as a file to save, never as a page to
   render — regardless of what `Content-Type` the object claims. Both call
   sites (`artifacts.views.ArtifactDetailView`,
   `presentation.public.public_artifact_view`) always pass a
   `download_filename`. The filename itself is sanitized
   (`_safe_disposition_filename`, in the same module) so a
   quote/CR/LF in an artifact's title can never break out of the header
   value or inject a second header line.
2. **A handful of actively-executable content types are rejected outright**
   at validation time (`artifacts.validators._ACTIVE_CONTENT_TYPES`):
   `text/html`, `application/xhtml+xml`, and `image/svg+xml` — the last one
   deliberately, since it passes a naive `content_type.startswith("image/")`
   check (used for the `image` artifact kind) but can embed and execute
   `<script>`. This check applies to every stored artifact kind, not only
   `image`/`video`.

## What this replaced

Before this control, only the `image`/`video` artifact kinds had any
content-type check at all (matching their own kind, e.g. rejecting an
`image`-kind upload whose content type didn't start with `image/`); `file`,
`document`, `dataset` and `secret` accepted any claimed content type and
passed straight to `READY` once their stored object's metadata matched.
Combined with the same-origin proxy above, an `image`-kind upload claiming
`image/svg+xml`, or a `file`/`document`/`dataset`-kind upload claiming
`text/html`, could reach a project's `PUBLIC`-visibility public-gallery
link and execute script in this application's own origin when a victim
(any workspace member, or an organizer/judge browsing the public gallery)
followed it. See `tests/security/test_stored_xss_hardening.py` for the
regression coverage, and `docs/batches/C-B28.md` for the gate record.
