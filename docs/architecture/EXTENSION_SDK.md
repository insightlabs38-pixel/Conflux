# Internal extension SDK v1

Import `extensions.sdk` after Django setup. It exposes the existing domain
contracts for code owned by the deployment. `SDK_VERSION = 1` identifies this
facade; it does not change `/api/v1` or canonical archive `format_version`.
Python protocols provide contributor type contracts; they are not runtime
permission checks or a plugin loader. Organizer requests cannot execute code.

| Family                | Contract                                                                                   | Integration boundary                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Artifact validators   | `ArtifactValidator(artifact, storage) -> ValidationResult`                                 | `artifacts.validators.VALIDATORS`; `inspect_artifact`/`validate_artifact`                        |
| Stage strategies      | `AdvancementStrategy.select(list[Candidate], **params) -> set[(subject_type, subject_id)]` | A unique class `slug` registers through the existing base class; `advance_stage` persists/audits |
| Assignment strategies | `AssignmentStrategy(plan, *, coverage=3) -> list[Pairing]`                                 | Existing heuristic/optimized computation and activation services                                 |
| Page blocks           | `PageBlockType` containing `title` and bounded `schema`                                    | `presentation.block_types.BLOCK_TYPES`, generated controls, `clean_config`                       |
| Archive converters    | `ArchiveConverter(archive, csv_text, mapping) -> dict`                                     | Convert source data into canonical v1, as `scripts.convert_project_csv.convert` does             |
| Import/export         | `ArchiveImporter`/`ArchiveExporter`                                                        | `import_archive`, `build_archive`, rollback-only `preview_archive_import`                        |

These definitions match the existing call signatures. Registry changes are
explicit application source changes loaded by the deployment. Use unique IDs
and slugs; replacing a built-in entry is a behavior change requiring its domain
review/tests, not a safe way to add an extension.

## Artifact boundary

`ValidationResult` contains `validator`, `outcome`, and `detail`. Existing outcomes
are `ok`, `warning`, `blocked`, and `retry`; missing uploads/temporary storage
failures cannot become ready evidence. Validators inspect without mutating;
`validate_artifact` locks and rejects stale inspection before persisting evidence.
New stored kinds must preserve metadata verification, active-content rejection,
attachment downloads, secret visibility and readiness rules. Add model choices,
stored/external classification, validators, API/schema/UI support and portability
tests together. Returning `ok` cannot replace stored-object verification.
See `ARTIFACT_SERVING.md`.

## Strategy boundary

Candidates use the complete `(subject_type, subject_id)` identity. Never merge
subjects by name or ID alone. Selection is separate from audited stage moves;
use `advance_stage` and existing transition/entry invariants. Assignment computation
returns `Pairing(judge_id, project_id)` using existing database identities;
activation owns frozen version/evidence, conflicts, coverage, connectivity,
transactional writes and audit. Computation must not persist assignments.
Normalization/pairwise math retains its existing domain APIs.

## Block boundary

Declare a code-owned `PageBlockType`; `normalize_config` implements the bounded
schema contract. `clean_config` additionally applies existing kind-specific
sanitization; use it before storage and retain safe public rendering.
`BLOCK_CONFIG_SCHEMAS.md` documents the subset, defaults, generated controls and
freshness commands. New persisted kinds need migrations/model choices and renderers;
a dictionary entry alone does not deploy a complete block.

## Import boundary

Converters return canonical data and do not create identities, call external
services, or write database rows. Reuse `import_archive` with explicit workspace,
archive, name and slug inside the caller's `transaction.atomic()`. It validates
each domain row and creates a private draft event; the caller retains workspace
authorization and mutation auditing. Prefer `preview_archive_import` for a
rollback-only preflight. Imported users must already exist; unknown versions and
references must fail rather than be guessed or dropped. Exports use documented
modes/sections; current archive limitations remain.

## Contributor verification

Add positive, negative and compatibility tests at the affected boundary. Include
artifact security/readiness tests, strategy identity/conflict/math tests, block
schema/sanitization/UI tests, or importer rollback/roundtrip tests as appropriate.
Regenerate/check OpenAPI/SDK artifacts for HTTP changes and block schemas for
schema changes. Run affected Core gates when their invariants change. The facade
adds no alternate authentication, persistence, publication or audit path.
