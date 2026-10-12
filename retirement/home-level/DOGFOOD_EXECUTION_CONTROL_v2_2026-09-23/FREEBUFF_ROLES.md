# Freebuff Role Definitions

Use reusable user-level custom agents (kept outside the competition repo before kickoff):

1. `dogfood-orchestrator` — read/status/schedule/launch only; no product editing.
2. `dogfood-backend` — Django/domain/API scoped implementation.
3. `dogfood-frontend` — React/builders/public/operator UI.
4. `dogfood-verification` — matrices/property/fuzz/adversarial/E2E/load; prefers tests/harnesses and minimized regressions.
5. `dogfood-polish` — UX/accessibility/responsive/loading/empty/error/copy only; no new domain semantics.
6. `dogfood-ops` — Compose/CI/scripts/seeds/docs/health/backup/release.
7. `dogfood-review` — read-only by default; structured findings.
8. `dogfood-integration` — conservative merge/schema/contract/build repair; not a feature developer.

Multiple worker instances may use one role definition. Role definitions are not worker-count limits.
