#!/usr/bin/env bash
set +e
cd /home/insightlabs38/conflux-worktrees/sol-C-B04
export DISABLE_AUTOUPDATER=1
unset OPENAI_API_KEY CODEX_API_KEY CODEX_ACCESS_TOKEN ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL
(set -o pipefail; (/home/insightlabs38/.local/bin/codex exec --model gpt-6-sol -c model_reasoning_effort=medium --dangerously-bypass-approvals-and-sandbox --json -C /home/insightlabs38/conflux-worktrees/sol-C-B04 'UNATTENDED ASSIGNMENT — DO NOT SELECT OR CLAIM OTHER WORK.
Exact assigned batch: C-B04
Executor lane: sol
Branch and isolated worktree are already assigned.
Follow canonical dependencies and the frozen architecture. Keep T1 correctness as minimum product priority; once its dependencies/work are complete, keep taking eligible T2 and later Core work. No artificial tier cutoff or idling at tier boundaries.
Read first with targeted rg/grep/sed: execution/AGENTS.md, the relevant batch/task definitions, domain plan sections, and lane protocol. Do not dump whole large files.

--- Existing lane protocol ---
# Codex GPT-6 Sol Senior-Batch Protocol

This protocol is for Codex GPT-6 Sol. Sol consumes coherent senior batches selected with `conflux-control next-batch sol` and reserved atomically with `claim-batch sol <id>`. Sol does not compete with Luna for individual task claims once a task is reserved.

If a Sol batch is reserved, bulk workers must not enter conflicting tasks in that batch unless the controller explicitly permits split ownership. Sol may handle difficult ordinary engineering, large coherent implementation batches, cross-stack integration, and major gates. Focused semantic tests belong with implementation; bulk verification breadth belongs to Freebuff/Luna. Do not control other model sessions or edit canonical YAML state directly. Record a concise receipt with lane, model, branch/worktree, verification and integration notes.


--- Unattended additions ---
No questions to owner. Do not interact with another session or pane. Stay inside the assigned ID and owned paths. Do not steal work. Run focused tests. Keep changes on assigned branch/worktree. Commit coherent changes and push assigned branch. Write a schema-valid JSON receipt at /home/dogfood-control/execution/receipts/C-B04.json with exact task_id, status, summary, verification, executor_lane, model, worktree, branch, and session_id. status must be done only when all assigned acceptance checks passed; otherwise use needs-review or blocked and explain. Do not autonomously integrate into main. On quota, stop model work and preserve lease/tree.

FOOTAGE IMPACT: do not assume or invent recorded surfaces before a real baseline exists. If /home/dogfood-control/demo-assets/FOOTAGE_BASELINE.yaml exists, derive scene IDs/routes/components only from that manifest and task scope. Before receipt/integration include `footage_impact` with `reviewed_task_id` equal to this unit ID and `task_scope_reviewed` exactly equal to `<unit ID>: <canonical assignment title>`; then disposition UNAFFECTED, BASELINE_VALID, or RECAPTURE_REQUIRED; visual_scope NO_VISUAL_CHANGE, SCOPED_COMPATIBLE, or BROAD_REDESIGN; concise rationale; exact affected baseline scene IDs; and verification_evidence paths. For BASELINE_VALID include the affected scene run and current screenshot evidence. For RECAPTURE_REQUIRED name only invalidated scenes and include replacement evidence when captured. Do not infer redesign from UI-file changes alone; report task scope and functional/demo evidence. The integration controller enforces this receipt gate. It computes H+ from unattended.env: at H60 broad redesign and footage-invalidating changes are blocked; at H68+ UI changes require a scoped critical fix and verification, while work with no visual change may continue. Broad redesign remains blocked. Preserve the established visual direction and key actions.
If this task lands a materially UI-visible Stretch capability, write `/home/dogfood-control/run/video-stretch-delta.json` with task ID, feature, routes and why it changes the demo story. This queues an isolated footage delta after integration, never a product dependency. Do not signal backend-only or visually immaterial changes.

--- Explicit canonical assignment data ---
{
  "id": "C-B04",
  "title": "Event, tracks, dates and base prize configuration",
  "phase": "core",
  "preferred_executor": "codex-sol",
  "dependencies": [
    "C-B02"
  ],
  "owned_paths": [
    "src/api/events/**",
    "src/web/features/event-builder/**"
  ],
  "task_ids": [
    "EV-001",
    "EV-002",
    "EV-003",
    "EV-004"
  ],
  "completion_rule": "all tasks complete + scoped verification + no unresolved blocker; core gates additionally require explicit gate decision"
}

Tasks in this batch (complete as a coherent batch):
[
  {
    "id": "EV-001",
    "batch": "C-B04",
    "phase": "core",
    "title": "Workspace/Event CRUD and status lifecycle",
    "status": "BLOCKED",
    "batch_dependencies": [
      "C-B02"
    ],
    "task_dependencies": [],
    "goal": "Dates/timezones/public state.",
    "preferred_executor": "codex-sol",
    "risk": "medium",
    "owned_paths": [
      "src/api/events/**",
      "src/web/features/event-builder/**"
    ],
    "required_reading": [
      "AGENTS.md",
      "BATCHES.yaml#C-B04",
      "relevant post-spec plan domain docs",
      "current code/tests in owned paths"
    ],
    "acceptance": [
      "implementation/behavior matches goal",
      "scoped tests pass",
      "no out-of-scope ownership changes",
      "receipt emitted with verification evidence"
    ],
    "escalate_if": [
      "architecture/invariant ambiguity",
      "unexpected cross-domain rewrite",
      "P0/P1 security or data-integrity issue",
      "weird failure persists after bounded retry"
    ],
    "bulk_eligible": true
  },
  {
    "id": "EV-002",
    "batch": "C-B04",
    "phase": "core",
    "title": "Tracks and base prize configuration",
    "status": "BLOCKED",
    "batch_dependencies": [
      "C-B02"
    ],
    "task_dependencies": [
      "EV-001"
    ],
    "goal": "T1 configurable metadata.",
    "preferred_executor": "codex-sol",
    "risk": "medium",
    "owned_paths": [
      "src/api/events/**",
      "src/web/features/event-builder/**"
    ],
    "required_reading": [
      "AGENTS.md",
      "BATCHES.yaml#C-B04",
      "relevant post-spec plan domain docs",
      "current code/tests in owned paths"
    ],
    "acceptance": [
      "implementation/behavior matches goal",
      "scoped tests pass",
      "no out-of-scope ownership changes",
      "receipt emitted with verification evidence"
    ],
    "escalate_if": [
      "architecture/invariant ambiguity",
      "unexpected cross-domain rewrite",
      "P0/P1 security or data-integrity issue",
      "weird failure persists after bounded retry"
    ],
    "bulk_eligible": true
  },
  {
    "id": "EV-003",
    "batch": "C-B04",
    "phase": "core",
    "title": "Organizer event dashboard shell",
    "status": "BLOCKED",
    "batch_dependencies": [
      "C-B02"
    ],
    "task_dependencies": [
      "EV-002"
    ],
    "goal": "Core event settings/health entry point.",
    "preferred_executor": "codex-sol",
    "risk": "medium",
    "owned_paths": [
      "src/api/events/**",
      "src/web/features/event-builder/**"
    ],
    "required_reading": [
      "AGENTS.md",
      "BATCHES.yaml#C-B04",
      "relevant post-spec plan domain docs",
      "current code/tests in owned paths"
    ],
    "acceptance": [
      "implementation/behavior matches goal",
      "scoped tests pass",
      "no out-of-scope ownership changes",
      "receipt emitted with verification evidence"
    ],
    "escalate_if": [
      "architecture/invariant ambiguity",
      "unexpected cross-domain rewrite",
      "P0/P1 security or data-integrity issue",
      "weird failure persists after bounded retry"
    ],
    "bulk_eligible": true
  },
  {
    "id": "EV-004",
    "batch": "C-B04",
    "phase": "core",
    "title": "Event API/UI validation",
    "status": "BLOCKED",
    "batch_dependencies": [
      "C-B02"
    ],
    "task_dependencies": [
      "EV-003"
    ],
    "goal": "Server/client schemas and errors.",
    "preferred_executor": "codex-sol",
    "risk": "medium",
    "owned_paths": [
      "src/api/events/**",
      "src/web/features/event-builder/**"
    ],
    "required_reading": [
      "AGENTS.md",
      "BATCHES.yaml#C-B04",
      "relevant post-spec plan domain docs",
      "current code/tests in owned paths"
    ],
    "acceptance": [
      "implementation/behavior matches goal",
      "scoped tests pass",
      "no out-of-scope ownership changes",
      "receipt emitted with verification evidence"
    ],
    "escalate_if": [
      "architecture/invariant ambiguity",
      "unexpected cross-domain rewrite",
      "P0/P1 security or data-integrity issue",
      "weird failure persists after bounded retry"
    ],
    "bulk_eligible": true
  }
]
The completion receipt must include `completed_tasks` listing every task ID in this batch exactly once. Do not claim batch success or downstream eligibility unless each listed task acceptance criterion is complete and the required checks passed.
Receipt schema: version: 3
required: [task_id, status, summary, verification, executor_lane, model, worktree]
fields:
  task_id: string
  status: done|blocked|needs-review
  summary: concise string
  verification: list of commands and outcomes
  executor_lane: claude|sol|luna|freebuff|human
  model: string
  worktree: absolute path or null
  branch: string or null
  session_id: optional string
  blockers: optional list
  critical_fix: "optional boolean; required true after H68 for any integrated UI-affecting fix"
  footage_impact: "required when /home/dogfood-control/demo-assets/FOOTAGE_BASELINE.yaml exists; see footage_impact_schema"
footage_impact_schema:
  reviewed_task_id: exact assigned unit ID
  task_scope_reviewed: '"'"'exact string "<unit ID>: <canonical assignment title>"'"'"'
  disposition: UNAFFECTED|BASELINE_VALID|RECAPTURE_REQUIRED
  visual_scope: NO_VISUAL_CHANGE|SCOPED_COMPATIBLE|BROAD_REDESIGN
  rationale: concise functional/demo meaning assessment
  scenes: list of exact scene IDs from the established FOOTAGE_BASELINE.yaml; empty only when no recorded scene is affected
  verification_evidence: "list of objects: kind (scene_run|screenshot|replacement_scene), scene_id (baseline ID or affected route), path (existing absolute file path)"


USAGE HANDOFF REQUIRED: /home/dogfood-control/handoffs/sol/C-B04.md. At meaningful boundaries and known usage-risk points, write an agent-authored checkpoint with `/home/dogfood-control/bin/conflux-handoff sol C-B04 --worktree /home/insightlabs38/conflux-worktrees/sol-C-B04 --branch sol/C-B04 --phase PHASE --checkpoint "completed work; current state; decisions/invariants; relevant symbols; tests/results; failures; next actions" --next "next concrete action"`. Do this after investigation/plan, substantial implementation, before/after major tests, and before integration or intentional stop; avoid frequent injected prompts. Controller polling separately captures Git/controller/receipt/log state and preserves checkpoint authorship time. Do not copy transcripts or planning documents. On quota preserve lease/worktree and set HANDOFF_REQUIRED; never restart with this full prompt.
Exact branch: sol/C-B04
Exact worktree: /home/insightlabs38/conflux-worktrees/sol-C-B04
Pinned model for this invocation: gpt-6-sol/medium') 2>&1 | /home/dogfood-control/bin/conflux-redact-log >> /home/dogfood-control/logs/unattended/sol-C-B04.jsonl) &
pid=$!
printf "%s\n" "$pid" > /home/dogfood-control/run/unattended-sol-c-b04.pid
wait "$pid"
rc=$?
printf "%s\n" "$rc" > /home/dogfood-control/run/unattended-sol-c-b04.exit
sleep 86400
