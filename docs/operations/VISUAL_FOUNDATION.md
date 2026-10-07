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

## Public hero

The default hero is compact (V-HERO-1, D-005, D-012). It is a band: a lockup or art column, the title, the status and the timezone kicker, with the description and the one primary action in a row beneath. The band is about 140-240px on desktop (the lower bound is not a floor) and at most 120px on mobile, where art, lockup and kicker step aside. Text never sits over art; with no artwork the fallback is a typographic lockup (initial and year in a hairline frame).

The organizer chooses the size in Event setup, Public page, Appearance, "Hero size": `compact` (default), `none` (title and action only), `standard` (larger art, band at most 360px) or `immersive`. It is `hero_size` in the page's `theme_config`, validated server-side with the other presentation enums in `presentation/themes.py` and stored with the page, so it travels with Event-as-Code and archives like every other theme setting. A theme saved before the setting existed has no key and means `compact`; no data migration is needed. Both public renderers (the server-rendered site and `EventSite.tsx`) read it as `data-hero-size`; `hero` (split, poster, editorial) stays the separate layout choice. `immersive` (artwork-led, opt-in, PD-F004-B03-T01) needs a hero image URL: the server refuses it without one, and the form keeps the option disabled until one is set. The art is its own full-width strip above the title row (at most 352px desktop, 120px mobile), never behind the text, so contrast never depends on the picture. Tests: `tests/integration/test_event_themes.py`, `tests/e2e/hero-size.spec.ts` (isolated, 390 and 1440, saves through the real form and measures the public page) and the "default public hero" test in `visual-foundation.spec.ts`.

### Hero image crop and phone image

Under the brand settings, a disclosure ("Hero image crop and phone image") holds the focal point and a phone image. `banner_focus_x` and `banner_focus_y` are whole percents from the left and the top (the CSS `object-position`; 50 is the centre and is stored as no setting) and are sent to both renderers as `--hero-focus-x` and `--hero-focus-y` in the presentation `variables`. `banner_mobile_url` is an optional alternative picture for a phone: the public site draws `<picture>` with a `<source media="(max-width: 48rem)">`, so the browser picks one image (it needs the hero image first and passes the same safe-URL check). Only the immersive size shows art on a phone.

### Lead block and block links

An event with something better to open with than a banner adds a **Lead** block (Public page, Content, Add block). It is an h1, a short body, up to four label/value facts and one action; it has no art, it is placed first when added, and its presence replaces the default hero (`has_hero` in `site_views.py`), so a page keeps exactly one h1 (the accessibility audit warns when hero and lead are both present). Links typed into blocks (hero, lead and call-to-action links, sponsor and resource URLs) must be a path or anchor on this site, an `http(s)` or `mailto` link: the server refuses anything else (`presentation/blocks.py safe_href`) and the template drops an unsafe value again at render time, because the public site shares an origin with the application.

## Touch and density

Controls are `--h-ctl` (32px) on desktop and `--h-touch` (44px) below 768px or with a coarse pointer. Per-user density and theme preferences are PD-F005; nothing here changes by viewport width except that touch sizing.
