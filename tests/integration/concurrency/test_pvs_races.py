"""PVS03/PVS05/PVS01/PVS02 invariants under real concurrent transactions."""

import threading

import pytest
from accounts.models import Session, User
from awards.models import Award, AwardWinner
from deliberation.models import DeliberationStance
from django.db import close_old_connections, connection, connections
from django.test import Client
from eligibility.models import EligibilityReview
from integrations import eventascode
from integrations.demo_scenarios import generate_demo_event
from onsite.models import Attendance, Location, ProjectLocation

requires_real_db = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Needs a real multi-connection DB: set DATABASE_URL to a PostgreSQL instance.",
)
pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]
JSON = "application/json"


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def race(calls):
    """Run each callable on its own connection, released together; returns statuses."""
    barrier = threading.Barrier(len(calls))
    out = [None] * len(calls)

    def run(index, call):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            out[index] = call()
        except Exception as exc:  # noqa: BLE001 - surfaced to the assertion below
            out[index] = exc
        finally:
            connections.close_all()

    threads = [threading.Thread(target=run, args=(i, c)) for i, c in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for value in out:
        assert not isinstance(value, Exception), value
    return out


def world(seed, participants=6, judges=3):
    event = generate_demo_event(seed=seed, participants=participants, judges=judges)
    prefix = f"demo-hackathon-{seed}-"
    organizer = User.objects.get(username=prefix + "organizer")
    return event, organizer, prefix


def base(event):
    return f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/"


def test_a_single_slot_table_takes_exactly_one_of_many_simultaneous_placements():
    event, organizer, _ = world(71)
    org = client_for(organizer)
    table = org.post(
        base(event) + "locations/", {"kind": "table", "name": "Only"}, content_type=JSON
    ).json()["public_id"]
    projects = list(event.projects.all())
    clients = [client_for(organizer) for _ in projects]
    statuses = race(
        [
            (
                lambda c=c, p=p: c.put(
                    base(event) + f"projects/{p.public_id}/location/",
                    {"location": table},
                    content_type=JSON,
                ).status_code
            )
            for c, p in zip(clients, projects)
        ]
    )
    assert sorted(statuses) == [200] + [400] * (len(projects) - 1)
    assert ProjectLocation.objects.filter(location__name="Only").count() == 1


def test_simultaneous_auto_assignment_never_double_books_a_slot():
    event, organizer, prefix = world(72)
    for index, user in enumerate(User.objects.filter(username__startswith=prefix + "participant")):
        Attendance.objects.create(event=event, user=user, mode="in_person")
    org = client_for(organizer)
    for name in ("A", "B", "C"):
        org.post(base(event) + "locations/", {"kind": "table", "name": name}, content_type=JSON)
    clients = [client_for(organizer) for _ in range(4)]
    race(
        [
            (
                lambda c=c: c.post(
                    base(event) + "locations/auto-assign/", {"apply": True}, content_type=JSON
                ).status_code
            )
            for c in clients
        ]
    )
    placed = list(ProjectLocation.objects.values_list("location_id", flat=True))
    assert len(placed) == len(set(placed)) == 3
    assert Location.objects.filter(event=event, kind="table").count() == 3


def test_two_applies_of_the_same_plan_succeed_once_and_conflict_once():
    event, organizer, _ = world(73)
    document = eventascode.export_document(event)
    document["event"]["description"] = "Raced"
    digest = eventascode.digest(event)
    clients = [client_for(organizer) for _ in range(2)]
    statuses = race(
        [
            (
                lambda c=c: c.post(
                    base(event) + "as-code/apply/",
                    {"document": document, "expected_digest": digest},
                    content_type=JSON,
                ).status_code
            )
            for c in clients
        ]
    )
    assert sorted(statuses) == [200, 409]


def test_concurrent_stances_and_finalization_leave_one_consistent_outcome():
    event, organizer, prefix = world(74, judges=3)
    award = Award.objects.get(event=event, name="Grand Prize")
    AwardWinner.objects.filter(award__event=event).delete()
    Award.objects.filter(event=event).update(published_at=None)
    org = client_for(organizer)
    org.post(
        base(event) + f"awards/{award.public_id}/deliberation/", {"quorum": 2}, content_type=JSON
    )
    project = event.projects.order_by("name").first()
    judges = [User.objects.get(username=f"{prefix}judge-0{i}") for i in (1, 2, 3)]
    stance_url = (
        base(event) + f"awards/{award.public_id}/deliberation/projects/{project.public_id}/stance/"
    )
    calls = [
        (
            lambda u=u: client_for(u)
            .put(stance_url, {"stance": "endorse"}, content_type=JSON)
            .status_code
        )
        for u in judges
    ] + [
        (
            lambda: client_for(organizer)
            .post(
                base(event) + f"awards/{award.public_id}/deliberation/finalize/",
                {"winners": [str(project.public_id)], "override_reason": "chair"},
                content_type=JSON,
            )
            .status_code
        )
    ]
    statuses = race(calls)
    assert all(code in (200, 400) for code in statuses), statuses
    assert AwardWinner.objects.filter(award=award).count() == 1
    assert DeliberationStance.objects.filter(room__award=award, project=project).count() <= 3
    winner = AwardWinner.objects.get(award=award)
    recorded = winner.evidence["deliberation"]["endorse"]
    assert (
        recorded
        == DeliberationStance.objects.filter(
            room__award=award, project=project, stance="endorse"
        ).count()
        or recorded < 3
    )


def test_concurrent_remediation_responses_never_lose_a_revision():
    event, organizer, prefix = world(75)
    project = event.projects.order_by("name").first()
    owner = project.memberships.get().user
    org = client_for(organizer)
    findings = [
        org.post(
            base(event) + f"projects/{project.public_id}/eligibility/findings/",
            {"message": f"Issue {i}"},
            content_type=JSON,
        ).json()["public_id"]
        for i in range(4)
    ]
    before = EligibilityReview.objects.get(project=project).revision
    clients = [client_for(owner) for _ in findings]
    statuses = race(
        [
            (
                lambda c=c, f=f: c.post(
                    base(event) + f"projects/{project.public_id}/eligibility/findings/{f}/respond/",
                    {"response": "Fixed"},
                    content_type=JSON,
                ).status_code
            )
            for c, f in zip(clients, findings)
        ]
    )
    assert statuses == [200] * 4
    review = EligibilityReview.objects.get(project=project)
    assert review.revision == before + 4 and review.status == "pending"
