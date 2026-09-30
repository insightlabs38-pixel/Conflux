# D-004 · Status, colour, accessibility
- Status = icon shape + word; colour is redundant. Shapes: ✓circle done, △ needs action, ✕circle blocked, ◔ in progress, dashed circle not started, ⓘ info, lock restricted, ban recusal.
- All text pairs measured ≥4.5:1 (tokens in `tokens.json`; table on Foundations board). Control borders ≥3:1 (`--line-3`). Dark theme pairs ≥6.7:1.
- Focus ring 2px accent + 2px gap, never removed; forced-colors safe (icons are masks).
- Grids: role=grid, single tab stop, roving focus; heat/matrix views have table twins.
- Headings: one h1 per page; panels h2; no skipped levels (story editor lints this for participants too).
- Reduced motion: no ambient animation; spinners/skeletons static with text.
- Math: MathML/text alternative + copy-source; code: mono 12.5–13px, ≥1.6 line height, wrap or scroll inside container.
- Mobile: targets ≥44px, inputs 16px, no horizontal page scroll.
