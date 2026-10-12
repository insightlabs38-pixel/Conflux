# Git and Worktree Policy

## Before kickoff
Public GitHub repo may exist but remains blank: no README, license, scaffold or initial commit. Authentication/PAT may be configured outside repo.

## After kickoff
Clone blank repo; BOOT-B00 creates first legal project files/commit. Main should remain green and demonstrable.

## Branches
`claude/<batch-id>`, `codex/<batch-id>`, `fb/<task-id>`, `fix/<id>`; short-lived worktrees deleted after merge.

## Ownership
Every active task has an ownership lease. Scope-check script compares changed paths against owned/shared paths before merge. Shared central files are changed by integration or explicitly leased.

## Migrations
Workers may generate domain migrations, but integration reconciles numbering/dependencies and validates the migration graph before merge. Avoid simultaneous schema writers in the same Django app when practical.

## Commits
No AI attribution/session metadata unless rules explicitly require it. No force-push/rebase of shared active branches. No bypassing hooks/verification.
