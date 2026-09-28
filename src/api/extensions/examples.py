"""Opt-in contributor examples; importing this module changes no registries."""

import math

from django.core.exceptions import ValidationError
from django.db import transaction
from evaluations.assignment import compute_assignment
from stages.advancement import REGISTRY

from extensions.sdk import (
    AdvancementStrategy,
    PageBlockType,
    ValidationResult,
    build_archive,
    import_archive,
    inspect_artifact,
)


def inspect_pdf(artifact, storage=None):
    result = inspect_artifact(artifact, storage=storage)
    if result.outcome != "ok":
        return result
    if artifact.content_type.split(";", 1)[0].strip().lower() != "application/pdf":
        return ValidationResult("example_pdf", "blocked", "PDF evidence is required.")
    return result


def register_scored_threshold():
    slug = "example_scored_threshold"
    if slug in REGISTRY:
        raise ValueError(f"Strategy {slug!r} is already registered.")

    class ScoredThreshold(AdvancementStrategy):
        slug = "example_scored_threshold"

        def select(self, candidates, *, minimum, **params):
            if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
                raise ValidationError("Minimum must be a finite number.")
            if not math.isfinite(minimum):
                raise ValidationError("Minimum must be a finite number.")
            return {
                (candidate.subject_type, candidate.subject_id)
                for candidate in candidates
                if candidate.score is not None
                and math.isfinite(candidate.score)
                and candidate.score >= minimum
            }

    return ScoredThreshold


def ordered_assignment(plan, *, coverage=3):
    if isinstance(coverage, bool) or not isinstance(coverage, int) or coverage < 1:
        raise ValidationError("Coverage must be a positive integer.")
    return sorted(
        compute_assignment(plan, coverage=coverage),
        key=lambda pair: (pair.judge_id, pair.project_id),
    )


NOTICE_BLOCK: PageBlockType = {
    "title": "Plain notice",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "message": {
                "type": "string",
                "maxLength": 240,
                "default": "",
                "x-nonblank": True,
            },
            "priority": {"type": "integer", "minimum": 1, "maximum": 3, "default": 1},
        },
    },
}


def export_configuration(event, mode="config", sections=None):
    if mode != "config":
        raise ValidationError("This example exports configuration only.")
    return build_archive(event, mode=mode, sections=sections)


def import_private_copy(*, workspace, archive, name, slug):
    with transaction.atomic():
        return import_archive(workspace=workspace, archive=archive, name=name, slug=slug)
