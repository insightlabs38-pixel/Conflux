import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from evaluations.models import EvaluationPlan
from events.models import Event, EventStatus
from integrations.models import EventTemplate
from integrations.template_library import LIBRARY
from stages.models import ParticipationMode, Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    owner = User.objects.create_user(username="owner", password="unused")
    judge = User.objects.create_user(username="judge", password="unused")
    workspace = Workspace.objects.create(name="Templates", slug="templates")
    Membership.objects.create(user=owner, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    owner_client = Client()
    owner_client.cookies["session"] = Session.issue(owner).token
    judge_client = Client()
    judge_client.cookies["session"] = Session.issue(judge).token
    base = f"/api/v1/workspaces/{workspace.public_id}/event-templates/library/"
    return workspace, owner_client, judge_client, base


def post_json(client, url, data):
    return client.post(url, data=data, content_type="application/json")


@pytest.mark.parametrize("template_slug", list(LIBRARY))
def test_each_local_template_instantiates_editable_draft_configuration(template_slug):
    workspace, owner, _, base = fixture()
    listed = owner.get(base)
    assert listed.status_code == 200
    assert {entry["slug"] for entry in listed.json()} == set(LIBRARY)
    assert len(listed.json()) == 5

    response = post_json(
        owner,
        base + f"{template_slug}/instantiate/",
        {"name": "Autumn program", "slug": "autumn-program"},
    )
    assert response.status_code == 201, response.content
    event = Event.objects.get(workspace=workspace, slug="autumn-program")
    spec = LIBRARY[template_slug]
    assert event.status == EventStatus.DRAFT
    assert event.is_public is False
    assert event.description == spec["description"]
    assert list(event.tracks.values_list("name", flat=True)) == spec["tracks"]
    stages = list(Stage.objects.filter(event=event).order_by("position"))
    assert [stage.name for stage in stages] == spec["stages"]
    assert stages[0].is_initial is True
    assert stages[0].participation_mode == ParticipationMode.TEAM_FORMATION
    assert all(stage.participation_mode == ParticipationMode.TEAM_LOCKED for stage in stages[1:])
    assert all(a.reaches(b) for a, b in zip(stages, stages[1:]))
    plans = list(EvaluationPlan.objects.filter(stage__event=event).order_by("stage__position"))
    assert [plan.stage.position for plan in plans] == spec["judging_stages"]
    assert all(plan.draft_criteria and not plan.rubric_versions.exists() for plan in plans)
    assert EventTemplate.objects.count() == 0
    assert AuditEvent.objects.filter(action="event_template.library_instantiated").count() == 1


def test_local_template_rejects_unknown_slug_and_duplicate_event_atomically():
    workspace, owner, judge, base = fixture()
    path = base + "hackathon/instantiate/"
    payload = {"name": "Autumn", "slug": "autumn"}
    assert post_json(judge, path, payload).status_code == 403
    assert Client().get(base).status_code in (401, 403)
    assert post_json(owner, base + "unknown/instantiate/", payload).status_code == 400
    assert Event.objects.filter(workspace=workspace).count() == 0
    assert post_json(owner, path, payload).status_code == 201
    assert post_json(owner, path, payload).status_code == 400
    assert Event.objects.filter(workspace=workspace).count() == 1
    assert Stage.objects.filter(event__workspace=workspace).count() == len(
        LIBRARY["hackathon"]["stages"]
    )
