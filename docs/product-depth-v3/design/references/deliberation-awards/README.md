# Deliberation & awards — design/deliberation-awards (r2.1)
**Boards**: Deliberation, Deliberation-Finalize
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Finalist table with normalized + raw + raw-rank shift + spread + coverage + per-award eligibility + stance; close-call marker; criterion compare; deterministic "why A over B"; sensitivity; notes with author/time/visibility; recusal; override needs category + reason; approvals with no-self-approve; plan → approve → apply; exact publication preview; immutable receipt.

## Adaptable implementation details
- Number of finalists shown, weights display, sensitivity scenarios list.

## Keyboard / focus / a11y
- Table twin for spread glyphs; disabled Apply explains why; dialogs restore focus.

## Known limitations
- Evidence graph link is a placeholder.

## r2 changes
- Deliberation-Finalize: columns re-proportioned (288 / 600 / flex) so the plan table and approval actions no longer clip; top bar keeps 44px; added a "what changes for teams" table under the override reason.
- Deliberation unchanged. Pairwise head-to-head row is fed by `../judge-review/` Pairwise boards (tiebreak only).

## r2.1 changes
- Deliberation: the “Add note” input reserved icon padding with no icon; icon added.
- Deliberation-Finalize: footer/approval row audited — aligned, no change.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
