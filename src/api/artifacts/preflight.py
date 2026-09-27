from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.utils import timezone
from forms.models import FormDefinition, FormResponse
from forms.validation import field_scopes, validate_response_answers
from policies.models import Action
from policies.services import base_facts, explain_action

from .models import Artifact, ArtifactStatus, ArtifactVisibility


@dataclass(frozen=True)
class Check:
    code: str
    severity: str
    detail: str


@dataclass(frozen=True)
class Preflight:
    status: str
    checks: tuple[Check, ...]

    def as_dict(self):
        return {"status": self.status, "checks": [check.__dict__ for check in self.checks]}


def run_preflight(project, *, stage=None, artifact_ids=None, at=None):
    event = project.event
    now = at or timezone.now()
    checks = []
    if stage is not None and stage.event_id != event.id:
        raise ValidationError("Stage must belong to the project's event.")
    if event.status != "open":
        checks.append(Check("event_not_open", "blocked", "Event is not open for submissions."))
    if event.starts_at and now < event.starts_at:
        checks.append(Check("event_not_started", "blocked", "Event has not started."))
    if event.ends_at and now >= event.ends_at:
        checks.append(Check("event_deadline", "blocked", "Event submission deadline has passed."))
    decision = explain_action(
        event,
        Action.SUBMIT,
        base_facts(event, at=now),
        subject_type="project",
        subject_id=str(project.public_id),
    )
    if not decision.allowed:
        checks.append(Check("submit_policy", "blocked", decision.explain()))

    forms = FormDefinition.objects.filter(event=event, stage__isnull=True)
    if stage is not None:
        forms = FormDefinition.objects.filter(
            event=event, stage__isnull=True
        ) | FormDefinition.objects.filter(event=event, stage=stage)
    for form in forms.distinct():
        version = form.versions.order_by("-number").first()
        if version is None:
            checks.append(
                Check("form_unpublished", "blocked", f"Form {form.name} has no published version.")
            )
            continue
        response = FormResponse.objects.filter(project=project, version=version).first()
        if response is None:
            checks.append(
                Check(
                    "form_missing",
                    "blocked",
                    f"Form {form.name} version {version.number} has no response.",
                )
            )
            continue
        values = {answer.field_id: answer.value for answer in response.answers.all()}
        participant_ids = {
            field["id"]
            for field in version.schema["fields"]
            if "participant" in field_scopes(field) or "public" in field_scopes(field)
        }
        participant = {key: value for key, value in values.items() if key in participant_ids}
        try:
            validate_response_answers(version.schema, participant, "participant")
        except ValidationError as exc:
            checks.append(
                Check("form_invalid", "blocked", f"Form {form.name}: {' '.join(exc.messages)}")
            )
        for field in version.schema["fields"]:
            if field["type"] != "artifact" or not participant.get(field["id"]):
                continue
            artifact = Artifact.objects.filter(
                project=project, public_id=participant[field["id"]]
            ).first()
            if (
                artifact is None
                or artifact.status != ArtifactStatus.READY
                or artifact.visibility
                not in {ArtifactVisibility.PUBLIC, ArtifactVisibility.PARTICIPANT}
            ):
                checks.append(
                    Check(
                        "artifact_reference",
                        "blocked",
                        f"Form {form.name} field {field['label']} needs a ready artifact.",
                    )
                )

    artifacts = Artifact.objects.filter(project=project)
    if artifact_ids is not None:
        artifacts = artifacts.filter(public_id__in=artifact_ids)
        if artifacts.count() != len(set(artifact_ids)):
            checks.append(
                Check(
                    "artifact_selection",
                    "blocked",
                    "Selected artifact is missing from this project.",
                )
            )
    for artifact in artifacts:
        if artifact.status != ArtifactStatus.READY:
            checks.append(
                Check(
                    "artifact_not_ready",
                    "blocked",
                    f"Artifact {artifact.title} is {artifact.status}.",
                )
            )
        else:
            latest = artifact.validations.first()
            if latest and latest.outcome == "warning":
                checks.append(
                    Check(
                        "artifact_warning", "warning", f"Artifact {artifact.title}: {latest.detail}"
                    )
                )
    status = (
        "BLOCKED"
        if any(check.severity == "blocked" for check in checks)
        else "WARNING"
        if checks
        else "READY"
    )
    return Preflight(status, tuple(checks))
