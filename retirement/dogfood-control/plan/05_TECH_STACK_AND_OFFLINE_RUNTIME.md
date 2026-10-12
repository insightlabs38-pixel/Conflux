# Technology Stack and Offline Runtime

Conflux is designed to run locally and offline after dependencies and images are cached. The application uses a generic S3-compatible adapter and does not contain provider-specific domain logic.

## Object storage

- Primary offline object store: RustFS.
- Required compatibility target: SeaweedFS, exercised through the same S3 contract suite and an opt-in compatibility profile.
- Optional later compatibility/easter-egg target: ZeroS3. It is not a release dependency.
- `docker compose up` starts RustFS as the normal local object store. SeaweedFS and ZeroS3 are compatibility targets, not ordinary runtime dependencies.

Presigned uploads/downloads, metadata, overwrite, listing and multipart behavior must be tested through common S3 semantics. Provider configuration stays behind the generic adapter.

## Execution environment

The development VM caches ARM64-compatible RustFS and SeaweedFS images and supports offline startup. Runtime health and storage compatibility are separate checks; the default runtime remains intentionally small.
