"""External qualifier result import (EXTQ-001/002): lets an API credential
or organizer report the outcome of a qualifying round run outside this
platform -- a partner site, a manual review, an earlier season -- as a
direct entry into one of this event's stages, without ever inventing a new
participant identity. See `ExternalQualifierBinding` for the identity-
continuity mechanism this relies on.
"""

from audit.services import record_mutation
from django.core.exceptions import ValidationError
from django.db import transaction
from projects.models import Project
from stages.models import StageEntry

from .models import ExternalQualifierBinding, ExternalQualifierImport


def _resolve_project(event, binding, entry):
    external_ref = entry.get("external_ref")
    if not isinstance(external_ref, str) or not external_ref.strip():
        raise ValidationError({"entries": "Each entry needs a non-empty 'external_ref'."})
    external_ref = external_ref.strip()
    existing = binding.get(external_ref)
    project_ref = entry.get("project")
    if existing is None:
        if not project_ref:
            raise ValidationError(
                {
                    "entries": (
                        f"external_ref {external_ref!r} is not yet bound to a project; "
                        "supply 'project' to bind it."
                    )
                }
            )
        project = Project.objects.filter(event=event, public_id=project_ref).first()
        if project is None:
            raise ValidationError({"entries": f"No project {project_ref!r} exists in this event."})
        return external_ref, project, True
    if project_ref and str(existing.project.public_id) != str(project_ref):
        raise ValidationError(
            {"entries": (f"external_ref {external_ref!r} is already bound to a different project.")}
        )
    return external_ref, existing.project, False


def import_external_qualifiers(*, event, stage, entries, actor):
    """Enter every resolved project's team directly into `stage`
    (idempotent -- a project whose team already holds an active entry
    there is left alone) and record one receipt for the whole call.
    """
    if stage.event_id != event.id:
        raise ValidationError({"stage": "Stage must belong to this event."})
    if stage.expected_subject_type() != "team":
        raise ValidationError(
            {"stage": "External qualifier import only supports team-based stages."}
        )
    if not isinstance(entries, list) or not entries:
        raise ValidationError({"entries": "At least one entry is required."})

    with transaction.atomic():
        existing_bindings = {
            binding.external_ref: binding
            for binding in ExternalQualifierBinding.objects.filter(event=event).select_related(
                "project"
            )
        }
        receipt_entries = []
        advanced_count = 0
        for entry in entries:
            external_ref, project, needs_binding = _resolve_project(event, existing_bindings, entry)
            if project.team_id is None:
                raise ValidationError(
                    {"entries": f"Project {project.name!r} has no team to advance."}
                )
            if needs_binding:
                binding = ExternalQualifierBinding.objects.create(
                    event=event, external_ref=external_ref, project=project
                )
                existing_bindings[external_ref] = binding
            team_subject_id = str(project.team.public_id)
            already_active = StageEntry.objects.filter(
                stage=stage,
                subject_type="team",
                subject_id=team_subject_id,
                exited_at__isnull=True,
            ).exists()
            advanced = not already_active
            if advanced:
                StageEntry.objects.enter(stage, "team", team_subject_id)
                advanced_count += 1
            receipt_entries.append(
                {
                    "external_ref": external_ref,
                    "project": str(project.public_id),
                    "advanced": advanced,
                }
            )

        receipt = ExternalQualifierImport.objects.create(
            event=event,
            stage=stage,
            imported_by=actor,
            entries=receipt_entries,
            advanced_count=advanced_count,
        )
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="external_qualifiers.imported",
            target=receipt,
            metadata={
                "stage": str(stage.public_id),
                "entry_count": len(receipt_entries),
                "advanced_count": advanced_count,
            },
            event_type="external_qualifiers.imported",
            payload={"event": str(event.public_id), "stage": str(stage.public_id)},
        )
        return receipt
