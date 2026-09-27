import pytest
from accounts.models import User
from evaluations.models import EvaluationPool, PoolMembership
from events.models import Event
from presentation.records import (
    RecordVerificationError,
    build_event_record,
    build_judge_record,
    build_project_record,
    sign_record,
    verify_record,
)
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def make_event():
    workspace = Workspace.objects.create(name="Records", slug="records")
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    return workspace, event


def test_event_record_roundtrips():
    _workspace, event = make_event()
    claims = build_event_record(event)
    token = sign_record(claims)
    verified = verify_record(token)
    assert verified == claims
    assert verified["kind"] == "event"
    assert verified["event"]["public_id"] == str(event.public_id)


def test_project_record_carries_track():
    workspace, event = make_event()
    from events.models import Track

    track = Track.objects.create(event=event, name="Hardware")
    project = Project.objects.create(
        event=event,
        track=track,
        name="Widget",
        created_by=User.objects.create_user(username="builder", password="unused"),
    )
    claims = build_project_record(project)
    verified = verify_record(sign_record(claims))
    assert verified["subject"]["name"] == "Widget"
    assert verified["subject"]["track"] == "Hardware"


def test_judge_record_requires_real_pool_membership():
    workspace, event = make_event()
    judge = User.objects.create_user(username="judge", password="unused")
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    with pytest.raises(ValueError):
        build_judge_record(judge, event)

    pool = EvaluationPool.objects.create(event=event, name="Main pool")
    PoolMembership.objects.create(pool=pool, judge=judge)
    claims = build_judge_record(judge, event)
    verified = verify_record(sign_record(claims))
    assert verified["kind"] == "judge"
    assert verified["subject"]["public_id"] == str(judge.public_id)


def test_tampered_record_fails_verification():
    _workspace, event = make_event()
    token = sign_record(build_event_record(event))
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}Z.{signature}"
    with pytest.raises(RecordVerificationError):
        verify_record(tampered)


def test_unsigned_record_fails_verification():
    with pytest.raises(RecordVerificationError):
        verify_record("not-a-jwt-at-all")
