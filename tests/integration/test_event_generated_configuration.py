"""PD-F001-B02-T01: generated configuration states only what is necessary."""

import json

import pytest
import yaml
from accounts.models import Session, User
from django.test import Client
from eventconfig.registry import SPECS
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup(role=Role.ORGANIZER):
    user = User.objects.create_user(username="org", password="unused")
    workspace = Workspace.objects.create(name="Gen", slug="gen")
    Membership.objects.create(user=user, workspace=workspace, role=role)
    client = client_for(user)
    root = f"/api/v1/workspaces/{workspace.public_id}/"
    return workspace, client, root


def create(client, root, name="Spring", key="hackathon", **body):
    response = client.post(
        root + f"event-templates/library/{key}/instantiate/",
        data={"name": name, **body},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return Event.objects.get(public_id=response.json()["public_id"])


def generated(client, root, event):
    response = client.get(root + f"events/{event.public_id}/configuration/generated/")
    assert response.status_code == 200, response.content
    return response.json()


def keys(entries):
    return {e["key"] for e in entries}


def test_a_fresh_event_states_only_what_the_organizer_gave():
    _, client, root = setup()
    event = create(client, root, starts_at="2027-03-05T09:00:00Z")
    body = generated(client, root, event)
    # Name and dates are the organizer's; nothing else needs saying.
    assert keys(body["explicit"]) == {"event.name", "event.starts_at", "event.ends_at"}
    assert {e["reason"] for e in body["explicit"]} == {"organizer"}
    assert body["document"]["format"] == "hackathon@1"
    assert set(body["document"]["settings"]) == keys(body["explicit"])
    # What the format supplies is listed for reading but never stated.
    inherited = {e["key"]: e for e in body["inherited"]}
    assert inherited["registration.mode"]["value"] == "open"
    assert inherited["registration.mode"]["origin"] == "preset"
    assert inherited["team.max_size"]["value"] == 5
    assert keys(body["derived"]) == {"workflow.source", "dates.duration_hours"}
    assert not keys(body["inherited"]) & keys(body["explicit"])


def test_a_changed_value_is_stated_with_what_it_started_as_and_how_to_write_it():
    _, client, root = setup()
    event = create(client, root, registration_mode="invite_only", max_team_size=3)
    body = generated(client, root, event)
    explicit = {e["key"]: e for e in body["explicit"]}
    assert explicit["registration.mode"]["reason"] == "changed"
    assert explicit["registration.mode"]["value"] == "invite_only"
    assert explicit["registration.mode"]["baseline"] == "open"
    assert explicit["registration.mode"]["origin"] == "preset"
    assert explicit["registration.mode"]["write"]["field"] == "mode"
    assert explicit["team.max_size"]["baseline"] == 5
    # A value back at the format's own value is no longer necessary.
    fixed = client.put(
        root + f"events/{event.public_id}/registration-settings/",
        data={"mode": "open"},
        content_type="application/json",
    )
    assert fixed.status_code == 200, fixed.content
    assert "registration.mode" not in keys(generated(client, root, event)["explicit"])


def test_the_text_is_valid_yaml_that_matches_the_document_and_explains_the_rest():
    _, client, root = setup()
    event = create(client, root, registration_mode="invite_only", name="Spring: Hack #1")
    body = generated(client, root, event)
    parsed = yaml.safe_load(body["text"])
    assert parsed == {"format": "hackathon@1", "settings": body["document"]["settings"]}
    text = body["text"]
    assert "# Inherited, not stated" in text and "#   team.min_size: 1  # preset" in text
    assert 'registration.mode: "invite_only"  # changed; the format uses "open"' in text
    assert "# Derived, computed and never stated:" in text
    assert "# Not set:" in text and "#   event.starts_at" in text


def test_an_event_without_a_format_is_stated_against_the_registry_defaults():
    workspace, client, root = setup()
    event = Event.objects.create(workspace=workspace, name="By hand", slug="by-hand")
    body = generated(client, root, event)
    assert body["preset"] is None and body["document"]["format"] is None
    assert keys(body["explicit"]) == {"event.name"}
    assert all(e["origin"] == "default" for e in body["inherited"])
    assert yaml.safe_load(body["text"])["format"] == "none"
    # Changing a default makes it explicit, relative to the default.
    changed = client.patch(
        root + f"events/{event.public_id}/",
        data={"is_public": True},
        content_type="application/json",
    )
    assert changed.status_code == 200
    explicit = {e["key"]: e for e in generated(client, root, event)["explicit"]}
    assert explicit["event.is_public"]["origin"] == "default"
    assert explicit["event.is_public"]["baseline"] is False


def test_every_registry_setting_is_accounted_for_exactly_once():
    _, client, root = setup()
    event = create(client, root, registration_mode="application", starts_at="2027-03-05T09:00:00Z")
    body = generated(client, root, event)
    seen = [
        *(e["key"] for e in body["explicit"]),
        *(e["key"] for e in body["inherited"]),
        *(e["key"] for e in body["derived"]),
        *body["unset"],
    ]
    assert sorted(seen) == sorted(spec.key for spec in SPECS)


def test_stating_only_the_explicit_values_reproduces_the_event():
    """Sufficiency: apply just the stated values to a new event of the same format."""
    _, client, root = setup()
    source = create(
        client,
        root,
        name="Original",
        registration_mode="application",
        min_team_size=2,
        max_team_size=4,
        starts_at="2027-03-05T09:00:00Z",
    )
    for write in (
        ("registration-settings/", "PUT", {"capacity": 40, "waitlist_enabled": True}),
        ("", "PATCH", {"description": "Hand-written", "is_public": True}),
    ):
        path, method, payload = write
        response = client.generic(
            method,
            root + f"events/{source.public_id}/{path}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
    body = generated(client, root, source)
    assert {"registration.capacity", "event.description", "event.is_public"} <= keys(
        body["explicit"]
    )

    target = create(client, root, name="Copy", slug="copy")
    for entry in body["explicit"]:
        write = entry["write"]
        url = "/api/v1/" + write["path"].format(
            workspace=target.workspace.public_id, event=target.public_id
        )
        payload = {write["field"]: entry["value"]}
        if write["body"] == "whole":
            current = client.get(url).json()
            current.pop("updated_at", None)
            payload = {**current, **payload}
        response = client.generic(
            write["method"], url, data=json.dumps(payload), content_type="application/json"
        )
        assert response.status_code == 200, (entry["key"], response.content)

    again = generated(client, root, target)
    assert again["document"] == body["document"]
    assert {e["key"]: e["value"] for e in again["inherited"]} == {
        e["key"]: e["value"] for e in body["inherited"]
    }


def test_generated_configuration_is_organizer_only_and_tenant_scoped():
    workspace, client, root = setup()
    event = create(client, root)
    url = root + f"events/{event.public_id}/configuration/generated/"
    assert Client().get(url).status_code in (401, 403)
    judge = User.objects.create_user(username="jdg", password="unused")
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    assert client_for(judge).get(url).status_code == 403
    other = Workspace.objects.create(name="Other", slug="other")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert outsider.get(url).status_code == 403
    cross = (
        f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/configuration/generated/"
    )
    assert outsider.get(cross).status_code == 404
