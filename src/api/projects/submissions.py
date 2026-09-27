import hashlib
import json
from uuid import UUID

from artifacts.models import Artifact
from artifacts.preflight import run_preflight
from audit.services import record_mutation
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from forms.models import FormDefinition, FormResponse
from policies.models import Action
from policies.services import base_facts, explain_action

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
    project = Project.objects.select_for_update().select_related("event").get(pk=project.pk)
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
    version = SubmissionVersion.objects.create(
        submission=submission,
        number=1,
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
        payload={"submission": str(submission.public_id), "version": str(version.public_id)},
    )
    return submission, version, True
