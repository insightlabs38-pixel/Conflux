"""PD-F001-B01-T08: defaults, baselines and derived values are queryable from one registry."""

from datetime import UTC, datetime

import pytest
from accounts.models import Session, User
from django.test import Client
from django.urls import resolve
from eligibility.models import EligibilityRules
from eventconfig.presets import PRESETS, baseline
from eventconfig.registry import BY_KEY, SPECS
from events.models import Event, EventRegistrationSettings, EventStatus
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

START = datetime(2027, 3, 5, 9, 0, tzinfo=UTC)
UUID = "00000000-0000-0000-0000-000000000000"


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Config", slug="config")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    return workspace, client_for(organizer), client_for(judge)


def preset_event(client, workspace, key="hackathon", **body):
    response = client.post(
        f"/api/v1/workspaces/{workspace.public_id}/event-templates/library/{key}/instantiate/",
        data={"name": "Spring", "slug": "spring", **body},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return Event.objects.get(workspace=workspace, slug="spring")


def configuration(client, workspace, event, query=""):
    return client.get(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/configuration/{query}"
    )


def entries(response):
    return {e["key"]: e for e in response.json()["settings"]}


def test_the_registry_is_well_formed_and_every_write_target_exists():
    assert len({s.key for s in SPECS}) == len(SPECS)
    for spec in SPECS:
        assert spec.tier in ("base", "advanced", "expert")
        assert spec.schema.get("type") is not None
        if spec.derived:
            assert spec.write is None
            continue
        assert spec.write and spec.write.field
        # The documented write is a real route, so automation can call it as described.
        path = "/api/v1/" + spec.write.path.format(workspace=UUID, event=UUID)
        assert resolve(path), spec.key


def test_a_preset_event_reports_where_each_value_comes_from():
    workspace, client, _ = setup()
    event = preset_event(client, workspace, starts_at=START.isoformat(), timezone="Europe/Berlin")
    response = configuration(client, workspace, event)
    assert response.status_code == 200
    body = response.json()
    assert body["preset"] == {"key": "hackathon", "version": 1, "label": "Hackathon"}
    settings = entries(response)
    preset = PRESETS["hackathon"]

    assert settings["registration.mode"]["value"] == "open"
    assert settings["registration.mode"]["source"] == "preset"
    assert settings["registration.mode"]["baseline"] == "open"
    assert settings["team.max_size"]["value"] == preset.max_team_size
    assert settings["team.max_size"]["source"] == "preset"
    assert settings["submission.required_artifact_kinds"]["value"] == ["repository"]
    # Values only the organizer knows are "set" (or "unset"), never "default" or "overridden".
    assert settings["event.name"]["source"] == "set"
    assert settings["event.starts_at"]["source"] == "set"
    assert settings["event.is_public"]["source"] == "default"
    # Derived values are computed, have no write, and follow the dates.
    duration = settings["dates.duration_hours"]
    assert duration["source"] == "derived" and duration["write"] is None
    assert duration["value"] == baseline(preset)["dates.duration_hours"] == 48.0
    assert not duration["editable"]
    # Every writable value says how to write it.
    assert settings["registration.mode"]["write"] == {
        "method": "PUT",
        "path": "workspaces/{workspace}/events/{event}/registration-settings/",
        "field": "mode",
        "body": "partial",
    }
    assert settings["team.min_size"]["write"]["body"] == "whole"
    assert (
        settings["registration.mode"]["editable"] and settings["registration.mode"]["lock"] is None
    )


def test_overriding_through_the_domain_endpoint_is_reflected_and_reversible():
    workspace, client, _ = setup()
    event = preset_event(client, workspace)
    url = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/registration-settings/"
    )
    assert (
        entries(configuration(client, workspace, event))["registration.mode"]["source"] == "preset"
    )

    assert (
        client.put(url, data={"mode": "invite_only"}, content_type="application/json").status_code
        == 200
    )
    mode = entries(configuration(client, workspace, event))["registration.mode"]
    assert (mode["value"], mode["source"], mode["baseline"]) == (
        "invite_only",
        "overridden",
        "open",
    )

    assert (
        client.put(url, data={"mode": "open"}, content_type="application/json").status_code == 200
    )
    assert (
        entries(configuration(client, workspace, event))["registration.mode"]["source"] == "preset"
    )
    # Filtering by source finds exactly what was changed.
    client.put(url, data={"waitlist_enabled": True}, content_type="application/json")
    changed = configuration(client, workspace, event, "?source=overridden")
    assert [e["key"] for e in changed.json()["settings"]] == ["registration.waitlist_enabled"]


def test_a_legacy_event_has_no_preset_and_reading_creates_nothing():
    workspace, client, _ = setup()
    event = Event.objects.create(workspace=workspace, name="Old", slug="old")
    response = configuration(client, workspace, event)
    body = response.json()
    assert body["preset"] is None
    settings = entries(response)
    assert settings["registration.mode"]["source"] == "default"
    assert (
        settings["team.min_size"]["value"] is None
        and settings["team.min_size"]["source"] == "default"
    )
    assert settings["event.starts_at"]["source"] == "unset"
    assert settings["dates.duration_hours"]["value"] is None
    # A read never writes: no lazily created registration or eligibility row appears.
    assert not EventRegistrationSettings.objects.filter(event=event).exists()
    assert not EligibilityRules.objects.filter(event=event).exists()


def test_filters_select_by_module_tier_source_and_key_prefix_and_reject_unknown_values():
    workspace, client, _ = setup()
    event = preset_event(client, workspace)

    def keys(query):
        body = configuration(client, workspace, event, query).json()
        return [e["key"] for e in body["settings"]]

    assert set(keys("?key=registration.")) == {
        "registration.mode",
        "registration.capacity",
        "registration.waitlist_enabled",
    }
    assert keys("?module=eligibility_review") == ["eligibility.require_clearance"]
    assert all(BY_KEY[k].tier == "base" for k in keys("?tier=base"))
    assert "dates.duration_hours" in keys("?source=derived")
    assert keys("?tier=base&key=team.") == ["team.min_size", "team.max_size"]
    assert configuration(client, workspace, event, "?tier=secret").status_code == 400
    assert configuration(client, workspace, event, "?source=whatever").status_code == 400


def test_an_archived_event_locks_every_writable_setting_with_a_reason():
    workspace, client, _ = setup()
    event = preset_event(client, workspace)
    event.status = EventStatus.ARCHIVED
    event.save(update_fields=["status"])
    settings = entries(configuration(client, workspace, event))
    writable = [e for e in settings.values() if e["write"]]
    assert writable and all(not e["editable"] for e in writable)
    assert all(e["lock"]["code"] == "event_archived" for e in writable)
    assert settings["dates.duration_hours"]["lock"] is None


def test_settings_of_a_module_that_is_off_say_so():
    workspace, client, _ = setup()
    event = preset_event(client, workspace)
    clearance = entries(configuration(client, workspace, event))["eligibility.require_clearance"]
    assert clearance["module"] == "eligibility_review" and clearance["module_enabled"] is False
    client.patch(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/modules/eligibility_review/",
        data={"enabled": True},
        content_type="application/json",
    )
    clearance = entries(configuration(client, workspace, event))["eligibility.require_clearance"]
    assert clearance["module_enabled"] is True


def test_configuration_is_organizer_only_and_tenant_scoped():
    workspace, client, judge = setup()
    event = preset_event(client, workspace)
    assert configuration(judge, workspace, event).status_code == 403
    assert configuration(Client(), workspace, event).status_code in (401, 403)
    other = Workspace.objects.create(name="Other", slug="other")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert configuration(outsider, workspace, event).status_code == 403
    assert configuration(outsider, other, event).status_code == 404
