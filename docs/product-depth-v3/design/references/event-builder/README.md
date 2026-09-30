# Event builder — design/event-builder (r2.1)
**Boards**: Builder-Setup, Builder-Pages, Builder-Plan
**Standalone HTML**: `html/` · **Screenshots**: `screenshots/` · **Live source**: `../../exports/r2.1/canvas/project/`

## Must preserve
- Essentials vs Advanced with collapsed advanced groups; setup checklist; diagnostics rail with jump-to-field and fixes; live preview; unapplied-changes bar → plan; impact table; Event-as-Code diff parity; schema-driven extension form with permissions, https validation and test connection; hero style control with contrast-validated theme tokens.

## Adaptable implementation details
- Section names/order, which fields are Advanced, extension form field widgets.

## Keyboard / focus / a11y
- Errors linked from summary; every diagnostic focuses its field; plan buttons state prerequisites.

## Known limitations
- Drag-reorder affordances drawn, not specified in detail.

## r2 changes
- Builder-Plan: Checks/Approval text wraps instead of clipping; Builder-Pages/Plan top bars keep 44px. Builder-Setup unchanged.
- Known limitations: Builder-Pages preview is intentionally a skeleton (event not yet open).

## r2.1 changes
- Builder-Plan top action group audited — aligned, no change.
- All outlined buttons now use the `line-3` border (D-008); no layout change.
