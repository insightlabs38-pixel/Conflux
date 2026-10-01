"""PD-F002-B01-T07: threads with explicit audiences, through one primitive and two adopters."""

import uuid
from types import SimpleNamespace

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from communications.models import Message, MessageRecipient
from core import threads
from core.models import Thread, ThreadComment
from django.test import Client
from events.models import Event, EventApplication
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ITEM = SimpleNamespace(public_id=uuid.uuid4(), name="Widget")
TEAM = set()


def _any_member(user, workspace, event, subject):
    return bool(Membership.objects.filter(user=user, workspace=workspace).exists())


def _role(*roles):
    return lambda user, workspace, event, subject: Membership.objects.filter(
        user=user, workspace=workspace, role__in=roles
    ).exists()


def _team(user, workspace, event, subject):
    return user.username in TEAM


TOY = threads.ThreadSubject(
    key="test_item",
    label="Item",
    get=lambda event, sid: ITEM if str(ITEM.public_id) == str(sid) and event.slug == "e" else None,
    describe=lambda item: f"the item {item.name}",
    audiences={
        "organizers": threads.AudienceRule(_role(Role.ORGANIZER, Role.ADMIN)),
        "judges": threads.AudienceRule(_role(Role.JUDGE, Role.ORGANIZER)),
        "participants": threads.AudienceRule(_any_member),
        "project_team": threads.AudienceRule(_team),
        "public": threads.AudienceRule(can_read=lambda *a: True, can_post=_role(Role.ORGANIZER)),
    },
)


@pytest.fixture(autouse=True)
def subject():
    TEAM.clear()
    threads.register_subject(TOY)
    yield
    threads.SUBJECTS.pop("test_item", None)


def _client(user):
    c = Client()
    c.cookies["session"] = Session.issue(user).token
    return c


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    people = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("org2", Role.ORGANIZER),
        ("judge", Role.JUDGE),
        ("par", Role.PARTICIPANT),
        ("mate", Role.PARTICIPANT),
    ):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["out"] = User.objects.create_user(username="out", password="unused")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    return {
        "workspace": workspace,
        "event": event,
        "people": people,
        "client": {n: _client(u) for n, u in people.items()},
        "base": f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/",
    }


def url(w, audience="organizers", subject="test_item", sid=None):
    return w["base"] + f"threads/{subject}/{sid or ITEM.public_id}/{audience}/"


def say(w, who="org", body="Hello", audience="organizers", **extra):
    return w["client"][who].post(
        url(w, audience), data={"body": body, **extra}, content_type="application/json"
    )


def comment_url(w, comment_id):
    return w["base"] + f"thread-comments/{comment_id}/"


def test_the_first_comment_creates_the_thread_and_everyone_with_access_sees_it(world):
    empty = world["client"]["org"].get(url(world)).json()
    assert empty["comments"] == [] and empty["can_post"] is True and empty["total"] == 0
    assert empty["subject"] == {
        "type": "test_item",
        "id": str(ITEM.public_id),
        "label": "the item Widget",
    }
    assert not Thread.objects.exists()  # reading creates nothing

    posted = say(world, body="  First note  ")
    assert posted.status_code == 201
    assert posted.json()["body"] == "First note" and posted.json()["can_edit"] is True
    seen = world["client"]["org2"].get(url(world)).json()
    assert [c["body"] for c in seen["comments"]] == ["First note"]
    assert seen["comments"][0]["can_edit"] is False and seen["comments"][0]["can_remove"] is True
    assert Thread.objects.count() == 1
    assert AuditEvent.objects.filter(action="thread.comment_posted").count() == 1
    assert "First note" not in str(AuditEvent.objects.get(action="thread.comment_posted").metadata)


@pytest.mark.parametrize(
    "audience,readers,writers",
    [
        ("organizers", {"org", "org2"}, {"org", "org2"}),
        ("judges", {"judge", "org", "org2"}, {"judge", "org", "org2"}),
        (
            "participants",
            {"org", "org2", "judge", "par", "mate"},
            {"org", "org2", "judge", "par", "mate"},
        ),
        ("project_team", {"par", "mate"}, {"par", "mate"}),
        ("public", {"org", "org2", "judge", "par", "mate"}, {"org", "org2"}),
    ],
)
def test_each_audience_is_exactly_what_its_rule_says(world, audience, readers, writers):
    TEAM.update({"par", "mate"})
    for name in ("org", "org2", "judge", "par", "mate", "out"):
        got = world["client"][name].get(url(world, audience)).status_code
        # Not a member of the workspace: refused at the door, like every workspace endpoint.
        expected = 403 if name == "out" else 200 if name in readers else 404
        assert got == expected, (audience, name, got)
    for name in readers:
        wrote = say(world, name, audience=audience).status_code
        assert wrote == (201 if name in writers else 403), (audience, name, wrote)
    assert say(world, "out", audience=audience).status_code == 403


def test_a_reader_who_may_not_write_is_refused_clearly(world):
    # Every member may read the toy "public" audience, but only organizers write in it.
    forbidden = say(world, "mate", audience="public")
    assert forbidden.status_code == 403
    assert not ThreadComment.objects.exists()


def test_unknown_things_are_not_found_not_forbidden(world):
    c = world["client"]["org"]
    assert c.get(url(world, "nope")).status_code == 404
    assert c.get(url(world, subject="nope")).status_code == 404
    assert c.get(url(world, sid=uuid.uuid4())).status_code == 404
    assert c.get(url(world, sid="not-a-uuid")).status_code == 404
    other = Event.objects.create(workspace=world["workspace"], name="O", slug="o")
    foreign = world["base"].replace(str(world["event"].public_id), str(other.public_id))
    assert c.get(foreign + f"threads/test_item/{ITEM.public_id}/organizers/").status_code == 404


def test_comments_are_plain_text_within_bounds(world):
    assert say(world, body="   ").status_code == 400
    assert say(world, body="x" * 4001).status_code == 400
    assert say(world, body="x" * 4000).status_code == 201
    assert (
        world["client"]["org"]
        .post(url(world), data={"body": ["x"]}, content_type="application/json")
        .status_code
        == 400
    )
    html = say(world, body="<script>alert(1)</script> [x](javascript:y)").json()
    assert html["body"] == "<script>alert(1)</script> [x](javascript:y)"  # text, never markup


def test_replies_go_one_level_deep_and_stay_in_the_thread(world):
    top = say(world, body="top").json()
    reply = say(world, "org2", body="reply", parent=top["public_id"])
    assert reply.status_code == 201
    deeper = say(world, body="deeper", parent=reply.json()["public_id"])
    assert deeper.status_code == 400
    assert say(world, body="x", parent=str(uuid.uuid4())).status_code == 400
    other_thread = say(world, "judge", body="j", audience="judges").json()
    assert say(world, body="x", parent=other_thread["public_id"]).status_code == 400
    page = world["client"]["org"].get(url(world)).json()
    assert page["total"] == 1 and page["comments"][0]["replies"][0]["body"] == "reply"


def test_mentions_reach_only_people_who_can_read_and_never_carry_the_text(world):
    posted = say(world, body="Please look @org2 and @par and @ghost and @org itself")
    assert posted.status_code == 201
    assert posted.json()["mentions"] == [
        "org2"
    ]  # par cannot read; ghost does not exist; self ignored
    notice = Message.objects.get(audience_kind="thread_mention")
    assert [r.user.username for r in notice.recipients.all()] == ["org2"]
    assert notice.subject == "@org mentioned you" and "Please look" not in notice.body
    assert "the item Widget" in notice.body
    assert not MessageRecipient.objects.filter(user=world["people"]["par"]).exists()
    # The mentioned person finds it in their inbox; it is not in the organizers' sent list.
    inbox = world["client"]["org2"].get(f"/api/v1/workspaces/{world['workspace'].public_id}/inbox/")
    assert [m["subject"] for m in inbox.json()] == ["@org mentioned you"]
    sent = world["client"]["org"].get(world["base"] + "communications/messages/").json()
    assert all(m["audience_kind"] != "thread_mention" for m in sent)
    # More than ten distinct names: the rest stay plain text.
    many = " ".join(f"@u{i}" for i in range(15))
    assert say(world, body=many).json()["mentions"] == []


def test_the_author_edits_and_only_new_mentions_are_notified(world):
    comment = say(world, body="Hi @org2").json()
    assert Message.objects.filter(audience_kind="thread_mention").count() == 1
    edit = world["client"]["org"].patch(
        comment_url(world, comment["public_id"]),
        data={"body": "Hi @org2 and @judge"},
        content_type="application/json",
    )
    assert edit.status_code == 200 and edit.json()["edited"] is True
    assert sorted(edit.json()["mentions"]) == ["org2"]  # judge cannot read organizers
    judges = say(world, "judge", body="hello", audience="judges").json()
    again = world["client"]["judge"].patch(
        comment_url(world, judges["public_id"]),
        data={"body": "hello @org"},
        content_type="application/json",
    )
    assert again.json()["mentions"] == ["org"]
    assert Message.objects.filter(audience_kind="thread_mention").count() == 2
    assert (
        world["client"]["org2"]
        .patch(
            comment_url(world, comment["public_id"]),
            data={"body": "mine now"},
            content_type="application/json",
        )
        .status_code
        == 403
    )
    assert (
        world["client"]["par"]
        .patch(
            comment_url(world, comment["public_id"]),
            data={"body": "x"},
            content_type="application/json",
        )
        .status_code
        == 404
    )
    assert (
        world["client"]["org"]
        .patch(
            comment_url(world, comment["public_id"]),
            data={"body": " "},
            content_type="application/json",
        )
        .status_code
        == 400
    )


def test_removal_is_a_tombstone_that_erases_the_text_and_keeps_the_replies(world):
    top = say(world, body="Secret @org2").json()
    say(world, "org2", body="a reply", parent=top["public_id"])
    assert world["client"]["par"].delete(comment_url(world, top["public_id"])).status_code == 404
    removed = world["client"]["org2"].delete(comment_url(world, top["public_id"]))  # a moderator
    assert removed.status_code == 200 and removed.json()["removed"] is True
    row = ThreadComment.objects.get(public_id=top["public_id"])
    assert row.body == "" and row.removed_by.username == "org2" and not row.mentions.exists()
    page = world["client"]["org"].get(url(world)).json()["comments"][0]
    assert page["body"] == "" and page["removed"] and page["replies"][0]["body"] == "a reply"
    assert page["can_remove"] is False and page["can_edit"] is False
    assert world["client"]["org2"].delete(comment_url(world, top["public_id"])).status_code == 200
    assert AuditEvent.objects.filter(action="thread.comment_removed").count() == 1  # not repeated
    assert say(world, body="x", parent=top["public_id"]).status_code == 400
    assert (
        world["client"]["org"]
        .patch(
            comment_url(world, top["public_id"]),
            data={"body": "back"},
            content_type="application/json",
        )
        .status_code
        == 400
    )
    assert "Secret" not in str(list(AuditEvent.objects.values_list("metadata", flat=True)))


def test_an_author_can_remove_their_own_comment_in_a_team_thread(world):
    TEAM.update({"par", "mate"})
    mine = say(world, "par", audience="project_team").json()
    assert world["client"]["mate"].delete(comment_url(world, mine["public_id"])).status_code == 404
    assert world["client"]["par"].delete(comment_url(world, mine["public_id"])).status_code == 200
    # An organizer may moderate a thread they cannot read, by its id.
    other = say(world, "mate", audience="project_team").json()
    assert world["client"]["org"].delete(comment_url(world, other["public_id"])).status_code == 200


def test_an_archived_event_can_be_read_but_not_written(world):
    posted = say(world).json()
    world["event"].status = "archived"
    world["event"].save()
    assert world["client"]["org"].get(url(world)).status_code == 200
    assert say(world).status_code == 400
    assert (
        world["client"]["org"]
        .patch(
            comment_url(world, posted["public_id"]),
            data={"body": "x"},
            content_type="application/json",
        )
        .status_code
        == 400
    )
    assert world["client"]["org"].delete(comment_url(world, posted["public_id"])).status_code == 400


def test_a_thread_is_bounded_and_top_level_comments_page(world, monkeypatch):
    monkeypatch.setattr(threads, "MAX_COMMENTS", 3)
    for i in range(3):
        assert say(world, body=f"c{i}").status_code == 201
    assert say(world, body="one more").status_code == 400
    page = world["client"]["org"].get(url(world) + "?limit=2&offset=1").json()
    assert page["total"] == 3 and [c["body"] for c in page["comments"]] == ["c1", "c2"]
    assert world["client"]["org"].get(url(world) + "?limit=0").status_code == 400


def test_a_retried_post_with_the_same_key_posts_once(world):
    c = world["client"]["org"]
    first = c.post(
        url(world),
        data={"body": "once"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="k1",
    )
    again = c.post(
        url(world),
        data={"body": "once"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="k1",
    )
    assert first.status_code == again.status_code == 201
    assert first.json()["public_id"] == again.json()["public_id"]
    assert ThreadComment.objects.count() == 1


def test_registration_is_strict(world):
    with pytest.raises(ValueError):
        threads.register_subject(
            threads.ThreadSubject("test_item", "Other", TOY.get, TOY.describe, TOY.audiences)
        )
    threads.register_subject(TOY)  # the identical one is harmless
    for audiences in ({}, {"everyone": threads.AudienceRule(lambda *a: True)}):
        with pytest.raises(ValueError):
            threads.register_subject(
                threads.ThreadSubject("test_bad", "B", TOY.get, TOY.describe, audiences)
            )


def test_the_real_adopters_application_and_project_notes_are_organizer_only(world):
    application = EventApplication.objects.create(event=world["event"], user=world["people"]["par"])
    project = Project.objects.create(
        event=world["event"], name="Apollo", created_by=world["people"]["par"]
    )
    for subject, row, text in (
        ("application", application, "the application of @par"),
        ("project", project, "the project Apollo"),
    ):
        u = world["base"] + f"threads/{subject}/{row.public_id}/organizers/"
        assert world["client"]["org"].get(u).json()["subject"]["label"] == text
        posted = world["client"]["org"].post(
            u, data={"body": "Check this @org2"}, content_type="application/json"
        )
        assert posted.status_code == 201
        assert world["client"]["org2"].get(u).json()["comments"][0]["body"] == "Check this @org2"
        for outsider in ("par", "judge", "mate", "out"):
            assert world["client"][outsider].get(u).status_code in (403, 404)
        # Not offered to any other audience.
        assert world["client"]["org"].get(u.replace("organizers", "public")).status_code == 404
    notices = Message.objects.filter(audience_kind="thread_mention").order_by("id")
    assert [n.body.split(".")[0] for n in notices] == [
        "In the application of @par",
        "In the project Apollo",
    ]
    # A subject of another event is not reachable through this one.
    other = Event.objects.create(workspace=world["workspace"], name="O", slug="o")
    stray = Project.objects.create(event=other, name="Stray", created_by=world["people"]["par"])
    assert (
        world["client"]["org"]
        .get(world["base"] + f"threads/project/{stray.public_id}/organizers/")
        .status_code
        == 404
    )
