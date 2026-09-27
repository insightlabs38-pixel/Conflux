import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import EvaluationPool, PoolMembership
from events.models import Event, EventStatus
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    organizer = User.objects.create_user(username="record-organizer", password="unused")
    workspace = Workspace.objects.create(name="Records", slug="records")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    return workspace, event, client


def base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/records/"


def test_event_record_requires_organizer_role():
    _workspace, event, _client = fixture()
    url = base(event.workspace, event) + "event/"
    assert Client().post(url).status_code in (401, 403)


def test_issued_event_record_verifies_through_the_public_endpoint():
    workspace, event, client = fixture()
    issued = client.post(base(workspace, event) + "event/")
    assert issued.status_code == 201
    token = issued.json()["token"]

    verified = Client().post(
        "/api/v1/records/verify/", {"token": token}, content_type="application/json"
    )
    assert verified.status_code == 200
    assert verified.json()["valid"] is True
    assert verified.json()["claims"]["kind"] == "event"


def test_tampered_token_fails_public_verification():
    workspace, event, client = fixture()
    token = client.post(base(workspace, event) + "event/").json()["token"]
    bad = Client().post(
        "/api/v1/records/verify/", {"token": token + "x"}, content_type="application/json"
    )
    assert bad.status_code == 200
    assert bad.json()["valid"] is False


def test_project_record_requires_a_real_project_in_this_event():
    workspace, event, client = fixture()
    creator = User.objects.create_user(username="builder", password="unused")
    project = Project.objects.create(event=event, name="Widget", created_by=creator)
    ok = client.post(
        base(workspace, event) + "project/",
        {"project": str(project.public_id)},
        content_type="application/json",
    )
    assert ok.status_code == 201
    assert ok.json()["claims"]["subject"]["name"] == "Widget"

    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    foreign = Project.objects.create(event=other_event, name="Foreign", created_by=creator)
    assert (
        client.post(
            base(workspace, event) + "project/",
            {"project": str(foreign.public_id)},
            content_type="application/json",
        ).status_code
        == 404
    )


def test_judge_record_rejects_a_non_judge():
    workspace, event, client = fixture()
    judge = User.objects.create_user(username="judge", password="unused")
    rejected = client.post(
        base(workspace, event) + "judge/",
        {"user": str(judge.public_id)},
        content_type="application/json",
    )
    assert rejected.status_code == 400

    pool = EvaluationPool.objects.create(event=event, name="Main pool")
    PoolMembership.objects.create(pool=pool, judge=judge)
    accepted = client.post(
        base(workspace, event) + "judge/",
        {"user": str(judge.public_id)},
        content_type="application/json",
    )
    assert accepted.status_code == 201
    assert accepted.json()["claims"]["kind"] == "judge"


def test_verification_key_endpoint_is_public_and_stable():
    response = Client().get("/api/v1/records/verification-key/")
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "EdDSA"
    assert "BEGIN PUBLIC KEY" in body["public_key_pem"]
    again = Client().get("/api/v1/records/verification-key/")
    assert again.json()["public_key_pem"] == body["public_key_pem"]


def test_verify_page_renders_result_from_a_query_string_token():
    workspace, event, client = fixture()
    token = client.post(base(workspace, event) + "event/").json()["token"]

    ok = Client().get("/e/verify/", {"token": token})
    assert ok.status_code == 200
    assert b"Valid" in ok.content

    bad = Client().get("/e/verify/", {"token": token + "x"})
    assert bad.status_code == 200
    assert b"Not a valid record" in bad.content

    empty = Client().get("/e/verify/")
    assert empty.status_code == 200


def test_public_gallery_json_lists_finalized_projects():
    workspace, event, client = fixture()
    event.is_public = True
    event.status = EventStatus.OPEN
    event.starts_at = None
    event.save(update_fields=["is_public", "status"])
    from django.utils import timezone

    event.starts_at = timezone.now()
    event.ends_at = timezone.now() + timezone.timedelta(days=1)
    event.save(update_fields=["starts_at", "ends_at"])

    creator = User.objects.create_user(username="builder2", password="unused")
    project = Project.objects.create(event=event, name="Gadget", created_by=creator)
    from projects.models import Submission, SubmissionStatus
    from stages.models import Stage

    stage = Stage.objects.create(event=event, name="Submission")
    Submission.objects.create(
        project=project, stage=stage, status=SubmissionStatus.FINALIZED, updated_by=creator
    )

    response = Client().get(f"/api/v1/events/{event.public_id}/gallery/")
    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert names == ["Gadget"]
