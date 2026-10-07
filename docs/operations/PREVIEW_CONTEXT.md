# Preview as a person, a version or a time (PREVIEW_CONTEXT)

An organizer often needs to know what somebody else would see: a participant looking at a form, a judge at a rubric, the public at a page, as it is now, as it was at a deadline, or as it was in version 2. This is one primitive for all of them, **without impersonation**. Code: `core/preview_context.py` (model, parsing, version choice), `core/preview_context_views.py` (endpoint). Web: `lib/previewContext.ts` and `components/PreviewBar.tsx`. Adopters: the saved-form preview in the form builder (`forms/preview.py`, `features/form-builder/FormPreviewAs.tsx`) and the public page preview in the appearance settings (`presentation/preview.py`, `features/page-builder/PagePreview.tsx`).

## A context is data, not an identity

`{role, at, version}` inside one request body.

- `role` is one of the roles the surface declares it can be viewed as (the form surface: `participant`, `judge`, `organizer`, `public`). Empty means the organizer's own, complete view.
- `at` is an instant with an explicit offset (`2027-03-06T10:00:00Z`), between the years 2000 and 2100.
- `version` is a version id of the surface's version source (`core.version_diff`); `"draft"` where the source lists a draft.
- `at` and `version` are two ways to pick one version, so they are exclusive. Neither is allowed on a surface that keeps no versions, and `role` is refused on one with no roles.

It is not a header, a cookie, a session value or a stored row, and no domain endpoint reads it (a test scans the source for that). The caller stays the actor throughout, so their authorization still applies and a role preview can only show a **subset** of what the organizer could already read. There is no session switching, so nothing a preview does can be mistaken for the previewed person's action, because it does nothing: it stores and sends nothing.

## The endpoint

`POST /api/v1/workspaces/{id}/preview-as/{surface}/` (organizers and admins; `Cache-Control: private, no-store`; no other method). POST only because the reference and input are structured.

```
{ "ref": {"event": "...", "form": "..."},
  "context": {"role": "judge", "at": "2027-03-06T10:00:00Z"},      // or "version": "<id>"
  "input": {...} }                                                   // only if the surface takes one
```

returns

```
{ surface, label, summary, roles[], versions[{id, label, at, by, current}],
  resolved {role, at, version, live}, notices[{code, message}], data }
```

`summary` is one sentence to show verbatim ("Previewing as judge, Version 2 (live). Nothing is saved or sent."). `resolved.version` names the version actually used, so a caller can pin it: a pinned version or time gives the same answer every time while the stored versions are unchanged. With neither, the surface's own rule picks the live one (forms: the latest published version, which is what participants get; with nothing published yet, the draft and the notice `unpublished`).

`at` selects the latest version kept at or before that instant; a time before the first version is a 400 that says when the first one was kept. Errors are keyed `context.role`, `context.at`, `context.version`, `ref.<param>` and `input.<path>` (the input is validated by the surface's `schema_subset` schema); 404 for a surface, reference or version source the caller may not see.

## Adding a surface

```python
from core import preview_context

def resolve(user, workspace, ref, resolved, values):
    # resolved.role, resolved.version (VersionInfo), resolved.value (the version's snapshot)
    return {...}            # or None when the caller may not see it (404)

preview_context.register_surface(preview_context.Surface(
    key="rubric", label="Rubric", params=("event", "plan"), resolve=resolve,
    roles=("judge", "organizer"), version_source="rubric"))
```

Register from `<app>/preview.py` in `AppConfig.ready()` (after the version source) and declare `("preview_surface", "rubric")` in the app's `manifest.py`; the extensions inventory lists the capability `preview_surface` and `manage.py check` fails until the two agree. The surface must not return a role more than that role is shown on its real endpoint: reuse the domain's own visibility function (the form surface uses `forms.validation.field_in_scope`) rather than writing another rule.

## What it is not

No impersonation, no way to act as another person, no persisted preview, no client-supplied surface, schema or version snapshot. Unsaved edits are previewed only where a surface declares them as its `input`: the form surface takes none (the form builder's live editor preview stays local beside it), the `page` surface takes the drafted appearance.

## The `page` surface (PD-F004-B03-T07)

`ref: {event}`, no roles, no versions; `input: {theme, theme_config}` is the appearance as it is in the form (every key optional; omitted means the saved one, so an event with no page yet previews the default). The server renders the real landing template with the saved blocks and that appearance (`site_views.landing_context` is shared with the visitor's view, so the two cannot differ), validates the input with `themes.clean_theme_config` (the same rule as saving: a refusal is a 400 keyed `input.theme_config` with the same sentence) and returns `data: {html, theme, theme_config}`. It stores and audits nothing, creates no page, and strips scripts and `noscript` from the HTML; the web draws it in an `<iframe sandbox>` with no flags (no scripts, storage or navigation) at the width of the chosen device (1440, 768 or 390px, scaled to the room), debounced 350ms after the last change. The organizer sees the saved blocks; unsaved block edits are not previewed.

## Compatibility

Additive: no migration and no existing endpoint changes. `forms.validation.field_visible` was split into `field_in_scope` (the role check) and the condition check with identical behavior.

## Verification

`tests/integration/test_preview_context.py`: an independent surface (not a form) with its own version source runs through the same primitive (live default, by version, by time at, before and after the instant, offsets, determinism); every bad context part is named; unversioned and roleless surfaces refuse what they cannot do; the live rule and the draft notice; input validated by the schema subset; hidden or declined is not visible; strict registration; for forms, each role sees what the form shows that role, as of a time, pinned versions, a property test of 40 random forms against the form's own rule (a role never sees more than the organizer), role boundaries, no audit rows or writes and no stored state, no other code reads a context, and the inventory claims the surface. Web: `PreviewBar.test.tsx`, `FormPreviewAs.test.tsx`, `FormBuilder.previewas.test.tsx`, `lib/primitives.b03.contract.test.ts`. Browser: `tests/e2e/preview-context.spec.ts` at 390 and 1440 (axe clean, no overflow, no writes besides the preview).
