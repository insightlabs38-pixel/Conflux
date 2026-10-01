# Version comparison (VERSION_DIFF)

One way to say what changed between two versions of the same thing: form versions, rubric versions, a configuration change and whatever keeps versions next. Code: `core/version_diff.py` (the pure diffs and the source registry), `core/version_views.py` (endpoints); web `lib/versions.ts`, `components/DiffView.tsx` (draws a diff) and `components/VersionCompare.tsx` (pick two versions of a source and see the diff). Adopters: Setup > Forms > Compare versions and Operations > Configuration history.

## What it does and does not do

A diff is **computed on the server and drawn by the browser**; the browser never compares anything itself, so what is shown is exactly what the server worked out. Comparing is read-only and deterministic: the same two values always give the same answer in the same order. It writes nothing and audits nothing, and restoring a version stays the owning feature's own endpoint (form version restore, rubric restore, configuration restore). It decides no score, permission or deadline.

## The two diffs

`diff_json(before, after)` returns `{kind: "json", changes: [{path, op, before, after, clipped}], total, truncated}`.

- `path` is a JSON Pointer (RFC 6901): `/fields/2/label`, `~` and `/` escaped as `~0` and `~1`, `""` for the value itself. Keys are visited in sorted order.
- `op` is `added`, `removed`, `changed` or `moved`. `true` is not `1`; `1` and `1.0` are the same number.
- A list whose items are all objects with a unique `id`, `key` or `public_id` in both versions is compared **by that identity**: inserting, removing or reordering one item is one change, not a change to every item after it. A `moved` change carries the old and new position (`before`, `after`), and only items that left the longest run of unmoved items count as moved. Any other list is compared by position.
- Removals come first (paths are positions in the old list), then everything else in the new order.
- Bounds: at most 500 changes (`total` still counts all, `truncated` says so); a value over 1,000 characters is cut and flagged `clipped`; nesting past 24 levels is compared as one value.

`diff_text(before, after)` returns `{kind: "text", hunks: [{lines: [{op: equal|add|remove, text, before_line, after_line}]}], added, removed, truncated}` with three lines of context. Over 5,000 lines or 200,000 characters it is refused (`DiffError`, code `too_large`); lines are cut at 500 characters and a diff shows at most 2,000 lines. `diff_value(before, after)` picks one for a changed field: text for prose (a line break, or over 120 characters), structure for everything else; text too large to compare line by line falls back to one clipped change.

## Sources and endpoints

A feature that keeps versions registers a source with `version_diff.register_source(VersionSource(key, label, params, versions, snapshot, kind="json"|"text"))`. `versions(user, workspace, ref)` lists what the caller may compare, oldest first (the live draft is a version with `current: true`); `snapshot(user, workspace, ref, version_id)` returns `(found, value)`. Both return nothing for what the caller may not see.

- `GET /api/v1/workspaces/{workspace}/versions/{source}/?<params>` lists the versions.
- `GET /api/v1/workspaces/{workspace}/versions/{source}/diff/?<params>&older=<id>&newer=<id>` returns `{source, older, newer, diff}` with `Cache-Control: private, no-store`.

Workspace members reach the endpoints; **the source decides who may see anything** (404 otherwise, 400 naming a missing parameter). Registered sources:

| Source   | Params          | Versions                                                                                       | Who                   |
| -------- | --------------- | ---------------------------------------------------------------------------------------------- | --------------------- |
| `form`   | `event`, `form` | each published version (`id` is its public id) and the draft (`draft`)                         | organizers and admins |
| `rubric` | `event`, `plan` | each published rubric version and the draft; compared as `{criteria: [...]}` by criterion `id` | organizers and admins |

The **configuration history** keeps its flat `changes` (`{field: {before, after}}`) unchanged and now also returns `diff` (`{field: diff_value(before, after)}`), so structured values and prose show as a diff instead of raw JSON, and an older client keeps working.

## Compatibility

Stateless and additive: no table, no migration, no stored change. The audit capture (`snapshot_fields`, `diff_snapshots`) is untouched and is the first level the history diff reads; form and rubric versions stay immutable.

## Verification

`tests/fixtures/diff_cases.json` holds 27 cases (structure, keyed and positional lists, moves, escaping, prose); pytest checks the server and vitest draws each case. `tests/integration/test_version_diff.py` also applies random diffs back to rebuild the new value, checks stable order, caps, clipping, depth, limits and hostile input, runs both sources through their role matrices (organizer, participant, judge, other workspace, signed out), checks that comparing writes nothing, and registers an independent text source.
