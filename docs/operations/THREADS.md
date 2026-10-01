# Threads (THREADS)

Comments on one subject for one closed audience. A feature never adds its own `*Note` model: it registers a **subject** with one rule per **audience** and uses the generic endpoints and the `ThreadPanel` component. Code: `core/threads.py` (contract), `core/thread_views.py`, web `lib/threads.ts`, `components/ThreadPanel.tsx`, `components/NotesDialog.tsx`. First adopters: organizer notes on **applications** (`events/threads.py`) and **projects** (`projects/threads.py`), opened as "Notes" from the Registration and Projects grids.

## Contract

- **Subject and audience.** A thread is (event, subject type, subject id, audience); one thread per subject per audience. The audience is a closed set: `organizers`, `judges`, `participants`, `project_team`, `public`. The client names a subject and an audience; the **registration** decides who may read and who may post (`AudienceRule(can_read, can_post)`, `can_post` defaults to `can_read`). A subject registers only the audiences it supports.
- **No leaks.** An unregistered audience, a subject that is not in this event, an invalid id and a caller who may not read are all **404**, not 403. A reader who may not write gets 403. Callers outside the workspace are refused at the door (403) like every workspace endpoint, so the `public` audience is a rule for members until a public surface exists.
- **Text.** Plain text, 1 to 4,000 characters, stored and shown as text (the web renders it as text: no markup, no auto-links). One level of replies. At most 500 comments per thread.
- **Mentions.** Write `@username`. Only people who can read the thread are mentioned (ten at most per comment); a name that does not exist, cannot read, or is the author's own stays plain text and nothing tells the writer which case it was. A mention is delivered through the inbox (`communications/threads.py`, kind `thread_mention`, hidden from the organizers' sent list) and **never carries the comment text**, so removing a comment removes its content everywhere. Editing notifies only newly added mentions.
- **Edit and remove.** The author edits (and may remove). An organizer or admin may remove any comment, even in a thread they cannot read (moderation). Removal is a **tombstone**: text and mentions are erased, the row stays so replies keep their place; removing twice does nothing. Archived events are read-only.
- **Audit.** `thread.comment_posted`, `thread.comment_edited`, `thread.comment_removed` with ids and audience, never the text. Posts accept `Idempotency-Key`.

## Registering a subject

```python
from core import threads

threads.register_subject(threads.ThreadSubject(
    key="submission", label="Submission",
    get=lambda event, sid: Submission.objects.filter(project__event=event, public_id=sid).first(),
    describe=lambda s: f"the submission {s.title}",
    audiences={"organizers": threads.AudienceRule(can_read=is_organizer),
               "project_team": threads.AudienceRule(can_read=on_team)}))
```

`get` must return the subject **only if it belongs to the event**. Register in the app's `AppConfig.ready()`.

## API

| Call                                                                | Notes                                                                                                                           |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `GET /workspaces/{w}/events/{e}/threads/{subject}/{id}/{audience}/` | `limit` (1-100) and `offset` over top-level comments; an empty thread is returned without creating one; `can_post` tells the UI |
| `POST` the same URL                                                 | `{body, parent?}`; creates the thread on first use                                                                              |
| `PATCH /workspaces/{w}/events/{e}/thread-comments/{id}/`            | `{body}`, author only                                                                                                           |
| `DELETE` the same URL                                               | tombstone; author or organizer/admin                                                                                            |

## Compatibility and limits

Additive: tables `core_thread`, `core_threadcomment` (migration `core/0005_threads`), new endpoints, no change to an existing response; the only touched response is the organizers' message list, which now leaves out `thread_mention` notices. The four existing note/comment models (`community.Comment`, `deliberation.DeliberationNote`, `projects.MentorNote`, `communications.Message`) are **not migrated or dual-written**; new features use threads. Threads are not part of the event archive (internal notes are private by design). Not built: a note count column in the grids, a people picker (the thread offers people who already wrote there), reactions, attachments, editing history, and a public (signed-out) read surface.
