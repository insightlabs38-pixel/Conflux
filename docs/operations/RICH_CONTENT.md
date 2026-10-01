# Rich content (RICH_DOC)

One renderer for text that people write and other people read: project stories, page text and whatever a feature adds next. Code: `core/rich.py` (profiles, `render_html`, `render_tree`), `core/rich_page.py` (the allowlist sanitizer), `core/rich_views.py` (the preview endpoint); web `lib/rich.ts`, `components/RichDoc.tsx` (draws a tree) and `components/RichEditor.tsx` (a text box with a preview). First adopter on the web: the participant's project story editor.

## Profiles

Source text is always read in a named **profile**, never guessed. A feature uses one of these; a new profile is added in `core/rich.py` beside them so every rendering keeps one set of rules.

| Profile | Source     | Used for                            | Keeps                                                                                                                              |
| ------- | ---------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `story` | CommonMark | project descriptions (participants) | paragraphs, headings (demoted one level), lists, quotes, tables, code (highlighted), emphasis, code spans, links                   |
| `page`  | HTML       | RichText page blocks (organizers)   | the twelve tags of `core/rich_page.py` (`p`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `a`, `h2`-`h4`, `blockquote`) and `href` only |

Never rendered, in either: raw HTML in a story, images, scripts, event handlers, styles. A link works only with no scheme (relative), `http`, `https` or `mailto`; anything else is shown as the text the author typed.

## Two renderings that agree

- `render_html(source, profile)` is for server-rendered pages (the public site, templates). It is unbounded on purpose: stored content keeps rendering whatever its length.
- `render_tree(source, profile)` is for the browser: a closed tree of nodes React draws, so no HTML from a participant or an organizer is ever injected into a page. It is bounded: a source over 100,000 characters is refused (`too_long`), a tree over 20,000 parts is refused (`too_complex`) and nesting over 32 levels is refused (`too_deep`); nothing is truncated. A refusal is a `RichError(code, message)`.

Nodes: blocks `paragraph`, `heading {level 2-6}`, `list {ordered, start}`, `item`, `quote`, `code {language, text, tokens}`, `table`, `row {header}`, `cell {align}`, `rule`; inlines `text`, `emphasis`, `strong`, `code_span`, `link {href}`, `break`. A tight list item or page text outside a paragraph holds inlines directly. `tokens` are highlighted runs `[kind, text]` (pygments' short class names; `""` is plain text) that the web colors from theme tokens. Anything else is dropped, never passed through.

## Preview endpoint

`POST /api/v1/workspaces/{workspace}/rich/preview/` with `{profile, source}` returns `{profile, length, max_length, tree}`. Any workspace member may use it; a person outside the workspace gets 403. It renders for the caller only, stores nothing and writes no audit row (the save of the text is the audited mutation, as before). 400 bodies name the field: `{"profile": [...]}` or `{"source": [...]}`. The same input always gives the same tree.

## Using it

```python
from core import rich
html = rich.render_html(project.description, "story")      # a page
tree = rich.render_tree(source, "story")                    # the preview; raises rich.RichError
```

```tsx
<RichEditor label="Project description" profile="story" workspaceId={workspace}
            value={text} onChange={setText} />          // text box + Preview
<RichDoc tree={tree} label="Preview" />                    // draw a server tree
```

## Compatibility

Stateless and additive: no table, no migration, no stored value changes. `presentation.technical.render_technical_description` and `presentation.sanitize.sanitize_html` keep their names and delegate. The public HTML of stories is byte-identical to the previous renderer (`tests/integration/test_rich.py` holds a frozen copy of the old one as the oracle over 300 generated documents) with **one intended difference**: a story link is a link only on `http`, `https`, `mailto` or a relative URL; the old renderer also linked `ftp:`, `tel:`, `git:` and similar schemes, which now show as plain text. The page profile is the same sanitizer, moved unchanged.

## Verification

`tests/fixtures/rich_cases.json` holds 22 sources with the trees the server must produce; pytest checks the server, vitest draws each tree and checks the markup (no active element or handler, only safe links). Hostile and random input is checked to stay inside the node set.
