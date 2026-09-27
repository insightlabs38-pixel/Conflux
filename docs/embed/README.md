# Embedding the project gallery (EMB-001/002)

`<conflux-gallery>` is a self-contained Web Component that renders an
event's public project gallery on any external page. It has **zero runtime
dependencies** — the built file is the entire thing, ~2KB minified, with no
CDN, framework, or build step required on the page that embeds it.

## Quick start

```html
<script src="https://your-conflux-host.example.com/embed/conflux-gallery.js"></script>
<conflux-gallery event="EVENT_PUBLIC_ID"></conflux-gallery>
```

Or self-hosted, fully offline (see [examples/embed.html](../../examples/embed.html)):

```html
<script src="./conflux-gallery.js"></script>
<conflux-gallery
  event="EVENT_PUBLIC_ID"
  api-base="https://your-conflux-host.example.com"
></conflux-gallery>
```

## Attributes

| Attribute  | Required | Meaning                                                                                                                                                      |
| ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `event`    | yes      | The event's `public_id` (UUID).                                                                                                                              |
| `api-base` | no       | Origin to fetch from (default: same origin as the embedding page). Set this when the widget's `<script>` isn't served from the same host as the Conflux API. |
| `q`        | no       | Initial search filter, forwarded as `?q=` to the gallery API.                                                                                                |

The component only ever reads `GET /api/v1/events/<event>/gallery/` —
public, unauthenticated, and safe to call from any origin. It only shows
projects with a finalized submission, exactly like the server-rendered
gallery page.

## Self-host / offline compatibility

The build (`pnpm --filter @conflux/embed build`) produces one file,
`dist/conflux-gallery.js`, with no imports and no `fetch` calls to anything
but the `api-base` you configure. Copy it next to your HTML and reference it
with a relative `<script src>` — no internet access is needed beyond
reaching your own Conflux API for the gallery data. There's nothing to
license or attribute to embed it, and no telemetry.

## Building it yourself

```sh
cd src/embed
pnpm install
pnpm build   # -> dist/conflux-gallery.js
pnpm test    # vitest, incl. XSS-escaping and error/empty-state coverage
```
