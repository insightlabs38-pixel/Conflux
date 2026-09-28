import hashlib
import json
from uuid import UUID

from artifacts.models import Artifact, ArtifactStatus, ArtifactVisibility
from artifacts.preflight import run_preflight
from artifacts.services import inspection_data
from artifacts.storage import S3Storage
from audit.services import record_mutation
from core.authz import has_any_role
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from forms.models import FormDefinition, FormResponse
from policies.models import Action
from policies.services import base_facts, explain_action
from workspaces.models import Role

from .models import Project, Submission, SubmissionStatus, SubmissionVersion


def _require_window(project, at):
    event = project.event
    if event.status != "open" or (event.starts_at and at < event.starts_at):
        raise ValidationError("The event is not open for submissions.")
    if event.ends_at and at >= event.ends_at:
        raise ValidationError("The event submission deadline has passed.")
    decision = explain_action(
        event,
        Action.SUBMIT,
        base_facts(event, at=at),
        subject_type="project",
        subject_id=str(project.public_id),
    )
    if not decision.allowed:
        raise ValidationError(decision.explain())


def _validate_payload(payload):
    if not isinstance(payload, dict) or set(payload) - {"notes", "artifact_ids"}:
        raise ValidationError("Draft accepts notes and artifact_ids only.")
    notes = payload.get("notes", "")
    identifiers = payload.get("artifact_ids", [])
    if not isinstance(notes, str) or len(notes) > 10000:
        raise ValidationError("Notes must be text of at most 10000 characters.")
    if (
        not isinstance(identifiers, list)
        or len(identifiers) > 100
        or len(set(map(str, identifiers))) != len(identifiers)
    ):
        raise ValidationError("Artifact IDs must be a unique list of at most 100 items.")
    try:
        identifiers = [str(UUID(value)) for value in identifiers]
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValidationError("Artifact IDs must be UUIDs.") from exc
    return {"notes": notes, "artifact_ids": identifiers}


def _locked_submission(project, stage, actor):
    project = (
        Project.objects.select_for_update(of=("self",)).select_related("event").get(pk=project.pk)
    )
    if not project.memberships.filter(user=actor).exists():
        raise ValidationError("Only project members can submit.")
    if stage.event_id != project.event_id:
        raise ValidationError("Stage must belong to the project's event.")
    submission, _ = Submission.objects.get_or_create(
        project=project, stage=stage, defaults={"updated_by": actor}
    )
    return project, Submission.objects.select_for_update().get(pk=submission.pk)


@transaction.atomic
def save_draft(project, stage, actor, *, payload, revision):
    project, submission = _locked_submission(project, stage, actor)
    _require_window(project, timezone.now())
    if submission.status == SubmissionStatus.FINALIZED:
        raise ValidationError("This submission is finalized.")
    if (
        not isinstance(revision, int)
        or isinstance(revision, bool)
        or revision != submission.draft_revision
    ):
        raise ValidationError("Draft revision is stale; reload before saving.")
    submission.draft_payload = _validate_payload(payload)
    submission.draft_revision += 1
    submission.updated_by = actor
    submission.save(update_fields=["draft_payload", "draft_revision", "updated_by", "updated_at"])
    return submission


def _snapshot(project, stage, payload, preflight):
    forms = FormDefinition.objects.filter(event=project.event).filter(
        Q(stage__isnull=True) | Q(stage=stage)
    )
    form_evidence = []
    for form in forms.order_by("id"):
        version = form.versions.order_by("-number").first()
        response = FormResponse.objects.get(project=project, version=version)
        form_evidence.append(
            {
                "form": str(form.public_id),
                "version": str(version.public_id),
                "answers": {answer.field_id: answer.value for answer in response.answers.all()},
            }
        )
    artifacts = Artifact.objects.filter(project=project, public_id__in=payload["artifact_ids"])
    artifact_evidence = [
        {
            "id": str(item.public_id),
            "kind": item.kind,
            "visibility": item.visibility,
            "title": item.title,
            "url": item.external_url,
            "object_key": item.object_key,
            "sha256": item.sha256,
            "byte_size": item.byte_size,
        }
        for item in artifacts.order_by("public_id")
    ]
    return {
        "project": str(project.public_id),
        "project_name": project.name,
        "stage": str(stage.public_id),
        "draft": payload,
        "forms": form_evidence,
        "artifacts": artifact_evidence,
        "preflight": preflight.as_dict(),
    }


@transaction.atomic
def finalize_submission(project, stage, actor, *, revision):
    project, submission = _locked_submission(project, stage, actor)
    if submission.status == SubmissionStatus.FINALIZED:
        return submission, submission.current_version, False
    at = timezone.now()
    _require_window(project, at)
    if (
        not isinstance(revision, int)
        or isinstance(revision, bool)
        or revision != submission.draft_revision
    ):
        raise ValidationError("Draft revision is stale; reload before finalizing.")
    payload = _validate_payload(submission.draft_payload)
    list(FormDefinition.objects.select_for_update().filter(event=project.event).order_by("pk"))
    list(Artifact.objects.select_for_update().filter(project=project).order_by("pk"))
    preflight = run_preflight(project, stage=stage, artifact_ids=payload["artifact_ids"], at=at)
    if preflight.status == "BLOCKED":
        raise ValidationError(
            [check.detail for check in preflight.checks if check.severity == "blocked"]
        )
    snapshot = _snapshot(project, stage, payload, preflight)
    digest = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    next_number = (
        submission.versions.order_by("-number").values_list("number", flat=True).first() or 0
    ) + 1
    version = SubmissionVersion.objects.create(
        submission=submission,
        number=next_number,
        snapshot=snapshot,
        digest=digest,
        finalized_by=actor,
    )
    submission.status = SubmissionStatus.FINALIZED
    submission.current_version = version
    submission.updated_by = actor
    submission.save(update_fields=["status", "current_version", "updated_by", "updated_at"])
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="submission.finalized",
        target=version,
        metadata={"submission": str(submission.public_id), "digest": digest},
        event_type="submission.finalized",
        payload={
            "event": str(project.event.public_id),
            "submission": str(submission.public_id),
            "version": str(version.public_id),
        },
    )
    from governance.services import issue_receipt

    issue_receipt(version)
    return submission, version, True


@transaction.atomic
def reopen_submission(project, stage, actor, *, reason=""):
    """Allow an organizer to request a correction while preserving the prior version."""
    project = (
        Project.objects.select_for_update(of=("self",)).select_related("event").get(pk=project.pk)
    )
    if not has_any_role(actor, project.event.workspace, Role.ORGANIZER, Role.ADMIN):
        raise ValidationError("Only organizers can reopen a submission.")
    _require_window(project, timezone.now())
    if stage.event_id != project.event_id:
        raise ValidationError("Stage must belong to the project's event.")
    try:
        submission = Submission.objects.select_for_update().get(project=project, stage=stage)
    except Submission.DoesNotExist as exc:
        raise ValidationError("This project has no submission for this stage.") from exc
    if submission.status != SubmissionStatus.FINALIZED:
        raise ValidationError("Only a finalized submission can be reopened.")
    reopened_version = submission.current_version
    submission.status = SubmissionStatus.DRAFT
    submission.updated_by = actor
    submission.save(update_fields=["status", "updated_by", "updated_at"])
    record_mutation(
        actor=actor,
        workspace=project.event.workspace,
        action="submission.reopened",
        target=submission,
        metadata={
            "reason": reason,
            "reopened_version": reopened_version.number if reopened_version else None,
        },
    )
    return submission


JUDGE_VISIBLE = {ArtifactVisibility.PUBLIC, ArtifactVisibility.JUDGE}


def preview_frozen_submission(project, stage):
    """The judge-visible artifacts of this submission's latest finalized
    version, exactly as they were frozen at finalize time.

    Each artifact is checked against its live row: if the row was deleted or
    its content/visibility/kind has since changed, the snapshot is untrusted
    for that artifact (drift) and no download is offered for it, so a
    preview can never show something other than what was actually frozen.
    Returns None when this submission has never been finalized.
    """
    submission = Submission.objects.filter(project=project, stage=stage).first()
    version = submission.current_version if submission else None
    if version is None:
        return None
    frozen = [
        item
        for item in version.snapshot.get("artifacts", [])
        if item["visibility"] in JUDGE_VISIBLE
    ]
    live = {
        str(a.public_id): a
        for a in Artifact.objects.filter(public_id__in=[i["id"] for i in frozen])
    }
    storage = S3Storage()
    rows = []
    verified = True
    for snap in frozen:
        artifact = live.get(snap["id"])
        if artifact is None:
            drift = "removed"
        elif (
            artifact.kind != snap["kind"]
            or artifact.visibility != snap["visibility"]
            or artifact.object_key != snap["object_key"]
            or artifact.sha256 != snap["sha256"]
        ):
            drift = "content_changed"
        else:
            drift = None
        if drift:
            verified = False
        latest = artifact.inspections.first() if artifact else None
        download = None
        if (
            drift is None
            and artifact.object_key
            and artifact.status == ArtifactStatus.READY
            and (latest is None or latest.verdict != "blocked")
        ):
            download = storage.presign_get(artifact.object_key, download_filename=artifact.title)
        rows.append(
            {
                "id": snap["id"],
                "title": snap["title"],
                "kind": snap["kind"],
                "drift": drift,
                "inspection": inspection_data(latest) if latest else None,
                "download_url": download,
            }
        )
    return {"version": version.number, "verified": verified, "artifacts": rows}
