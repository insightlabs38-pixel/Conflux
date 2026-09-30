# Participant My Event — design/participant-my-event (r2.1)
**Boards**: MyEvent (desktop), MyEvent-Mobile (action-needed + ready)
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Ordered next-actions list with one primary; progress track; team/project block; personalized schedule with Now marker; event pass QR with offline save; where/help/what-happens-next; explicit "You're ready" state.
- Hub is derived from canonical state only.

## Adaptable implementation details
- Which cards appear depends on enabled features; copy; ordering rules beyond urgency.

## Keyboard / focus / a11y
- Progress track is an ordered list with aria-current=step; countdowns have text equivalents; QR has alt text and printable fallback.

## Known limitations
- Wallet pass shown as button only.

## r2 changes
- MyEvent artboard normalised from 1280×1380 to 1280×1090 (full page height; the fold is at ~900). No modules were added — the r1 content was already complete.
- Dark: `../dark-mode/Dark-MyEvent` (mobile action-needed + ready pair). Ready state at desktop: see Shell-Participant.
- Known limitations: desktop shows the action-needed state only; ready state is drawn on mobile and in Shell-Participant.

## r2.1 changes
- Event-pass and help action rows audited — aligned, no change.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
