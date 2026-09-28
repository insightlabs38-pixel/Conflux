import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from extensions.sdk import (
    AdvancementStrategy,
    Candidate,
    build_archive,
    clean_config,
    import_archive,
    inspect_artifact,
    normalize_config,
    preview_archive_import,
)
from presentation.block_types import BLOCK_TYPES
from stages.advancement import REGISTRY
from test_public_site import make_public_event_with_finalized_project


def test_contributor_strategy_uses_canonical_subject_identity(monkeypatch):
    monkeypatch.setattr("stages.advancement.REGISTRY", REGISTRY.copy())

    class QualifiedOnly(AdvancementStrategy):
        slug = "sdk-test-qualified"

        def select(self, candidates, **params):
            return {
                (c.subject_type, c.subject_id)
                for c in candidates
                if c.score is not None and c.score >= params["minimum"]
            }

    candidates = [
        Candidate("team", "same-id", 7),
        Candidate("user", "same-id", 2),
        Candidate("team", "missing", None),
    ]
    assert QualifiedOnly().select(candidates, minimum=5) == {("team", "same-id")}
    assert QualifiedOnly().select(candidates, minimum=10) == set()


def test_contributor_block_schema_does_not_bypass_content_sanitization(monkeypatch):
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "count": {"type": "integer", "minimum": 1, "maximum": 3, "default": 2},
        },
    }
    monkeypatch.setitem(BLOCK_TYPES, "sdk-example", {"title": "Example", "schema": schema})
    assert clean_config("sdk-example", {}) == {"count": 2}
    with pytest.raises(ValidationError):
        normalize_config(schema, {"count": True})
    assert clean_config("rich_text", {"html": "<p>Safe<script>bad()</script></p>"}) == {
        "html": "<p>Safe</p>"
    }


def test_sdk_artifact_inspection_retains_upload_and_content_guards():
    from types import SimpleNamespace

    from artifacts.models import Artifact

    pending = Artifact(kind="file", status="pending")
    assert inspect_artifact(pending).outcome == "retry"
    unknown = Artifact(kind="unsupported", status="ready")
    assert inspect_artifact(unknown).outcome == "blocked"
    artifact = Artifact(
        kind="file", status="uploaded", object_key="test", byte_size=1, content_type="text/html"
    )
    storage = SimpleNamespace(
        head=lambda key: {
            "ContentLength": 1,
            "ContentType": "text/html",
            "Metadata": {"artifact-id": str(artifact.public_id)},
        }
    )
    assert inspect_artifact(artifact, storage=storage).outcome == "blocked"


@pytest.mark.django_db
def test_sdk_archive_boundary_preserves_private_import_and_atomic_rollback():
    event, _, _ = make_public_event_with_finalized_project()
    event.refresh_from_db()
    archive = build_archive(event)
    preview_archive_import(
        workspace=event.workspace, archive=archive, name="Preview", slug="preview"
    )
    assert not event.workspace.events.filter(slug="preview").exists()
    with transaction.atomic():
        imported = import_archive(
            workspace=event.workspace, archive=archive, name="Imported", slug="imported"
        )
    assert imported.status == "draft" and not imported.is_public
    imported_stages = build_archive(imported)["stages"]
    assert [
        {key: value for key, value in stage.items() if key != "ref"} for stage in imported_stages
    ] == [
        {key: value for key, value in stage.items() if key != "ref"} for stage in archive["stages"]
    ]
    assert {stage["ref"] for stage in imported_stages}.isdisjoint(
        stage["ref"] for stage in archive["stages"]
    )
    invalid = {
        **archive,
        "stages": [
            *archive["stages"],
            {"ref": "invalid", "name": "", "participation_mode": "team_formation"},
        ],
    }
    with pytest.raises(ValidationError), transaction.atomic():
        import_archive(workspace=event.workspace, archive=invalid, name="Rejected", slug="rejected")
    assert not event.workspace.events.filter(slug="rejected").exists()
