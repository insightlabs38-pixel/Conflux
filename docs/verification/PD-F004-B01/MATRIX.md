# PD-F004-B01 verification matrix — visual direction: the foundation

Each capability has at least one executable proof; the e2e column runs from `tests/e2e/visual-foundation.spec.ts` (read-only, three roles, 390 and 1440) unless stated. Contract: spec 004 "PD-F004-B01 canonical contract". Rules cited are `V-*` in `design/system/VISUAL_CONTRACT.md`.

| Task | Capability                                                                      | Positive proof                                                                                                              | Negative / boundary proof                                                                                                   | Compatibility and authority                                                                         |
| ---- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| T01  | Neutral content-first shell (44px bar, 216px rail, ink mark, no marketing copy) | e2e `shellGeometry`; `workspace-shell` navigation specs                                                                     | a wrapped rail label or a 57px bar fails the spec (both occurred and were fixed)                                            | routes, aria and keyboard unchanged: workspace-shell (14), uiv2-gate                                |
| T02  | Radii 3/5/8, pill for circles, badge is a tag                                   | `test_radii_equal_the_design...`; e2e `offScaleRadii`                                                                       | ratchet names file, selector and value; `test_no_status_label_is_a_pill`                                                    | organizer `square` and `expressive` personalities override `--r-*` (sanctioned exception)           |
| T03  | Elevation: shadows on popover and dialog only                                   | `test_elevation_tokens_equal_the_design...` (light and dark); e2e `shadowed` plus open account popover                      | ratchet rejects any other shadow selector or value; closed `details` panel is not counted                                   | focus ring stays outline-based (forced-colors safe)                                                 |
| T04  | Type scale 11-32, headings at most 20px in the app                              | `test_type_scale_equals_the_design_in_px`; e2e `offScale` and h1 cap                                                        | e2e lists every off-scale element (proved by removing the 14px step); ratchet on `font-size` and weights                    | rem sizes scale with browser font size; `public.spec` still sees `system-ui`                        |
| T05  | Spacing scale, control heights, 44px touch hit area                             | `test_spacing_and_height_tokens_equal...`; `test_touch_layouts_raise...`; e2e `shortControls` (28px, 44px at 390)           | spacing ratchet; found and fixed a bare 40px button and a WCAG 2.2 target-size failure                                      | legacy `--space-*` renamed in place, no alias                                                       |
| T06  | One primary per context, secondary default, danger only as final confirm        | `Button.test.tsx`; e2e `actionHierarchy` (no context with two primaries, no danger at rest)                                 | `entity-grid`, `bulk-planner`, `approvals` specs pass with the new confirm steps; template delete now confirms              | no handler or request changed; ViewBar and templates keep their endpoints                           |
| T07  | One Icon component, rail and status icons                                       | `Icon.test.tsx` (all 28 shapes, decorative vs named, status pairs); e2e `iconProblems`, rail icons                          | ratchets: no inline svg, no coloured tile, no glyph characters in CSS content                                               | `ButtonLink` shares the Button contract                                                             |
| T08  | v3 colour tokens, legacy names as aliases, server contrast gate mirrored        | `test_colour_tokens_equal_the_approved_design...`; `test_server_contrast_table_mirrors_the_css`; ratchet on saturated fills | `test_every_accent_the_old_gate_accepted_is_still_accepted` (4,000+ accents), gate still refuses `#cccccc` with its message | public `variables` keep the legacy keys and add v3 names; stored `theme_config` unchanged and valid |

## State and viewport coverage

- Normal, loading, empty, error and denied states: unchanged components, now with icons for error and denied (`Icon.test.tsx`); `uiv2-gate` "error, empty, loading and denied states are explicit and accessible" passes.
- Dense and large data: row-height tokens defined and tested; their application is the density work of PD-F005-B02-T08 (stated limitation).
- Mobile: touch hit area 44px asserted at 390 for organizer, participant and judge; mobile disclosure navigation unchanged (bottom navigation is PD-F005).
- Public pages: `public`, `foundations` and `event-themes` specs; axe and no-overflow at 390 and 1440.

## Authorization, lifecycle, concurrency

- No API, model, permission or migration change in this batch, so there is no new authorization, lifecycle or concurrency case; the one behavior change (template delete asks first) calls the same endpoint after confirmation.
- Compatibility: the public presentation payload keeps every existing key (`test_event_themes.py`), stored accents remain valid (monotonic palette proof), `--color-*` names resolve to v3 tokens on every scope that may redeclare them.

## Commands

- `make verify-fast`: pytest 2877 passed, 34 skipped; web vitest; lint, build, sdk-check, block-schema-check clean.
- `make e2e-fast`: see `T90-e2e-fast.log`.
- `uv run --frozen pytest tests/test_visual_ratchets.py tests/integration/test_visual_tokens.py tests/test_design_manifest.py`.
