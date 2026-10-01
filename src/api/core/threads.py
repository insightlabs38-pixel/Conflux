"""Threads: comments on one thing for one closed audience (PD-F002-B01-T07).

A feature never adds its own `*Note` model. It registers a **subject** (what can be discussed) with
one rule per **audience** (who reads and writes) and the generic endpoints do the rest:

    threads.register_subject(threads.ThreadSubject(
        "application", "Application", get=lookup, describe=label,
        audiences={"organizers": threads.AudienceRule(can_read=is_organizer)}))

Rules
- The client names a subject and an audience; the *registration* decides who may read and post,
  and the subject must belong to the event. An audience the subject does not register, a subject
  of another event and a reader without access are all 404: nothing leaks by guessing ids.
- Plain text only, 1 to 4,000 characters, shown as text (never interpreted). One level of replies.
  A thread keeps at most 500 comments.
- `@username` mentions are accepted only for people who can read the thread; anything else stays
  plain text and nobody learns whether the name exists. A mention notifies through the inbox
  (a registered notifier), without the comment text, so removing a comment removes its content
  everywhere.
- Edit is the author's. Removal (author, or an organizer/admin) is a tombstone: text and mentions
  are erased, the row stays so replies keep their place. Archived events are read-only.
- Posting, editing and removal are audited (ids and kinds, never the text).
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from audit.services import record_mutation
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .authz import has_any_role
from .models import Thread, ThreadComment

MAX_BODY = 4000
MAX_COMMENTS = 500
MAX_MENTIONS = 10
_MENTION = re.compile(r"(?<![\w@])@([A-Za-z0-9][A-Za-z0-9_.+-]{0,149})")


@dataclass(frozen=True)
class AudienceRule:
    """`can_read(user, workspace, event, subject)`; `can_post` defaults to the same rule."""

    can_read: Callable
    can_post: Callable | None = None


@dataclass(frozen=True)
class ThreadSubject:
    """What can be discussed. `get(event, subject_id)` returns the subject *in that event* or None;
    `describe(subject)` is a short label for notifications."""

    key: str
    label: str
    get: Callable
    describe: Callable
    audiences: dict = field(default_factory=dict)


SUBJECTS: dict[str, ThreadSubject] = {}
NOTIFIERS: list[Callable] = []


def register_subject(subject: ThreadSubject):
    """Add a subject once; a different registration under a taken key is a bug."""
    if subject.key in SUBJECTS and SUBJECTS[subject.key] != subject:
        raise ValueError(f"Thread subject {subject.key!r} is already registered")
    unknown = set(subject.audiences) - set(Thread.Audience.values)
    if unknown or not subject.audiences:
        raise ValueError(f"Thread subject {subject.key!r} needs audiences from the closed set")
    SUBJECTS[subject.key] = subject
    return subject


def register_notifier(notifier: Callable):
    """`notifier(event, actor, users, subject_label)` tells mentioned users (DB only)."""
    if notifier not in NOTIFIERS:
        NOTIFIERS.append(notifier)
    return notifier


class Target:
    """A resolved (subject, audience) the caller has already been checked against."""

    def __init__(self, event, definition, subject, audience, rule):
        self.event, self.definition, self.subject = event, definition, subject
        self.audience, self.rule = audience, rule

    def readable_by(self, user):
        return bool(self.rule.can_read(user, self.event.workspace, self.event, self.subject))

    def postable_by(self, user):
        check = self.rule.can_post or self.rule.can_read
        return bool(check(user, self.event.workspace, self.event, self.subject))


def resolve(event, user, subject_type, subject_id, audience):
    """The target if it exists in the event and `user` may read it; otherwise 404."""
    definition = SUBJECTS.get(subject_type)
    rule = definition.audiences.get(audience) if definition else None
    if rule is None:
        raise Http404
    subject = definition.get(event, subject_id)
    if subject is None:
        raise Http404
    target = Target(event, definition, subject, audience, rule)
    if not target.readable_by(user):
        raise Http404
    return target


def _thread(target):
    return Thread.objects.filter(
        event=target.event,
        subject_type=target.definition.key,
        subject_id=str(target.subject.public_id),
        audience=target.audience,
    ).first()


def _clean(body):
    if not isinstance(body, str):
        raise ValidationError({"body": ["Write some text."]})
    body = body.strip()
    if not body:
        raise ValidationError({"body": ["A comment cannot be empty."]})
    if len(body) > MAX_BODY:
        raise ValidationError({"body": [f"Keep a comment under {MAX_BODY} characters."]})
    return body


def _mentioned(target, author, body):
    """Users named with @username who can read this thread (never the author)."""
    from accounts.models import User

    names = list(dict.fromkeys(_MENTION.findall(body)))[:MAX_MENTIONS]
    if not names:
        return []
    found = User.objects.filter(username__in=names).exclude(pk=author.pk)
    return [u for u in found if target.readable_by(u)]


def _notify(target, actor, users):
    if users:
        label = target.definition.describe(target.subject)
        for notifier in NOTIFIERS:
            notifier(target.event, actor, users, label)


def _ensure_writable(event):
    if event.status == "archived":
        raise ValidationError({"detail": "Archived events are read-only."})


def post(target, author, body, parent_id=None):
    """Add a comment (creating the thread on first use); returns the comment."""
    if not target.postable_by(author):
        raise PermissionDenied("You may read this thread but not write in it.")
    _ensure_writable(target.event)
    body = _clean(body)
    with transaction.atomic():
        thread = _thread(target)
        if thread is None:
            try:
                with transaction.atomic():
                    thread = Thread.objects.create(
                        workspace=target.event.workspace,
                        event=target.event,
                        subject_type=target.definition.key,
                        subject_id=str(target.subject.public_id),
                        audience=target.audience,
                    )
            except IntegrityError:
                thread = _thread(target)
        thread = Thread.objects.select_for_update(of=("self",)).get(pk=thread.pk)
        if thread.comments.count() >= MAX_COMMENTS:
            raise ValidationError({"detail": "This thread is full."})
        parent = None
        if parent_id:
            parent = thread.comments.filter(public_id=parent_id).first()
            if parent is None:
                raise ValidationError({"parent": ["Reply to a comment in this thread."]})
            if parent.parent_id:
                raise ValidationError({"parent": ["Replies go one level deep."]})
            if parent.removed_at:
                raise ValidationError({"parent": ["That comment was removed."]})
        mentioned = _mentioned(target, author, body)
        comment = ThreadComment.objects.create(
            thread=thread, parent=parent, author=author, body=body
        )
        comment.mentions.set(mentioned)
        record_mutation(
            actor=author,
            workspace=target.event.workspace,
            action="thread.comment_posted",
            target=comment,
            metadata={
                "subject": [target.definition.key, str(target.subject.public_id)],
                "audience": target.audience,
                "reply": parent is not None,
                "mentions": len(mentioned),
            },
        )
        _notify(target, author, mentioned)
    return comment


def comment_target(event, user, comment_public_id):
    comment = (
        ThreadComment.objects.select_related("thread", "author")
        .filter(thread__event=event, public_id=comment_public_id)
        .first()
    )
    if comment is None:
        raise Http404
    thread = comment.thread
    definition = SUBJECTS.get(thread.subject_type)
    rule = definition.audiences.get(thread.audience) if definition else None
    subject = definition.get(event, thread.subject_id) if definition else None
    if rule is None or subject is None:
        raise Http404
    return comment, Target(event, definition, subject, thread.audience, rule)


def _moderator(user, event):
    from workspaces.models import Role

    return has_any_role(user, event.workspace, Role.ORGANIZER, Role.ADMIN)


def edit(event, user, comment_public_id, body):
    comment, target = comment_target(event, user, comment_public_id)
    if not target.readable_by(user):
        raise Http404
    if comment.author_id != user.pk:
        raise PermissionDenied("Only the author can edit a comment.")
    _ensure_writable(event)
    if comment.removed_at:
        raise ValidationError({"detail": "That comment was removed."})
    body = _clean(body)
    with transaction.atomic():
        before = set(comment.mentions.values_list("pk", flat=True))
        mentioned = _mentioned(target, user, body)
        comment.body = body
        comment.edited_at = timezone.now()
        comment.save(update_fields=["body", "edited_at"])
        comment.mentions.set(mentioned)
        record_mutation(
            actor=user,
            workspace=event.workspace,
            action="thread.comment_edited",
            target=comment,
            metadata={"audience": target.audience},
        )
        _notify(target, user, [u for u in mentioned if u.pk not in before])
    return comment


def remove(event, user, comment_public_id):
    """Tombstone: the author or an organizer/admin removes the text and mentions."""
    comment, target = comment_target(event, user, comment_public_id)
    is_author = comment.author_id == user.pk and target.readable_by(user)
    if not is_author and not _moderator(user, event):
        raise Http404
    _ensure_writable(event)
    if comment.removed_at:
        return comment
    with transaction.atomic():
        comment.body = ""
        comment.removed_at = timezone.now()
        comment.removed_by = user
        comment.save(update_fields=["body", "removed_at", "removed_by"])
        comment.mentions.clear()
        record_mutation(
            actor=user,
            workspace=event.workspace,
            action="thread.comment_removed",
            target=comment,
            metadata={"audience": target.audience, "by_author": comment.author_id == user.pk},
        )
    return comment


def _iso(value):
    return value.isoformat().replace("+00:00", "Z") if value else None


def describe_comment(comment, viewer, target, replies=()):
    removed = comment.removed_at is not None
    mine = comment.author_id == viewer.pk
    return {
        "public_id": str(comment.public_id),
        "author": {"public_id": str(comment.author.public_id), "username": comment.author.username},
        "body": "" if removed else comment.body,
        "removed": removed,
        "edited": comment.edited_at is not None and not removed,
        "mentions": [] if removed else sorted(u.username for u in comment.mentions.all()),
        "created_at": _iso(comment.created_at),
        "can_edit": mine and not removed and target.postable_by(viewer),
        "can_remove": not removed and (mine or _moderator(viewer, target.event)),
        "replies": [describe_comment(r, viewer, target) for r in replies],
    }


def view(target, viewer, limit=50, offset=0):
    """The thread as `viewer` may see it (an empty one if nobody has written yet)."""
    thread = _thread(target)
    base = {
        "subject": {
            "type": target.definition.key,
            "id": str(target.subject.public_id),
            "label": target.definition.describe(target.subject),
        },
        "audience": target.audience,
        "can_post": target.postable_by(viewer),
    }
    if thread is None:
        return {**base, "total": 0, "comments": []}
    tops = thread.comments.filter(parent__isnull=True).select_related("author")
    total = tops.count()
    page = list(tops.prefetch_related("mentions")[offset : offset + limit])
    replies = {}
    for reply in (
        thread.comments.filter(parent__in=page)
        .select_related("author")
        .prefetch_related("mentions")
    ):
        replies.setdefault(reply.parent_id, []).append(reply)
    return {
        **base,
        "total": total,
        "comments": [describe_comment(c, viewer, target, replies.get(c.pk, ())) for c in page],
    }
