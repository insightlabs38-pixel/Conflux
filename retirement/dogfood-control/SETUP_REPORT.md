> **Superseded:** The routing, custom-agent and pack details below describe the earlier setup state. See [FINAL_PREKICKOFF_REPORT.md](/home/dogfood-control/FINAL_PREKICKOFF_REPORT.md) for the reconciled 2026-09-24 state.

# CONFLUX / DOGFOOD 2026 Pre-kickoff VM Setup

Updated 2026-09-24 UTC. Reboot and snapshot were skipped as explicitly requested.

## Machine and storage

- Ubuntu 24.04.5 LTS, GCP kernel 7.0.0-1011-gcp, ARM64 (`aarch64`), 8 Neoverse-V2 vCPUs, 31.3 GiB RAM.
- Swap: functioning 4 GiB `/swapfile`, currently unused; swappiness 10.
- Disk before: 100 GiB NVMe device, 49 GiB root partition, 48 GiB ext4 root filesystem, 35 GiB free. Layout was GPT, non-LVM, root `/dev/nvme0n1p1`; EFI and boot partitions were separate.
- Expanded safely with `growpart /dev/nvme0n1 1` then online `resize2fs /dev/nvme0n1p1`. After: 99 GiB root partition, 96 GiB ext4 filesystem, 82 GiB free. No filesystem was formatted. The root volume now uses the available disk capacity.
- UTC timezone; `timedatectl` reports clock synchronized and NTP active.

## System tuning

- `/etc/sysctl.d/99-conflux-dev.conf`: `vm.swappiness=10`, `fs.inotify.max_user_watches=1048576`, `fs.inotify.max_user_instances=1024`, `fs.file-max=2097152`.
- `/etc/security/limits.d/99-conflux-dev.conf`: user `insightlabs38` soft nofile 65536, hard nofile 1048576. The already-running shell still has its original `ulimit -n` 1024; PAM applies the new value on a fresh SSH/login session.

## Toolchain

- Docker Engine 29.8.1; Compose v5.5.1; Buildx v0.37.1 with running BuildKit and `linux/arm64` support. Docker works as the normal user (docker group). No containers are running.
- Python 3.12.3, pip 24.0, pipx 1.4.3, uv 0.12.18. Control-only Python environment is `/home/dogfood-control/.venv`; no app environment exists.
- Node v24.21.0, npm 11.19.0, pnpm 12.6.0, Corepack 0.36.0.
- Git 2.43.0, Git LFS 3.4.1, GitHub CLI 2.101.0. Global identity set to `insightlabs38-pixel <insightlabs38@gmail.com>`, rerere enabled, `zdiff3` conflict style, and `gc.auto=256`.
- Codex CLI 0.156.1 (ARM64, ChatGPT login verified); Claude Code 2.1.281 binary present, authentication not checked/performed; Freebuff 0.0.188 binary present, authentication not performed.
- Playwright 1.63.0 with cached Chromium 153 ARM64; disposable headless launch passed. k6 2.3.0 ARM64 launches. PostgreSQL client 16.15, redis-cli 7.0.15, SQLite 3.45.1.
- Compiler/build stack is present: build-essential, GCC/G++ 13.3, Clang/LLVM 18.1, LLD, make, CMake 3.28, Ninja 1.11, pkg-config, Autoconf, Automake, Libtool, Python/PostgreSQL and common image/XML/YAML/crypto development headers. ShellCheck 0.9, shfmt 3.8, valgrind and ltrace installed.
- Generic CLI coverage includes git-lfs, rg, GNU grep/sed/awk, jq/yq, fd (`~/.local/bin/fd`), fzf, tree, bat (`~/.local/bin/bat`), less, parallel, entr, inotify-tools, rsync, tmux/screen, curl/wget/HTTPie, socat/netcat, DNS/iproute tools, lsof, htop/btop, sysstat, iotop/procps/psmisc, hyperfine, GNU time, strace and gdb.
- Caches remain in normal persistent home locations: Docker `/var/lib/docker`, uv `~/.cache/uv`, pip `~/.cache/pip`, npm `~/.npm`, pnpm `~/.local/share/pnpm`, Playwright `~/.cache/ms-playwright`, and model CLI home caches.

## Docker cache

- Cached ARM64 images: `postgres:17`, `valkey/valkey:8`, `caddy:2`, `ghcr.io/rustfs/rustfs:latest`, `chrislusf/seaweedfs:latest`, `python:3.12-slim`, `node:24-slim`, and `hello-world:latest`. RustFS and SeaweedFS image metadata both report `linux/arm64`.
- `docker system df`: 2.249 GB images; no containers, volumes, or build cache. No pruning was performed.
- `/home/dogfood-control/bin/conflux-disk` displays filesystem, Docker, and worktree disk use.

## Control environment

- Control packs are preserved in `releases/`; `sha256sum -c releases/SHA256SUMS` and both ZIP integrity checks pass. Plan files are directly in `/home/dogfood-control/plan/`; execution files, canonical `BATCHES.yaml` and `TASKS.yaml`, are directly in `/home/dogfood-control/execution/` and parse as YAML. No standalone YAML copies were supplied for comparison.
- Canonical pack hashes: plan `bd1768c827ac3aa01f0675bea30ff79344a62d773c848d62c5ecedf3f7252038`; execution `9d44f6d4c53039753bb7936f2de703fc8bc16e3a65217842e8259f4a01fbdad8`.
- Eight trusted user-level Freebuff definitions from `execution/freebuff-agents/` are installed in `~/.agents/` (directory 0700, files 0600). No repository-local agents or registry agents were added. Discovery awaits owner authentication.
- `~/.config/dogfood/` is 0700 and `secrets.env` is 0600. `dogfood-secrets` safely loads configured variables in a shell; the value of secrets is not in this report or control packs.
- `/home/dogfood-control/runtime-mode` is `NORMAL` (0600). Runtime-mode validation and the external kickoff guard are installed in `bin/`. The guard was checked and refuses before `2026-09-25T18:00:00Z`. Worker helpers are generic and do not create a repo, branch, worktree, or source.
- `/home/dogfood-control/bin/conflux-status` reports readiness without inspecting an application. `/home/dogfood-control/bin/conflux-session` prepares/attaches the primary tmux session. Session `conflux` is present with windows/panes: status 2, freebuff 2, claude 1, codex 1, integration 3, verify 2, metrics 3, shell 2. The windows are placeholders/host monitoring; no agents or implementation were launched. Tmux has 100,000 lines of history, mouse support, truecolor, UTF-8, and detach/reconnect behavior.

## Authentication and recovery

- GitHub authentication is available through the protected secrets file. Read-only API verification of `insightlabs38-pixel/Conflux`: repository size 0; contents endpoint reports empty; commits endpoint reports empty repository.
- Codex authentication reports ChatGPT login. Claude Code and Freebuff logins remain owner-managed and were not attempted.
- Reboot validation was skipped as requested. Snapshot was skipped as requested; authenticated GCP service account tooling exists, but snapshot creation was not attempted.

## Pre-kickoff compliance

- Implementation unlock: **NO** until 2026-09-25 18:00 UTC. No BOOT-B00 started.
- No Conflux clone or local Conflux Git history exists. `/home/dogfood-worktrees/` is empty; no `/home/conflux*` checkout exists. No Conflux source, application scaffold, manifests, migrations, tests, Docker Compose, Dockerfiles, app docs, branches or commits were created.
- The GitHub Conflux repository remains blank. No repository writes, branches, issues, releases, actions, or pushes were made.

## Remaining owner actions

- Complete Claude Code and Freebuff sign-in when appropriate.
- Reconnect through SSH/login to activate the configured 65,536 soft file descriptor limit.
- Provide/rotate a GitHub PAT only if the current protected credential stops working.

## Reconciliation amendment — 2026-09-24

This earlier setup report is superseded for execution routing and pack state by `FINAL_PREKICKOFF_REPORT.md`. The eight Conflux/Dogfood Freebuff custom definitions have been backed up under `backups/freebuff-custom-agents-disabled/` and removed from the active execution pack and `~/.agents/`. No unrelated user agents were changed. Freebuff now uses one serial GLM bulk lane; its exact source-checkout executable is pinned in `execution/FREEBUFF_RECOVERY.md` and was not updated/rebuilt. The active execution package has no custom agents. Updated v2.2 packs and standalone queue YAML are listed in the final report.
