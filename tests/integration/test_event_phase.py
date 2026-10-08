"""PD-F005-B02-T01: the phase an event is in, derived once on the server (events.lifecycle) and
shown the same everywhere: draft, open, closed, judging, published, archived."""

import pytest
from accounts.models import Session, User
from awards.models import Award
from django.test import Client
from django.utils import timezone
from evaluations.models import Ballot, EvaluationPlan, EvaluationPool, RubricVersion
from events import lifecycle
from events.models import Event, EventStatus
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def world():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    participant = User.objects.create_user(username="ptc", password="unused")
    workspace = Workspace.objects.create(name="W", slug="w")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    Membership.objects.create(user=participant, workspace=workspace, role=Role.PARTICIPANT)
    return workspace, organizer, judge, participant


def make_event(workspace, name, status, public=True):
    return Event.objects.create(
        workspace=workspace, name=name, slug=name.lower(), status=status, is_public=public
    )


def ballot(event, judge, calibration=False):
    stage = Stage.objects.create(event=event, name="Final", position=1)
    pool = EvaluationPool.objects.create(event=event, name="Pool")
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", pool=pool)
    rubric = RubricVersion.objects.create(
        plan=plan,
        number=1,
        criteria=[{"id": "c", "name": "C", "weight": 1, "min_score": 0, "max_score": 10}],
    )
    project = Project.objects.create(event=event, name="P", created_by=judge)
    return Ballot.objects.create(
        project=project, rubric_version=rubric, judge=judge, is_calibration=calibration
    )


def test_each_stored_status_reads_as_itself_until_something_has_happened():
    workspace, *_ = world()
    expected = {
        EventStatus.DRAFT: "draft",
        EventStatus.OPEN: "open",
        EventStatus.CLOSED: "closed",
        EventStatus.ARCHIVED: "archived",
    }
    for status, key in expected.items():
        event = make_event(workspace, f"E-{status}", status)
        found = lifecycle.phase(event)
        assert found["key"] == key
        assert found["label"] and found["reason"]


def test_a_submitted_ballot_means_judging_but_calibration_practice_does_not():
    workspace, _, judge, _ = world()
    practice = make_event(workspace, "Practice", EventStatus.CLOSED)
    ballot(practice, judge, calibration=True)
    assert lifecycle.phase_key(practice) == "closed"
    live = make_event(workspace, "Live", EventStatus.CLOSED)
    ballot(live, judge)
    assert lifecycle.phase_key(live) == "judging"
    still_open = make_event(workspace, "StillOpen", EventStatus.OPEN)
    ballot(still_open, judge)
    assert lifecycle.phase_key(still_open) == "judging"  # judging can begin before the event closes


def test_a_published_award_means_published_and_beats_judging_but_not_archived_or_draft():
    workspace, _, judge, _ = world()
    event = make_event(workspace, "Out", EventStatus.CLOSED)
    ballot(event, judge)
    Award.objects.create(event=event, name="Unpublished")
    assert lifecycle.phase_key(event) == "judging"  # an award that is not out yet changes nothing
    Award.objects.create(event=event, name="Out", published_at=timezone.now())
    assert lifecycle.phase_key(event) == "published"
    event.status = EventStatus.ARCHIVED
    event.save()
    assert lifecycle.phase_key(event) == "archived"
    draft = make_event(workspace, "Dr", EventStatus.DRAFT)
    Award.objects.create(event=draft, name="Early", published_at=timezone.now())
    assert lifecycle.phase_key(draft) == "draft"  # nothing is out before the event is open


def test_every_list_that_lets_a_person_choose_an_event_says_its_phase():
    workspace, organizer, judge, participant = world()
    open_event = make_event(workspace, "Alpha", EventStatus.OPEN)
    ballot(open_event, judge)
    make_event(workspace, "Beta", EventStatus.DRAFT)
    base = f"/api/v1/workspaces/{workspace.public_id}"
    organizer_rows = client_for(organizer).get(f"{base}/events/").json()
    assert {r["name"]: r["phase"]["key"] for r in organizer_rows} == {
        "Alpha": "judging",
        "Beta": "draft",
    }
    assert set(organizer_rows[0]["phase"]) == {"key", "label", "reason"}
    judge_rows = client_for(judge).get(f"{base}/judge-events/").json()
    assert {r["name"]: r["phase"]["key"] for r in judge_rows} == {
        "Alpha": "judging",
        "Beta": "draft",
    }
    participant_rows = client_for(participant).get(f"{base}/participant-events/").json()
    assert [(r["name"], r["phase"]["key"]) for r in participant_rows] == [("Alpha", "judging")]


def test_the_phase_is_read_only_on_the_event_itself():
    workspace, organizer, _, _ = world()
    event = make_event(workspace, "Gamma", EventStatus.OPEN)
    event.starts_at = timezone.now()
    event.ends_at = timezone.now() + timezone.timedelta(days=1)
    event.save()
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    response = client_for(organizer).patch(
        base, {"phase": {"key": "published"}, "name": "Gamma 2"}, content_type="application/json"
    )
    assert response.status_code == 200, response.content
    assert response.json()["name"] == "Gamma 2"
    assert response.json()["phase"]["key"] == "open"  # asked to be published, still derived
