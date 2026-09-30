# Locking and Parallelism

The 330-batch DAG allows parallel work. `owned_paths` alone is not a safe parallelism guarantee.

## Parallelism test

Two mutating tasks may run concurrently only if all are true:

1. their batch/task dependencies allow it;
2. active `lock_groups` do not intersect;
3. their expected mutation paths do not overlap materially;
4. neither changes a canonical primitive consumed by the other;
5. neither performs a schema/data migration that affects the other's assumptions;
6. neither changes the same generated API/client/design contract;
7. there is no active escalation that invalidates their shared assumptions.

When uncertain, serialize.

## Lock classes

Typical lock groups include:

- `db-schema`
- `api-contract`
- `generated-sdk`
- `frontend`
- `web-shell`
- `design-system`
- `query-engine`
- `rich-document`
- `judging-core`
- `results-publication`
- `event-as-code`
- `extension-registry`
- `offline-sync`
- `authz`
- `archive-format`
- `deployment`
- `integration-main`

Existing batch `lock_groups` are the starting point, not the full runtime truth. The controller may add a temporary lock when the actual files/primitive reveal additional coupling.

## Main integration lock

Only one controller integration operation may mutate canonical main/integration state at a time.

Workers may continue in independent worktrees while another branch integrates, subject to dependency/lock safety.

## High-risk serialization

Default to one active mutator for:
- authorization model;
- database schema migration touching shared tables;
- canonical archive format;
- Event-as-Code ownership/apply semantics;
- judging normalization/ranking/result publication;
- design-system tokens/component foundations;
- extension capability/permission registry.

This can be relaxed only after the architecture contract explicitly partitions ownership.

## Verification parallelism

Read-only verification can run concurrently if it does not:
- mutate shared fixtures/database state used by another test;
- restart/replace the one shared application stack;
- change generated artifacts;
- contend for a singleton external resource.

## Dev server invariant

Do not start multiple competing Conflux application stacks merely because multiple agents are active.

Use the persistent approved dev/test stack where possible. Browser tests that require isolated state should isolate data/workspaces/events, not solve isolation by spawning uncontrolled duplicate servers.

## Ownership spillover

A worker that discovers a necessary change outside its expected ownership may:
1. make a small correctness-critical adjacent fix if it cannot be safely separated, and record it; or
2. escalate/request a dependent task.

Large cross-domain rewrites require controller approval before implementation.
