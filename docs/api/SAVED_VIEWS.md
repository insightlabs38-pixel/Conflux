# Saved views

A saved view is a named, reusable way of looking at one entity in one event: a filter tree, a sort, the visible columns and a density. It stores a **definition, never rows**. Running a view goes through the [entity query](ENTITY_QUERY.md) under the viewer's own authorization, so sharing a view cannot expose data, and a person who may not query the entity cannot see or run the view at all (it is absent, not forbidden).

## Endpoints

All are event-scoped (`/workspaces/{w}/events/{e}/views/`), for members who may query the view's entity.

| Call                               | Meaning                                                                                                                                                                                      |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET views/?entity=`               | Views the caller may see: their own, and organizers' shared views of entities they may query.                                                                                                |
| `POST views/`                      | `{entity, name, query, visibility}`. `name` 1-80 characters, unique per owner, event and entity; at most 50 views per person per event. `visibility` is `private` (default) or `organizers`. |
| `GET views/{id}/`                  | The definition.                                                                                                                                                                              |
| `PATCH views/{id}/`                | Owner only. Any of `name`, `visibility`, `query`; send the `version` you loaded, a stale one is 409 `view_changed`.                                                                          |
| `DELETE views/{id}/`               | The owner, or a workspace admin (moderation). The data a view showed is untouched.                                                                                                           |
| `GET views/{id}/run/?limit&offset` | The page the definition produces now, plus the view and its density.                                                                                                                         |

`query` is `{filter, sort, columns, density}`; `filter`, `sort` and `columns` follow the entity query rules and are validated against the entity when saved (400 keyed by the offending part). `density` is `compact` or `comfortable`. Empty parts mean the defaults.

A definition that no longer fits its entity (a field was renamed or removed) is reported, never silently loosened: running it returns 409 `view_outdated` naming what no longer matches.

## Audit

`saved_view.created`, `saved_view.updated` and `saved_view.deleted` are audited with the entity, name and visibility (and the name or visibility change). **Filter values are never copied into the audit record** because they can hold personal data; an update records only that the query changed.

## URLs

The shareable form is `?view=<public id>`: the URL carries the id only (URL-state rules: no free text or personal data in URLs). A link to a view someone else cannot see falls back to the default list.

## Web

`src/web/lib/savedViews.ts` (types, `useSavedViews`, create/update/delete) and `ViewBar` (pick, save, save as new, rename, share, copy link, delete with its consequence stated). The `view` param is the URL state; the list itself stays the caller's.

## Compatibility

Additive table (`core.SavedView`); no existing endpoint changes. `SavedPublicSearch` (anonymous public search) is a different audience and is unchanged. Saved views are per-user working state and are not part of the event archive.
