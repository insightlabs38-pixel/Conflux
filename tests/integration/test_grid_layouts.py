"""PD-F006-B03-T01: list, board, matrix and calendar are views of the one entity query."""

import json

import pytest
from core import entities

from tests.integration.test_entity_query import ROWS, applicants, ask, names, tree, world
from tests.integration.test_saved_views import post

pytestmark = pytest.mark.django_db


def test_the_catalogue_offers_only_the_layouts_that_mean_something_for_the_list():
    _, _, _, client, _, base = world()
    catalogue = {e["key"]: e for e in client.get(base).json()}
    applications, projects = catalogue["applications"], catalogue["projects"]
    assert applications["layouts"] == ["list", "board", "matrix", "calendar"]
    assert applications["board_field"] == "status"
    assert applications["calendar_fields"] == ["created_at", "decided_at"]
    assert projects["layouts"] == ["list", "board", "matrix", "calendar"]
    assert projects["board_field"] == "track" and projects["calendar_fields"] == ["created_at"]
    bare = entities.Entity(
        key="bare", label="Bare", roles=(), base=lambda e, u: None, fields=(), default_sort=()
    )
    assert bare.layouts() == ["list"]


def test_a_calendar_places_the_filtered_rows_on_days_and_a_day_opens_through_the_ordinary_query():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)  # created 2027-03-01 .. 2027-03-05, one a day
    page = ask(client, base, calendar="created_at", month="2027-03").json()
    assert page["calendar"] == "created_at" and page["month"] == "2027-03"
    assert page["rows"] == [] and page["total"] == 5
    assert [d["date"] for d in page["days"]] == [f"2027-03-0{n}" for n in range(1, 6)]
    assert all(d["count"] == 1 for d in page["days"])
    # a day is opened with two ordinary conditions, so counts and rows cannot disagree
    day = tree(
        **{
            "and": [
                {"field": "created_at", "op": "gte", "value": "2027-03-03"},
                {"field": "created_at", "op": "lt", "value": "2027-03-04"},
            ]
        }
    )
    assert names(ask(client, base, filter=day)) == ["cyd"]
    # the filter and the search narrow the days exactly as they narrow rows
    narrowed = ask(client, base, calendar="created_at", month="2027-03", search="berlin").json()
    assert [d["date"] for d in narrowed["days"]] == ["2027-03-03", "2027-03-04"]
    filtered = ask(
        client,
        base,
        calendar="created_at",
        month="2027-03",
        filter=tree(field="status", op="eq", value="waitlisted"),
    ).json()
    assert filtered["total"] == 2
    # another month is empty, not an error; a date field with no values places nothing
    assert ask(client, base, calendar="created_at", month="2027-04").json()["days"] == []
    assert ask(client, base, calendar="decided_at", month="2027-03").json()["days"] == []


def test_the_calendar_reads_a_day_in_utc_and_a_month_boundary_belongs_to_one_month_only():
    _, event, _, client, _, base = world()
    applicants(event, [("ada", "pending", "", 0), ("ben", "pending", "", 30)])
    from datetime import UTC, datetime

    from events.models import EventApplication

    first, second = EventApplication.objects.order_by("created_at")
    EventApplication.objects.filter(pk=first.pk).update(
        created_at=datetime(2027, 2, 28, 23, 59, 59, 999999, tzinfo=UTC)
    )
    EventApplication.objects.filter(pk=second.pk).update(
        created_at=datetime(2027, 3, 1, 0, 0, 0, tzinfo=UTC)
    )
    february = ask(client, base, calendar="created_at", month="2027-02").json()
    march = ask(client, base, calendar="created_at", month="2027-03").json()
    assert [d["date"] for d in february["days"]] == ["2027-02-28"]
    assert [d["date"] for d in march["days"]] == ["2027-03-01"]
    december = ask(client, base, calendar="created_at", month="2027-12").json()
    assert december["days"] == []


@pytest.mark.parametrize(
    ("params", "key", "fragment"),
    [
        ({"calendar": "status"}, "calendar", "Cannot place rows by"),
        ({"calendar": "nope"}, "calendar", "Cannot place rows by"),
        ({"calendar": "created_at", "month": "2027-13"}, "month", "written 2027-03"),
        ({"calendar": "created_at", "month": "March"}, "month", "written 2027-03"),
        ({"calendar": "created_at", "month": "1500-01"}, "month", "written 2027-03"),
        ({"calendar": "created_at", "group": "status"}, "calendar", "cannot also be grouped"),
    ],
)
def test_calendar_refusals_name_the_part(params, key, fragment):
    _, event, _, client, _, base = world()
    response = ask(client, base, **params)
    assert response.status_code == 400
    assert any(k.startswith(key) and fragment in v[0] for k, v in response.json().items())


def test_a_judge_cannot_ask_for_a_calendar_and_the_caller_keeps_their_own_rows():
    _, event, _, _, judge, base = world()
    assert ask(judge, base, calendar="created_at", month="2027-03").status_code == 403


def test_a_saved_view_keeps_its_layout_and_runs_it_under_the_viewers_rights():
    from tests.integration.test_saved_views import world as views_world

    _, _, event, _, clients, root = views_world()
    applicants(event, ROWS)

    def make(name, query):
        response = post(clients["ana"], root, name=name, query=query)
        assert response.status_code == 201, response.content
        return response.json()

    plain = make("Plain", {"filter": None, "sort": "", "columns": []})
    assert "layout" not in plain["query"] and "calendar" not in plain["query"]  # older views same
    board = make("Board", {"layout": "board"})
    assert board["query"]["layout"] == "board" and "calendar" not in board["query"]
    matrix = make("Matrix", {"layout": "matrix", "group": "status", "subgroup": "decided_by"})
    cal = make("Calendar", {"layout": "calendar"})
    assert cal["query"]["layout"] == "calendar" and cal["query"]["calendar"] == "created_at"

    def run(view, **params):
        return clients["ana"].get(root + f"views/{view['public_id']}/run/", params).json()

    ran = run(board)
    assert ran["layout"] == "board" and ran["group"] == "status"
    assert {g["key"]: g["count"] for g in ran["groups"]} == {
        "approved": 1,
        "pending": 1,
        "rejected": 1,
        "waitlisted": 2,
    }
    grid = run(matrix)
    assert grid["layout"] == "matrix" and grid["subgroup"] == "decided_by"
    month = run(cal, month="2027-03")
    assert month["layout"] == "calendar" and month["total"] == 5 and month["month"] == "2027-03"
    assert run(plain)["layout"] == "list" and len(run(plain)["rows"]) == 5
    assert (
        clients["ana"].get(root + f"views/{cal['public_id']}/run/", {"month": "soon"}).status_code
        == 400
    )
    # a judge never sees the view of an entity they may not query
    assert clients["judge"].get(root + f"views/{board['public_id']}/run/").status_code == 404


@pytest.mark.parametrize(
    ("query", "key", "fragment"),
    [
        ({"layout": "gantt"}, "layout", "Use one of"),
        ({"layout": "matrix"}, "layout", "needs a group and a subgroup"),
        ({"layout": "matrix", "group": "status"}, "layout", "needs a group and a subgroup"),
        (
            {"layout": "board", "group": "status", "subgroup": "decided_by"},
            "layout",
            "no subgroup",
        ),
        ({"layout": "calendar", "group": "status"}, "layout", "not grouped"),
        ({"layout": "calendar", "calendar": "status"}, "calendar", "Cannot place rows by"),
        ({"layout": "board", "calendar": "created_at"}, "calendar", "Only a calendar"),
    ],
)
def test_a_view_with_a_layout_that_does_not_fit_is_refused_with_the_part_named(
    query, key, fragment
):
    from tests.integration.test_saved_views import world as views_world

    _, _, _, _, clients, root = views_world()
    response = post(clients["ana"], root, query=query)
    assert response.status_code == 400, response.content
    assert key in json.dumps(response.json()) and fragment in json.dumps(response.json())


def test_one_record_is_found_by_id_with_every_field_and_only_if_the_list_would_show_it():
    from events.models import EventApplication

    _, event, _, client, judge, base = world()
    applicants(event, ROWS)
    ada = EventApplication.objects.get(user__username="ada")
    response = client.get(f"{base}applications/{ada.public_id}/")
    assert response.status_code == 200
    row = response.json()["row"]
    assert row["id"] == str(ada.public_id) and row["username"] == "ada"
    assert {"status", "note", "decided_by", "decided_at", "created_at"} <= set(
        row
    )  # non-default too
    # the same row the list returns, so the inspector can never show more than the grid
    listed = ask(client, base, columns=",".join(row.keys() - {"id"}), search="ada").json()["rows"][
        0
    ]
    assert listed == row
    # a role that may not query the list, an unknown entity and an unknown id are all refused
    assert judge.get(f"{base}applications/{ada.public_id}/").status_code == 403
    assert client.get(f"{base}nope/{ada.public_id}/").status_code == 404
    assert client.get(f"{base}applications/{ada.public_id.__class__(int=1)}/").status_code == 404


def test_a_record_of_another_event_is_not_reachable_by_its_id():
    from events.models import Event, EventApplication

    workspace, event, _, client, _, base = world()
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    elsewhere = applicants(other, [("zed", "pending", "", 0)])[0]
    assert EventApplication.objects.filter(pk=elsewhere.pk).exists()
    assert client.get(f"{base}applications/{elsewhere.public_id}/").status_code == 404
