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

## The anti-slop audit

The visual guardrails of spec 004 (V-SLOP-1..12 and 14) are measured on the rendered pages, not on a screenshot: `tests/e2e/slop.ts` exports `slopProblems(page, rules)`, which runs each rule in the page and returns what breaks it as short strings, and `tests/e2e/slop-audit.spec.ts` runs it (read-only tier, seed 7) on every destination and task tab of the organizer, participant and judge roles and on the three public pages, at 390 and 1440. The rules: `gradient`, `iconTile`, `kpiCards` (three boxed siblings in a row), `operatorCopy` (nothing over 20px in the app, no tagline over ten words), `pills`, `nestedCards`, `repeatedLabels` (no heading, selected tab or crumb says the same thing twice) and `hiddenActions` (no menu popup, dots-glyph or icon-only "More" control in the page), `recordGrids` (a list of records is a table, never boxes laid out three across), `alarmColors` (red only on the failing item and a final destructive button), `fakeAi` (no sparkle, "AI", copilot or smart-suggest control on scoring, eligibility or publication), `precision` (no figure with more than two decimals; add `data-raw` to a value that is meant to be exact) and `opaqueIds` (a record is chosen by name from a list, never typed as an id; a key the author invents is marked `data-authored-key`).

Choosing a record: use `RecordPicker` (`src/web/components/RecordPicker.tsx`) with `entitySource` over a registered query entity, or `participantSource` for a person. It shows names, narrows by typing part of a name on the server, and says when nothing matches or when the list is longer than shown.

To add a rule: add its name to `SlopRule`, a block to `slopProblems`, the name to `RULES` in the spec, and a self-test that injects a violation and expects the finding (a gate that cannot fail proves nothing). To except something, narrow the rule's selector with a reason in a comment; never loosen a threshold to make a page pass. Not walked: dialogs, open disclosures and per-record detail views.

## Touch and density

Controls are `--h-ctl` (32px) on desktop and `--h-touch` (44px) below 768px or with a coarse pointer. Per-user density and theme preferences are PD-F005; nothing here changes by viewport width except that touch sizing.

## The application shell (PD-F005-B01)

Every workspace screen (organizer, participant, judge, mentor, volunteer) has the same shell; the pieces below are the only places it is built, so a new feature plugs into them instead of making its own.

- **Places and URLs.** `roleDestinations` in `WorkspaceNavigation.tsx` is the one list of a role's places (optional modules that are off are removed). A place is a `RouteTarget` (`view`, optional `section`, `event`, params) and its URL is `routes.target(workspaceId, target)` in `lib/routes.ts`; nothing else composes a workspace URL. A param is an id or a fixed name, never typed text (`TypeError` otherwise), the query is always in the order event, stage, plan, invite, other keys, section. `parseWorkspaceLocation` reads one back.
- **Navigation by width.** From 1440 the 216px rail with words; 1024 to 1439 a 52px icon rail (the words are the tooltip and the accessible name); 768 to 1023 the top bar with a Navigation drawer; below 768 a bottom bar of at most five controls - when a role has more than five places, the ones marked `bar: true` in `roleDestinations` (at most four) and **More**, which opens the rest as a sheet (`barDestinations`). Give a new destination a `short` label for the bar if its name is long.
- **Event and workspace switcher** (`EventSwitcher`): the selected event is the `event` URL param; the lists are the ones each role already loads. Favorites (12) and recents (8) are stored on the device by `lib/shellPreferences.ts`, the only module that remembers anything for the shell (keys `conflux:v1:<user>:<workspace>:<name>`, validated on read, cleared at sign-out).
- **Command palette and search** (`CommandPalette`, Ctrl+K or Cmd+K): commands come from the registry in `lib/commands.ts`. Add one by registering a provider (`registerCommandProvider`) that returns `Command` objects for the context; `when(context)` narrows what is offered, `run(context)` may navigate or change presentation, and must never change domain state itself (a command that must calls the canonical endpoint through the shared client and shows the consequence step). Records come from the universal query engine: add an entry to `src/web/lib/searchTargets.json` for every new query entity (`tests/integration/test_search_targets.py` fails until you do).
- **Notification center** (`InboxCenter`) is a view of the member's inbox through `useInbox`; only it subscribes to the realtime topic, so other readers pass `live: false`.
- **Account menu** holds the profile and notification preferences links and the theme (System, Light, Dark) of the app's own screens; the theme is applied by `useAppTheme` in the workspace shell only, never to the public pages.
- **Breadcrumbs** (`Breadcrumbs` in `Foundation.tsx`) list ancestors only and only for a page three levels deep; the audit rule `crumbs` fails a trail on a destination or tab.

### The application shell, second slice (PD-F005-B02)

- **Event phase.** `events/lifecycle.py` derives draft, open, closed, judging, published or archived from what is stored (archived and draft are what they say; a published award is published; a submitted non-calibration ballot is judging; otherwise closed or open) and the three event lists carry it as `phase` (`key`, `label`, `reason`). The switcher draws it as a quiet status beside the name; never derive it in the browser.
- **Roles.** A person may hold several roles in a workspace. `as` (a URL context param) picks which of their own roles to view as (`lib/roles.ts`, `pickRole`: the requested one if held, else the most privileged); it chooses a screen, never a permission. Build links with `navigation.target(...)`, which keeps the event and the role.
- **Density, theme, shortcuts.** `data-density` (comfortable, compact, high) and `data-theme` are set on the document by the workspace shell only, from `shellPreferences`. `lib/shortcuts.ts` holds the key logic apart from React (`?`, `/`, `G then a letter`; single-key shortcuts can be switched off, WCAG 2.1.4); give a destination a `key` in `roleDestinations` and a command a `shortcut` and the help lists them.
- **Pinned and recent.** A pinned view is three ids on the device (`event:entity:view`); recent views the same; both resolve against the server's saved-view lists, so a deleted view is not offered. Recent actions are the caller's own audit rows (`GET /audit/{workspace}/?mine=1&limit=8`).
- **Inspector.** `EntityGrid` has a Details button per row (`inspect={false}` opts out) that opens `Inspector` beside the list, docked from 1024px and a sheet below; the open record is the `row_<entity>` URL param; the list is not remounted. `DataGrid` takes `highlightedId`.
- **Preview as.** `PreviewAsDialog` asks `previewAs` (PREVIEW_CONTEXT) for the saved form as a participant, judge or the public and for the public page in a script-less frame; register a new surface with the primitive and add it to the dialog to preview it.
- Keep the shell's key listeners in layout effects or behind a ref: a re-render must not drop a half-typed chord, and a key pressed as the control appears must work.

### The application shell, third slice (PD-F005-B03)

- **Remembered columns.** `columnPreference` and `setColumnPreference` in `lib/shellPreferences.ts` (key `columns:<entity>`, per person and workspace). `EntityGrid` order of precedence: an open saved view's columns, the person's choice, the list's defaults; keys the list no longer has are dropped and never leave it empty.
- **Route state.** A list's sort and page are panel params `sort_<entity>` and `page_<entity>`. `lib/shareLink.ts` rebuilds the address that reopens exactly the view from an allowlist (`as`, `stage`, `plan`, `event`, `sort_`, `page_`, `row_`, `view_` keys): the invite token and typed text never ride along. Use `shareableTarget` for in-app navigation and `shareableHref` for a copied address.
- **Drafts and tabs.** Replace `useState` with `useDraft(scope, initial, label)` (`hooks/useDraft.ts`) in a form whose edits must survive leaving the screen; call `saved()` after the server accepts it. Drafts are memory only (`lib/drafts.ts`), cleared at sign-out. `WorkspaceTabs` shows kept places and places holding a draft; `DraftGuard` warns on reload and asks before sign-out. `ThemeSettings` is the first adopter.
- **Selection commands.** A selectable `EntityGrid` publishes its selection (`lib/selection.ts`); the palette lists commands for it. Pass `selectionCommands` for list-specific ones; a command starts the list's workflow (the bulk preview) and never changes state itself.
- **Live operations.** `lib/liveOps.ts`, `LiveStatus`, a per-list live topic (`liveOpsTopic`, polled every 15 s) and `useLoad().updatedAt`. Device choice (`live-operations`). Offline holds row actions with the reason.
- **Operations mode.** `OperationsHost` renders a second pane from 1800px (`useWideDisplay`). The pane is a slot: register a panel with `registerOpsPanel` (`lib/opsPanels.ts`; the first three are in `components/opsPanels.tsx`). Panels are read-only, own no data and report `updatedAt`. Class names: the pane is `cx-opspane`, not `cx-ops` (the operations overview owns that).
- **Listener rule for specs.** A palette-driven browser step waits for the option to be visible before pressing Enter.
