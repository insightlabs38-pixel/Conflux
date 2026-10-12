# Testing and Verification Strategy

## Principle
Enough testing to make important behavior hard to break; not a repository that is mostly repetitive tests.

## Ownership
Implementation agents write focused tests that express their feature semantics. Freebuff verification workers own breadth: matrices, property tests, fuzzing, fixture mutation, malformed input, RBAC permutations, browser scenarios and routine load runs. Frontier models enter for major gates, weird failures, concurrency/security/math/invariant bugs and final review.

## Prefer leverage over LOC
Use parameterization, generators, property tests and reusable harnesses. Disposable fuzz cases are not committed; minimize real failures into compact regressions.

## Verification layers
1. feature-local unit/API tests
2. continuous Freebuff verification campaigns
3. subsystem/core gates
4. release verification: offline Compose, official checker, E2E, import/export, migration, backup/restore and load/security smoke

## `make verify`
Should present concise evidence for official T1/T2 checks, internal T3/T4 proof, RBAC, deadline races, normalization fixture, import/export roundtrip, offline cold boot, restart persistence, migration/backup and bonus status.

## Shared runtime
Unit/property tests use isolated test DBs/worktrees. Shared E2E is serialized. BENCHMARK/DEMO modes obtain an exclusive runtime lock.
