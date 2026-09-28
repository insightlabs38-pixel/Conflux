import pytest
from accounts.models import User
from audit.models import AuditEvent
from awards.models import Award, AwardWinner
from communications.models import MessageRecipient
from evaluations.models import Ballot
from integrations.demo_scenarios import generate_demo_event
from projects.models import Project
from test_sponsor_portal import client_for

pytestmark = pytest.mark.django_db
JSON = "application/json"


def world(participants=5, judges=3):
    event = generate_demo_event(seed=31, participants=participants, judges=judges)
    prefix = "demo-hackathon-31-"
    users = {
        "org": User.objects.get(username=prefix + "organizer"),
        "part": User.objects.get(username=prefix + "participant-01"),
        **{f"j{i}": User.objects.get(username=f"{prefix}judge-0{i}") for i in range(1, judges + 1)},
    }
    award = Award.objects.get(event=event, name="Grand Prize")
    AwardWinner.objects.filter(award__event=event).delete()
    Award.objects.filter(event=event).update(published_at=None)
    award.refresh_from_db()
    return event, award, users


def url(event, award, suffix=""):
    return (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}"
        f"/awards/{award.public_id}/deliberation/{suffix}"
    )


def top_projects(event):
    return list(Project.objects.filter(event=event).order_by("name"))


def open_room(event, award, users, **body):
    return client_for(users["org"]).post(url(event, award), body, content_type=JSON)


def stance(client, event, award, project, value, rationale=""):
    return client.put(
        url(event, award, f"projects/{project.public_id}/stance/"),
        {"stance": value, "rationale": rationale},
        content_type=JSON,
    )


def test_only_organizers_open_rooms_validated_and_judges_are_notified():
    event, award, users = world()
    for name in ("j1", "part"):
        assert (
            client_for(users[name]).post(url(event, award), {}, content_type=JSON).status_code
            == 403
        )
    assert open_room(event, award, users, quorum=4).status_code == 400
    assert open_room(event, award, users, quorum=0).status_code == 400
    assert open_room(event, award, users, extra=1).status_code == 400
    created = open_room(event, award, users)
    assert created.status_code == 201, created.content
    assert created.json()["quorum"] == 2 and created.json()["status"] == "open"
    assert open_room(event, award, users).status_code == 400
    assert MessageRecipient.objects.filter(user=users["j1"]).count() == 1
    assert not MessageRecipient.objects.filter(user=users["part"]).exists()
    track_award = Award.objects.get(event=event, name="Best in Open Data")
    assert open_room(event, track_award, users).status_code == 201
    manual = Award.objects.create(event=event, name="Manual", selection_source="manual")
    assert open_room(event, manual, users).status_code == 400
    Award.objects.filter(pk=award.pk).update(published_at="2026-01-01T00:00:00Z")


def test_participants_and_outsiders_cannot_see_or_join_the_room():
    event, award, users = world()
    open_room(event, award, users)
    outsider = User.objects.create_user(username="other-judge", password="x")
    from workspaces.models import Membership, Role

    Membership.objects.create(workspace=event.workspace, user=outsider, role=Role.JUDGE)
    for name in ("part",):
        assert client_for(users[name]).get(url(event, award)).status_code == 403
    assert client_for(outsider).get(url(event, award)).status_code == 404
    assert (
        client_for(outsider)
        .post(url(event, award, "notes/"), {"body": "x"}, content_type=JSON)
        .status_code
        == 404
    )
    project = top_projects(event)[0]
    assert stance(client_for(outsider), event, award, project, "endorse").status_code == 404


def test_discussion_is_only_visible_on_projects_the_judge_evaluated_and_never_shows_scores():
    event, award, users = world()
    open_room(event, award, users)
    first, second = top_projects(event)[:2]
    j1, j2 = client_for(users["j1"]), client_for(users["j2"])
    Ballot.objects.filter(judge=users["j2"], project=second).delete()
    assert (
        j1.post(
            url(event, award, "notes/"), {"body": "General thought"}, content_type=JSON
        ).status_code
        == 201
    )
    assert (
        j1.post(
            url(event, award, "notes/"),
            {"body": "Strong on " + second.name, "project": str(second.public_id)},
            content_type=JSON,
        ).status_code
        == 201
    )
    assert stance(j1, event, award, second, "endorse", "great").status_code == 200
    assert (
        j2.post(
            url(event, award, "notes/"),
            {"body": "hi", "project": str(second.public_id)},
            content_type=JSON,
        ).status_code
        == 403
    )
    assert stance(j2, event, award, second, "object").status_code == 403
    view = j2.get(url(event, award)).json()
    assert [n["body"] for n in view["notes"]] == ["General thought"]
    assert view["stances"] == [] and view["tally"] == []
    organizer_view = client_for(users["org"]).get(url(event, award)).json()
    assert len(organizer_view["notes"]) == 2 and len(organizer_view["stances"]) == 1
    text = str(view) + str(organizer_view)
    assert "score" not in text and "responses" not in text and str(first.public_id) not in text


def test_tally_recommendation_and_audited_stance_changes():
    event, award, users = world()
    open_room(event, award, users, quorum=2)
    project = top_projects(event)[0]
    clients = {name: client_for(users[name]) for name in ("j1", "j2", "j3")}
    assert stance(clients["j1"], event, award, project, "endorse").status_code == 200
    row = clients["j1"].get(url(event, award)).json()["tally"][0]
    assert row["endorse"] == 1 and row["recommended"] is False
    stance(clients["j2"], event, award, project, "endorse")
    stance(clients["j3"], event, award, project, "object", "concern")
    assert clients["j1"].get(url(event, award)).json()["tally"][0]["recommended"] is True
    stance(clients["j3"], event, award, project, "endorse")
    stance(clients["j2"], event, award, project, "abstain")
    row = clients["j1"].get(url(event, award)).json()["tally"][0]
    assert (row["endorse"], row["abstain"], row["object"]) == (2, 1, 0)
    changes = [
        (e.metadata["before"], e.metadata["after"])
        for e in AuditEvent.objects.filter(action="deliberation.stance_set").order_by("id")
    ]
    assert changes[-1] == ("endorse", "abstain") and (None, "endorse") in changes
    assert stance(clients["j1"], event, award, project, "maybe").status_code == 400


def test_finalize_records_deliberation_evidence_and_requires_reason_for_unrecommended():
    event, award, users = world()
    open_room(event, award, users, quorum=2)
    a, b = top_projects(event)[:2]
    j1, j2, org = client_for(users["j1"]), client_for(users["j2"]), client_for(users["org"])
    stance(j1, event, award, a, "endorse")
    stance(j2, event, award, a, "endorse")
    bad = org.post(
        url(event, award, "finalize/"), {"winners": [str(b.public_id)]}, content_type=JSON
    )
    assert bad.status_code == 400 and "not recommended" in str(bad.json())
    assert (
        org.post(
            url(event, award, "finalize/"),
            {"winners": [str(a.public_id), str(b.public_id)]},
            content_type=JSON,
        ).status_code
        == 400
    )
    assert (
        j1.post(
            url(event, award, "finalize/"), {"winners": [str(a.public_id)]}, content_type=JSON
        ).status_code
        == 403
    )
    assert org.post(url(event, award, "close/")).status_code == 200
    assert stance(j1, event, award, b, "endorse").status_code == 400
    assert (
        j1.post(url(event, award, "notes/"), {"body": "late"}, content_type=JSON).status_code == 400
    )
    done = org.post(
        url(event, award, "finalize/"),
        {"winners": [str(a.public_id)], "override_reason": "Top ranked and endorsed"},
        content_type=JSON,
    )
    assert done.status_code == 200, done.content
    winner = AwardWinner.objects.get(award=award)
    assert winner.project == a
    assert winner.evidence["deliberation"] == {
        "room": str(award.deliberation_room.public_id),
        "quorum": 2,
        "endorse": 2,
        "object": 0,
        "recommended": True,
    }
    assert done.json()["status"] == "finalized" and done.json()["finalization"]["winners"] == [
        str(a.public_id)
    ]
    again = org.post(
        url(event, award, "finalize/"), {"winners": [str(a.public_id)]}, content_type=JSON
    )
    assert again.status_code == 400
    assert AuditEvent.objects.filter(action="deliberation.finalized").count() == 1


def test_override_finalization_is_labelled_and_existing_winners_block_it():
    event, award, users = world()
    open_room(event, award, users)
    project = top_projects(event)[-1]
    org = client_for(users["org"])
    done = org.post(
        url(event, award, "finalize/"),
        {"winners": [str(project.public_id)], "override_reason": "Panel chair decision"},
        content_type=JSON,
    )
    assert done.status_code == 200, done.content
    winner = AwardWinner.objects.get(award=award)
    assert winner.override_reason == "Panel chair decision"
    assert winner.evidence["deliberation"]["recommended"] is False


def test_ineligible_projects_cannot_be_discussed_or_finalized():
    from eligibility.models import EligibilityReview

    event, award, users = world()
    open_room(event, award, users)
    project = top_projects(event)[0]
    EligibilityReview.objects.create(project=project, status="ineligible")
    assert stance(client_for(users["j1"]), event, award, project, "endorse").status_code == 400
    org = client_for(users["org"])
    assert (
        org.post(
            url(event, award, "finalize/"),
            {"winners": [str(project.public_id)], "override_reason": "x"},
            content_type=JSON,
        ).status_code
        == 400
    )
