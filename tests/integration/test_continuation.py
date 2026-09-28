import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from continuation.models import MAX_UPDATES_PER_PROJECT, ContinuationUpdate, ProjectContinuation
from django.core.exceptions import ValidationError
from django.test import Client
from events.models import Event
from integrations.archive import build_archive, import_archive
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


def put(client, url, data):
    return client.put(url, data, content_type="application/json")


def post(client, url, data=None):
    return client.post(url, data or {}, content_type="application/json")


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="C", slug="c")
    event = Event.objects.create(
        workspace=workspace, name="E", slug="e", status="closed", is_public=True
    )
    stage = Stage.objects.create(event=event, name="Final")
    organizer = User.objects.create_user(username="org")
    member = User.objects.create_user(username="member")
    other = User.objects.create_user(username="other")
    for user, role in (
        (organizer, Role.ORGANIZER),
        (member, Role.PARTICIPANT),
        (other, Role.PARTICIPANT),
    ):
        Membership.objects.create(workspace=workspace, user=user, role=role)

    def project(name, owner, finalized=True):
        item = Project.objects.create(event=event, name=name, created_by=owner)
        ProjectMembership.objects.create(project=item, user=owner, role="owner")
        submission = Submission.objects.create(project=item, stage=stage, updated_by=owner)
        if finalized:
            version = SubmissionVersion.objects.create(
                submission=submission,
                number=1,
                snapshot={"draft": {}, "artifacts": [], "forms": []},
                digest="b" * 64,
                finalized_by=owner,
            )
            submission.status = SubmissionStatus.FINALIZED
            submission.current_version = version
            submission.save()
        return item

    return dict(
        workspace=workspace,
        event=event,
        organizer=organizer,
        member=member,
        other=other,
        project=project("Robot", member),
        unfinished=project("Draft", member, finalized=False),
        rival=project("Rival", other),
    )


def base(w, project=None):
    prefix = f"/api/v1/workspaces/{w['workspace'].public_id}/events/{w['event'].public_id}/"
    return prefix + (f"projects/{project.public_id}/continuation/" if project else "")


GOOD = {
    "summary": "Keeps going as an open-source library.",
    "url": "https://example.test/robot",
    "seeking": ["contributors", "feedback"],
    "is_public": True,
}


def test_a_member_publishes_a_continuation_after_the_event_closes(world):
    w = world
    member = client_for(w["member"])
    saved = put(member, base(w, w["project"]), GOOD)
    assert saved.status_code == 200 and saved.json()["seeking"] == ["contributors", "feedback"]
    assert (
        put(member, base(w, w["project"]), {**GOOD, "summary": "Edited"}).json()["summary"]
        == "Edited"
    )
    assert ProjectContinuation.objects.count() == 1
    assert AuditEvent.objects.filter(action="continuation.saved").count() == 2
    assert member.get(base(w, w["project"])).json()["is_public"] is True


def test_it_is_refused_while_the_event_is_open_or_without_a_finalized_submission(world):
    w = world
    member = client_for(w["member"])
    assert put(member, base(w, w["unfinished"]), GOOD).status_code == 400
    Event.objects.filter(pk=w["event"].pk).update(status="open")
    assert put(member, base(w, w["project"]), GOOD).status_code == 400
    Event.objects.filter(pk=w["event"].pk).update(status="archived")
    assert put(member, base(w, w["project"]), GOOD).status_code == 200
    assert not ProjectContinuation.objects.filter(project=w["unfinished"]).exists()


def test_only_members_can_write_and_other_teams_cannot_even_see_it(world):
    w = world
    other = client_for(w["other"])
    assert put(other, base(w, w["project"]), GOOD).status_code == 404
    assert other.get(base(w, w["project"])).status_code == 404
    outsider = User.objects.create_user(username="outsider")
    assert put(client_for(outsider), base(w, w["project"]), GOOD).status_code == 403
    assert Client().get(base(w, w["project"])).status_code in (401, 403)
    assert not ProjectContinuation.objects.exists()


@pytest.mark.parametrize(
    "patch",
    [
        {"summary": ""},
        {"summary": "x" * 1001},
        {"summary": 5},
        {"summary": "bad\x00text"},
        {"url": "javascript:alert(1)"},
        {"url": "ftp://example.test/x"},
        {"url": "https://user:pw@example.test/"},
        {"url": "https://example.test@evil.test/"},
        {"seeking": ["funding"]},
        {"seeking": "contributors"},
        {"is_public": "yes"},
    ],
)
def test_input_is_validated(world, patch):
    w = world
    assert put(client_for(w["member"]), base(w, w["project"]), {**GOOD, **patch}).status_code == 400
    assert not ProjectContinuation.objects.exists()


def test_updates_are_append_only_and_bounded(world):
    w = world
    member = client_for(w["member"])
    url = base(w, w["project"]) + "updates/"
    assert post(member, url, {"body": "early"}).status_code == 400
    put(member, base(w, w["project"]), GOOD)
    for i in range(MAX_UPDATES_PER_PROJECT):
        assert post(member, url, {"body": f"note {i}"}).status_code == 201
    assert post(member, url, {"body": "one too many"}).status_code == 400
    assert post(member, url, {"body": ""}).status_code == 400
    assert post(client_for(w["other"]), url, {"body": "x"}).status_code == 404
    update = ContinuationUpdate.objects.first()
    update.body = "changed"
    with pytest.raises(ValidationError):
        update.save()


def test_the_public_listing_shows_only_visible_public_continuations(world):
    w = world
    put(client_for(w["member"]), base(w, w["project"]), GOOD)
    put(client_for(w["other"]), base(w, w["rival"]), {**GOOD, "is_public": False})
    for i in range(5):
        post(client_for(w["member"]), base(w, w["project"]) + "updates/", {"body": f"n{i}"})
    public_url = f"/api/v1/events/{w['event'].public_id}/continuations/"
    body = Client().get(public_url).json()
    assert [c["name"] for c in body] == ["Robot"]
    assert [u["body"] for u in body[0]["updates"]] == ["n4", "n3", "n2"]
    assert "hidden" not in body[0] and "is_public" not in body[0] and "public_id" not in body[0]
    Event.objects.filter(pk=w["event"].pk).update(is_public=False)
    assert Client().get(public_url).status_code == 404
    Event.objects.filter(pk=w["event"].pk).update(is_public=True, status="draft")
    assert Client().get(public_url).status_code == 404


def test_organizers_can_hide_and_restore_with_a_reason(world):
    w = world
    put(client_for(w["member"]), base(w, w["project"]), GOOD)
    org, member = client_for(w["organizer"]), client_for(w["member"])
    public_url = f"/api/v1/events/{w['event'].public_id}/continuations/"
    assert post(member, base(w, w["project"]) + "hide/", {"reason": "x"}).status_code == 403
    assert post(org, base(w, w["project"]) + "hide/").status_code == 400
    hidden = post(org, base(w, w["project"]) + "hide/", {"reason": "Spam link"})
    assert hidden.json()["hidden"] is True
    assert Client().get(public_url).json() == []
    assert member.get(base(w, w["project"])).json()["hidden_reason"] == "Spam link"
    assert put(member, base(w, w["project"]), GOOD).json()["hidden"] is True
    assert Client().get(public_url).json() == []
    assert post(org, base(w, w["project"]) + "restore/").json()["hidden"] is False
    assert len(Client().get(public_url).json()) == 1
    assert (
        AuditEvent.objects.filter(
            action__in=["continuation.hidden", "continuation.restored"]
        ).count()
        == 2
    )
    assert [c["name"] for c in org.get(base(w) + "continuations/").json()] == ["Robot"]
    assert member.get(base(w) + "continuations/").status_code == 403


def test_continuations_survive_a_final_archive_round_trip(world):
    w = world
    member = client_for(w["member"])
    put(member, base(w, w["project"]), GOOD)
    post(member, base(w, w["project"]) + "updates/", {"body": "shipped v1"})
    archive = build_archive(w["event"], mode="final")
    copied = import_archive(workspace=w["workspace"], archive=archive, name="Copy", slug="copy")
    item = ProjectContinuation.objects.get(project__event=copied)
    assert item.summary == GOOD["summary"] and item.seeking == ["contributors", "feedback"]
    assert item.updates.get().body == "shipped v1"
