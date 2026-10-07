# Source of the committed handoff
- Revision: r2.1 (`DESIGN_MANIFEST.yaml` `design_revision`), approved 2026-09-30, QA ledger `reviews/R2_1_BOARD_QA.md` (45/45 boards opened).
- Delivered as `conflux_v3_claude_design_handoff_r2_1.zip` (repo root, owner's, untracked), sha256 `19c4da23c964cd37c6afe23a3a8a35cfcf7f94e0e199d7013658cd79e7497e2a`.
- Ingest check (2026-10-07, PD-DESIGN-B00-T01): `unzip` of that archive and `diff -rq` against `docs/product-depth-v3/design/` report no difference; the committed tree is authoritative and nothing depends on the hosted canvas or the zip.
- `tests/test_design_manifest.py` keeps the manifest honest: every reference id, artifact path and design ref used by the queue must resolve to a committed file.
