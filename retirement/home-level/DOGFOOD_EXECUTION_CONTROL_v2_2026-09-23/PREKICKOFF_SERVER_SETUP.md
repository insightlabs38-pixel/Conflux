# Pre-Kickoff VM Setup (No Dogfood Project Code)

The VM may be fully provisioned and authenticated before kickoff. Dogfood application/project files must not be created before 2026-09-25 18:00 UTC.

## Machine baseline
Target: persistent Linux VM (planned Google C4A ARM64, 8 vCPU / 32 GB). Detect the actual OS/architecture first; do not assume package names blindly.

Install/verify, where supported:
- base: `git`, `git-lfs`, `curl`, `wget`, CA certs, `openssh-client`, `rsync`, `unzip`, `zip`, `xz`, `tar`;
- shell/inspection: `tmux`, `screen`, `ripgrep`, `grep`, `sed`, `awk`, `jq`, `yq`, `fd`, `fzf`, `tree`, `less`, `bat`, `lsof`, `socat`, `netcat`, `psmisc`, `procps`;
- monitoring: `htop`/`btop`, `iotop`, `sysstat`, `time`, `hyperfine` when available;
- build/native: `build-essential`, GCC/G++, Clang/LLVM, `lld`, `make`, `cmake`, `ninja-build`, `pkg-config`, `autoconf`, `automake`, `libtool`, `gdb`, `strace`;
- common Python/C-extension headers: Python dev/venv/pip tooling, `libpq-dev`, `libssl-dev`, `libffi-dev`, zlib/bzip2/lzma/readline/sqlite headers, JPEG/PNG/WebP headers, XML/XSLT/YAML/magic headers where available;
- DB/network clients: PostgreSQL client, Redis-compatible CLI, SQLite;
- quality/tools: `shellcheck`, `shfmt`;
- load/browser prerequisites: Playwright/Chromium system dependencies and a load tool such as k6 plus ordinary curl-based tooling.

Install a stable system Node LTS suitable for the planned React/Vite toolchain, enable Corepack, install current pnpm, and optionally Bun as a useful utility. Install/verify the system Python used for Django plus `uv` and `pipx`.

Install Docker Engine from Docker's official repository when possible, plus Buildx and the Compose plugin. Add the operator user to the docker group, re-login as needed, and verify a non-root `docker run` and `docker compose version`.

Install current CLIs from their official installation paths:
- Claude Code; run `claude doctor`;
- Codex CLI; verify the Linux ARM64 binary/install and `codex --version`;
- Freebuff CLI; verify `freebuff --version`;
- GitHub CLI; verify `gh --version`.

Authenticate Claude, Codex, Freebuff and GitHub before kickoff. Store PAT/secrets outside the future repository with restrictive permissions. Prefer a fine-grained GitHub PAT scoped to the blank Dogfood repository and expose it through a secure environment file, not committed `.env` or shell-history plaintext.

## Control-pack layout
Create:
- `/home/dogfood-control/releases/` — received ZIP/YAML artifacts;
- `/home/dogfood-control/plan/` — extracted product/architecture pack;
- `/home/dogfood-control/execution/` — extracted execution-control pack;
- `/home/dogfood-control/logs/`;
- `/home/dogfood-control/scratch/` — disposable rehearsal only;
- `/home/dogfood-worktrees/` — empty before kickoff;
- `/home/dogfood/` — keep absent/empty before kickoff.

Copy the two supplied ZIPs into `releases/`, verify hashes/archive integrity, extract each into a temporary directory, then move the single top-level directory from each ZIP to the canonical `plan/` and `execution/` locations. Preserve the original ZIPs in `releases/`. Copy the standalone BATCHES/TASKS YAML into `execution/` only if their version/hash matches the embedded versions; otherwise prefer the embedded canonical files and report the mismatch.

If `execution/freebuff-agents/` exists, copy those trusted user-owned definitions into `~/.agents/` after backing up any same-named existing files. Do not place them in the future Dogfood repository. Validate that Freebuff loads them from `~/.agents`.

## Generic dependency caches
Pre-pull/warm only generic dependencies, not project-generated files: common Postgres, Valkey, Caddy, Python, Node and selected S3-compatible object-store images may be cached. Playwright browser binaries/system deps and package-manager caches may also be warmed. Do not create Dogfood package manifests/lockfiles/Compose files merely to warm caches.

## tmux/control environment
Prepare a tmux layout/config for `status`, `freebuff`, `claude`, `codex`, `integration`, `verify`, `metrics`, `shell`. Do not start Dogfood implementation sessions before kickoff.

## Rehearsal
Use only `/home/dogfood-control/scratch/` to test:
- Git worktrees/branches in a throwaway repo;
- multiple tmux sessions;
- Claude/Codex/Freebuff startup/auth;
- Freebuff custom agents or role-prompt fallback;
- Docker/Compose;
- Python/Node native-extension compilation;
- Playwright Chromium;
- k6/load tooling;
- reboot/reconnect/tmux recovery.

Delete disposable project artifacts afterward. Do not clone/populate the real Dogfood repo or make Dogfood commits.

## Pre-kickoff final state
The public GitHub repository may exist but remains blank: no README/license/.gitignore/initial commit. `/home/dogfood` contains no submission project. Control packs, CLIs, credentials, caches and generic tooling are ready. Record versions and any ARM64 caveats in `/home/dogfood-control/SETUP_REPORT.md`.
