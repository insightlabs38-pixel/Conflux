# Conflux — GCP VM retirement manifest (2026-10-12)

Branch: `archive/gcp-vm-retirement-20261012` (based on `main` @ `86fd316b9e64e02607d7d7a28e9370eaf3cf789e`). Not for merging; all added material is under `retirement/`.

## Git state at retirement (all pushed to origin = github.com/insightlabs38-pixel/Conflux)
| Branch | Commit |
|---|---|
| main | 86fd316b9e64e02607d7d7a28e9370eaf3cf789e (WIP partial commit on top of 250 previously-unpushed commits; fast-forward from e1888de) |
| claude/C-B02 | cb6d3dffea3b3024e271cee705fbc548fc1889aa (newly pushed) |
| freebuff/RT-001 | b4be7a8938d761a624bb59edf00e7fe0183db583 |
| sol/BOOT-B00 | 3906bf1aac468fbb964c47e730f2817f335a0e3a |
| sol/C-B04 | b601d85383fcd4a3e21b5c802375e2affd8b9881 |

The top commit on main ("WIP (partial, uncommitted-at-retirement)") snapshots uncommitted working-tree edits (entity query/saved views/events, supervisor.py, tests/integration/test_grid_aggregates.py). It was NOT run through verify-fast and may be incomplete/failing. History was not rewritten.

## What is saved here (outside normal Git history)
- `retirement/home-level/` — design/review/agent prompts and bundles that lived in `~` (7 `.md` files, `conflux-ui-v2-media.zip`, `conflux_product_depth_v3_execution_bundle.zip`, DOGFOOD_EXECUTION_CONTROL_v2 / DOGFOOD_POST_SPEC_PLAN_v2 dirs + zips, and the three `conflux_v3_claude_design_handoff*.zip` that were untracked in the repo root).
- `retirement/dogfood-control/` — copy of `/home/dogfood-control` (campaign control plane): `bin/` supervisor scripts, plan/, execution/, handoffs/, releases/, backups/, run/ and logs/ (locks/pids removed), status reports. 
- `retirement/repo-ignored/` — gitignored-but-valuable repo files: `.dogfood/`, `.claude-supervisor/` QUESTIONS.md + logs + all session transcripts (`claude-supervisor-sessions.tar.gz`), `artifacts/` final-pass, final-demo-media (+zip), verify-final.log, e2e-fast-final.log.
- `retirement/systemd/` — `conflux-unattended.service|timer` user units.
- `retirement/freebuff-local-changes.patch` + `freebuff-base-commit.txt` — local modifications to the third-party clone `~/src/freebuff` (CodebuffAI/freebuff @ base commit; branch base2-subagents).
- `retirement/env/` — OS/tool versions, pip freeze, docker image/container/volume inventory, env-var NAMES only, Postgres non-empty-table row counts.

## Deliberately excluded
- Secrets: `~/conflux/.env`, `/home/dogfood-control/unattended.env`, `~/.config/dogfood/secrets.env` (GH token), `~/.config/gh`, `~/.ssh`. Variable names are in `retirement/env/`.
- Regenerable: `.venv` (4 of them), `node_modules`, caches, `__pycache__`, docker images/build cache, `artifacts/e2e-fast` (91 MB) and `artifacts/e2e-auth` screenshots/traces, `/home/dogfood-control/scratch` (test scratch, 28 MB), `.venv` of dogfood-control.
- Postgres/Valkey/RustFS docker-volume DATA (`conflux_db-data`, `confluxh00_*`, `confluxrel33_*`): dev stacks seeded by `make seed` / `scripts/demo-reset` (deterministic, shared demo password in docs). Not dumped: contains user rows/password hashes and is regenerable. Row counts recorded.
- `~/.codex` (5.8 GB agent session history), `~/.claude`, shell history: not project data.
- `~/src/freebuff` itself (third-party upstream clone; only local diff saved).

## Restore
```
git clone https://github.com/insightlabs38-pixel/Conflux && cd Conflux && git checkout main
uv sync   # uv.lock; Python 3.12; pnpm install (pnpm 12.x per env snapshot, node 24)
cp .env.example .env   # fill values
make up && make seed   # or: make demo-reset
git checkout archive/gcp-vm-retirement-20261012 -- retirement/   # to view archived material
```
Original locations: repo `/home/insightlabs38/conflux`, worktrees `/home/insightlabs38/conflux-worktrees/{claude-C-B02,freebuff-lane,sol-C-B04}`, control plane `/home/dogfood-control`. Services (user units, all disabled at retirement): conflux-unattended.service/.timer. Docker compose projects: conflux, confluxh00, confluxrel33 (stopped at retirement).
