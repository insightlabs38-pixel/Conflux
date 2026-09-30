"""PD-F001-B01-T04: modules follow choice or content, are never lost, never authorization."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from eventconfig.models import EventModuleSetting
from events.models import Event, EventStatus
from integrations.models import WebhookSubscription
from onsite.models import Location, LocationKind
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

OPTIONAL = {
    "eligibility_review",
    "onsite",
    "integrations",
    "community_voting",
    "mentorship",
    "public_page",
}


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Mods", slug="mods")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="A", slug="a")
    return workspace, event, client_for(organizer), client_for(judge)


def listing(client, workspace, event=None):
    suffix = f"?event={event}" if event else ""
    return client.get(f"/api/v1/workspaces/{workspace.public_id}/modules/{suffix}")


def by_key(response):
    return {m["key"]: m for m in response.json()["modules"]}


def toggle(client, workspace, event, key, enabled):
    return client.patch(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/modules/{key}/",
        data={"enabled": enabled},
        content_type="application/json",
    )


def test_a_new_event_offers_no_optional_module_and_a_legacy_event_loses_nothing():
    workspace, event, organizer, _ = setup()
    body = listing(organizer, workspace, event.public_id).json()
    assert (body["scope"], body["event"]) == ("event", str(event.public_id))
    assert {m["key"] for m in body["modules"]} == OPTIONAL
    assert all(
        not m["enabled"] and not m["in_use"] and m["explicit"] is None for m in body["modules"]
    )

    # An event that already has on-site content (no setting was ever written) stays enabled.
    Location.objects.create(event=event, kind=LocationKind.ROOM, name="Hall")
    onsite = by_key(listing(organizer, workspace, event.public_id))["onsite"]
    assert onsite["enabled"] and onsite["in_use"] and onsite["explicit"] is None
    assert not onsite["can_disable"] and "already has content" in onsite["reason"]
    assert EventModuleSetting.objects.count() == 0


def test_enable_and_disable_are_explicit_audited_and_reversible():
    workspace, event, organizer, _ = setup()
    response = toggle(organizer, workspace, event, "mentorship", True)
    assert response.status_code == 200, response.content
    mentorship = by_key(response)["mentorship"]
    assert mentorship["enabled"] and not mentorship["in_use"] and mentorship["explicit"] is True
    assert mentorship["can_disable"]
    assert toggle(organizer, workspace, event, "mentorship", True).status_code == 200  # idempotent

    off = toggle(organizer, workspace, event, "mentorship", False)
    assert off.status_code == 200
    assert (
        not by_key(off)["mentorship"]["enabled"] and by_key(off)["mentorship"]["explicit"] is False
    )
    setting = EventModuleSetting.objects.get(event=event, module="mentorship")
    assert setting.enabled is False and setting.changed_by.username == "org"
    actions = list(
        AuditEvent.objects.filter(target_id=str(event.public_id)).values_list("action", flat=True)
    )
    assert (
        actions.count("event.module_enabled") == 2 and actions.count("event.module_disabled") == 1
    )


def test_a_module_with_content_cannot_be_disabled_and_nothing_is_written():
    workspace, event, organizer, _ = setup()
    Location.objects.create(event=event, kind=LocationKind.ROOM, name="Hall")
    response = toggle(organizer, workspace, event, "onsite", False)
    assert response.status_code == 400
    assert "already has content" in str(response.json())
    assert not EventModuleSetting.objects.exists()
    assert not AuditEvent.objects.filter(action="event.module_disabled").exists()
    assert Location.objects.filter(event=event).count() == 1


def test_unknown_module_and_invalid_body_are_rejected():
    workspace, event, organizer, _ = setup()
    assert toggle(organizer, workspace, event, "telepathy", True).status_code == 400
    bad = organizer.patch(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/modules/onsite/",
        data={"enabled": "maybe"},
        content_type="application/json",
    )
    assert bad.status_code == 400
    assert not EventModuleSetting.objects.exists()


def test_archived_events_cannot_change_modules():
    workspace, event, organizer, _ = setup()
    event.status = EventStatus.ARCHIVED
    event.save(update_fields=["status"])
    assert toggle(organizer, workspace, event, "onsite", True).status_code == 400


def test_only_organizers_of_the_workspace_may_read_or_change_modules():
    workspace, event, organizer, judge = setup()
    assert listing(judge, workspace).status_code == 403
    assert toggle(judge, workspace, event, "onsite", True).status_code == 403
    assert listing(Client(), workspace).status_code in (401, 403)

    stranger = User.objects.create_user(username="str", password="unused")
    other = Workspace.objects.create(name="Other", slug="other")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert listing(outsider, workspace).status_code == 403
    assert toggle(outsider, workspace, event, "onsite", True).status_code == 403
    # An organizer of another workspace cannot reach this event through their own workspace either.
    assert toggle(outsider, other, event, "onsite", True).status_code == 404
    assert not EventModuleSetting.objects.exists()


def test_workspace_union_and_per_event_views():
    workspace, event, organizer, _ = setup()
    second = Event.objects.create(workspace=workspace, name="B", slug="b")
    toggle(organizer, workspace, event, "mentorship", True)
    Location.objects.create(event=second, kind=LocationKind.ROOM, name="Hall")

    union = by_key(listing(organizer, workspace))
    assert union["mentorship"]["enabled"] and union["onsite"]["enabled"]
    assert not union["integrations"]["enabled"]
    assert listing(organizer, workspace).json()["scope"] == "workspace"

    first = by_key(listing(organizer, workspace, event.public_id))
    assert first["mentorship"]["enabled"] and not first["onsite"]["enabled"]
    only_second = by_key(listing(organizer, workspace, second.public_id))
    assert only_second["onsite"]["enabled"] and not only_second["mentorship"]["enabled"]


def test_unknown_malformed_and_foreign_event_ids_fall_back_to_the_union_without_leaking():
    workspace, event, organizer, _ = setup()
    other = Workspace.objects.create(name="Other", slug="other")
    foreign = Event.objects.create(workspace=other, name="F", slug="f")
    Location.objects.create(event=foreign, kind=LocationKind.ROOM, name="Secret hall")
    for requested in ("not-a-uuid", "00000000-0000-0000-0000-000000000000", foreign.public_id):
        body = listing(organizer, workspace, requested).json()
        assert body["scope"] == "workspace" and body["event"] is None
        assert not by_key(listing(organizer, workspace, requested))["onsite"]["enabled"]


def test_a_workspace_wide_webhook_counts_for_the_union_not_for_one_event():
    workspace, event, organizer, _ = setup()
    WebhookSubscription.objects.create(
        workspace=workspace, event=None, url="https://example.com/hook", event_types=["*"]
    )
    assert by_key(listing(organizer, workspace))["integrations"]["in_use"]
    assert not by_key(listing(organizer, workspace, event.public_id))["integrations"]["in_use"]


def test_every_module_says_where_its_tools_live_and_deliberation_is_core():
    workspace, event, organizer, _ = setup()
    modules = by_key(listing(organizer, workspace, event.public_id))
    assert "deliberation" not in modules  # finalizing winners goes through it: core, not optional
    assert all(m["home"]["destination"] for m in modules.values())
    assert modules["community_voting"]["home"] == {
        "destination": "judging",
        "section": "CommunityVotingBuilder",
    }
