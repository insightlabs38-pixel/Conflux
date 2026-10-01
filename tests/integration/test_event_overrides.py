"""PD-F001-B01-T07: every registry default can be overridden through its documented write, and a
lock is exactly what the domain endpoint enforces."""

from datetime import datetime

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from eventconfig.registry import SPECS
from events.models import Event, EventStatus
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

# A different valid value for every writable setting (the proof that each one can be overridden).
ALTERNATIVE = {
    "event.name": "Renamed",
    "approvals.message_send": True,
    "event.description": "A new description",
    "event.timezone": "Europe/Berlin",
    "event.starts_at": "2027-03-06T09:00:00Z",
    "event.ends_at": "2027-03-09T09:00:00Z",
    "event.is_public": True,
    "registration.mode": "application",
    "registration.capacity": 50,
    "registration.waitlist_enabled": True,
    "team.min_size": 2,
    "team.max_size": 6,
    "submission.required_artifact_kinds": ["video", "document"],
    "submission.require_finalized": False,
    "eligibility.require_track": True,
    "eligibility.require_clearance": True,
}


def setup():
    organizer = User.objects.create_user(username="org", password="unused")
    workspace = Workspace.objects.create(name="Over", slug="over")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    client = Client()
    client.cookies["session"] = Session.issue(organizer).token
    response = client.post(
        f"/api/v1/workspaces/{workspace.public_id}/event-templates/library/hackathon/instantiate/",
        data={"name": "Spring", "slug": "spring", "starts_at": "2027-03-05T09:00:00Z"},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return workspace, client, Event.objects.get(workspace=workspace, slug="spring")


def settings_of(client, workspace, event):
    body = client.get(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/configuration/"
    ).json()
    return {e["key"]: e for e in body["settings"]}


def write_as_documented(client, workspace, event, entry, value):
    """Exactly what automation would do from the configuration answer."""
    write = entry["write"]
    url = "/api/v1/" + write["path"].format(workspace=workspace.public_id, event=event.public_id)
    if write["body"] == "whole":
        # The endpoint replaces every input field: start from its current answer.
        body = client.get(url).json()
        body.pop("updated_at", None)
        body[write["field"]] = value
    else:
        body = {write["field"]: value}
    return client.generic(write["method"], url, data=_json(body), content_type="application/json")


def _instant(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _json(body):
    import json

    return json.dumps(body)


def test_the_proof_table_covers_every_writable_setting():
    writable = {s.key for s in SPECS if s.write}
    assert set(ALTERNATIVE) == writable, "a new setting needs an override proof here"


@pytest.mark.parametrize("key", sorted(ALTERNATIVE))
def test_every_default_can_be_overridden_through_its_documented_write(key):
    workspace, client, event = setup()
    before = settings_of(client, workspace, event)[key]
    value = ALTERNATIVE[key]
    assert before["value"] != value, "the alternative must differ from the current value"
    assert before["editable"] and before["lock"] is None

    response = write_as_documented(client, workspace, event, before, value)
    assert response.status_code == 200, (key, response.content)

    after = settings_of(client, workspace, event)[key]
    if key.endswith("_at"):  # the same instant, in the API's display zone
        assert _instant(after["value"]) == _instant(value)
    else:
        assert after["value"] == value
    if after["source"] not in ("set", "unset"):
        assert after["source"] == "overridden"
        assert after["baseline"] == before["baseline"]  # the baseline itself never moves


@pytest.mark.parametrize("key", sorted(ALTERNATIVE))
def test_a_lock_is_exactly_what_the_domain_endpoint_refuses(key):
    workspace, client, event = setup()
    entry = settings_of(client, workspace, event)[key]
    event.status = EventStatus.ARCHIVED
    event.save(update_fields=["status"])

    locked = settings_of(client, workspace, event)[key]
    assert not locked["editable"] and locked["lock"]["code"] == "event_archived"
    response = write_as_documented(client, workspace, event, entry, ALTERNATIVE[key])
    assert response.status_code == 400, (key, response.content)
    assert locked["lock"]["message"] in str(response.json())
    # Refused means unchanged.
    assert settings_of(client, workspace, event)[key]["value"] == locked["value"]


def test_constraints_follow_the_event_state():
    workspace, client, event = setup()
    starts = settings_of(client, workspace, event)["event.starts_at"]
    assert starts["constraint"] == "Must be before the end when both are set."  # a draft: no more
    event.status = EventStatus.OPEN
    event.ends_at = event.starts_at.replace(year=2099)
    event.save(update_fields=["status", "ends_at"])
    settings = settings_of(client, workspace, event)
    for key in ("event.starts_at", "event.ends_at"):
        assert "required while the event is open" in settings[key]["constraint"]
    assert "Must be after the start" in settings["event.ends_at"]["constraint"]
    assert settings["team.max_size"]["constraint"].startswith("Between 1 and 100")


def test_a_constraint_is_what_the_endpoint_enforces():
    workspace, client, event = setup()
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    crossed = client.patch(
        base,
        data={"starts_at": "2027-06-03T09:00:00Z", "ends_at": "2027-06-01T09:00:00Z"},
        content_type="application/json",
    )
    assert crossed.status_code == 400
    capacity = client.put(
        base + "registration-settings/", data={"capacity": 0}, content_type="application/json"
    )
    assert capacity.status_code == 400
    rules = client.get(base + "eligibility-rules/").json()
    rules.pop("updated_at")
    rules.update(min_team_size=5, max_team_size=2)
    assert (
        client.put(
            base + "eligibility-rules/", data=rules, content_type="application/json"
        ).status_code
        == 400
    )


def test_registration_changes_are_on_the_record_with_what_they_were():
    workspace, client, event = setup()
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/registration-settings/"
    )
    assert (
        client.put(url, data={"mode": "invite_only"}, content_type="application/json").status_code
        == 200
    )
    row = AuditEvent.objects.get(action="registration.settings_updated")
    assert row.metadata["event_id"] == str(event.public_id)
    assert row.metadata["changes"] == {"mode": {"before": "open", "after": "invite_only"}}
    # It shows up in the event's configuration history like every other setting change.
    history = client.get(
        f"/api/v1/audit/workspaces/{workspace.public_id}/events/{event.public_id}/config-history/"
    )
    if history.status_code == 200:
        assert any(e["action"] == "registration.settings_updated" for e in history.json())
    # A failed change leaves no record.
    before = AuditEvent.objects.count()
    assert client.put(url, data={"capacity": 0}, content_type="application/json").status_code == 400
    assert AuditEvent.objects.count() == before
