"""PD-F002-B01-T08: one derived timeline, advisory conflicts, writes through the domain."""

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from accounts.models import Session, User
from communications.models import Message, Reminder
from community.models import VotingPlan
from core import timeline
from django.test import Client
from events.models import Event, Track
from mentorship.models import OfficeHourSlot
from onsite.models import AgendaSession, Location
from policies.models import TemporalGate
from presentation.models import PublicationSchedule
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

UTC = ZoneInfo("UTC")


def at(day, hour, minute=0):
    return datetime(2027, 3, day, hour, minute, tzinfo=UTC)


def _client(user):
    c = Client()
    c.cookies["session"] = Session.issue(user).token
    return c


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("par", Role.PARTICIPANT), ("men", Role.MENTOR)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    event = Event.objects.create(
        workspace=workspace,
        name="E",
        slug="e",
        timezone="America/New_York",
        starts_at=at(6, 14),
        ends_at=at(8, 22),
    )
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    return {
        "workspace": workspace,
        "event": event,
        "people": people,
        "client": {n: _client(u) for n, u in people.items()},
        "base": base,
    }


def get(w, query="", who="org"):
    response = w["client"][who].get(w["base"] + "timeline/" + query)
    assert response.status_code == 200, response.content
    return response.json()


def keys(body):
    return [i["key"] for i in body["items"]]


def codes(body):
    return sorted(c["code"] for c in body["conflicts"])


def test_the_timeline_is_ordered_derived_and_in_the_event_zone(world):
    event = world["event"]
    TemporalGate.objects.create(
        event=event, name="Registration", opens_at=at(1, 12), closes_at=at(5, 12)
    )
    AgendaSession.objects.create(
        event=event, title="Opening", starts_at=at(6, 15), ends_at=at(6, 16)
    )
    body = get(world)
    assert body["timezone"] == "America/New_York"
    assert [i["kind"] for i in body["items"]] == ["gate", "event", "agenda"]
    gate = body["items"][0]
    assert gate["starts_at"] == "2027-03-01T12:00:00Z"
    assert gate["local_starts_at"] == "2027-03-01T07:00:00-05:00"  # before the US clocks change
    assert body["items"][2]["local_starts_at"] == "2027-03-06T10:00:00-05:00"
    assert body["total"] == 3 and body["conflicts"] == []
    assert get(world) == body  # nothing is stored or consumed: same answer twice


def test_a_window_across_a_daylight_saving_change_says_so(world):
    # US clocks change on 14 March 2027.
    TemporalGate.objects.create(
        event=world["event"], name="Submissions", opens_at=at(12, 12), closes_at=at(16, 12)
    )
    gate = next(i for i in get(world)["items"] if i["kind"] == "gate")
    assert "daylight-saving" in gate["dst_note"]
    assert gate["local_starts_at"].endswith("-05:00") and gate["local_ends_at"].endswith("-04:00")


def test_a_gate_with_one_date_is_an_instant_and_an_empty_event_adds_nothing(world):
    TemporalGate.objects.create(
        event=world["event"], name="Late", opens_at=None, closes_at=at(9, 9)
    )
    Event.objects.filter(pk=world["event"].pk).update(starts_at=None, ends_at=None)
    body = get(world)
    assert [(i["label"], i["ends_at"]) for i in body["items"]] == [("Late closes", None)]


def test_agenda_conflicts_are_found_per_room_and_per_track(world):
    event = world["event"]
    room = Location.objects.create(event=event, kind="room", name="Main")
    other = Location.objects.create(event=event, kind="room", name="Side")
    track = Track.objects.create(event=event, name="AI")
    a = AgendaSession.objects.create(
        event=event, title="A", starts_at=at(6, 15), ends_at=at(6, 17), location=room
    )
    b = AgendaSession.objects.create(
        event=event, title="B", starts_at=at(6, 16), ends_at=at(6, 18), location=room
    )
    c = AgendaSession.objects.create(
        event=event, title="C", starts_at=at(6, 16), ends_at=at(6, 18), location=other, track=track
    )
    d = AgendaSession.objects.create(
        event=event, title="D", starts_at=at(6, 17), ends_at=at(6, 19), location=other, track=track
    )
    AgendaSession.objects.create(
        event=event, title="E", starts_at=at(7, 15), ends_at=at(7, 16), location=room
    )
    body = get(world)
    found = {(c["code"], tuple(sorted(c["items"]))) for c in body["conflicts"]}
    key = lambda s: f"agenda:{s.public_id}"  # noqa: E731
    assert ("location_overlap", tuple(sorted([key(a), key(b)]))) in found
    # C and D touch (17:00 to 18:00 and 17:00 start) and overlap in the track between 17:00-18:00.
    assert ("track_overlap", tuple(sorted([key(c), key(d)]))) in found
    assert sum(1 for code, _ in found if code == "location_overlap") == 2  # A-B and C-D in "other"
    # Touching ends are not an overlap: A ends 17:00, D starts 17:00 in other rooms anyway.
    assert all("E" not in x["message"] for x in body["conflicts"])


def test_sessions_that_only_touch_do_not_conflict(world):
    event = world["event"]
    room = Location.objects.create(event=event, kind="room", name="Main")
    AgendaSession.objects.create(
        event=event, title="A", starts_at=at(6, 15), ends_at=at(6, 16), location=room
    )
    AgendaSession.objects.create(
        event=event, title="B", starts_at=at(6, 16), ends_at=at(6, 17), location=room
    )
    assert get(world)["conflicts"] == []


def test_items_outside_the_event_and_inverted_windows_are_reported(world):
    event = world["event"]
    AgendaSession.objects.create(event=event, title="Early", starts_at=at(5, 9), ends_at=at(5, 10))
    TemporalGate.objects.create(
        event=event, name="Backwards", opens_at=at(4, 12), closes_at=at(3, 12)
    )
    TemporalGate.objects.create(event=event, name="Fine", opens_at=at(1, 12), closes_at=at(2, 12))
    body = get(world)
    assert codes(body) == ["outside_event", "window_inverted"]
    inverted = next(c for c in body["conflicts"] if c["code"] == "window_inverted")
    assert inverted["message"] == "Backwards ends before it starts."
    assert all(c["severity"] == "advisory" for c in body["conflicts"])
    # A gate before the event is normal, and with no event dates nothing is "outside".
    Event.objects.filter(pk=event.pk).update(starts_at=None, ends_at=None)
    assert "outside_event" not in codes(get(world))


def test_office_hours_conflict_per_mentor_and_publication_waits_for_voting(world):
    event, mentor = world["event"], world["people"]["men"]
    OfficeHourSlot.objects.create(
        event=event, mentor=mentor, starts_at=at(7, 10), ends_at=at(7, 12)
    )
    OfficeHourSlot.objects.create(
        event=event, mentor=mentor, starts_at=at(7, 11), ends_at=at(7, 13)
    )
    VotingPlan.objects.create(event=event, opens_at=at(7, 9), closes_at=at(8, 20))
    PublicationSchedule.objects.create(event=event, surface="winners", opens_at=at(8, 19))
    PublicationSchedule.objects.create(event=event, surface="gallery", opens_at=at(8, 19))
    body = get(world)
    assert codes(body) == ["mentor_overlap", "publication_before_voting_closes"]
    late = next(c for c in body["conflicts"] if c["code"] == "publication_before_voting_closes")
    assert late["items"] == ["publication:winners", "voting:plan"]  # the gallery may open earlier
    PublicationSchedule.objects.filter(surface="winners").update(opens_at=at(8, 21))
    assert "publication_before_voting_closes" not in codes(get(world))


def test_reminders_appear_only_while_they_are_still_to_be_sent(world):
    event, org = world["event"], world["people"]["org"]
    make = lambda subject, **kw: Reminder.objects.create(  # noqa: E731
        event=event,
        created_by=org,
        kind="deadline",
        due_at=at(5, 12),
        audience_kind="all_participants",
        subject=subject,
        body="b",
        **kw,
    )
    make("Pending")
    make("Cancelled", cancelled_at=at(4, 1))
    sent = Message.objects.create(
        event=event, sent_by=org, subject="s", body="b", audience_kind="x"
    )
    make("Sent", sent_message=sent)
    assert [i["label"] for i in get(world)["items"] if i["kind"] == "reminder"] == [
        "Reminder: Pending"
    ]


def test_the_range_and_kinds_filters_and_the_limit(world):
    event = world["event"]
    TemporalGate.objects.create(
        event=event, name="Registration", opens_at=at(1, 12), closes_at=at(5, 12)
    )
    for hour in (15, 16, 17):
        AgendaSession.objects.create(
            event=event, title=f"S{hour}", starts_at=at(6, hour), ends_at=at(6, hour + 1)
        )
    assert keys(get(world, "?kinds=gate")) == [f"gate:{TemporalGate.objects.get().public_id}"]
    only = get(world, "?from=2027-03-06T15:30:00Z&to=2027-03-06T16:30:00Z&kinds=agenda")
    assert [i["label"] for i in only["items"]] == ["S15", "S16"]  # S15 still running, S17 not yet
    page = get(world, "?limit=2")
    assert len(page["items"]) == 2 and page["total"] == 5
    # Conflicts are judged on the whole event, then shown when they touch what is shown.
    AgendaSession.objects.create(
        event=event, title="Clash", starts_at=at(6, 15, 30), ends_at=at(6, 16, 30)
    )
    clash_free = get(world, "?kinds=gate")
    assert clash_free["conflicts"] == []


@pytest.mark.parametrize(
    "query",
    [
        "?kinds=nope",
        "?from=2027-03-06T10:00:00",
        "?from=zzz",
        "?limit=0",
        "?limit=501",
        "?limit=x",
        "?from=2027-03-07T00:00:00Z&to=2027-03-06T00:00:00Z",
    ],
)
def test_bad_parameters_are_refused_with_the_reason(world, query):
    response = world["client"]["org"].get(world["base"] + "timeline/" + query)
    assert response.status_code == 400 and response.json()


def test_only_organizers_see_the_timeline(world):
    for who in ("par", "men"):
        assert world["client"][who].get(world["base"] + "timeline/").status_code == 403
    assert Client().get(world["base"] + "timeline/").status_code in (401, 403)
    other = Workspace.objects.create(name="O", slug="o")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    foreign = world["base"].replace(str(world["workspace"].public_id), str(other.public_id))
    assert _client(stranger).get(foreign + "timeline/").status_code == 404


def _apply(world, item, starts, ends):
    """Exactly what a client would do from the item's `write` descriptor."""
    write = item["write"]
    url = "/api/v1/" + write["path"].format(
        workspace=world["workspace"].public_id, event=world["event"].public_id
    )
    c = world["client"]["org"]
    values = {
        **write["extra"],
        write["fields"]["starts_at"]: starts,
        write["fields"]["ends_at"]: ends,
    }
    return c.generic(write["method"], url, data=json.dumps(values), content_type="application/json")


def test_every_editable_item_changes_through_its_own_domain_endpoint(world):
    event = world["event"]
    room = Location.objects.create(event=event, kind="room", name="Main")
    TemporalGate.objects.create(
        event=event, name="Registration", opens_at=at(1, 12), closes_at=at(5, 12)
    )
    AgendaSession.objects.create(
        event=event,
        title="Talk",
        starts_at=at(6, 15),
        ends_at=at(6, 16),
        location=room,
        created_by=world["people"]["org"],
    )
    VotingPlan.objects.create(event=event, opens_at=at(7, 9), closes_at=at(8, 12))
    PublicationSchedule.objects.create(
        event=event, surface="winners", opens_at=at(8, 20), closes_at=at(8, 21)
    )
    items = [i for i in get(world)["items"] if i["editable"]]
    assert {i["kind"] for i in items} == {"event", "gate", "agenda", "voting", "publication"}
    for item in items:
        starts = datetime.fromisoformat(item["starts_at"].replace("Z", "+00:00")) + timedelta(
            minutes=30
        )
        ends = datetime.fromisoformat(item["ends_at"].replace("Z", "+00:00")) + timedelta(
            minutes=30
        )
        response = _apply(world, item, starts.isoformat(), ends.isoformat())
        assert response.status_code == 200, (item["kind"], response.content)
    after = {i["key"]: i for i in get(world)["items"]}
    for item in items:
        moved = after[item["key"]]
        assert moved["starts_at"] != item["starts_at"], item["kind"]
        assert datetime.fromisoformat(
            moved["starts_at"].replace("Z", "+00:00")
        ) - datetime.fromisoformat(item["starts_at"].replace("Z", "+00:00")) == timedelta(
            minutes=30
        )


def test_items_without_a_domain_write_say_so(world):
    event = world["event"]
    OfficeHourSlot.objects.create(
        event=event, mentor=world["people"]["men"], starts_at=at(7, 10), ends_at=at(7, 11)
    )
    Reminder.objects.create(
        event=event,
        created_by=world["people"]["org"],
        kind="deadline",
        due_at=at(5, 1),
        audience_kind="all_participants",
        subject="x",
        body="b",
    )
    items = [i for i in get(world)["items"] if i["kind"] in ("office_hours", "reminder")]
    assert len(items) == 2 and all(not i["editable"] and i["write"] is None for i in items)


def test_a_domain_can_add_a_provider_and_a_rule_without_touching_the_timeline(world):
    toy = timeline.Provider(
        "test_toy",
        "Toy",
        lambda event: [
            timeline.TimelineItem(
                "test_toy", "test_toy:a", "Toy A", at(6, 16), at(6, 17), group={"desk": "1"}
            ),
            timeline.TimelineItem(
                "test_toy", "test_toy:b", "Toy B", at(6, 16, 30), at(6, 18), group={"desk": "1"}
            ),
        ],
    )
    rule = lambda event, items: [  # noqa: E731
        timeline.Conflict(
            "test_rule", "Toy rule", tuple(i.key for i in items if i.kind == "test_toy")
        )
    ]
    timeline.register_provider(toy)
    timeline.register_rule(rule)
    try:
        body = get(world, "?kinds=test_toy")
        assert keys(body) == ["test_toy:a", "test_toy:b"]
        assert codes(body) == ["desk_overlap", "test_rule"]
        assert body["items"][0]["kind_label"] == "Toy"
        with pytest.raises(ValueError):
            timeline.register_provider(timeline.Provider("test_toy", "Other", lambda e: []))
        timeline.register_provider(toy)  # the identical one is harmless
    finally:
        timeline.PROVIDERS.pop("test_toy")
        timeline.RULES.remove(rule)
    assert "test_toy" not in {i["kind"] for i in get(world)["items"]}


def test_many_items_stay_cheap(world, django_assert_max_num_queries):
    event = world["event"]
    room = Location.objects.create(event=event, kind="room", name="Main")
    for i in range(60):
        AgendaSession.objects.create(
            event=event,
            title=f"S{i}",
            starts_at=at(6, 15) + timedelta(minutes=i),
            ends_at=at(6, 15) + timedelta(minutes=i + 1),
            location=room,
        )
    with django_assert_max_num_queries(16):
        assert get(world)["total"] == 61  # 60 sessions and the event itself
