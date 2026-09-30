"""PD-F001-B01-T01: creating an event takes a name, a format and a few base decisions."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent, DomainEvent
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

START = "2027-03-05T09:00:00Z"


def setup(role=Role.ORGANIZER):
    user = User.objects.create_user(username="owner", password="unused")
    workspace = Workspace.objects.create(name="Create", slug="create")
    Membership.objects.create(user=user, workspace=workspace, role=role)
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    root = f"/api/v1/workspaces/{workspace.public_id}/"
    return workspace, client, root


def post(client, url, **body):
    return client.post(url, data=body, content_type="application/json")


def test_a_name_and_format_are_enough_and_the_address_is_derived_and_unique():
    workspace, client, root = setup()
    url = root + "event-templates/library/hackathon/instantiate/"
    first = post(client, url, name="Spring Hack 2027!")
    assert first.status_code == 201, first.content
    assert first.json()["slug"] == "spring-hack-2027"
    second = post(client, url, name="Spring Hack 2027!")
    assert second.json()["slug"] == "spring-hack-2027-2"
    third = post(client, url, name="???")  # nothing slug-able in the name
    assert third.json()["slug"] == "event"
    assert Event.objects.filter(workspace=workspace).count() == 3


def test_a_chosen_address_is_kept_and_a_taken_one_is_refused_with_a_reason():
    workspace, client, root = setup()
    url = root + "event-templates/library/hackathon/instantiate/"
    assert post(client, url, name="One", slug="my-address").json()["slug"] == "my-address"
    clash = post(client, url, name="Two", slug="my-address")
    assert clash.status_code == 400 and "slug" in str(clash.json()).lower()
    assert Event.objects.filter(workspace=workspace).count() == 1


def test_the_base_decisions_are_applied_and_visibility_defaults_to_private():
    workspace, client, root = setup()
    url = root + "event-templates/library/science_fair/instantiate/"
    private = post(client, url, name="Private")
    assert Event.objects.get(slug="private").is_public is False
    assert private.status_code == 201
    public = post(
        client,
        url,
        name="Public",
        is_public=True,
        starts_at=START,
        timezone="Europe/Berlin",
        registration_mode="invite_only",
        min_team_size=2,
        max_team_size=3,
    )
    assert public.status_code == 201, public.content
    event = Event.objects.get(slug="public")
    assert event.is_public is True and event.timezone == "Europe/Berlin"
    assert event.starts_at is not None and event.ends_at is not None
    assert event.registration_settings.mode == "invite_only"
    assert (event.eligibility_rules.min_team_size, event.eligibility_rules.max_team_size) == (2, 3)


def test_creation_audit_records_what_was_chosen_and_whether_the_address_was_derived():
    workspace, client, root = setup()
    url = root + "event-templates/library/hackathon/instantiate/"
    post(client, url, name="Audited", timezone="UTC", min_team_size=1)
    audit = AuditEvent.objects.get(action="event_template.library_instantiated")
    assert audit.workspace == workspace
    domain = DomainEvent.objects.get(event_type="event_template.library_instantiated")
    assert domain.payload["slug_derived"] is True
    assert domain.payload["chosen"] == ["min_team_size", "timezone"]
    assert domain.payload["template"] == "hackathon"


def test_a_blank_event_also_derives_its_address():
    workspace, client, root = setup()
    created = post(client, root + "events/", name="By Hand")
    assert created.status_code == 201, created.content
    assert created.json()["slug"] == "by-hand"
    explicit = post(client, root + "events/", name="Other", slug="chosen")
    assert explicit.json()["slug"] == "chosen"
    assert post(client, root + "events/", name="").status_code == 400


def test_only_organizers_create_events_from_a_format():
    _, client, root = setup(role=Role.JUDGE)
    url = root + "event-templates/library/hackathon/instantiate/"
    assert post(client, url, name="Nope").status_code == 403
    assert Client().post(url, data={"name": "x"}, content_type="application/json").status_code in (
        401,
        403,
    )
