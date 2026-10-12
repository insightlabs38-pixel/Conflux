# Kickoff Sequence

At/after 2026-09-25 18:00 UTC:
1. verify UTC clock with external/system source available to operator;
2. clone the blank public repository;
3. create canonical main and BOOT-B00 branch/worktree as appropriate;
4. run BOOT-B00 with Sol/Luna as selected;
5. first legal commit/push;
6. immediately unlock runtime, identity/application-spine and fixture/acceptance work according to dependencies;
7. start one canonical integration runtime only after enough scaffold exists;
8. orchestrator begins adaptive worker scheduling.

A local external kickoff guard script may refuse Dogfood bootstrap before the timestamp; keep that guard outside the submission repo.


After BOOT-B00, normal Claude/Codex prompts do not need IDs; they automatically select the next safe eligible batch for their lane. The operator names an ID only to override ordering or assign escalation/remediation.
