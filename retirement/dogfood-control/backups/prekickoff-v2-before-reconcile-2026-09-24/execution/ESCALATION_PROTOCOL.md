# Escalation Protocol

## Severity/routing
P0: data corruption, auth leakage, deadline bypass, broken invariant, migration failure, critical race → Claude immediately.
P1: domain behavior, major perf regression, normalization/stage mismatch, cross-module architecture bug → Claude or Sol by reasoning vs implementation complexity.
P2: ordinary incomplete feature/integration/UI bug → Codex or Freebuff.
P3: visual/copy/accessibility polish → Freebuff.

## Freebuff retry
1. normal attempt;
2. at most one fresh-context correction with failure evidence when scope remains mechanical;
3. still failing: split if oversized, Codex if implementation-hard, Claude if architecture/unexplained/security/concurrency/math, infra owner if environmental.

## Packet contents
ID, source tasks/batches, severity, recommended harness/model, reason, attempts, observed failure, reproduction, relevant files, required reading, invariants, requested outcome, blockers/unlocks.

## Batch escalations
Related packets sharing subsystem context should be combined into a single Claude/Codex remediation batch to exploit context amortization.
