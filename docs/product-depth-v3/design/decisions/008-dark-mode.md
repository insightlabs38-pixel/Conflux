# D-008 · Dark mode
**Status**: accepted (r2) · closed (r2.1)
**Decision**: Dark is a per-user preference (*system / light / dark*, default system) for authenticated app surfaces. Public event/project pages follow organizer theme tokens and are never overridden by the viewer's app theme.
**Rules**: same tokens/geometry/accent; theme root re-declares `color` and `background-color`; raised layers (popover, dialog, palette) use surface-2 with a light 1px edge and stronger shadow; primary-on-accent text uses `--accent-ink`; QR/badges stay light.
**Evidence**: Sys-Dark + four dark boards; lowest measured text pair 5.37:1; control border line-3 4.62:1. Dark comps found three r1 token bugs (inherited ink, hard-coded white/greys, flat elevation).

## Outlined-button border (owner-approved, r2.1)
- Normal outlined (secondary) buttons use `--line-3` in light (3.1:1) and dark (4.62:1). Both clear WCAG 1.4.11 without relying on the label.
- Unchanged: primary buttons stay filled; ghost/text actions stay borderless; panel, table and divider hairlines stay `--line` / `--line-2`; disabled keeps `surface-2` fill + `--line` border + a visible reason, so it stays distinct from enabled outlined buttons.
- Segmented controls are one bordered group (`line-3` outside, selected segment `accent-line`); tags/status are not buttons and keep their tint borders.
- Dense-toolbar check (Data-Surface, Wide-1920, Story editor, Builder-Plan, Deliberation-Finalize): not noisy. **No compact/toolbar variant was introduced**; if one is ever needed it must be a documented `.btn` variant, not a global revert.

## Public "Dark base" preset (owner-approved, r2.1)
- Keep an optional, organizer-selectable **Dark base** public theme preset, contrast-checked at save like any organizer theme.
- It is independent of the authenticated app light/dark/system preference: a signed-in viewer in dark app mode still sees the organizer's chosen public theme.
- No separate public dark board set is drawn; existing theme rules (Public-Event-Themed, Builder-Pages theme tokens, D-005) are sufficient.
