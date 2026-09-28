from datetime import datetime
from unittest.mock import patch

import pytest
from accounts.models import Session
from audit.models import AuditEvent, DomainEvent
from django.test import Client
from evaluations.models import EvaluationPlan, RubricVersion
from events.models import BasePrize, Event, EventStatus, Track
from forms.models import FormVersion
from forms.services import create_form, publish_form, save_draft
from policies.models import Policy, TemporalGate
from stages.models import Stage

from tests.integration.test_config_history_api import (
    CRITERIA,
    cookie_client,
    event_url,
    history_url,
    make_fixture,
    stages_url,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def context():
    workspace, event, organizer, participant = make_fixture()
    return workspace, event, organizer, participant, cookie_client(Session.issue(organizer).token)


def restore_url(workspace, event, row):
    return history_url(workspace, event) + f"{row.public_id}/restore/"


def recorded(event, target, changes, action="stage.updated"):
    return AuditEvent.objects.create(
        workspace=event.workspace,
        target_type=type(target).__name__,
        target_id=str(target.public_id),
        action=action,
        metadata={"event_id": str(event.public_id), "changes": changes},
    )


def test_stage_restore_preserves_history_and_is_itself_reversible(context):
    workspace, event, _, _, client = context
    stage = Stage.objects.create(event=event, name="Original")
    assert (
        client.patch(
            stages_url(workspace, event, f"{stage.public_id}/"),
            {"name": "Changed"},
            content_type="application/json",
        ).status_code
        == 200
    )
    row = AuditEvent.objects.get(action="stage.updated")
    original_metadata = row.metadata.copy()
    response = client.post(restore_url(workspace, event, row))
    assert response.status_code == 200
    stage.refresh_from_db()
    assert stage.name == "Original"
    row.refresh_from_db()
    assert row.metadata == original_metadata
    restored = AuditEvent.objects.get(action="stage.restored")
    assert restored.metadata["restored_from"] == str(row.public_id)
    assert restored.metadata["changes"]["name"] == {"before": "Changed", "after": "Original"}
    assert DomainEvent.objects.filter(event_type="stage.restored").count() == 1
    assert client.post(restore_url(workspace, event, restored)).status_code == 200
    stage.refresh_from_db()
    assert stage.name == "Changed"


def test_temporal_restore_parses_datetime_and_rejects_now_invalid_window(context):
    workspace, event, _, _, client = context
    gate = TemporalGate.objects.create(
        event=event,
        name="Deadline",
        opens_at=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        closes_at=datetime.fromisoformat("2026-01-10T00:00:00+00:00"),
    )
    row = recorded(
        event,
        gate,
        {"closes_at": {"before": "2026-01-05T00:00:00Z", "after": "2026-01-10T00:00:00Z"}},
        "temporal_gate.updated",
    )
    assert client.post(restore_url(workspace, event, row)).status_code == 200
    gate.refresh_from_db()
    assert gate.closes_at.day == 5
    gate.opens_at = datetime.fromisoformat("2026-01-06T00:00:00+00:00")
    gate.closes_at = datetime.fromisoformat("2026-01-10T00:00:00+00:00")
    gate.save()
    before = AuditEvent.objects.count()
    assert client.post(restore_url(workspace, event, row)).status_code == 400
    gate.refresh_from_db()
    assert gate.closes_at.day == 10
    assert AuditEvent.objects.count() == before


def test_policy_update_and_restore_use_validated_ast(context):
    workspace, event, _, _, client = context
    url = event_url(workspace, event) + "policies/"
    created = client.post(
        url, {"name": "Access", "preset": "organizers_only"}, content_type="application/json"
    )
    assert created.status_code == 201
    policy = Policy.objects.get(public_id=created.json()["public_id"])
    old_ast = policy.ast
    updated = client.patch(
        url + f"{policy.public_id}/", {"name": "Updated"}, content_type="application/json"
    )
    assert updated.status_code == 200
    row = AuditEvent.objects.get(action="policy.updated")
    assert client.post(restore_url(workspace, event, row)).status_code == 200
    policy.refresh_from_db()
    assert policy.name == "Access" and policy.ast == old_ast
    invalid = recorded(
        event,
        policy,
        {"ast": {"before": {"op": "execute_code"}, "after": old_ast}},
        "policy.updated",
    )
    assert client.post(restore_url(workspace, event, invalid)).status_code == 400
    policy.refresh_from_db()
    assert policy.ast == old_ast


@pytest.mark.parametrize(
    "changes,action",
    [
        ({"event": {"before": 1, "after": 2}}, "stage.updated"),
        ({"public_id": {"before": "bad", "after": "bad"}}, "stage.updated"),
        ({"name": {"after": "Current"}}, "stage.updated"),
        ({"name": {"before": "Old", "after": "Current"}}, "stage.deleted"),
        ({}, "stage.updated"),
    ],
)
def test_unsupported_or_malformed_entries_fail_without_mutation(context, changes, action):
    workspace, event, _, _, client = context
    stage = Stage.objects.create(event=event, name="Current")
    row = recorded(event, stage, changes, action)
    assert client.post(restore_url(workspace, event, row)).status_code == 400
    stage.refresh_from_db()
    assert stage.name == "Current"
    assert AuditEvent.objects.count() == 1


def test_target_scope_and_permissions_are_enforced_independently_of_audit_metadata(context):
    workspace, event, _, participant, client = context
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    foreign = Stage.objects.create(event=other, name="Foreign")
    row = recorded(event, foreign, {"name": {"before": "Stolen", "after": "Foreign"}})
    assert client.post(restore_url(workspace, event, row)).status_code == 404
    assert client.post(restore_url(workspace, other, row)).status_code == 404
    url = restore_url(workspace, event, row)
    assert Client().post(url).status_code in (401, 403)
    assert cookie_client(Session.issue(participant).token).post(url).status_code in (401, 403)
    foreign.refresh_from_db()
    assert foreign.name == "Foreign"


def test_conflicting_stage_name_and_archived_event_fail_closed(context):
    workspace, event, _, _, client = context
    stage = Stage.objects.create(event=event, name="Current")
    Stage.objects.create(event=event, name="Taken")
    row = recorded(event, stage, {"name": {"before": "Taken", "after": "Current"}})
    assert client.post(restore_url(workspace, event, row)).status_code == 400
    event.status = EventStatus.ARCHIVED
    event.save()
    assert client.post(restore_url(workspace, event, row)).status_code == 400
    assert AuditEvent.objects.count() == 1


def test_event_restore_runs_serializer_validation(context):
    workspace, event, _, _, client = context
    row = recorded(
        event, event, {"timezone": {"before": "Invalid/Zone", "after": "UTC"}}, "event.updated"
    )
    assert client.post(restore_url(workspace, event, row)).status_code == 400
    event.refresh_from_db()
    assert event.timezone == "UTC"


def test_restore_rolls_back_when_audit_write_fails(context):
    workspace, event, _, _, client = context
    stage = Stage.objects.create(event=event, name="Current")
    row = recorded(event, stage, {"name": {"before": "Old", "after": "Current"}})
    with patch("audit.views.record_mutation", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError, match="audit unavailable"):
            client.post(restore_url(workspace, event, row))
    stage.refresh_from_db()
    assert stage.name == "Current"
    assert AuditEvent.objects.count() == 1


@pytest.mark.parametrize("kind", ["form", "rubric"])
def test_version_restore_changes_only_draft_and_republish_creates_new_version(context, kind):
    workspace, event, _, participant, client = context
    if kind == "form":
        definition = create_form(event, "Application")
        original = {"fields": [{"id": "pitch", "label": "Pitch", "type": "text"}]}
        save_draft(definition, original)
        version = publish_form(definition)
        save_draft(definition, {"fields": []})
        base = event_url(workspace, event) + f"forms/{definition.public_id}/"
        url = base + f"versions/{version.public_id}/restore/"
        model, attr, payload, publish_path = FormVersion, "draft_schema", "schema", "publish/"
    else:
        stage = Stage.objects.create(event=event, name="Finals")
        definition = EvaluationPlan.objects.create(
            stage=stage, name="Plan", draft_criteria=CRITERIA
        )
        original = CRITERIA
        version = RubricVersion.objects.create(plan=definition, number=1, criteria=original)
        original = version.criteria
        definition.draft_criteria = [{**CRITERIA[0], "weight": 4}]
        definition.save()
        base = stages_url(
            workspace, event, f"{stage.public_id}/evaluation-plans/{definition.public_id}/"
        )
        url = base + f"rubric-versions/{version.public_id}/restore/"
        model, attr, payload, publish_path = (
            RubricVersion,
            "draft_criteria",
            "criteria",
            "publish-rubric/",
        )
    assert cookie_client(Session.issue(participant).token).post(url).status_code in (401, 403)
    assert client.post(url).status_code == 200
    definition.refresh_from_db()
    version.refresh_from_db()
    assert getattr(definition, attr) == original
    assert getattr(version, payload) == original
    assert model.objects.count() == 1
    published = client.post(base + publish_path)
    assert published.status_code == 201
    assert published.json()["number"] == 2
    assert published.json()[payload] == original
    event.status = EventStatus.ARCHIVED
    event.save()
    assert client.post(url).status_code == 400


def test_deleted_target_cannot_be_resurrected(context):
    workspace, event, _, _, client = context
    track = Track.objects.create(event=event, name="Gone")
    row = recorded(event, track, {"name": {"before": "Old", "after": "Gone"}}, "track.updated")
    track.delete()
    assert client.post(restore_url(workspace, event, row)).status_code == 404
    assert not Track.objects.exists()


def test_prize_restore_resolves_internal_track_snapshot_within_event(context):
    workspace, event, _, _, client = context
    track = Track.objects.create(event=event, name="Original")
    prize = BasePrize.objects.create(event=event, name="Prize", kind=BasePrize.Kind.OTHER)
    row = recorded(event, prize, {"track": {"before": track.pk, "after": None}}, "prize.updated")
    assert client.post(restore_url(workspace, event, row)).status_code == 200
    prize.refresh_from_db()
    assert prize.track_id == track.pk
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    foreign = Track.objects.create(event=other, name="Foreign")
    bad = recorded(
        event, prize, {"track": {"before": foreign.pk, "after": track.pk}}, "prize.updated"
    )
    assert client.post(restore_url(workspace, event, bad)).status_code == 404
    prize.refresh_from_db()
    assert prize.track_id == track.pk


@pytest.mark.parametrize("kind", ["form", "rubric"])
def test_version_from_another_definition_is_rejected_and_audit_failure_is_atomic(context, kind):
    workspace, event, _, _, client = context
    if kind == "form":
        definition = create_form(event, "Application")
        foreign = create_form(event, "Other")
        version = publish_form(definition)
        foreign_version = publish_form(foreign)
        original = {"fields": [{"id": "pitch", "type": "text", "label": "Pitch"}]}
        save_draft(definition, original)
        url = event_url(workspace, event) + f"forms/{definition.public_id}/versions/"
        attr, module = "draft_schema", "forms.views.record_mutation"
    else:
        stage = Stage.objects.create(event=event, name="Finals")
        definition = EvaluationPlan.objects.create(
            stage=stage, name="Plan", draft_criteria=CRITERIA
        )
        foreign = EvaluationPlan.objects.create(stage=stage, name="Other", draft_criteria=CRITERIA)
        version = RubricVersion.objects.create(plan=definition, number=1, criteria=CRITERIA)
        foreign_version = RubricVersion.objects.create(plan=foreign, number=1, criteria=CRITERIA)
        definition.draft_criteria = [{**CRITERIA[0], "weight": 4}]
        definition.save()
        original = definition.draft_criteria
        url = stages_url(
            workspace,
            event,
            f"{stage.public_id}/evaluation-plans/{definition.public_id}/rubric-versions/",
        )
        attr, module = "draft_criteria", "evaluations.views.record_mutation"
    assert client.post(url + f"{foreign_version.public_id}/restore/").status_code == 404
    with patch(module, side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError, match="audit unavailable"):
            client.post(url + f"{version.public_id}/restore/")
    definition.refresh_from_db()
    assert getattr(definition, attr) == original
    assert not AuditEvent.objects.filter(action__endswith="draft_restored").exists()
