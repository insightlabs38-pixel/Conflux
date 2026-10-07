# Visual foundation (PD-F004-B01)

How the Conflux v3 look is kept consistent, for people changing `src/web`. The design authority is `docs/product-depth-v3/design/` (start at `IMPLEMENTATION_HANDOFF.md`); the contract for this layer is spec 004, "PD-F004-B01 canonical contract".

## One token layer

`src/web/styles/tokens.css` is the only place a colour, size, space, radius, shadow or height is defined, under the v3 names: `--bg --surface --line* --ink* --accent* --ok/warn/err/info/mute` (+ `-tint`, `-line`), `--fs-11..32`, `--sp-1..12`, `--r-1..3`, `--sh-pop`, `--sh-dlg`, `--h-ctl*`, `--h-touch`, `--w-rail`. React and the server-rendered public pages both load it. Dark values live under `[data-theme="dark"]`. The `--color-*` names are aliases to the colour tokens for one release; do not add new uses.

## Rules a test enforces

| Rule                                                                                                                                                                                    | Test                                                   |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| tokens equal the design JSON (colour, type, space, radii, elevation, heights) in px                                                                                                     | `tests/integration/test_visual_tokens.py`              |
| the server's organizer-accent contrast gate mirrors the CSS, and old accents stay valid                                                                                                 | same file (`THEME_COLORS`, monotonic proof)            |
| no gradient, no hex outside tokens, solid saturated fills only on actions and state markers, font sizes and radii and spacing and shadows from the scale, no inline svg, no glyph icons | `tests/test_visual_ratchets.py`                        |
| rendered type, radii, shadows, control heights, icons, one primary per context, shell geometry on three roles at 390 and 1440                                                           | `tests/e2e/visual-foundation.spec.ts` (read-only tier) |

An exception is an edit to the allowlist in the ratchet test, with a reason; a new decorative fill or off-scale size fails the test by default.

## Components

- `Button` (`primary` only by choice, `secondary` default, `ghost`, `danger` = final confirm only; sizes `sm|md|lg`). `ButtonLink` and `buttonClass` share it.
- `Icon` (28 Lucide-shaped names, 16px, `currentColor`, hidden from assistive technology unless it has a `label`). Add a shape to the table in `Icon.tsx`.
- State components carry an icon for error and denied; the remaining state fields (kept data, retry scope, error reference, cancel) are PD-F004-B02.

## Advanced never means chaotic

Advanced content opens into the page, not into a different layout. Every `<details>` inside the shell shares one look in `components.css` ("Disclosure"): a hairline above, a medium-weight summary, one chevron that turns when open, no native marker. Borders are solid hairlines everywhere; `dashed` and `dotted` are banned in every stylesheet. A disclosure that needs its own surface (account menu, entity tools bar) opts out of the hairline by class, never by a second chevron. `test_no_dashed_or_dotted_borders_and_every_disclosure_has_the_one_chevron` and the "every organizer disclosure shares one look" spec in `visual-foundation.spec.ts` enforce it.

## Touch and density

Controls are `--h-ctl` (32px) on desktop and `--h-touch` (44px) below 768px or with a coarse pointer. Per-user density and theme preferences are PD-F005; nothing here changes by viewport width except that touch sizing.
