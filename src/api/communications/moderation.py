import hashlib
import json

from artifacts.models import Artifact, ArtifactStatus, ArtifactValidation
from audit.services import record_mutation
from community.models import AbuseSignal, Comment
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Exists, F, Max, OuterRef, Q, Subquery
from django.utils import timezone
from events.models import Event, EventApplication, EventStatus, RegistrationStatus
from events.registration import decide_application
from rest_framework.utils.encoders import JSONEncoder

from .models import ModerationReview

KINDS = ("duplicate", "voting", "content", "artifact", "eligibility")
ACTIONS = {
    "duplicate": ["dismiss", "escalate"],
    "voting": ["resolve", "escalate"],
    "content": ["hide", "dismiss", "escalate"],
    "artifact": ["acknowledge", "escalate"],
    "eligibility": ["approve", "reject", "waitlist", "escalate"],
}
PAGE_SIZE = 50


class ChangedEvidence(Exception):
    pass


def _json(value):
    return json.loads(json.dumps(value, cls=JSONEncoder))


def _digest(evidence):
    return hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()


def _latest_validations():
    latest = (
        ArtifactValidation.objects.filter(
            artifact_id=OuterRef("artifact_id"), validator=OuterRef("validator")
        )
        .order_by("-checked_at", "-pk")
        .values("pk")[:1]
    )
    return ArtifactValidation.objects.annotate(latest_pk=Subquery(latest)).filter(pk=F("latest_pk"))


def _sources(event, kind):
    if kind == "duplicate":
        return (
            Artifact.objects.filter(project__event=event, sha256__regex=r"^[a-f0-9]{64}$")
            .values("sha256")
            .annotate(
                project_count=Count("project_id", distinct=True),
                artifact_count=Count("id"),
                last_changed=Max("updated_at"),
            )
            .filter(project_count__gt=1)
            .order_by("sha256")
        )
    if kind == "voting":
        return AbuseSignal.objects.filter(plan__event=event, resolved_at=None).order_by("public_id")
    if kind == "content":
        return (
            Comment.objects.filter(project__event=event, hidden_at=None)
            .select_related("project", "author")
            .order_by("public_id")
        )
    if kind == "artifact":
        issues = _latest_validations().filter(artifact_id=OuterRef("pk")).exclude(outcome="ok")
        return (
            Artifact.objects.filter(project__event=event)
            .select_related("project")
            .annotate(has_issue=Exists(issues))
            .filter(Q(status=ArtifactStatus.REJECTED) | Q(has_issue=True))
            .order_by("public_id")
        )
    return (
        EventApplication.objects.filter(
            event=event,
            status__in=[
                RegistrationStatus.PENDING,
                RegistrationStatus.WAITLISTED,
            ],
        )
        .select_related("user")
        .order_by("public_id")
    )


def _item(event, kind, source):
    if kind == "duplicate":
        key = source["sha256"]
        artifacts = Artifact.objects.filter(project__event=event, sha256=key).order_by("public_id")
        evidence = {
            **source,
            "samples": list(artifacts.values("public_id", "project__public_id")[:50]),
            "detail": "Matching declared artifact hashes across projects; indicator only.",
        }
    elif kind == "voting":
        key = str(source.public_id)
        evidence = {
            "signal_type": source.signal_type,
            "detail": source.detail,
            "evidence": source.evidence,
            "occurred_at": source.occurred_at,
        }
    elif kind == "content":
        key = str(source.public_id)
        evidence = {
            "project": str(source.project.public_id),
            "author": str(source.author.public_id),
            "body": source.body,
            "created_at": source.created_at,
        }
    elif kind == "artifact":
        key = str(source.public_id)
        validations = _latest_validations().filter(artifact=source).order_by("validator")
        evidence = {
            "project": str(source.project.public_id),
            "title": source.title,
            "status": source.status,
            "updated_at": source.updated_at,
            "validation_count": validations.count(),
            "last_checked": validations.aggregate(last=Max("checked_at"))["last"],
            "checks": list(
                validations.values("public_id", "validator", "outcome", "detail", "checked_at")[:50]
            ),
        }
    else:
        key = str(source.public_id)
        evidence = {
            "user": str(source.user.public_id),
            "status": source.status,
            "note": source.note,
            "waitlist_position": source.waitlist_position,
            "updated_at": source.updated_at,
        }
    evidence = _json(evidence)
    return {
        "kind": kind,
        "source_key": key,
        "evidence": evidence,
        "evidence_digest": _digest(evidence),
        "actions": ACTIONS[kind],
    }


def review_data(review):
    return {
        "public_id": str(review.public_id),
        "kind": review.kind,
        "source_key": review.source_key,
        "evidence_digest": review.evidence_digest,
        "evidence": review.evidence,
        "disposition": review.disposition,
        "note": review.note,
        "actor": str(review.actor.public_id),
        "created_at": review.created_at,
    }


def queue(event, *, kind=None, offset=0):
    sections = []
    for current in [kind] if kind else KINDS:
        query = _sources(event, current)
        total = query.count()
        items = [_item(event, current, row) for row in query[offset : offset + PAGE_SIZE]]
        keys = [item["source_key"] for item in items]
        latest = {}
        newest = (
            ModerationReview.objects.filter(
                event=event, kind=current, source_key=OuterRef("source_key")
            )
            .order_by("-created_at", "-pk")
            .values("pk")[:1]
        )
        reviews = (
            ModerationReview.objects.filter(event=event, kind=current, source_key__in=keys)
            .annotate(newest_pk=Subquery(newest))
            .filter(pk=F("newest_pk"))
            .select_related("actor")
            .order_by("-created_at", "-pk")
        )
        for review in reviews:
            if review.source_key not in latest:
                latest[review.source_key] = review
        for item in items:
            review = latest.get(item["source_key"])
            item["latest_review"] = review_data(review) if review else None
            item["review_current"] = bool(
                review and review.evidence_digest == item["evidence_digest"]
            )
        sections.append(
            {
                "kind": current,
                "count": total,
                "items": items,
                "offset": offset,
                "next_offset": offset + PAGE_SIZE if offset + PAGE_SIZE < total else None,
            }
        )
    return {"sections": sections}


@transaction.atomic
def review_source(*, event, actor, kind, source_key, evidence_digest, disposition, note):
    event = Event.objects.select_for_update().get(pk=event.pk)
    if event.status == EventStatus.ARCHIVED:
        raise ValidationError("Archived events cannot be moderated.")
    if disposition not in ACTIONS[kind]:
        raise ValidationError("This disposition is not available for this source kind.")
    query = _sources(event, kind)
    if kind == "duplicate":
        source = query.filter(sha256=source_key).first()
    else:
        source = query.select_for_update(of=("self",)).filter(public_id=source_key).first()
    if source is None:
        raise ChangedEvidence("Source is unavailable or no longer needs review; refresh the queue.")
    item = _item(event, kind, source)
    if item["evidence_digest"] != evidence_digest:
        raise ChangedEvidence("Evidence changed; refresh the queue before reviewing.")
    now = timezone.now()
    if kind == "voting" and disposition == "resolve":
        source.resolved_at, source.resolved_by, source.resolution_note = now, actor, note
        source.save(update_fields=["resolved_at", "resolved_by", "resolution_note"])
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="community_abuse.resolved",
            target=source,
            metadata={"event_id": str(event.public_id), "note": note},
        )
    elif kind == "content" and disposition == "hide":
        source.hidden_at, source.hidden_by = now, actor
        source.save(update_fields=["hidden_at", "hidden_by"])
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="comment.hidden",
            target=source,
            metadata={"event_id": str(event.public_id)},
        )
    elif kind == "eligibility" and disposition != "escalate":
        decision = {
            "approve": RegistrationStatus.APPROVED,
            "reject": RegistrationStatus.REJECTED,
            "waitlist": RegistrationStatus.WAITLISTED,
        }[disposition]
        decide_application(source, decision, actor=actor)
    review = ModerationReview.objects.create(
        event=event,
        actor=actor,
        kind=kind,
        source_key=source_key,
        evidence_digest=evidence_digest,
        evidence=item["evidence"],
        disposition=disposition,
        note=note,
    )
    record_mutation(
        actor=actor,
        workspace=event.workspace,
        action="moderation.reviewed",
        target=review,
        metadata={
            "event": str(event.public_id),
            "kind": kind,
            "source_key": source_key,
            "evidence_digest": evidence_digest,
            "disposition": disposition,
            "note": note,
        },
    )
    return review
