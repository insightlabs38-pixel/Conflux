from urllib.parse import urlsplit

from audit.services import record_mutation
from core.authz import has_any_role
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.utils import timezone
from events.models import EventStatus
from projects.models import Project, SubmissionStatus
from workspaces.models import Role

from .models import (
    MAX_UPDATES_PER_PROJECT,
    SEEKING_CHOICES,
    ContinuationUpdate,
    ProjectContinuation,
)

_url_validator = URLValidator(schemes=["http", "https"])


def _is_organizer(user, workspace):
    return has_any_role(user, workspace, Role.ORGANIZER, Role.ADMIN)


def _require_member(project, actor):
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only a project member can change its continuation.")


def _require_post_event(project):
    if project.event.status not in (EventStatus.CLOSED, EventStatus.ARCHIVED):
        raise ValidationError("Continuation opens once the event has closed.")
    if not project.submissions.filter(status=SubmissionStatus.FINALIZED).exists():
        raise ValidationError("Only projects with a finalized submission can continue.")


def _clean_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    _url_validator(value)
    if urlsplit(value).username is not None or "@" in urlsplit(value).netloc:
        raise ValidationError("URLs must not embed credentials.")
    return value


def _clean_text(value, name, limit):
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be text.")
    value = value.strip()
    if not value:
        raise ValidationError(f"{name} is required.")
    if len(value) > limit:
        raise ValidationError(f"{name} is limited to {limit} characters.")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValidationError(f"{name} contains control characters.")
    return value


@transaction.atomic
def save_continuation(project, actor, *, summary, url="", seeking=(), is_public=False):
    project = (
        Project.objects.select_for_update(of=("self",)).select_related("event").get(pk=project.pk)
    )
    _require_member(project, actor)
    _require_post_event(project)
    if not isinstance(seeking, (list, tuple)) or any(s not in SEEKING_CHOICES for s in seeking):
        raise ValidationError(f"seeking must be a list drawn from {list(SEEKING_CHOICES)}.")
    if not isinstance(is_public, bool):
        raise ValidationError("is_public must be a boolean.")
    fields = {
        "summary": _clean_text(summary, "summary", 1000),
        "url": _clean_url(url),
        "seeking": sorted(set(seeking)),
        "is_public": is_public,
    }
    try:
        with transaction.atomic():
            item, created = ProjectContinuation.objects.select_for_update().get_or_create(
                project=project, defaults=fields
            )
    except IntegrityError:
        item, created = ProjectContinuation.objects.select_for_update().get(project=project), False
    if not created:
        for name, value in fields.items():
            setattr(item, name, value)
        item.save()
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="continuation.saved",
        target=item,
        metadata={"project": str(project.public_id), "is_public": item.is_public},
    )
    return item


@transaction.atomic
def add_update(project, actor, *, body):
    project = (
        Project.objects.select_for_update(of=("self",)).select_related("event").get(pk=project.pk)
    )
    _require_member(project, actor)
    item = ProjectContinuation.objects.select_for_update().filter(project=project).first()
    if item is None:
        raise ValidationError("Create the continuation profile first.")
    if item.updates.count() >= MAX_UPDATES_PER_PROJECT:
        raise ValidationError(f"A project can post at most {MAX_UPDATES_PER_PROJECT} updates.")
    update = ContinuationUpdate.objects.create(
        continuation=item, body=_clean_text(body, "body", 1000), created_by=actor
    )
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="continuation.update_posted",
        target=update,
        metadata={"project": str(project.public_id)},
    )
    return update


@transaction.atomic
def set_hidden(item, actor, *, hidden, reason=""):
    item = (
        ProjectContinuation.objects.select_for_update(of=("self",))
        .select_related("project__event__workspace")
        .get(pk=item.pk)
    )
    workspace = item.project.event.workspace
    if not _is_organizer(actor, workspace):
        raise ValidationError("Only an organizer can moderate continuations.")
    if hidden:
        reason = reason.strip()
        if not reason:
            raise ValidationError("A reason is required to hide a continuation.")
        item.hidden_at, item.hidden_by, item.hidden_reason = timezone.now(), actor, reason[:300]
    else:
        item.hidden_at, item.hidden_by, item.hidden_reason = None, None, ""
    item.save()
    record_mutation(
        actor=actor,
        workspace=workspace,
        action="continuation.hidden" if hidden else "continuation.restored",
        target=item,
        metadata={"project": str(item.project.public_id)},
    )
    return item
