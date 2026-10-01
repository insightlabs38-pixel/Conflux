# Safe previews (ARTIFACT_PREVIEW)

One way to show what a file or a link is without opening it: submitted evidence, a job's output and whatever comes next. Code: `core/previews.py` (sources, descriptor), `core/preview_views.py` (endpoint), `artifacts/previews.py` (the two sources), `artifacts/access.py` (who may see an artifact); web `lib/preview.ts` and `components/ArtifactPreview.tsx` (`ArtifactPreview` draws a descriptor, `PreviewLoader` fetches and draws it with its loading, error and nothing-here states). Adopters: the judges' and organizers' artifact inspector and the job output list in Operations.

## What it does and does not do

A preview is **derived on every read and never stored**. Nothing is rendered, executed, unpacked or fetched by the pipeline: it reshapes an inspection the source already has (the stored static inspection of an artifact, or `artifacts.inspector.inspect_bytes` run on a job's output) into one descriptor. Looking writes nothing, audits nothing and does not start an inspection; the existing `POST .../inspection/` does that (and is audited as before).

## The descriptor

`GET /api/v1/workspaces/{workspace}/previews/{source}/?<params>` (workspace members; 404 for anything the caller may not see, 400 naming a missing parameter, `Cache-Control: private, no-store`).

| Field                    | Meaning                                                                                                                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `kind`                   | `text`, `image`, `video`, `document`, `archive`, `data`, `link` or `unavailable`                                                                                                                              |
| `state`                  | `ready`, `pending` (not inspected yet) or `unavailable`                                                                                                                                                       |
| `reason`                 | `{code, message}` when not ready: `not_inspected`, `purged`, `too_large`, `no_preview`, `unsafe_link`, or the first blocking finding (`active_content`, `executable`, `archive_bomb`, `digest_mismatch`, ...) |
| `detected_type`, `facts` | what the content looks like (by bytes, not name) and safe scalar facts (size, dimensions, pages, entries); every value is bounded text                                                                        |
| `findings`               | `{level: info, warning or blocked, code, message}`, at most 20 (`findings_total` counts all)                                                                                                                  |
| `text`                   | at most 4,000 characters, secrets already redacted by the inspector (`text` and `data` only)                                                                                                                  |
| `entries`                | the first 50 files of an archive (`entries_total` counts all)                                                                                                                                                 |
| `media`                  | `{url, filename}`: the source's existing attachment-only download; never inlined; absent when withheld                                                                                                        |
| `link`                   | the address of a link, only if it is http or https                                                                                                                                                            |

Content that can run (web pages, SVG, programs), anything that failed a safety check (including a checksum mismatch), a purged file and anything the source refuses are `unavailable` with the reason and **no download**. A file nobody recognises is `unavailable` (`no_preview`) with the download kept. `data` is text whose name ends `.csv`, `.tsv`, `.json`, `.jsonl` or `.ndjson`, or whose artifact kind is `dataset`.

## Sources

| Source             | Parameters                     | Who sees it                                                                                                                                                                                    | Content                                                                                              |
| ------------------ | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `project_artifact` | `event`, `project`, `artifact` | exactly the reviewer rules (`artifacts/access.py`): organizers and admins everything, project members their own, judges only what is visible to judges and only for projects they are assigned | the stored inspection; the download is the presigned attachment URL, withheld when blocked or purged |
| `job_output`       | `job`, `name`                  | whoever may see the job (`core.jobs.visible_to`: the requester, organizers and admins)                                                                                                         | inspected on the fly, not stored; the download is the job output route                               |

A feature registers its own with `previews.register_source(PreviewSource(key, label, params, resolve))`, where `resolve(user, workspace, ref)` returns a `Subject` (name, size, a ready inspection, an optional download address) or `None`. It never builds markup, and a source that refuses a thing says so with `Subject.unavailable`.

## Compatibility

Stateless and additive: no table, no migration, no change to artifact, inspection or job storage or to their endpoints. `ReviewBase` now delegates to `artifacts/access.py` and `_JobView` to `core.jobs.visible_to` (the same rules, one definition each). The inspector's output, serving (attachment only) and the review list are unchanged.

## Verification

`tests/integration/test_previews.py` runs the real inspector over images, video, PDF, archives, text with a secret, web pages, SVG and programs and checks each descriptor; the role matrix for both sources (member, judge, organizer, other participant, outsider, signed out, another workspace); no inspection row, audit row, storage read or link fetch caused by previewing; and an independent source registered by the test.
