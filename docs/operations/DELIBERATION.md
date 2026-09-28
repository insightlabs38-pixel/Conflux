# Judge deliberation and winner finalization

Per award selected from an evaluation plan: `.../awards/<a>/deliberation/`.

- `POST` (organizer) opens the room with a `quorum` (default: half the panel, rounded up). The panel is every judge with a live ballot or pairwise comparison on the plan; each is notified in-app. `GET` returns the room; non-panel judges get 404, participants 403.
- `POST notes/` and `PUT projects/<p>/stance/` (panel judges) write notes and `endorse`/`object`/`abstain` stances with a rationale. **A judge only sees, and may only write about, a project they evaluated themselves**, so the room cannot anchor an independent score; no ballot or score data is ever returned. Ineligible projects (PVS01) are excluded.
- A project is _recommended_ when endorsements reach the quorum and outnumber objections.
- `POST close/` stops input. `POST finalize/` (organizer) takes exactly `winner_count` projects; any that the panel did not recommend need an `override_reason`. It goes through the normal winner selection (stacking, track and ranking rules, and the existing ranking override) and stores the tally under `evidence.deliberation` on each `AwardWinner`; publishing stays a separate step.

Every open, note, stance change, close and finalization is audited. Rooms, notes, stances and the frozen tally travel in v2 final archives.
