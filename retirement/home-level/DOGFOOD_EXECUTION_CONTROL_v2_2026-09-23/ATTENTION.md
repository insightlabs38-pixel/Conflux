# NEEDS HUMAN ATTENTION

Pre-kickoff:
- Resolve/ask organizer: released checker has no T3/T4 assertions.
- Complete CLI/GitHub/model authentication on build VM.
- Run scratch orchestration/reboot rehearsal.

During event, orchestrator maintains concise HIGH/MED/LOW items here; do not use this as a log.

- RESOLVED (2026-09-27, owner-directed corrective fix before C-B15): added
  `Project.track` (nullable FK to events.Track, same-event enforced). GAL-
  001 gallery filtering and JDG-007 track-fit both now use the real
  association instead of degrading to a no-op. See DECISIONS.md X012.
