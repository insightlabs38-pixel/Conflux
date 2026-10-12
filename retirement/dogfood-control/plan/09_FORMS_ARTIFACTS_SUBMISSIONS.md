# Forms, Artifacts, Projects and Submission Correctness

## Forms
Published FormVersions are immutable. Supported field families include text, rich text, numeric, select/multi-select, boolean, URL, date/time and artifact references. Conditional visibility/requiredness is deterministic.

## Artifacts
Core kinds: file, image, video/external video, repository, live URL, technical document, dataset, secret/judge-only evidence. Visibility is explicit.

## Direct upload
API validates intent → returns short-lived presign/multipart info → browser uploads to generic S3 adapter backed by RustFS by default → API verifies object metadata → artifact becomes ready. Presign expiry may not bypass submission deadlines.

## Project vs submission
Project is long-lived identity. SubmissionVersion is immutable stage/time evidence.

## Finalization hot path
Lock submission → authenticate/authorize → evaluate policy/gate → validate required responses/artifacts → freeze immutable version → receipt/finalized_at → audit/outbox → commit. No remote I/O in this transaction.

## Preflight
Rule-based READY/WARNING/BLOCKED with evidence. Core validates required fields/artifacts, artifact readiness, policy/gate eligibility and common structural checks. Stretch adds external repo/license/link/demo validation.

## Duplicate handling
Detection creates signals; it does not silently merge/delete imported projects. This preserves the official fixture's deliberate duplicate while making it reviewable.
