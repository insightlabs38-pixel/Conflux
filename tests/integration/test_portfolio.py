from datetime import timedelta

import pytest
from accounts.models import Session, User
from awards.models import Award, AwardWinner
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from events.models import Event
from projects.models import (
    Project,
    ProjectMembership,
    Submission,
    SubmissionStatus,
    SubmissionVersion,
)
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def add_user(name, workspace, role=Role.PARTICIPANT):
    user = User.objects.create_user(username=name)
    Membership.objects.create(workspace=workspace, user=user, role=role)
    return user


def add_project(event, user, name, *, finalize=False, stage=None):
    project = Project.objects.create(event=event, name=name, created_by=user)
    ProjectMembership.objects.create(project=project, user=user, role="owner")
    if finalize:
        submission = Submission.objects.create(project=project, stage=stage, updated_by=user)
        version = SubmissionVersion.objects.create(
            submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=user
        )
        submission.status = SubmissionStatus.FINALIZED
        submission.current_version = version
        submission.save()
    return project


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="P", slug="p")
    now = timezone.now()
    spring = Event.objects.create(
        workspace=workspace,
        name="Spring",
        slug="spring",
        status="closed",
        starts_at=now - timedelta(days=90),
    )
    autumn = Event.objects.create(
        workspace=workspace,
        name="Autumn",
        slug="autumn",
        status="open",
        starts_at=now - timedelta(days=1),
    )
    spring_stage = Stage.objects.create(event=spring, name="Final")
    autumn_stage = Stage.objects.create(event=autumn, name="Build")
    organizer = add_user("org", workspace, Role.ORGANIZER)
    ada = add_user("ada", workspace)
    bob = add_user("bob", workspace)
    old = add_project(spring, ada, "Old Robot", finalize=True, stage=spring_stage)
    new = add_project(autumn, ada, "New Robot")
    add_project(autumn, bob, "Bob Bot", finalize=True, stage=autumn_stage)
    other_workspace = Workspace.objects.create(name="Other", slug="other")
    other_event = Event.objects.create(workspace=other_workspace, name="Elsewhere", slug="e")
    stranger = add_user("stranger", other_workspace)
    add_project(other_event, stranger, "Foreign")
    Membership.objects.create(workspace=workspace, user=stranger, role=Role.PARTICIPANT)
    return dict(
        workspace=workspace,
        spring=spring,
        autumn=autumn,
        organizer=organizer,
        ada=ada,
        bob=bob,
        old=old,
        new=new,
        stranger=stranger,
    )


def base(w):
    return f"/api/v1/workspaces/{w['workspace'].public_id}/portfolio/"


def test_a_participant_sees_only_their_own_projects_across_events(world):
    w = world
    body = client_for(w["ada"]).get(base(w) + "me/").json()
    assert [(p["name"], p["event"]["name"]) for p in body["projects"]] == [
        ("New Robot", "Autumn"),
        ("Old Robot", "Spring"),
    ]
    assert body["events"] == 2
    finalized = {p["name"]: p["finalized"] for p in body["projects"]}
    assert finalized == {"New Robot": False, "Old Robot": True}
    old = next(p for p in body["projects"] if p["name"] == "Old Robot")
    assert old["submissions"][0]["version"] == 1 and old["submissions"][0]["stage"] == "Final"
    assert client_for(w["stranger"]).get(base(w) + "me/").json()["projects"] == []


def test_awards_appear_only_after_the_award_is_published(world):
    w = world
    award = Award.objects.create(event=w["spring"], name="Grand Prize")
    AwardWinner.objects.create(
        award=award, project=w["old"], selected_by=w["organizer"], source="manual"
    )
    ada = client_for(w["ada"])
    assert ada.get(base(w) + "me/").json()["projects"][1]["awards"] == []
    Award.objects.update(published_at=timezone.now())
    assert ada.get(base(w) + "me/").json()["projects"][1]["awards"][0]["award"] == "Grand Prize"


def test_outsiders_and_participants_cannot_use_organizer_surfaces(world):
    w = world
    nobody = User.objects.create_user(username="nobody")
    assert client_for(nobody).get(base(w) + "me/").status_code == 403
    assert Client().get(base(w) + "me/").status_code in (401, 403)
    for suffix in ("projects/", "participants/", f"participants/{w['ada'].public_id}/"):
        assert client_for(w["ada"]).get(base(w) + suffix).status_code == 403
        assert Client().get(base(w) + suffix).status_code in (401, 403)


def test_organizer_lists_projects_with_filters_and_pagination(world):
    w = world
    org = client_for(w["organizer"])
    everything = org.get(base(w) + "projects/").json()
    assert everything["total"] == 3
    assert "Foreign" not in str(everything)
    page = org.get(base(w) + "projects/", {"limit": 1, "offset": 1}).json()
    assert page["total"] == 3 and len(page["results"]) == 1
    only_spring = org.get(base(w) + "projects/", {"event": str(w["spring"].public_id)}).json()
    assert [p["name"] for p in only_spring["results"]] == ["Old Robot"]
    finalized = org.get(base(w) + "projects/", {"status": "finalized"}).json()
    assert sorted(p["name"] for p in finalized["results"]) == ["Bob Bot", "Old Robot"]
    unfinalized = org.get(base(w) + "projects/", {"status": "unfinalized"}).json()
    assert [p["name"] for p in unfinalized["results"]] == ["New Robot"]
    assert [p["name"] for p in org.get(base(w) + "projects/", {"q": "bob"}).json()["results"]] == [
        "Bob Bot"
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "1000"},
        {"limit": "-1"},
        {"limit": "x"},
        {"offset": "-5"},
        {"event": "nope"},
        {"status": "weird"},
        {"q": "x" * 101},
    ],
)
def test_bad_query_parameters_are_rejected_not_crashed(world, params):
    assert client_for(world["organizer"]).get(base(world) + "projects/", params).status_code == 400


def test_participant_aggregates_span_events(world):
    w = world
    body = client_for(w["organizer"]).get(base(w) + "participants/").json()
    by_name = {r["username"]: r for r in body["results"]}
    assert body["total"] == 2 and "stranger" not in by_name
    assert (
        by_name["ada"]["events"],
        by_name["ada"]["projects"],
        by_name["ada"]["finalized_projects"],
    ) == (2, 2, 1)
    assert (by_name["bob"]["events"], by_name["bob"]["finalized_projects"]) == (1, 1)
    assert [
        r["username"]
        for r in client_for(w["organizer"])
        .get(base(w) + "participants/", {"q": "AD"})
        .json()["results"]
    ] == ["ada"]


def test_participant_detail_is_workspace_scoped(world):
    w = world
    org = client_for(w["organizer"])
    detail = org.get(base(w) + f"participants/{w['ada'].public_id}/").json()
    assert detail["username"] == "ada" and detail["events"] == 2 and len(detail["projects"]) == 2
    assert org.get(base(w) + f"participants/{w['stranger'].public_id}/").status_code == 404
    assert org.get(base(w) + f"participants/{w['organizer'].public_id}/").status_code == 404


def test_query_count_does_not_grow_with_the_number_of_projects(world):
    w = world
    org, ada = client_for(w["organizer"]), client_for(w["ada"])
    stage = Stage.objects.filter(event=w["autumn"]).first()

    def measure():
        counts = []
        for client, path in ((org, "projects/"), (ada, "me/"), (org, "participants/")):
            with CaptureQueriesContext(connection) as queries:
                assert client.get(base(w) + path).status_code == 200
            counts.append(len(queries))
        return counts

    before = measure()
    for i in range(25):
        add_project(w["autumn"], w["ada"], f"Bulk {i}", finalize=i % 2 == 0, stage=stage)
    assert measure() == before
