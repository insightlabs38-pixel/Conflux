"""PD-F006-B03-T02: footer values are computed over every matching row, by the one query."""

from datetime import UTC, datetime

import pytest
from core import entities

from tests.integration.test_entity_query import ROWS, applicants, ask, tree, world
from tests.integration.test_saved_views import post

pytestmark = pytest.mark.django_db


def footer(page):
    return {(a["field"], a["fn"]): a["value"] for a in page["aggregates"]}


def test_the_catalogue_says_which_summaries_each_field_offers():
    _, _, _, client, _, base = world()
    applications = next(e for e in client.get(base).json() if e["key"] == "applications")
    offered = {f["key"]: f["aggregates"] for f in applications["fields"]}
    assert offered["waitlist_position"] == ["min", "max"]  # narrowed: no sum of places
    assert offered["created_at"] == ["min", "max"]  # a date has a range, not a sum
    assert offered["username"] == [] and offered["status"] == []


def test_footer_values_cover_every_matching_row_not_the_page():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)  # waitlist places 3 and 4 for cyd and dee
    page = ask(
        client, base, aggregate="waitlist_position:min,waitlist_position:max", limit=2
    ).json()
    assert len(page["rows"]) == 2 and page["total"] == 5  # a page of two ...
    assert footer(page) == {("waitlist_position", "min"): 3, ("waitlist_position", "max"): 4}
    dates = ask(client, base, aggregate="created_at:min,created_at:max").json()
    assert footer(dates)[("created_at", "min")].startswith("2027-03-01")
    assert footer(dates)[("created_at", "max")].startswith("2027-03-05")
    # the filter and the search narrow the footer as they narrow the rows
    narrowed = ask(
        client,
        base,
        aggregate="created_at:max",
        filter=tree(field="status", op="eq", value="pending"),
    ).json()
    assert footer(narrowed)[("created_at", "max")].startswith("2027-03-01")
    berlin = ask(client, base, aggregate="waitlist_position:max", search="too").json()
    assert footer(berlin) == {("waitlist_position", "max"): 4}
    # nothing matching summarises to empty, not zero
    empty = ask(client, base, aggregate="waitlist_position:max", search="zzzz").json()
    assert footer(empty) == {("waitlist_position", "max"): None}
    # no parameter, no footer
    assert "aggregates" not in ask(client, base).json()


def test_a_number_field_offers_sum_and_average_with_two_decimals_at_most():
    entity = entities.Entity(
        key="figures",
        label="Figures",
        roles=(),
        base=lambda e, u: None,
        fields=(entities.Field("score", entities.NUMBER, "score", "Score"),),
    )
    assert entity.field("score").summaries() == ("sum", "avg", "min", "max")
    from core import query

    parsed = query.parse_aggregates(entity, "score:avg,score:sum,score:avg")
    assert [(f.key, fn) for f, fn in parsed] == [("score", "avg"), ("score", "sum")]  # no repeats
    assert query._summary("avg", 2 / 3) == 0.67
    assert query._summary("sum", 7) == 7
    from decimal import Decimal

    assert query._summary("max", Decimal("2.50")) == 2.5
    with pytest.raises(ValueError, match="cannot be summed"):
        entities.register(
            entities.Entity(
                key="bad",
                label="Bad",
                roles=(),
                base=lambda e, u: None,
                fields=(
                    entities.Field("when", entities.DATE, "when", "When", aggregates=("sum",)),
                ),
            )
        )


def test_groups_carry_their_own_footer_values_and_the_whole_result_its_own():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)
    page = ask(
        client, base, group="status", aggregate="waitlist_position:max,created_at:min"
    ).json()
    by_status = {g["key"]: g for g in page["groups"]}
    waitlisted = {(a["field"], a["fn"]): a["value"] for a in by_status["waitlisted"]["aggregates"]}
    assert waitlisted[("waitlist_position", "max")] == 4
    pending = {(a["field"], a["fn"]): a["value"] for a in by_status["pending"]["aggregates"]}
    assert pending[("waitlist_position", "max")] is None
    assert pending[("created_at", "min")].startswith("2027-03-01")
    assert footer(page)[("waitlist_position", "max")] == 4  # the whole result
    # a subgroup does not change a group's own values
    nested = ask(
        client,
        base,
        group="status",
        subgroup="decided_by",
        aggregate="waitlist_position:max",
    ).json()
    again = {g["key"]: g["aggregates"][0]["value"] for g in nested["groups"]}
    assert again["waitlisted"] == 4


@pytest.mark.parametrize(
    ("value", "fragment"),
    [
        ("username:max", "Cannot summarise"),
        ("nope:min", "Cannot summarise"),
        ("created_at:sum", "offers min, max, not 'sum'"),
        ("waitlist_position", "not ''"),
        ("a:min,b:min,c:min,d:min,e:min,f:min,g:min", "At most 6"),
    ],
)
def test_refusals_name_the_part(value, fragment):
    _, event, _, client, _, base = world()
    response = ask(client, base, aggregate=value)
    assert response.status_code == 400
    assert any(k.startswith("aggregate") and fragment in v[0] for k, v in response.json().items())


def test_a_saved_view_keeps_its_footer_and_runs_it_for_the_viewer():
    from tests.integration.test_saved_views import world as views_world

    _, _, event, _, clients, root = views_world()
    applicants(event, ROWS)
    made = post(
        clients["ana"],
        root,
        name="Footer",
        query={"aggregate": ["created_at:max", "created_at:min"]},
    )
    assert made.status_code == 201, made.content
    assert made.json()["query"]["aggregate"] == ["created_at:max", "created_at:min"]
    plain = post(clients["ana"], root, name="Plain", query={})
    assert "aggregate" not in plain.json()["query"]  # additive: older views are unchanged
    ran = clients["ana"].get(root + f"views/{made.json()['public_id']}/run/").json()
    assert footer(ran)[("created_at", "max")].startswith("2027-03-05")
    refused = post(clients["ana"], root, name="Bad", query={"aggregate": ["username:max"]})
    assert refused.status_code == 400 and "aggregate" in str(refused.json())
    assert (
        post(clients["ana"], root, name="Bad2", query={"aggregate": "created_at:max"}).status_code
        == 400
    )
    assert datetime(2027, 3, 1, tzinfo=UTC)  # the fixture dates are those of ROWS
