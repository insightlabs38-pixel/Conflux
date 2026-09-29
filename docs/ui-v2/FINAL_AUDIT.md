# UI-v2 final visual, accessibility and regression audit (UIV2-B10)

Evidence: real rendered pages from the existing Playwright harness against the rebuilt app image
after `scripts/demo-reset`. Stills: `docs/verification/UIV2-B10` (scenes repeat the baseline names;
[AFTER_MEDIA.md](AFTER_MEDIA.md) vs [BASELINE_MEDIA.md](BASELINE_MEDIA.md)); per-batch stills in
`docs/verification/UIV2-B01…B09`. Run with `make e2e-fast`: **144 passed, 0 failed** across all 18 spec
files (read-only 50, public 48, stateful 40, final-states 6).

## Hard visual completion conditions

| Condition                                              | Result | Where / how verified                                                                             |
| ------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------ |
| Raw browser-looking primary controls                   | Met    | Button system; older raw forms share one responsive layout (B09); native selects kept on purpose |
| Prominent actions as plain blue links                  | Met    | Overview/next actions are buttons (`DestinationLink` button classes); text links are secondary   |
| Participant/judge/organizer as one giant vertical page | Met    | Destinations plus retained-draft task tabs (B02, B06, B08, B09); judge desk (B07)                |
| Unclear active navigation                              | Met    | Sidebar `aria-current`, grouped destinations, selected task tab (B02); roles/workspace-shell     |
| Gallery primarily text-link cards                      | Met    | Visual project cards, search/filter/count (B05); showcase spec to 1920px                         |
| Project detail visually sparse                         | Met    | Story/media/team/evidence structure (B05)                                                        |
| Profile only a history table                           | Met    | Identity header, editable reusable profile, portfolio (B04)                                      |
| Judge scoring lacks a workflow                         | Met    | Queue list, evidence and rubric split, autosave, prev/next, recuse, sticky mobile actions (B07)  |
| Deliberation looks like generic admin data             | Met    | Steps, evidence tiles, merged finalist table, override/conflict cues, immutable banner (B08)     |
| Page builder mirrors raw model fields                  | Met    | Outline plus single editor, grouped appearance, preview, confirmed removal (B09)                 |
| Mobile merely wraps desktop                            | Met    | Task tabs, nav disclosure, judge list/evidence/rubric order and sticky bar, stacked builders     |
| Advanced metadata overwhelms the task                  | Met    | Signatures/digests/history, schemas and contracts sit in disclosures                             |
| Event customization only palette switching             | Met    | Typography, corner style, density, width, hero, background, project cards (B03)                  |

## Accessibility (WCAG 2.2 AA-quality, automated plus targeted manual review)

- axe now runs with `wcag2a/2aa/21a/21aa/22aa` (includes `target-size`); confirmed the rule executes and passes.
- Matrix: sign-in/landmarks 360/390/768/1024/1440/1920; finalized/published/submitted states the same six
  widths; participant, judge, organizer and builder tours 390/768/1024/1440; public showcase to 1920.
- Found and fixed during the gate: skip link contrast when revealed; keyboard focus hidden under the sticky judge
  action bar (2.4.11, `scroll-padding`); page-builder/settings inputs overflowing at desktop widths; a foundations
  dark-theme spec that forced an impossible state (server brand style overrides `<html data-theme>`).
- Also checked: one `main`/`h1` per shell page, visible focus on every scoring control, reduced motion honored,
  keyboard-only scoring traversal, account/mobile disclosure Escape and return-focus (workspace-shell).
- States (route interception, no server writes): per-card error with retry, slow loading, forbidden events, empty
  queue, 60 long-named projects at 360/390/768/1440 with no overflow.
- Alternate themes: public dark/minimal (event-themes, foundations); authenticated shell dark and minimal palettes.

## Regression

`make verify-fast` exit 0: ruff format/check, 1400 pytest passed (23 skipped), frontend 168 passed, typecheck,
build, OpenAPI/SDK checks, block-schema check. No API, model, RBAC, deadline, COI, normalization or
immutable-evidence semantics changed in UI-v2 batches B06–B10.

## Known limitations (not hidden)

- No real screen-reader pass; accessibility is axe plus scripted keyboard and manual inspection.
- Organizer/participant tours are not run at 360px or 1920px (only sign-in, final states and public pages are).
- The authenticated app has no user theme control; dark/minimal there is checked by forcing the token attributes.
- API-absent items are not invented: pairwise evidence and a "scheduled" publish step in deliberation/publication,
  judge-visible peer scores (must never exist), a decision timeline, an analytics page.
- Demo seed has no judge assignment rows or shared artifacts for some judges, so those states are unit-tested.
- Pre-existing test noise remains: `JudgeRoutePanel` error-boundary output from stubs returning the wrong shape,
  and a React key warning in the on-site manual check-in unit test (present before UI-v2's B08).
- Public agenda and expo map were redesigned in B10 (day-grouped timeline, place cards); they were listed in the
  census for B03/B08 but had not been restyled until this gate.
