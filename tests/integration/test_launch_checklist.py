from datetime import timedelta

import pytest
from accounts.models import Session, User
from django.test import Client
from django.utils import timezone
from evaluations.models import EvaluationPlan, EvaluationPoolStrategy
from events.models import Event
from forms.models import FormDefinition, FormVersion
from policies.models import TemporalGate
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="checklist-organizer", password="unused")
    workspace = Workspace.objects.create(name="Checklist", slug="checklist")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    return workspace, event, client


def url(workspace, event):
    return (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/operations/checklist/"
    )


def item(body, item_id):
    return next(entry for entry in body["items"] if entry["id"] == item_id)


def test_missing_dates_blocks_launch():
    workspace, event, client = fixture()
    response = client.get(url(workspace, event))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert item(body, "event_dates")["passed"] is False


def test_fully_configured_event_is_ready():
    workspace, event, client = fixture()
    now = timezone.now()
    event.starts_at = now - timedelta(days=1)
    event.ends_at = now + timedelta(days=1)
    event.save(update_fields=["starts_at", "ends_at"])

    stage = Stage.objects.create(event=event, name="Finals")
    form = FormDefinition.objects.create(event=event, name="Submission")
    FormVersion.objects.create(definition=form, number=1, schema={"fields": []})

    gate = TemporalGate.objects.create(
        event=event,
        name="submissions",
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=1),
    )
    assert gate.is_open(now)

    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    plan.rubric_versions.create(
        number=1,
        criteria=[{"id": "c1", "name": "C1", "weight": 1, "min_score": 0, "max_score": 10}],
    )

    response = client.get(url(workspace, event))
    body = response.json()
    assert item(body, "event_dates")["passed"] is True
    assert item(body, "forms_published")["passed"] is True
    assert item(body, "gate_windows")["passed"] is True
    assert item(body, "judging_rubrics")["passed"] is True
    # No pool configured for the plan yet, but ALL_JUDGES with zero judges is a warning.
    assert plan.pool_strategy == EvaluationPoolStrategy.ALL_JUDGES
    assert item(body, "judging_pools")["passed"] is False
    assert body["status"] == "warning"


def test_unpublished_form_and_contradictory_gate_are_flagged():
    workspace, event, client = fixture()
    now = timezone.now()
    event.starts_at = now - timedelta(days=1)
    event.ends_at = now + timedelta(days=1)
    event.save(update_fields=["starts_at", "ends_at"])
    FormDefinition.objects.create(event=event, name="Unpublished draft")
    TemporalGate.objects.create(
        event=event,
        name="way-past",
        opens_at=now - timedelta(days=10),
        closes_at=now - timedelta(days=9),
    )

    response = client.get(url(workspace, event))
    body = response.json()
    assert item(body, "forms_published")["passed"] is False
    assert item(body, "gate_windows")["passed"] is False
    assert body["status"] == "blocked"
