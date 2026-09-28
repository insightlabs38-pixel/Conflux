"""Per-event participant-data export, erasure and retention enforcement.

Erasure removes only personal data that no result depends on. Rows that back
finalized submissions, judging evidence or awards are retained and reported,
never silently rewritten. Private artifact bytes are purged in two phases
(mark, then delete the object) so a storage failure is retried, not forgotten.
"""

import json
from datetime import timedelta

from artifacts.models import Artifact, ArtifactStatus, ArtifactVisibility
from artifacts.storage import S3Storage
from audit.services import record_mutation
from communications.models import MessageRecipient
from community.models import Comment
from django.db import transaction
from evaluations.models import Appeal, AppealStatus, Assignment, Ballot, PairwiseComparison
from events.models import EventApplication, ParticipantCheckIn
from participation.models import MarketplaceProfile, TeamMembership
from presentation.models import SavedPublicSearch
from projects.models import ProjectMembership, Submission, SubmissionVersion
from rest_framework.utils.encoders import JSONEncoder
from taxonomy.models import TaxonomyAssignment
from workspaces.models import Membership

from .models import EventRetentionPolicy

RETAINED_REASON = (
    "Retained: finalized submissions, judging evidence, results and audit history must "
    "remain verifiable."
)


def _personal(event, user=None):
    def only(queryset, field):
        return queryset.filter(**{field: user}) if user else queryset

    return {
        "event_applications": only(EventApplication.objects.filter(event=event), "user"),
        "marketplace_profiles": only(MarketplaceProfile.objects.filter(event=event), "user"),
        "saved_searches": only(SavedPublicSearch.objects.filter(event=event), "owner"),
        "check_ins": only(ParticipantCheckIn.objects.filter(event=event), "participant"),
        "message_receipts": only(MessageRecipient.objects.filter(message__event=event), "user"),
        "comments": only(Comment.objects.filter(project__event=event), "author"),
        "person_labels": only(
            TaxonomyAssignment.objects.filter(event=event, subject_type="person"), "person"
        ),
    }


def _retained(event, user):
    return {
        "team_memberships": TeamMembership.objects.filter(team__event=event, user=user),
        "project_memberships": ProjectMembership.objects.filter(project__event=event, user=user),
        "submissions": Submission.objects.filter(project__event=event, updated_by=user),
        "submission_versions": SubmissionVersion.objects.filter(
            submission__project__event=event, finalized_by=user
        ),
        "ballots": Ballot.objects.filter(project__event=event, judge=user),
        "assignments": Assignment.objects.filter(project__event=event, judge=user),
        "pairwise_comparisons": PairwiseComparison.objects.filter(
            plan__stage__event=event, judge=user
        ),
        "appeals": Appeal.objects.filter(project__event=event, submitted_by=user),
    }


def _private_artifacts(event, user=None):
    queryset = (
        Artifact.objects.filter(project__event=event)
        .exclude(visibility=ArtifactVisibility.PUBLIC)
        .exclude(object_key="")
        .exclude(status=ArtifactStatus.PURGED)
    )
    return queryset.filter(created_by=user) if user else queryset


def _held(artifacts):
    """Projects with an undecided appeal keep their evidence until it is decided."""
    return artifacts.filter(
        project__appeals__status=AppealStatus.PENDING,
    ).distinct()


def _plain(value):
    return json.loads(json.dumps(value, cls=JSONEncoder))


def subject_exists(event, user):
    return (
        Membership.objects.filter(workspace=event.workspace, user=user).exists()
        or any(rows.exists() for rows in _personal(event, user).values())
        or any(rows.exists() for rows in _retained(event, user).values())
    )


def export_subject(event, user, *, actor):
    personal = {
        "event_applications": ("status", "note", "waitlist_position", "created_at"),
        "marketplace_profiles": (
            "skills",
            "roles",
            "interests",
            "availability_hours_per_week",
            "bio",
            "visible",
        ),
        "saved_searches": ("name", "filters", "created_at"),
        "check_ins": ("checked_in_at",),
        "message_receipts": ("message__subject", "read_at"),
        "comments": ("project__public_id", "body", "created_at", "hidden_at"),
        "person_labels": ("term__taxonomy__key", "term__key", "created_at"),
    }
    retained = {
        "team_memberships": ("team__public_id", "role", "joined_at"),
        "project_memberships": ("project__public_id", "role", "joined_at"),
        "submissions": ("project__public_id", "status", "updated_at"),
        "submission_versions": ("submission__project__public_id", "number", "finalized_at"),
        "ballots": ("project__public_id", "submitted_at"),
        "assignments": ("project__public_id",),
        "pairwise_comparisons": ("project_a__public_id", "project_b__public_id", "submitted_at"),
        "appeals": ("project__public_id", "status", "body", "created_at"),
    }
    with transaction.atomic():
        data = {
            "subject": {"id": str(user.public_id), "username": user.username},
            "event": str(event.public_id),
            "data": {
                name: list(rows.values(*personal[name]).order_by("pk"))
                for name, rows in _personal(event, user).items()
            },
            "retained_data": {
                name: list(rows.values(*retained[name]).order_by("pk"))
                for name, rows in _retained(event, user).items()
            },
            "artifacts": list(
                Artifact.objects.filter(project__event=event, created_by=user)
                .values(
                    "public_id",
                    "kind",
                    "visibility",
                    "title",
                    "external_url",
                    "content_type",
                    "byte_size",
                    "sha256",
                    "status",
                    "created_at",
                )
                .order_by("pk")
            ),
        }
        data = _plain(data)
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="privacy.subject_exported",
            target=user,
            metadata={
                "event_id": str(event.public_id),
                "counts": {name: len(rows) for name, rows in data["data"].items()},
            },
        )
    return data


def _artifact_plan(artifacts):
    held = _held(artifacts).count()
    return {"purge": artifacts.count() - held, "held_for_pending_appeals": held}


def _plan(event, user=None):
    plan = {name: rows.count() for name, rows in _personal(event, user).items()}
    plan["private_artifacts"] = _artifact_plan(_private_artifacts(event, user))
    return plan


def _purge_artifacts(artifacts):
    """Must run inside the caller's transaction, which also records the audit."""
    held = set(_held(artifacts).values_list("pk", flat=True))
    candidates = [pk for pk in artifacts.values_list("pk", flat=True) if pk not in held]
    locked = list(
        Artifact.objects.select_for_update().filter(pk__in=candidates).values_list("pk", flat=True)
    )
    Artifact.objects.filter(pk__in=locked).update(status=ArtifactStatus.PURGED)
    return locked


def complete_purges(event, *, storage=None):
    """Delete objects for every purged artifact still holding a key; a failure
    leaves the key so the next run retries instead of orphaning private data.
    """
    storage = storage or S3Storage()
    pending = Artifact.objects.filter(project__event=event, status=ArtifactStatus.PURGED).exclude(
        object_key=""
    )
    completed = 0
    for artifact in pending.order_by("pk"):
        try:
            storage.delete(artifact.object_key)
        except Exception:  # noqa: BLE001 - any storage failure must leave the key for retry
            continue
        with transaction.atomic():
            artifact.upload_intents.all().delete()
            Artifact.objects.filter(pk=artifact.pk, status=ArtifactStatus.PURGED).update(
                object_key=""
            )
        completed += 1
    return completed


def _apply(event, user, actor, action):
    with transaction.atomic():
        plan = _plan(event, user)
        for rows in _personal(event, user).values():
            rows.delete()
        purged = _purge_artifacts(_private_artifacts(event, user))
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action=action,
            target=user,
            metadata={"event_id": str(event.public_id), "plan": plan},
        )
    plan["private_artifacts"]["purge"] = len(purged)
    return plan


def erase_subject(event, user, *, actor, apply=False, storage=None):
    retained = {name: rows.count() for name, rows in _retained(event, user).items()}
    if not apply:
        plan = _plan(event, user)
    else:
        plan = _apply(event, user, actor, "privacy.subject_erased")
        complete_purges(event, storage=storage)
    return {
        "applied": apply,
        "erased": plan,
        "retained": retained,
        "retained_reason": RETAINED_REASON,
    }


def retention_due(event, now):
    policy = EventRetentionPolicy.objects.filter(event=event).first()
    if policy is None or event.ends_at is None:
        return {"participant_data": False, "private_artifacts": False}

    def due(days):
        return days is not None and now >= event.ends_at + timedelta(days=days)

    return {
        "participant_data": due(policy.participant_data_days),
        "private_artifacts": due(policy.private_artifact_days),
    }


def enforce_retention(event, now, *, actor=None, apply=False, storage=None):
    due = retention_due(event, now)
    plan = {name: 0 for name in _personal(event)}
    plan["private_artifacts"] = {"purge": 0, "held_for_pending_appeals": 0}
    if due["participant_data"]:
        plan.update({name: rows.count() for name, rows in _personal(event).items()})
    if due["private_artifacts"]:
        plan["private_artifacts"] = _artifact_plan(_private_artifacts(event))
    if apply:
        with transaction.atomic():
            if due["participant_data"]:
                for rows in _personal(event).values():
                    rows.delete()
            purged = _purge_artifacts(_private_artifacts(event)) if due["private_artifacts"] else []
            plan["private_artifacts"]["purge"] = len(purged)
            if any(v for k, v in plan.items() if k != "private_artifacts") or purged:
                record_mutation(
                    actor=actor,
                    workspace=event.workspace,
                    action="privacy.retention_enforced",
                    target=event,
                    metadata={"event_id": str(event.public_id), "due": due, "plan": plan},
                )
        complete_purges(event, storage=storage)
    return {"applied": apply, "due": due, "erased": plan}
