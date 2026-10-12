# Shared Runtime and Test Isolation

Exactly one canonical integration stack (`docker compose up`) runs from green main and is owned by the integration/runtime pane. Workers do not start competing full stacks.

Modes:
- NORMAL — normal integration/manual use.
- E2E — serialized browser/system tests.
- BENCHMARK — exclusive; no merges/restarts/other load against shared runtime.
- DEMO — exclusive freeze; no tests/resets/merges touching runtime.

Workers may run isolated unit/integration/property tests in worktrees with distinct test DB names/temp dirs/browser profiles. Shared E2E and load use locks.
