# Execution Decision Register

- X001 only three human-visible control lanes: Claude, Codex, Freebuff orchestrator.
- X002 Freebuff simultaneous writers use isolated CLI worker processes/worktrees; orchestrator is control plane.
- X003 one canonical shared application runtime from green main.
- X004 Freebuff owns most fuzz/property/permutation breadth; frontier models protect semantics and gates.
- X005 canonical queue state updated by orchestrator/integration control only; workers emit receipts.
- X006 main should remain green/demonstrable.
- X007 frontier escalation is human-approved; Freebuff cannot autonomously consume Claude/Codex allowance.
- X008 related escalations are batched when context overlaps.
- X009 Core/Stretch/Very Stretch are scheduling tiers; valuable features may be promoted whenever gates support it.
- X010 no Dogfood project code/Git commits before official kickoff.
