from types import SimpleNamespace

import pytest
from artifacts.models import Artifact
from django.core.exceptions import ValidationError
from evaluations.assignment import compute_assignment
from evaluations.models import ConflictOfInterest
from extensions.examples import (
    NOTICE_BLOCK,
    export_configuration,
    import_private_copy,
    inspect_pdf,
    ordered_assignment,
    register_scored_threshold,
)
from extensions.sdk import Candidate, clean_config, preview_archive_import
from presentation.block_types import BLOCK_TYPES
from stages.advancement import REGISTRY
from test_assignment_preview import make_fixture
from test_public_site import make_public_event_with_finalized_project


def test_strategy_registration_is_explicit_and_never_replaces_existing_entry(monkeypatch):
    monkeypatch.setattr("extensions.examples.REGISTRY", REGISTRY.copy())
    from extensions import examples

    monkeypatch.setattr("stages.advancement.REGISTRY", examples.REGISTRY)
    strategy = register_scored_threshold()
    candidates = [
        Candidate("team", "same", 0),
        Candidate("user", "same", -1),
        Candidate("team", "missing"),
        Candidate("team", "nan", float("nan")),
        Candidate("team", "inf", float("inf")),
    ]
    assert strategy().select(candidates, minimum=0) == {("team", "same")}
    assert strategy().select(candidates, minimum=-2) == {("team", "same"), ("user", "same")}
    for minimum in (True, "0", float("inf"), float("nan")):
        with pytest.raises(ValidationError):
            strategy().select(candidates, minimum=minimum)
    with pytest.raises(ValueError, match="already registered"):
        register_scored_threshold()
    assert examples.REGISTRY[strategy.slug] is strategy


def test_pdf_example_retains_pending_metadata_and_active_content_guards():
    artifact = Artifact(kind="file", status="pending", byte_size=1, object_key="pdf")
    assert inspect_pdf(artifact).outcome == "retry"
    artifact.status = "uploaded"
    artifact.content_type = "application/pdf"
    head = {
        "ContentLength": 1,
        "ContentType": artifact.content_type,
        "Metadata": {"artifact-id": str(artifact.public_id)},
    }
    storage = SimpleNamespace(head=lambda key: head)
    assert inspect_pdf(artifact, storage).outcome == "ok"
    head["Metadata"] = {}
    assert inspect_pdf(artifact, storage).outcome == "blocked"
    head["Metadata"] = {"artifact-id": str(artifact.public_id)}
    for content_type, validator in (
        ("text/plain", "example_pdf"),
        ("text/html", "active_content_type"),
    ):
        artifact.content_type = head["ContentType"] = content_type
        result = inspect_pdf(artifact, storage)
        assert result.outcome == "blocked" and result.validator == validator


def test_notice_uses_supported_schema_and_rejects_invalid_configs(monkeypatch):
    monkeypatch.setitem(BLOCK_TYPES, "example_notice", NOTICE_BLOCK)
    assert clean_config("example_notice", {"message": "Welcome"}) == {
        "message": "Welcome",
        "priority": 1,
    }
    for config in (
        {},
        {"message": " "},
        {"message": "x" * 241},
        {"message": "ok", "priority": True},
        {"message": "ok", "priority": 4},
        {"message": "ok", "html": "<script>bad()</script>"},
    ):
        with pytest.raises(ValidationError):
            clean_config("example_notice", config)


@pytest.mark.django_db
def test_assignment_example_is_deterministic_conflict_safe_and_read_only():
    _, event, _, plan, organizer, judges, projects = make_fixture()
    ConflictOfInterest.objects.create(
        event=event,
        judge=judges[0],
        project=projects[0],
        declared_by=organizer,
    )
    pairs = ordered_assignment(plan, coverage=2)
    assert pairs == ordered_assignment(plan, coverage=2)
    assert set(pairs) == set(compute_assignment(plan, coverage=2))
    assert all((p.judge_id, p.project_id) != (judges[0].id, projects[0].id) for p in pairs)
    assert not plan.assignment_versions.exists()
    for coverage in (True, 0, -1, 1.5):
        with pytest.raises(ValidationError):
            ordered_assignment(plan, coverage=coverage)


@pytest.mark.django_db
def test_archive_examples_use_private_remapping_and_atomic_rollback():
    event, _, _ = make_public_event_with_finalized_project()
    event.refresh_from_db()
    archive = export_configuration(event)
    assert archive["mode"] == "config" and "projects" not in archive
    with pytest.raises(ValidationError):
        export_configuration(event, mode="full")
    preview_archive_import(workspace=event.workspace, archive=archive, name="Copy", slug="copy")
    assert not event.workspace.events.filter(slug="copy").exists()
    imported = import_private_copy(
        workspace=event.workspace, archive=archive, name="Copy", slug="copy"
    )
    assert not imported.is_public and imported.status == "draft"
    assert imported.stages.exists()
    assert set(imported.stages.values_list("public_id", flat=True)).isdisjoint(
        event.stages.values_list("public_id", flat=True)
    )
    invalid = {
        **archive,
        "stages": [
            *archive["stages"],
            {"ref": "bad", "name": "", "participation_mode": "team_formation"},
        ],
    }
    with pytest.raises(ValidationError):
        import_private_copy(workspace=event.workspace, archive=invalid, name="Bad", slug="bad")
    assert not event.workspace.events.filter(slug="bad").exists()
