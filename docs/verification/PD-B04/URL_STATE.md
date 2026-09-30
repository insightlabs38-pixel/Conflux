# PD-B04-T04 — URL-state conventions

Source of truth: the rule table and rules in `src/web/lib/urlState.ts` (read with `lib/routes.ts` for paths). One primitive, `useUrlParam(key, { clears })`, reads and writes a search param; `carriedSearch` decides what follows the user to another view.

| Kind        | Lives in                                        | Examples                                                            | History |
| ----------- | ----------------------------------------------- | ------------------------------------------------------------------- | ------- |
| Location    | path                                            | workspace, view, person, public event                               | push    |
| Context     | search, carried across the views of a workspace | `event`, `stage`, `plan`                                            | push    |
| Panel state | search, dropped when leaving the view           | selected row, enumerated filter/sort, tab, page                     | replace |
| Entry token | search, read once                               | `invite`                                                            | none    |
| Local only  | component state / storage                       | drafts, form fields, scores, comments, free-text search, open menus | none    |

Rules: (1) params are public ids or values from a fixed set; free text, personal data and credentials never go in a URL (only exception: the single-use `invite` token, removed once redeemed). (2) Defaults are omitted; an unknown or no-longer-visible value falls back to the default and the URL is corrected with `replace`, so Back is not polluted. (3) Choosing a context pushes and clears the params below it (`event` clears `stage`/`plan`); choosing inside a panel replaces. (4) The URL is never authority: a value is honoured only once it appears in what the server lists for this user, and an unlisted id is never requested. (5) Panels that stay mounted while hidden keep drafts in component state; only the selection mirrors to the URL. (6) Two instances of a panel in one view namespace their keys (`<panel>.<key>`).

Setters called from async callbacks act on the URL at call time (a `useRef` of the latest location), so a late correction cannot send a user who navigated away back to the old view. A first version did exactly that and the browser repeat run caught it (1 in ~16).

## Applied now

| State                      | Before                        | Now                                                                                                               |
| -------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Participant selected event | `?event=` (T01)               | same, via `useUrlParam("event", { clears: ["invite"] })`                                                          |
| Organizer selected event   | local state (lost on refresh) | `?event=`: refresh, Back and shared link keep it; unlisted event dropped, never requested                         |
| Judge event, stage, plan   | local state (lost on refresh) | `?event=&stage=&plan=`; each level validated against the server's lists; single plan auto-selected with `replace` |
| Navigation between views   | carried the whole search      | carries `event`, `stage`, `plan`, `invite` only (`carriedSearch`)                                                 |
| Team invite token          | `?invite=` prefilled, kept    | prefilled once, removed from the URL (`replace`) when redeemed                                                    |

## Classified, deliberately not moved yet

| State (examples)                                                                                 | Class                  | Why not now / owner                                                                                    |
| ------------------------------------------------------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------ |
| Judge selected project (`PlanQueue`)                                                             | panel state            | the scoring draft lives under the selection; mirroring needs a draft-safe design with the judging work |
| Builder "selected item" (forms, pages, webhooks, awards, presets, evaluation pools, projects)    | panel state (`?item=`) | editors keep drafts while hidden; moves with each panel's migration (T07)                              |
| Enumerated filters (on-site attendance filter, eligibility status filter), workflow-section tabs | panel state            | same; namespaced keys per rule 6                                                                       |
| Free-text search (on-site, API explorer filter), form fields, ballots, comments                  | local only             | rule 1                                                                                                 |
| API explorer selected operation                                                                  | panel state            | own route; deferred                                                                                    |

Not changed: routes, legacy URL redirects, authorization (the server still decides what any id resolves to).

## Evidence

`lib/urlState.test.tsx` (push vs replace, defaults omitted, dependents cleared, no-op when unchanged, stale-callback correction, `carriedSearch`); `JudgeWorkspace.url.test.tsx` (deep link opens the queue, choices write the URL and clear lower levels, single plan, unknown event and foreign stage dropped without requests); `EventDashboard.url.test.tsx`; `TeamPanel.invite.test.tsx`; `WorkspaceNavigation.test.tsx` (carry rule); browser `url-state.spec.ts` (refresh, Back and shared link for organizer and judge; unknown event never requested and the correction adds no history entry; foreign stage dropped).
