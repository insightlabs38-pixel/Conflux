# Final pre-kickoff infrastructure/control report — 2026-09-26 UTC

This section supersedes earlier schedule/timer statements below. **The campaign is not started.** Current configured start remains in the future.

## Schedule and startup

The only authoritative schedule values are in [`unattended.env`](/home/dogfood-control/unattended.env): `CONFLUX_START_UTC=2026-09-26T18:00:00Z` and `CONFLUX_END_UTC=2026-09-29T18:00:00Z`. H+ milestones, including H48/H60/H68, are derived from the start. The enabled user timer is generated from this configuration, exact to the second, with `Persistent=true`; the service is inactive and awaits the timer. Systemd has explicit HOME/PATH, dependency/auth/lock/repository preflight checks, persisted phases (`WAITING_FOR_START`, `PREFLIGHT`, `BOOTSTRAPPING`, `BOOT_VERIFY`, `FANOUT`, `RUNNING`, `DEGRADED`, `HANDOFF`, `STOPPED`), idempotent BOOT marker handling, and bounded restart policy. Startup failure is persisted and surfaced in attention state. `conflux-schedule` now handles an unloaded unit without leaving a half-written schedule.

## Usage handoffs and recovery

External handoffs are stored in `/home/dogfood-control/handoffs/{claude,sol,luna,freebuff}/<unit>.md`. [`conflux-handoff`](/home/dogfood-control/bin/conflux-handoff) records unit, lane/model, branch, worktree, HEAD, phase, objective, dirty paths/diff summary, checkpoint fields, next actions, blockers, and continuation safety. Worker prompts require meaningful checkpoints. Quota, auth, hang/watchdog, and pre-integration paths checkpoint before session replacement. Recovery keeps the same lease/worktree and sends a targeted continuation prompt; it does not resend the original assignment. A completed `done` receipt is integrated before any model relaunch. Optional WIP commits remain an agent judgment for substantial work.

Owner controls:

- `/home/dogfood-control/bin/conflux-control provider-status`
- `/home/dogfood-control/bin/conflux-control provider-pause claude`
- `/home/dogfood-control/bin/conflux-control provider-pause codex` (`codex` pauses/resumes both Sol and Luna)
- `/home/dogfood-control/bin/conflux-control provider-pause freebuff`
- `/home/dogfood-control/bin/conflux-control provider-resume claude|codex|freebuff`

`sol` and `luna` are also accepted for individual lanes. Unknown reset times stay paused until owner/provider confirmation. Explicit reset times are surfaced and retried after the reset. Provider state is tracked per lane; an unavailable provider does not stop other runners.

The supervisor polls every ~25 seconds. It records runner/TUI presence, unit lease, lane pause, logs, and handoff ages; it does not treat quiet model output alone as a hang. Headless model wrappers retain the existing 40-minute inactivity and generous wall bounds. [`AUTONOMOUS_STATUS.md`](/home/dogfood-control/AUTONOMOUS_STATUS.md) is regenerated during polling and at handoff, with main/tier/Core state, active units, provider/reset state, handoff freshness, failures, Freebuff age, and footage state.

## Freebuff

The existing pinned source build and GLM 5.3 Flash route remain unchanged. Freebuff pane capture is polled and redacted. One TUI session is reused across completed serial tasks while its usage window is active: after each receipt and integration, the runner sends the next task as a normal message. A stable isolated Freebuff worktree path is used, with one task branch at a time; the branch rotates only after integration. The 50-minute mark is informational only. On the explicit ended-session UI, the runner never presses Continue: it waits for an active task's receipt, then starts a fresh TUI for the next task. If the session ends before a receipt, the lease/worktree/handoff are retained and the same task resumes in a fresh TUI. Actual account quota/auth errors pause without hammering; custom agents remain untouched.

## Video assets and UI stability

[`VIDEO_WORKSTREAM.md`](/home/dogfood-control/execution/VIDEO_WORKSTREAM.md) holds the canonical seven-beat demo story, 8–12 minute raw-footage target, 8–14 clip guidance, optional T3/T4 library, narration, baseline, H60/H68 stability, recapture, and delta rules. [`VIDEO_QUEUE.yaml`](/home/dogfood-control/execution/VIDEO_QUEUE.yaml) contains operational-only Core/H48/Stretch/final items. The supervisor queues Core capture only after all eight Core gate signals are true; `/home/dogfood-control/bin/conflux-unattended video-gate status|set` manages evidence-backed signals. `/home/dogfood-control/bin/conflux-unattended video-gate set SIGNAL true --evidence ...` records auditable readiness evidence; this is needed for the manual-review/UI-coherence signals; H48 insurance is derived as start + 48 hours and queues every currently stable scene if a full H-package does not exist. These items never block product work.

[`conflux-video-agent`](/home/dogfood-control/bin/conflux-video-agent) dispatches the operational unit to a fresh GPT-6 Luna session; [`conflux-video-capture`](/home/dogfood-control/bin/conflux-video-capture) and its Playwright harness capture each scene separately at 1920×1080, make screenshots, manifests, narration text, baseline YAML, and status. Each failed scene is recorded while successful clips remain. The capture holds the integration lock and sets DEMO runtime mode; it restores the prior mode in `finally`. [`conflux-video-package`](/home/dogfood-control/bin/conflux-video-package) creates named archives without overwriting prior packages. No Fish Audio call or final video assembly is made.

## Validation performed

- Python compilation, Node syntax check, and `systemd-analyze --user verify` passed.
- Generated timer shows the exact configured calendar event, `Persistent=true`; timer is active/waiting and service is inactive.
- Scratch supervisor state simulations passed exact-start fanout/end handoff, late/persistent trigger continuation, preflight-state restart, post-bootstrap recovery without rerunning BOOT, and duplicate-launch lock refusal. VM restart test was skipped as requested.
- Scratch controller reconciliation released one synthetic stale lease and restored only its task to READY. Poll health collection, operational video queue dispatch/quota no-hammer behavior, and done-receipt integration recovery-before-model-relaunch passed with tmux mocked. Freebuff mocked-TUI cases passed for two normal tasks in one instance, waiting through the ended-session wrap-up and task receipt before recycling, resuming the same incomplete task when no receipt exists, and never pressing Continue. A disposable Git remote verified serial worktree branch rotation only after integration. Explicit versus unknown reset-time handling was checked with synthetic provider logs.
- Scratch handoff test captured a synthetic commit plus dirty-path diff and emitted a recoverable checkpoint. Provider pause/resume controls passed on a synthetic Codex quota; classifier fixtures returned QUOTA, AUTH_FAILURE, and SUCCESS.
- Scratch video gate simulation passed the H48 trigger and all-signals Core trigger. Disposable local page capture produced WebM, screenshot, baseline, shot manifest, narration draft, and a valid ZIP. A deliberately failing scene left the successful scene/package artifacts intact and recorded the failure.
- Scratch integration tests confirmed a rebase conflict is aborted with the worktree preserved and task routed to REVIEW, and a failing verification command prevents bootstrap-green/main integration. Existing isolated successful ordinary-task/bootstrap integration dry-run evidence from the prior report remains applicable; integration code was not replaced.
- The exact GPT-6 Luna subscription probe returned `LUNA_SUBSCRIPTION_READY` in a scratch repository (13,497 input tokens, 11,008 cached, 10 output); earlier Claude Sonnet 5 and GPT-6 Sol auth probes are recorded below. No campaign task was issued.

## Kickoff boundary and remaining limits

No Conflux source, local clone/worktree, project commit, BOOT-B00, or product implementation was created. The configured repository/worktree locations are absent; no request was made to the configured remote during this work. The persistent startup state has no bootstrap-green marker or active lease, and the service is stopped until H0. Only external control files and disposable scratch assets were used.


**There is no live seeded Conflux demo or Conflux footage package.** The only footage currently on disk is a 7.3-second capture of a disposable static test page at `/home/dogfood-control/scratch/video-test/out/`; its “seed/demo state” is explicitly labeled “disposable static fixture.” The capture scripts, manifest, narration, baseline, and ZIP workflow were exercised against that fixture only. `run/demo-url.txt` and the bootstrap-green marker are absent. The live Core gate and actual Conflux footage cannot be validated until after kickoff and a coherent product/demo dataset exist. Gate signals remain false until their evidence is recorded. This is the remaining footage dependency, not a claim that live-demo assets were already produced.

The queue now dispatches one fresh GPT-6 Luna video unit in a dedicated tmux session; restart recovery resumes from the compact handoff, quota pauses wait for an owner/reset, and a reset command requeues it. The installed subscription-auth probes predate this delta, and real quota/reset behavior remains provider-controlled. No early campaign work has begun.

## Freebuff usage-window correction — 2026-09-26 UTC

The intended policy is now explicit: keep the same Freebuff session and send each next task as a standard message while its usage window remains active. A usage-limit/ended-session signal is recorded, but does not interrupt a task already running. Once that task has a receipt and integration, the old TUI is closed without pressing Continue; the next task starts in a fresh TUI. If the session ends before a receipt, the current lease/worktree/handoff remain owned and that same task resumes in a fresh TUI. The prior 55-minute timeout is removed; 50 minutes is informational only. The serial lane uses a stable dedicated worktree directory and rotates its task branch only after integration. Mocked scratch checks cover session reuse, same-task recovery after rollover, new-session creation after a completed task, and not sending Continue; actual provider rollover was not forced.

## Corrective append — footage gates and crash recovery — 2026-09-26 UTC

The controller now requires a `footage_impact` receipt disposition whenever the real `/home/dogfood-control/demo-assets/FOOTAGE_BASELINE.yaml` exists. Scene IDs are checked against that generated baseline, task-scope review must be recorded, and scoped UI work requires affected-scene run and screenshot evidence. Baseline-valid claims require both evidence types per named scene. At H60–H68, broad redesign and recapture-required changes are rejected. At H68+, broad redesign is rejected and UI changes require scoped critical fixes; no-visual-change work can continue. Recapture must name invalidated baseline scenes and provide replacement-scene and screenshot evidence. The freeze is applied at integration, not inferred from touched UI paths. No route/component list is invented before capture creates the manifest.

Every supervisor poll now writes `/home/dogfood-control/run/recovery/<unit>/snapshot.json` and working/staged diff patches for owned active units. The snapshot includes lease/controller state, branch/HEAD/status, receipts/verification results, latest redacted execution tail, and the latest agent-authored checkpoint with its actual authored time/age. Controller-only handoff refreshes preserve checkpoint authorship and timestamp; legacy notes retain unknown age. Continuation prompts point to both the handoff and passive snapshot. Capture is passive; no recurring model prompts were added. Freebuff retains its stable isolated worktree and per-task branch rotation.

Focused scratch-only validation was run for checkpoint timestamp preservation, recovery snapshot collection from a synthetic dirty Git worktree, footage receipt/freeze acceptance and rejection, plus source syntax checks. No Conflux repository or intended remote was accessed.

---

# Final Pre-Kickoff Report — Conflux / DOGFOOD 2026

Updated 2026-09-24 UTC. Implementation window begins 2026-09-25 18:00 UTC. No product implementation was started.

## Packs and validation

New packs:

- [Conflux post-spec plan v2.2 ZIP](/home/dogfood-control/releases/CONFLUX_POST_SPEC_PLAN_v2.2_2026-09-24.zip) — SHA-256 `2b3c90d85a83bf9111b6cbbfd70820111b6f3d4cb0b9099b0b8678c2d5c63a55`.
- [Conflux execution control v2.2 ZIP](/home/dogfood-control/releases/CONFLUX_EXECUTION_CONTROL_v2.2_2026-09-24.zip) — SHA-256 `ce1d885dedbfcb9859c15de820fd3c456bb3f8cf7f2529313c3ee48ad1b112eb`.
- [Standalone batches YAML](/home/dogfood-control/releases/CONFLUX_BATCHES_v2.2_2026-09-24.yaml) — SHA-256 `5873cc8b95d5ecd3695bf6c589dc4f763d57718d087549da96575d0afacf27d9`.
- [Standalone tasks YAML](/home/dogfood-control/releases/CONFLUX_TASKS_v2.2_2026-09-24.yaml) — SHA-256 `c79b36c21672d0e3f5ac595088fbd7eca0fbb0699f97b02f142b80ac1e7bbd89`.

Both ZIPs have one clean top-level directory, pass archive integrity checks, and match their file-manifest sidecars. The standalone YAML hashes exactly match the execution ZIP's embedded YAML. The original v2 ZIPs remain unchanged in `releases/` and have preserved backups. The original named standalone YAML copies were absent during inventory; the old ZIP-embedded BATCHES/TASKS matched the untouched pre-edit canonical files. Pre-edit backups and SHA-256 manifest are under `backups/prekickoff-v2-before-reconcile-2026-09-24/`.

YAML and DAG validation passed: unique IDs, valid dependencies/membership, no cycles, documented executor enums, boolean eligibility, no high-risk or human-preferred bulk tasks, human-only Stretch promotion gate, ART-006 in C-B09, and VS31-03 in VS31. Counts: **109 batches; 339 tasks**.

## Queue and routing

Batch preferences: bulk 50, Sol 40, Claude 13, shared Claude/Sol 5, human 1. Task preferences: bulk 101, Sol 158, Claude 64, shared Claude/Sol 15, human 1. **285 tasks are bulk-eligible; 54 are excluded** (including all 36 high-risk tasks and the human gate). Pre-kickoff, all 339 tasks remain BLOCKED and zero tasks are claimable.

- **Claude local:** senior reasoning and coherent senior batches; owner-controlled.
- **Codex GPT-6 Sol:** coherent senior implementation/integration batches.
- **Codex GPT-6 Luna:** one bulk task per invocation; initial concurrency cap 1, expansion awaits H0/H1 quota probe.
- **Freebuff:** one serial GLM 5.3 Flash bulk task lane; no orchestrator/custom-agent dependency. Provider-built-in helpers remain internal to the session. Custom Conflux/Dogfood agents were disabled after the current HTTP 403.
- **Claude Code Cloud:** owner-controlled reserve; approximately $100 promotional credit, separate environment, not normal scheduling.

## Freebuff pin and controller

The preserved source build is `/home/insightlabs38/src/freebuff/cli/bin/freebuff`, CLI version `0.0.189-base2.1`, source commit `1c7005e38693719d32bee3427db690b217718e85`, Node `v24.21.0`. Its executable SHA-256 is `ba54e37790ec01defce0b1e3a47f4c5908037d107f766ce2d143527194c7bb37`. Recovery wrapper and owner-managed config location are documented in [FREEBUFF_RECOVERY.md](/home/dogfood-control/execution/FREEBUFF_RECOVERY.md). The source checkout had pre-existing local modifications; they remain untouched. No npm build was substituted, no update/rebuild was performed, and no Claude/Freebuff authentication or private session was accessed. Eight matching user-level definitions and the pack copies are backed up under `backups/freebuff-custom-agents-disabled/`; unrelated agents were left alone.

[conflux-control](/home/dogfood-control/bin/conflux-control) is external to the product repo and uses `flock` plus atomic writes for canonical queue/ownership mutations. Commands include `status`, `next-batch`, `next-task`, `claim-batch`, `claim-task`, `reserve`, `release`, `review`, `done`, `block`, `reconcile`, `capacity`, `note`, and human-confirmed `open-gate`. Claims check kickoff time, dependencies/gates, executor and bulk eligibility, reservations, path overlap, human-only work, one-Freebuff-task cap and configured Luna cap. No autonomous lane edits canonical queue YAML directly. Luna start/attach wrappers are prepared for post-kickoff use only.

## VM and storage

The primary tmux session now has: `0 status`, `1 freebuff`, `2 claude`, `3 codex-sol`, `4 luna`, `5 integration`, `6 verify`, `7 metrics`, `8 shell`. Existing panes were preserved; the three Luna panes are placeholders, with #2/#3 disabled by the cap. No agent was launched.

The 100 GB disk state and 4 GB swap remain intact (96 GB root filesystem, about 79 GB free). Docker 29.8.1 / Compose 5.5.1, Python 3.12.3, Node 24.21.0 and Codex CLI 0.156.1 are present. Docker has no running containers. Cached RustFS and SeaweedFS images both report `arm64/linux`. `CONFLUX_CONTROL_ROOT`, `CONFLUX_PLAN_ROOT`, `CONFLUX_WORKTREE_ROOT`, and `CONFLUX_REPO_ROOT` are configured for login shells and tmux; they contain no secrets. Conflux uses generic S3 semantics: RustFS default, SeaweedFS required compatibility profile, ZeroS3 optional and noncritical.

The public GitHub API reports the Conflux repository size is zero, branches are empty, and commits return “Git Repository is empty.” Local `/home/conflux` and `/home/conflux-worktrees` remain absent. The prior empty `/home/dogfood-worktrees` directory was preserved.

## Remaining owner actions

At kickoff, owner-controlled sessions may be authenticated/launched as needed; run the Sol + Luna #1 capacity probe on real independent work before enabling Luna #2/#3. Resolve the organizer checker clarification if useful; it remains nonblocking. No additional pre-kickoff action is required.

## Kickoff-boundary compliance

- The Conflux GitHub repository remains blank; no local Conflux source or Git history exists.
- No application code, Django/React/Vite scaffold, product manifest, Docker/Compose project file, or product commit was generated.
- BOOT-B00 has not started. No product task was claimed or performed.
- Official copied specification/checker/fixture files under `plan/official/` were not modified.

## Unattended setup update — 2026-09-25 01:38 UTC

**Campaign status: NOT ARMED.** The exact requested trigger is `2026-09-25 18:00:10 UTC`. The production timer unit is installed but disabled, and the service has not been started. Per owner direction, setup must not launch campaign work; the owner will authenticate GitHub and provide the exact remote origin before production activation. The campaign supervisor also independently refuses any run before `2026-09-25T18:00:00Z`.

- **Claude:** `HEADLESS_SUBSCRIPTION` selected after successful `systemd --user` noninteractive print check. Exact `claude-sonnet-5`, effort `high`, `--dangerously-skip-permissions`, and `DISABLE_AUTOUPDATER=1`; response was `CLAUDE_SUBSCRIPTION_READY`. `claude auth status --text` identifies a Claude Pro account. No Anthropic API-key/auth/base-URL variables in environment or user manager; `~/.config/anthropic/` does not exist. No credentials were deleted.
- **Sol:** `gpt-6-sol`, `model_reasoning_effort=medium`, full unattended mode; harmless `systemd --user` `codex exec` returned `CODEX_SUBSCRIPTION_READY`. Login status says “Logged in using ChatGPT”. `OPENAI_API_KEY`, `CODEX_API_KEY`, and `CODEX_ACCESS_TOKEN` were absent from both shell and user manager.
- **Luna:** pinned to `gpt-6-luna`, medium in wrapper policy; concurrency remains exactly one. No Luna execution was started.
- **Freebuff:** pinned path is `/home/dogfood-control/bin/conflux-freebuff-source` → `/home/insightlabs38/src/freebuff/cli/bin/freebuff`, version `0.0.189-base2.1`, GLM 5.3 Flash. This deliberately bypasses the npm-global command. One isolated scratch TUI returned `FREEBUFF_BRACKET_READY` through the bracketed-paste driver. No custom agents used. No campaign Freebuff session remains running.
- **Control:** existing canonical roots remain `/home/dogfood-control/execution` and `/home/dogfood-control/plan`; no DAG change. Controller copy claim was refused by the pre-kickoff guard. New bootstrap prompt and operational wrapper policy specify Sol → Claude → Luna bootstrap fallback and exclusive BOOT-B00. NOTE: this initial supervisor build currently stops at preflight/bootstrap-ready and does not yet implement production lane loops/integration; do not arm it yet.
- **Resilience artifacts:** supervisor lock/state paths are `/home/dogfood-control/run/unattended.lock` and `unattended-state.json`; logs path is `/home/dogfood-control/logs/unattended/`. Outcome classifier synthetic fixtures returned QUOTA, AUTH_FAILURE, and SUCCESS; `timeout` hang fixture returned 124; integration lock excluded a competing lock holder. Transient systemd user timer fired as scheduled in scratch. No campaign timer test or campaign service was run.
- **Systemd:** user lingering is enabled (`Linger=yes`). Units are `conflux-unattended.timer` and `.service`; timer is loaded but disabled/inactive. Timer definition has `OnCalendar=2026-09-25 18:00:10 UTC`, `AccuracySec=1s`, `RandomizedDelaySec=0`, `Persistent=true`. The only systemd service invocation was the two harmless subscription-auth checks in `/home/dogfood-control/scratch/auth-check`.
- **GitHub:** `gh auth status` reports no authenticated host. No repo URL was configured in the canonical pack; guessed `insightlabs38/conflux` lookup returned 404, so no assertion is made about the actual remote. Awaiting owner's exact URL/auth. `/home/conflux` and `/home/conflux-worktrees` remain absent.
- **Kickoff boundary:** current UTC was `2026-09-25T01:38:23Z`, NTP synchronization was `yes`; this is before kickoff. No Conflux clone or local Git history, Conflux application source, project commits, or BOOT-B00 execution exists. The earlier 2026-09-24 setup report had observed an empty repository at that time; reverify the owner-specified remote after its URL/auth are supplied.

Owner recovery commands are available via `/home/dogfood-control/bin/conflux-unattended {status|stop|resume|attach-claude|attach-sol|attach-luna|attach-freebuff|worktrees|attention|handoff|disable-timer}`. Production activation is deliberately deferred until GitHub authentication and the exact remote are supplied and the incomplete supervisor is completed and validated.

## Final unattended setup — 2026-09-25 02:24 UTC

**Campaign timer: ARMED. Service: NOT STARTED.** The production timer is enabled and waiting for exactly `2026-09-25 18:00:10 UTC`; `systemctl --user status conflux-unattended.service` is `inactive (dead)`. I did not manually start it. The unit independently enforces H0 and synchronized NTP before cloning or invoking any model.

### Owner-supplied GitHub origin

`gh auth status` verifies the active `insightlabs38-pixel` account with HTTPS Git operations. `https://github.com/insightlabs38-pixel/Conflux` currently reports `isEmpty: true`, no default branch, and `git ls-remote` returns no refs. The URL is stored in mode-0600 `/home/dogfood-control/unattended.env`; it contains no credential. Startup repeats auth, identity, blank-state, and remote-ref checks. Neither `/home/conflux` nor `/home/conflux-worktrees` exists yet.

### Pinned lanes and authentication

- **Claude:** `HEADLESS_SUBSCRIPTION`. The exact `systemd --user` `claude --model claude-sonnet-5 --effort high --dangerously-skip-permissions --print` test returned `CLAUDE_SUBSCRIPTION_READY`; `claude auth status --text` reported the owner’s Claude Pro account. Production commands use only a fresh service-owned session and set `DISABLE_AUTOUPDATER=1`. No Anthropic API environment variables or `~/.config/anthropic/` credential files were found; nothing was disabled or deleted.
- **Sol:** `gpt-6-sol`, medium reasoning, `--dangerously-bypass-approvals-and-sandbox`. The pinned `systemd --user` ChatGPT-authenticated exec returned `CODEX_SUBSCRIPTION_READY`. No OpenAI/Codex API-key variables were present in the shell or user manager.
- **Luna:** `gpt-6-luna`, medium, same unattended permission mode. One worker is launched; no additional Luna lane is started automatically. Sol quota does not stop Luna.
- **Freebuff:** `/home/dogfood-control/bin/conflux-freebuff-source` launches the pinned source build at `/home/insightlabs38/src/freebuff/cli/bin/freebuff`, version `0.0.189-base2.1`, SHA-256 `ba54e37790ec01defce0b1e3a47f4c5908037d107f766ce2d143527194c7bb37`. It runs one serial interactive TUI on GLM 5.3 Flash; startup checks the visible route. The bracketed-paste helper passed its harmless scratch prompt test. npm’s global Freebuff command and custom agents are not used.

### Bootstrap, claims, progression, and integration

BOOT-B00 is claimed as the exclusive first batch. Executor order is Sol/medium, Claude Sonnet 5/high, then Luna/medium, preserving the same partial checkout between attempts. Dependent lanes start only after the integration gate writes `bootstrap-green`. Receipts must cover every task in a batch before the controller can mark that batch complete.

Workers atomically select and claim through the existing controller, use isolated `claude/<batch>`, `sol/<batch>`, `luna/<task>`, and `freebuff/<task>` branches/worktrees, and invoke a fresh model context per unit. Core and core-gate work ranks ahead of Stretch; existing dependencies and human gates remain authoritative. **T1 correctness has priority; after its dependencies/work are complete, claiming continues into eligible T2 and later Core work. There is no tier cutoff or idle-at-tier-boundary behavior.** The canonical DAG was not changed.

Integration validates the receipt, model pin, clean tree, branch, owned paths, focused checks and `scripts/verify-fast` when present; it serializes rebase and push with a global lock. Rebase conflicts or failed checks preserve the branch and route the unit to review/ATTENTION. Main advances only after green verification. A disposable unrelated Git repository passed both ordinary-task and blank-repository bootstrap integration dry runs.

### Resilience and recovery

Logs are under `/home/dogfood-control/logs/unattended/`; common credential patterns are redacted. The supervisor lock/state are under `/home/dogfood-control/run/`. Quota classification preserves claims and worktrees, records `PAUSED_QUOTA`, and headless workers use bounded backoff. Hang detection combines output and descendant process activity with lane wall-clock bounds; first hang gets an interrupt and one same-worktree retry, second escalates. Supervisor recovery recognizes an existing BOOT session/state and avoids duplicate fanout sessions. The owner handoff is written at 22:00 UTC without terminating useful active work; new claims stop at 21:50 UTC.

Owner commands: `/home/dogfood-control/bin/conflux-unattended {status|stop|resume|attach-claude|attach-sol|attach-luna|attach-freebuff|worktrees|attention|handoff|disable-timer}`.

### Validation and boundary

Passed syntax/systemd unit verification, exact calendar normalization, an isolated near-future systemd timer test, supervisor lock contention and scratch state/handoff recovery, copied-queue ordering and atomic claim checks, scratch quota/auth/success classification, dummy hang timeout, credential redaction, scratch Freebuff TUI input, and scratch integration-lock/main-push checks. The actual subscription-authenticated systemd exec checks passed for Codex and Claude. Current UTC at final check was `2026-09-25T02:24:06Z`, NTP synchronization was `yes`.

The timer is armed, but no campaign service/model session has run. The verified GitHub repository remains blank. No local Conflux clone/history, application source, scaffold, project Docker/Compose files, project commits, or BOOT-B00 work exist. Only external orchestration/control files and unrelated disposable scratch repos were created.
# Current correction — 2026-09-25 22:24 UTC

This historical report's timer-armed statement is superseded. The 18:00 UTC launch repeatedly failed at local clone directory creation (`/home/conflux` was not writable); no product work began. The timer is now disabled, campaign start/end are blank because the event was delayed, and no campaign has been restarted. Use `/home/dogfood-control/bin/conflux-schedule set START_UTC END_UTC` once the replacement window is known. The configured clone/worktree roots now live under `/home/insightlabs38`, and preflight failures no longer trigger an automatic 30-second restart loop.
