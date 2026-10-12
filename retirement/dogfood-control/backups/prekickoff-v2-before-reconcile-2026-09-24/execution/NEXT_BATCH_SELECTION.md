# Automatic Next-Batch Selection

Normal Claude/Codex prompts do not require batch IDs. Explicit IDs are overrides.

A batch is eligible only when:
- all dependency batches are DONE;
- its phase/gate is unlocked;
- it is not DONE/ACTIVE/reserved elsewhere;
- its owned paths do not conflict with an active lease;
- at least one task remains incomplete;
- it matches the current senior lane's preferred executor, unless current control state explicitly authorizes reassignment.

Selection order is the order in `BATCHES.yaml` after applying those filters. Never infer that an apparently idle batch is available if ownership/control state says otherwise. If the queue is ambiguous or stale, stop and surface the inconsistency rather than racing another session.

Escalation/remediation invocations are always explicit and may contain multiple related escalation IDs.
