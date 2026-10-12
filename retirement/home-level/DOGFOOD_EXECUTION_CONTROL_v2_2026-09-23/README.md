# DOGFOOD 2026 — Execution Control Pack v2

Planning/control only. This pack is kept **outside the competition repository before kickoff**.

## Contents

- `BATCHES.yaml`: 109 coherent execution batches (34 Core/Core-gate/release, 24 Stretch, 50 Very Stretch).
- `TASKS.yaml`: 337 executable task records.
- agent/logistics/model-routing rules.
- verification campaigns and release gates.
- templates for current state, handoff, ownership, attention, escalation and worker receipts.

## Scheduling model

Human controls three visible lanes: Claude Code, Codex CLI, Freebuff Orchestrator. Claude/Codex consume coherent batches. Freebuff consumes unlocked fine-grained tasks and verification campaigns, launching isolated worker processes/worktrees after kickoff.

## Critical pre-kickoff rule

Do not create Dogfood project code, project scaffold, migrations, Compose config or Git commits before 2026-09-25 18:00 UTC. Pre-kickoff setup may install/authenticate tools, unpack this control pack outside the future repo, cache generic dependencies/images, and rehearse orchestration in a disposable generic scratch repo.

## v2.1 logistics refinements

- Claude/Codex normal prompts automatically choose the next eligible lane-appropriate batch; explicit IDs are overrides/escalations.
- strict session isolation: workers do not call/control other running coding-agent sessions.
- mandatory rg/grep/sed-first targeted retrieval.
- complete Luna pre-kickoff VM provisioning/extraction procedure and user-level Freebuff agent templates included.
