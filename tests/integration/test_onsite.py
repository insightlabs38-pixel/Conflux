import pytest
from accounts.models import User
from audit.models import AuditEvent
from django.test import Client
from events.models import Event, ParticipantCheckIn, Track
from onsite import passes
from onsite.models import Attendance, Location, ProjectLocation
from projects.models import Project, ProjectMembership
from test_sponsor_portal import client_for
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
JSON = "application/json"


def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e", status="open")
    users = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("vol", Role.VOLUNTEER),
        ("judge", Role.JUDGE),
        ("a", Role.PARTICIPANT),
        ("b", Role.PARTICIPANT),
        ("c", Role.PARTICIPANT),
    ):
        users[name] = User.objects.create_user(username=name, password="x")
        Membership.objects.create(workspace=workspace, user=users[name], role=role)
    track = Track.objects.create(event=event, name="T")
    projects = {}
    for name in ("a", "b", "c"):
        project = Project.objects.create(
            event=event, created_by=users[name], name=f"P-{name}", track=track
        )
        ProjectMembership.objects.create(project=project, user=users[name], role="owner")
        projects[name] = project
    return workspace, event, users, projects


def base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"


def post(client, url, body=None):
    return client.post(url, body or {}, content_type=JSON)


def put(client, url, body):
    return client.put(url, body, content_type=JSON)


def make_location(client, url, **body):
    return post(client, url + "locations/", {"kind": "table", "name": "T1", **body})


def test_locations_are_organizer_managed_validated_and_readable_by_members():
    workspace, event, users, _ = world()
    url = base(workspace, event)
    org = client_for(users["org"])
    room = make_location(org, url, kind="room", name="Hall", x=0, y=0)
    assert room.status_code == 201, room.content
    table = make_location(org, url, name="T1", parent=room.json()["public_id"], x=3, y=4)
    assert table.status_code == 201 and table.json()["capacity"] == 1
    assert make_location(org, url, name="T1").status_code == 400
    assert make_location(org, url, name="X", x=1).status_code == 400
    assert (
        make_location(org, url, kind="room", name="R2", parent=room.json()["public_id"]).status_code
        == 400
    )
    assert make_location(org, url, name="Y", unknown=1).status_code == 400
    for name in ("vol", "judge", "a"):
        client = client_for(users[name])
        assert post(client, url + "locations/", {"kind": "table", "name": "Z"}).status_code == 403
        assert len(client.get(url + "locations/").json()) == 2
    assert Client().get(url + "locations/").status_code in (401, 403)


def test_placement_capacity_moves_and_visibility_by_role():
    workspace, event, users, projects = world()
    url = base(workspace, event)
    org = client_for(users["org"])
    t1 = make_location(org, url, name="T1").json()["public_id"]
    t2 = make_location(org, url, name="T2", capacity=2).json()["public_id"]
    room = make_location(org, url, kind="room", name="Hall").json()["public_id"]

    def place(name, location):
        return put(
            org, url + f"projects/{projects[name].public_id}/location/", {"location": location}
        )

    assert place("a", t1).status_code == 200
    assert place("b", t1).status_code == 400
    assert place("b", t2).status_code == 200 and place("c", t2).status_code == 200
    assert place("a", t2).status_code == 400
    assert place("a", room).status_code == 400
    assert place("b", t1).status_code == 400
    assert place("a", None).status_code == 200 and place("b", t1).status_code == 200
    seen_org = org.get(url + "project-locations/").json()
    assert len(seen_org) == 2
    assert len(client_for(users["judge"]).get(url + "project-locations/").json()) == 2
    mine = client_for(users["c"]).get(url + "project-locations/").json()
    assert [row["project_name"] for row in mine] == ["P-c"]
    assert client_for(users["a"]).get(url + "project-locations/").json() == []
    assert (
        put(
            client_for(users["a"]),
            url + f"projects/{projects['a'].public_id}/location/",
            {"location": t1},
        ).status_code
        == 403
    )
    delete = client_for(users["org"]).delete(url + f"locations/{t1}/")
    assert delete.status_code == 400
    assert place("a", t2).status_code == 200
    patch = org.patch(url + f"locations/{t2}/", {"capacity": 1}, content_type=JSON)
    assert patch.status_code == 400
    assert AuditEvent.objects.filter(action="onsite.project_placed").count() >= 5


def test_rsvp_is_self_service_and_summary_counts_are_staff_only():
    workspace, event, users, _ = world()
    url = base(workspace, event)
    a, b = client_for(users["a"]), client_for(users["b"])
    assert a.get(url + "my-attendance/").json() == {"mode": None}
    assert put(a, url + "my-attendance/", {"mode": "in_person"}).status_code == 200
    assert put(a, url + "my-attendance/", {"mode": "remote"}).status_code == 200
    assert put(b, url + "my-attendance/", {"mode": "sometimes"}).status_code == 400
    assert (
        put(client_for(users["judge"]), url + "my-attendance/", {"mode": "remote"}).status_code
        == 403
    )
    assert Attendance.objects.filter(user=users["a"]).get().mode == "remote"
    assert b.get(url + "attendance/").status_code == 403
    summary = client_for(users["vol"]).get(url + "onsite-summary/").json()
    assert (
        summary["participants"] == 3
        and summary["rsvp"]["remote"] == 1
        and summary["no_response"] == 2
    )
    listing = client_for(users["org"]).get(url + "attendance/").json()
    assert listing == [
        {
            "person": str(users["a"].public_id),
            "username": "a",
            "mode": "remote",
            "checked_in": False,
        }
    ]


def test_pass_is_signed_stable_event_bound_and_scannable_once():
    workspace, event, users, _ = world()
    url = base(workspace, event)
    other_event = Event.objects.create(workspace=workspace, name="O", slug="o", status="open")
    token = client_for(users["a"]).get(url + "my-pass/").json()["token"]
    assert token == client_for(users["a"]).get(url + "my-pass/").json()["token"]
    assert passes.verify(token, event) == users["a"].public_id
    assert passes.verify(token, other_event) is None
    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
    assert passes.verify(tampered, event) is None
    assert client_for(users["judge"]).get(url + "my-pass/").status_code == 403
    vol = client_for(users["vol"])
    put(client_for(users["a"]), url + "my-attendance/", {"mode": "remote"})
    first = post(vol, url + "checkins/scan/", {"token": token})
    assert first.status_code == 200 and first.json()["already_checked_in"] is False
    assert post(vol, url + "checkins/scan/", {"token": token}).json()["already_checked_in"] is True
    assert ParticipantCheckIn.objects.filter(event=event).count() == 1
    assert Attendance.objects.get(user=users["a"]).mode == "in_person"
    for bad in (
        "garbage",
        tampered,
        token.replace(users["a"].public_id.hex, users["b"].public_id.hex),
    ):
        assert post(vol, url + "checkins/scan/", {"token": bad}).status_code == 400
    assert post(client_for(users["a"]), url + "checkins/scan/", {"token": token}).status_code == 403
    assert (
        post(client_for(users["judge"]), url + "checkins/scan/", {"token": token}).status_code
        == 403
    )
    assert AuditEvent.objects.filter(action="onsite.scan_checkin").count() == 1
    summary = vol.get(url + "onsite-summary/").json()
    assert summary["checked_in"] == 1


def test_qr_is_an_svg_of_the_pass_only_for_the_owner():
    workspace, event, users, _ = world()
    url = base(workspace, event)
    response = client_for(users["a"]).get(url + "my-pass/qr/")
    assert response.status_code == 200 and response["Content-Type"] == "image/svg+xml"
    assert b"<svg" in response.content and "no-store" in response["Cache-Control"]
    assert client_for(users["judge"]).get(url + "my-pass/qr/").status_code == 403
    assert Client().get(url + "my-pass/qr/").status_code in (401, 403)


def test_auto_assign_previews_then_places_in_person_projects_deterministically():
    workspace, event, users, projects = world()
    url = base(workspace, event)
    org = client_for(users["org"])
    make_location(org, url, name="T1")
    make_location(org, url, name="T2")
    for name in ("a", "b"):
        put(client_for(users[name]), url + "my-attendance/", {"mode": "in_person"})
    put(client_for(users["c"]), url + "my-attendance/", {"mode": "remote"})
    preview = post(org, url + "locations/auto-assign/", {}).json()
    assert preview["applied"] is False and len(preview["assignments"]) == 2
    assert ProjectLocation.objects.count() == 0
    applied = post(org, url + "locations/auto-assign/", {"apply": True}).json()
    assert applied["assignments"] == preview["assignments"] and applied["unplaced"] == []
    assert {pl.project.name for pl in ProjectLocation.objects.all()} == {"P-a", "P-b"}
    assert post(org, url + "locations/auto-assign/", {"apply": True}).json()["assignments"] == []
    assert post(client_for(users["vol"]), url + "locations/auto-assign/", {}).status_code == 403
    assert post(org, url + "locations/auto-assign/", {"kind": "room"}).status_code == 400


def test_archived_events_freeze_onsite_changes():
    workspace, event, users, projects = world()
    url = base(workspace, event)
    org = client_for(users["org"])
    make_location(org, url)
    Event.objects.filter(pk=event.pk).update(status="archived")
    assert make_location(org, url, name="T9").status_code == 400
    assert (
        put(client_for(users["a"]), url + "my-attendance/", {"mode": "remote"}).status_code == 400
    )
    assert Location.objects.count() == 1
