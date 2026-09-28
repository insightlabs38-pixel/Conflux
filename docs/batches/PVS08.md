# PVS08 — Safe submission artifact and demo inspector
## Result
Judges, organizers and owning participants can safely inspect submitted evidence without executing it, and can preview exactly what a judge will see for a submission's frozen version.
## Changes
- `artifacts.inspector`/`artifacts.url_inspector`: static byte/link inspection (type sniffing, image/PDF/zip-bomb/path-traversal/secret checks, redirect and SSRF-safe link checks) — nothing is executed or rendered.
- `ArtifactInspection` model (immutable), `run_inspection` service, rate-limited and audited; `artifacts.review_views` gives judges/organizers/owners a scoped list + inspection endpoint.
- `projects.submissions.preview_frozen_submission` + `SubmissionPreviewView` (`.../submissions/<stage>/preview/`): judge-visible artifacts of the latest finalized version, checked against live rows for drift (removed/content_changed); drift blocks the download link and clears `verified`.
- Fixed a pre-existing leak: text previews now redact matched secret patterns instead of echoing them.
## Verification
- `test_artifact_inspector.py`, `test_submission_preview.py` → all passing (16 new/updated tests).
- Full suite: 1185 passed/20 skipped (`test_evaluation_api.py::test_ballot_and_audit_commit_together_without_a_test_transaction` flakes only under `-n auto`; passes standalone, pre-existing, unrelated to this batch).
- `spectacular --validate --fail-on-warn`, `generate_sdks.py` + `--check`, `check_openapi_artifact.py` → clean.
## Limitations
- Preview endpoint is API-only; no UI yet (PVS-H03).
- Drift check compares `kind`/`visibility`/`object_key`/`sha256`; it does not re-verify object bytes against storage (that's `run_inspection`'s digest check).
## Next
PVS09.
