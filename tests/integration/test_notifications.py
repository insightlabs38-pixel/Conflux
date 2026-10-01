"""PD-F002-B02-T04: notification preferences through one primitive and two adopters."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from communications import notifications as categories
from communications.models import Message, MessageRecipient
from communications.threads import notify_mentions
from core import notifications
from core.models import NotificationPreference
from django.core import mail
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import ValidationError
from test_communications_messages import fixture, messages_url
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ANNOUNCEMENT, MENTION, ESSENTIAL = categories.ANNOUNCEMENT, categories.MENTION, categories.ESSENTIAL
EMAIL, INBOX = notifications.EMAIL, notifications.INBOX


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world():
    workspace, event, organizer, with_email, no_email = fixture()
    other = Workspace.objects.create(name="Other", slug="other")
    Membership.objects.create(user=with_email, workspace=other, role=Role.PARTICIPANT)
    outsider = User.objects.create_user(username="outsider", password="unused")
    return {
        "workspace": workspace,
        "event": event,
        "organizer": organizer,
        "ada": with_email,
        "bob": no_email,
        "other": other,
        "outsider": outsider,
    }


# --- the rule ---------------------------------------------------------------------------------


def test_without_a_choice_everyone_gets_the_category_default(world):
    ada, workspace = world["ada"], world["workspace"]
    assert notifications.wants(ada, workspace, ANNOUNCEMENT, EMAIL) is True
    assert notifications.wants(ada, workspace, MENTION, EMAIL) is False
    assert notifications.wants(ada, workspace, ESSENTIAL, EMAIL) is True
    assert all(notifications.wants(ada, workspace, key, INBOX) for key in (ANNOUNCEMENT, MENTION))


def test_a_choice_changes_only_the_optional_email_in_that_workspace(world):
    ada, workspace, other = world["ada"], world["workspace"], world["other"]
    assert notifications.set_preference(ada, workspace, ANNOUNCEMENT, EMAIL, False) is True
    assert notifications.set_preference(ada, workspace, MENTION, EMAIL, True) is True
    assert notifications.wants(ada, workspace, ANNOUNCEMENT, EMAIL) is False
    assert notifications.wants(ada, workspace, MENTION, EMAIL) is True
    assert notifications.wants(ada, other, ANNOUNCEMENT, EMAIL) is True  # another workspace
    assert notifications.wants(ada, workspace, ANNOUNCEMENT, INBOX) is True
    assert notifications.wants(world["bob"], workspace, ANNOUNCEMENT, EMAIL) is True  # someone else


def test_the_inbox_and_essential_notices_cannot_be_turned_off_even_by_a_stored_row(world):
    ada, workspace = world["ada"], world["workspace"]
    for key, channel in ((ANNOUNCEMENT, INBOX), (ESSENTIAL, EMAIL), (ESSENTIAL, INBOX)):
        with pytest.raises(ValidationError) as caught:
            notifications.set_preference(ada, workspace, key, channel, False)
        assert "channel" in caught.value.detail
        # Even a row written around the API (an import, a bug) changes nothing.
        NotificationPreference.objects.create(
            user=ada, workspace=workspace, category=key, channel=channel, enabled=False
        )
        assert notifications.wants(ada, workspace, key, channel) is True


def test_a_choice_is_idempotent_and_audited_with_before_and_after_only(world):
    ada, workspace = world["ada"], world["workspace"]
    audits = AuditEvent.objects.filter(action="notification_preference.changed")
    assert notifications.set_preference(ada, workspace, ANNOUNCEMENT, EMAIL, False) is True
    assert notifications.set_preference(ada, workspace, ANNOUNCEMENT, EMAIL, False) is False
    assert audits.count() == 1
    assert notifications.set_preference(ada, workspace, ANNOUNCEMENT, EMAIL, True) is True
    first, second = audits.order_by("id")
    assert first.metadata == {
        "category": ANNOUNCEMENT, "channel": EMAIL, "before": True, "after": False,
    }  # fmt: skip
    assert second.metadata["before"] is False and second.metadata["after"] is True
    assert first.actor == ada and first.workspace == workspace
    assert NotificationPreference.objects.filter(user=ada).count() == 1


@pytest.mark.parametrize(
    "category, channel, field",
    [("nope", EMAIL, "category"), (ANNOUNCEMENT, "sms", "channel")],
)
def test_unknown_categories_and_channels_are_refused(world, category, channel, field):
    with pytest.raises(ValidationError) as caught:
        notifications.set_preference(world["ada"], world["workspace"], category, channel, True)
    assert field in caught.value.detail


def test_delivery_code_asking_about_an_unregistered_category_fails_loudly(world):
    with pytest.raises(KeyError):
        notifications.wants(world["ada"], world["workspace"], "nope", EMAIL)
    with pytest.raises(KeyError):
        notifications.wants(world["ada"], world["workspace"], ANNOUNCEMENT, "sms")


def test_wanting_is_one_query_and_keeps_the_order(world):
    people = [world["bob"], world["ada"], world["organizer"]]
    notifications.set_preference(world["ada"], world["workspace"], ANNOUNCEMENT, EMAIL, False)
    with CaptureQueriesContext(connection) as queries:
        found = notifications.wanting(people, world["workspace"], ANNOUNCEMENT, EMAIL)
    assert found == [world["bob"], world["organizer"]] and len(queries) == 1
    with CaptureQueriesContext(connection) as queries:
        assert notifications.wanting(people, world["workspace"], ESSENTIAL, EMAIL) == people
    assert len(queries) == 0


def test_categories_are_registered_once_and_not_redefined():
    mine = notifications.Category("test_toy", "Toy", "A toy category.", email_default=False)
    notifications.register_category(mine)
    try:
        notifications.register_category(mine)
        with pytest.raises(ValueError):
            notifications.register_category(notifications.Category("test_toy", "Other", "x"))
    finally:
        notifications.CATEGORIES.pop("test_toy")


def test_a_feature_outside_communications_uses_only_the_public_functions(world):
    """An independent consumer: registers its own category and asks the one question."""
    notifications.register_category(
        notifications.Category("test_digest", "Digest", "A weekly digest.", email_default=False)
    )
    try:
        ada, workspace = world["ada"], world["workspace"]
        assert notifications.wanting([ada], workspace, "test_digest", EMAIL) == []
        notifications.set_preference(ada, workspace, "test_digest", EMAIL, True)
        assert notifications.wanting([ada], workspace, "test_digest", EMAIL) == [ada]
        listed = {c["category"]: c for c in notifications.describe(ada, workspace)}
        assert listed["test_digest"]["channels"][1]["enabled"] is True
    finally:
        notifications.CATEGORIES.pop("test_digest")


# --- the person's own settings endpoint -------------------------------------------------------


def url(workspace):
    return f"/api/v1/workspaces/{workspace.public_id}/notification-preferences/"


def put(world, who, **body):
    return client_for(world[who]).put(
        url(world["workspace"]), data=body, content_type="application/json"
    )


def test_a_person_reads_every_category_with_its_channels(world):
    body = client_for(world["ada"]).get(url(world["workspace"])).json()
    rows = {c["category"]: c for c in body["categories"]}
    assert list(rows) == [ANNOUNCEMENT, MENTION, ESSENTIAL]  # optional first, essential last
    announcement = {c["channel"]: c for c in rows[ANNOUNCEMENT]["channels"]}
    assert announcement[INBOX] == {
        "channel": "inbox", "label": "In-app inbox", "enabled": True,
        "locked": True, "default": True, "chosen": False,
    }  # fmt: skip
    assert announcement[EMAIL]["enabled"] is True and announcement[EMAIL]["locked"] is False
    assert {c["channel"]: c["enabled"] for c in rows[MENTION]["channels"]} == {
        INBOX: True, EMAIL: False,
    }  # fmt: skip
    assert rows[ESSENTIAL]["essential"] is True
    assert all(c["locked"] and c["enabled"] for c in rows[ESSENTIAL]["channels"])


def test_a_person_changes_only_their_own_choice_and_gets_the_new_list(world):
    response = put(world, "ada", category=ANNOUNCEMENT, channel=EMAIL, enabled=False)
    assert response.status_code == 200
    row = {c["category"]: c for c in response.json()["categories"]}[ANNOUNCEMENT]
    email = {c["channel"]: c for c in row["channels"]}[EMAIL]
    assert email["enabled"] is False and email["chosen"] is True and email["default"] is True
    # Nobody else's choices moved, and there is no way to name another person.
    bob = client_for(world["bob"]).get(url(world["workspace"])).json()
    assert {c["category"]: c for c in bob["categories"]}[ANNOUNCEMENT]["channels"][1]["enabled"]
    assert NotificationPreference.objects.count() == 1
    assert put(world, "ada", category=ANNOUNCEMENT, channel=EMAIL, enabled=False).status_code == 200
    assert NotificationPreference.objects.count() == 1
    assert AuditEvent.objects.filter(action="notification_preference.changed").count() == 1


def test_choices_that_may_not_change_or_make_no_sense_are_refused_with_the_field(world):
    locked = put(world, "ada", category=ESSENTIAL, channel=EMAIL, enabled=False)
    assert locked.status_code == 400 and "always delivered" in locked.json()["channel"][0]
    inbox = put(world, "ada", category=ANNOUNCEMENT, channel=INBOX, enabled=False)
    assert inbox.status_code == 400 and "always kept" in inbox.json()["channel"][0]
    assert put(world, "ada", category="x", channel=EMAIL, enabled=True).json().keys() == {
        "category"
    }
    bad = put(world, "ada", category=5, channel=None, enabled="yes")
    assert bad.status_code == 400 and set(bad.json()) == {"category", "channel", "enabled"}
    assert NotificationPreference.objects.count() == 0


def test_only_workspace_members_have_preferences_there(world):
    assert (
        put(world, "outsider", category=ANNOUNCEMENT, channel=EMAIL, enabled=False).status_code
        == 403
    )
    assert client_for(world["outsider"]).get(url(world["workspace"])).status_code == 403
    assert Client().get(url(world["workspace"])).status_code in (401, 403)
    assert NotificationPreference.objects.count() == 0


# --- adopter 1: broadcasts and reminders ------------------------------------------------------


def send(world):
    return client_for(world["organizer"]).post(
        messages_url(world["workspace"], world["event"]),
        {"subject": "Hello", "body": "Body", "audience_kind": "all_participants"},
        content_type="application/json",
    )


def test_a_broadcast_still_emails_everyone_who_has_not_chosen(world):
    assert send(world).status_code == 201
    assert [m.to for m in mail.outbox] == [["participant@example.com"]]


def test_an_opted_out_person_keeps_the_inbox_copy_but_gets_no_email(world):
    notifications.set_preference(world["ada"], world["workspace"], ANNOUNCEMENT, EMAIL, False)
    response = send(world)
    assert response.status_code == 201 and response.json()["recipient_count"] == 2
    assert mail.outbox == []
    row = MessageRecipient.objects.get(
        message__public_id=response.json()["public_id"], user=world["ada"]
    )
    assert row.email_sent_at is None and row.email_error == "" and row.read_at is None
    inbox = client_for(world["ada"]).get(
        f"/api/v1/workspaces/{world['workspace'].public_id}/inbox/"
    )
    assert [m["subject"] for m in inbox.json()] == ["Hello"]
    # Opting back in restores the email for the next message.
    notifications.set_preference(world["ada"], world["workspace"], ANNOUNCEMENT, EMAIL, True)
    send(world)
    assert len(mail.outbox) == 1


def test_a_choice_in_another_workspace_does_not_stop_this_workspaces_email(world):
    notifications.set_preference(world["ada"], world["other"], ANNOUNCEMENT, EMAIL, False)
    send(world)
    assert len(mail.outbox) == 1


# --- adopter 2: mention notices ---------------------------------------------------------------


def test_a_mention_notice_is_inbox_only_until_the_person_asks_for_email(world):
    event, ada, bob = world["event"], world["ada"], world["bob"]
    bob.email = "bob@example.com"
    bob.save()
    notifications.set_preference(ada, world["workspace"], MENTION, EMAIL, True)
    notify_mentions(event, world["organizer"], [ada, bob], "the application of @x")
    assert Message.objects.filter(audience_kind="thread_mention").count() == 1
    assert MessageRecipient.objects.filter(user__in=[ada, bob]).count() == 2  # inbox for both
    assert [m.to for m in mail.outbox] == [["participant@example.com"]]
    sent = mail.outbox[0]
    assert sent.subject == "@msg-organizer mentioned you"
    assert "In the application of @x" in sent.body and "comment" in sent.body
