"""PD-F002-B01-T01: one query contract for listing, filtering and sorting registered entities."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from accounts.models import Session, User
from core import entities, query
from django.test import Client
from events.models import Event, EventApplication, RegistrationStatus, Track
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

NOW = datetime(2027, 3, 1, 12, 0, tzinfo=UTC)


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def world():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Q", slug="q")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/entities/"
    return workspace, event, organizer, client_for(organizer), client_for(judge), base


def applicants(event, rows):
    made = []
    for index, (name, status, note, days) in enumerate(rows):
        user = User.objects.create_user(username=name, password="unused")
        application = EventApplication.objects.create(
            event=event, user=user, status=status, note=note
        )
        EventApplication.objects.filter(pk=application.pk).update(
            created_at=NOW + timedelta(days=days),
            waitlist_position=index + 1 if status == RegistrationStatus.WAITLISTED else None,
        )
        made.append(application)
    return made


def ask(client, base, entity="applications", **params):
    response = client.get(base + f"{entity}/", {k: v for k, v in params.items() if v is not None})
    return response


def tree(**node):
    return json.dumps(node, separators=(",", ":"))


ROWS = [
    ("ada", RegistrationStatus.PENDING, "likes compilers", 0),
    ("ben", RegistrationStatus.APPROVED, "", 1),
    ("cyd", RegistrationStatus.WAITLISTED, "from Berlin", 2),
    ("dee", RegistrationStatus.WAITLISTED, "from Berlin too", 3),
    ("eve", RegistrationStatus.REJECTED, "", 4),
]


def names(response):
    assert response.status_code == 200, response.content
    return [row["username"] for row in response.json()["rows"]]


def test_the_catalogue_lists_what_the_caller_may_query_with_types_and_operators():
    _, _, _, client, judge, base = world()
    catalogue = client.get(base).json()
    assert {e["key"] for e in catalogue} == {"applications", "projects"}
    applications = next(e for e in catalogue if e["key"] == "applications")
    status = next(f for f in applications["fields"] if f["key"] == "status")
    assert status["type"] == "enum" and "in" in status["operators"]
    assert status["choices"] == ["pending", "approved", "waitlisted", "rejected"]
    created = next(f for f in applications["fields"] if f["key"] == "created_at")
    assert "eq" not in created["operators"] and "between" in created["operators"]
    # A judge holds none of the roles the entities register: nothing to offer, nothing to query.
    assert judge.get(base).json() == []


def test_filter_sort_columns_and_paging():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)
    everyone = ask(client, base).json()
    assert everyone["total"] == 5 and everyone["limit"] == 25 and everyone["offset"] == 0
    assert everyone["columns"] == ["username", "status", "note", "waitlist_position", "created_at"]
    status = ask(client, base, filter=tree(field="status", op="eq", value="waitlisted"))
    assert names(status) == ["cyd", "dee"]
    assert status.json()["total"] == 2
    listed = ask(client, base, sort="-username", columns="username,status", limit=2, offset=1)
    body = listed.json()
    assert [r["username"] for r in body["rows"]] == ["dee", "cyd"]
    assert set(body["rows"][0]) == {"id", "username", "status"} and body["total"] == 5
    assert body["sort"] == ["-user__username"]


def test_groups_operators_and_nulls():
    _, event, organizer, client, _, base = world()
    made = applicants(event, ROWS)
    EventApplication.objects.filter(pk=made[-1].pk).update(decided_by=organizer)

    def q(**node):
        return names(ask(client, base, filter=tree(**node)))

    waiting = {"field": "status", "op": "eq", "value": "waitlisted"}
    berlin = {"field": "note", "op": "contains", "value": "BERLIN"}  # case-insensitive
    assert q(**{"and": [waiting, berlin]}) == ["cyd", "dee"]
    assert sorted(q(**{"or": [waiting, {"field": "status", "op": "eq", "value": "pending"}]})) == [
        "ada",
        "cyd",
        "dee",
    ]
    assert sorted(q(**{"not": waiting})) == ["ada", "ben", "eve"]
    assert q(field="status", op="ne", value="waitlisted") and "cyd" not in q(
        field="status", op="ne", value="waitlisted"
    )
    assert sorted(q(field="status", op="in", value=["approved", "rejected"])) == ["ben", "eve"]
    assert q(field="username", op="startswith", value="C") == ["cyd"]
    assert q(field="username", op="eq", value="ben") == ["ben"]
    assert sorted(q(field="decided_by", op="is_null", value=False)) == ["eve"]
    assert len(q(field="decided_by", op="is_null", value=True)) == 4
    assert sorted(q(field="decided_by", op="eq", value="org")) == ["eve"]
    assert q(field="note", op="eq", value="") == ["ben", "eve"]
    assert q(field="waitlist_position", op="between", value=[3, 3]) == ["cyd"]
    assert sorted(q(field="waitlist_position", op="gte", value=4)) == ["dee"]
    assert sorted(q(field="decided_at", op="is_null", value=False)) == []
    window = ["2027-03-02T00:00:00Z", "2027-03-03T23:59:59Z"]
    assert sorted(q(field="created_at", op="between", value=window)) == ["ben", "cyd"]
    assert q(field="created_at", op="gt", value="2027-03-06") == []
    assert q(field="created_at", op="gt", value="2027-03-05") == ["eve"]  # date-only: start of day
    assert sorted(q(field="created_at", op="lt", value="2027-03-02")) == ["ada"]


@pytest.mark.parametrize(
    "raw, key, fragment",
    [
        ("not json", "filter", "valid JSON"),
        (tree(field="password", op="eq", value="x"), "filter.field", "Unknown field"),
        (tree(field="user__password", op="eq", value="x"), "filter.field", "Unknown field"),
        (tree(field="status", op="contains", value="x"), "filter.op", "does not support"),
        (tree(field="status", op="eq", value="maybe"), "filter.value", "Use one of"),
        (tree(field="created_at", op="eq", value="2027-03-01"), "filter.op", "between"),
        (tree(field="created_at", op="gt", value="yesterday"), "filter.value", "ISO 8601"),
        (tree(field="waitlist_position", op="eq", value="1"), "filter.value", "number"),
        (tree(field="waitlist_position", op="eq", value=True), "filter.value", "number"),
        (tree(field="waitlist_position", op="in", value=[]), "filter.value", "non-empty"),
        (tree(field="username", op="in", value=["a"] * 51), "filter.value", "At most 50"),
        (tree(field="username", op="eq", value="x" * 201), "filter.value", "200 characters"),
        (tree(field="username", op="eq", value="x", extra=1), "filter", "Unknown keys"),
        (tree(**{"and": []}), "filter.and", "non-empty"),
        (
            tree(**{"and": [{"field": "status", "op": "nope", "value": "x"}]}),
            "filter.and[0].op",
            "does not support",
        ),
        (tree(**{"and": "x"}), "filter.and", "non-empty list"),
        (tree(**{"and": [{}], "or": [{}]}), "filter", "only one"),
        (json.dumps([1]), "filter", "object"),
    ],
)
def test_bad_filters_are_400_and_name_the_offending_part(raw, key, fragment):
    _, _, _, client, _, base = world()
    response = ask(client, base, filter=raw)
    assert response.status_code == 400, response.content
    assert key in response.json(), response.json()
    assert fragment in " ".join(response.json()[key])


def test_complexity_is_bounded():
    _, _, _, client, _, base = world()
    leaf = {"field": "username", "op": "eq", "value": "x"}
    deep = leaf
    for _ in range(5):
        deep = {"not": deep}
    assert "nested at most" in str(ask(client, base, filter=json.dumps(deep)).json())
    wide = {"or": [leaf] * 21}
    response = ask(client, base, filter=json.dumps(wide))
    assert response.status_code == 400 and "At most 20" in str(response.json())
    twenty = {"or": [leaf] * 20}
    assert ask(client, base, filter=json.dumps(twenty)).status_code == 200


@pytest.mark.parametrize(
    "params, key",
    [
        ({"sort": "nope"}, "sort"),
        ({"sort": "note"}, "sort"),  # registered, but not sortable
        ({"sort": "username,status,created_at,note"}, "sort"),
        ({"columns": "username,secret"}, "columns"),
        ({"limit": 0}, "limit"),
        ({"limit": 101}, "limit"),
        ({"limit": "x"}, "limit"),
        ({"offset": -1}, "offset"),
    ],
)
def test_bad_sort_columns_and_paging_are_400(params, key):
    _, _, _, client, _, base = world()
    response = ask(client, base, **params)
    assert response.status_code == 400 and key in response.json(), response.content


def test_values_are_data_never_code():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)
    hostile = "x'); DROP TABLE events_eventapplication; --"
    assert names(ask(client, base, filter=tree(field="username", op="eq", value=hostile))) == []
    assert names(ask(client, base, filter=tree(field="note", op="contains", value="%"))) == []
    assert EventApplication.objects.count() == 5  # `%` is a literal, not a wildcard


def test_entities_are_organizer_only_tenant_scoped_and_unknown_is_404():
    workspace, event, _, client, judge, base = world()
    assert judge.get(base + "applications/").status_code == 403
    assert Client().get(base + "applications/").status_code in (401, 403)
    assert ask(client, base, entity="nonsense").status_code == 404
    other = Workspace.objects.create(name="Other", slug="other")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert outsider.get(base + "applications/").status_code == 403
    cross = f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/entities/applications/"
    assert outsider.get(cross).status_code == 404


def test_rows_never_cross_events():
    workspace, event, _, client, _, base = world()
    applicants(event, ROWS[:2])
    other = Event.objects.create(workspace=workspace, name="Other", slug="other-e")
    applicants(other, [("zed", RegistrationStatus.PENDING, "", 0)])
    assert sorted(names(ask(client, base))) == ["ada", "ben"]


def test_projects_filter_by_track_and_flags():
    workspace, event, organizer, client, _, base = world()
    hardware = Track.objects.create(event=event, name="Hardware")
    Project.objects.create(event=event, name="Arm", created_by=organizer, track=hardware)
    Project.objects.create(event=event, name="Bot", created_by=organizer, gallery_blocked=True)
    Project.objects.create(event=event, name="Cam", created_by=organizer, gallery_visible=False)

    def projects(**node):
        response = ask(client, base, entity="projects", filter=tree(**node))
        assert response.status_code == 200, response.content
        return [r["name"] for r in response.json()["rows"]]

    assert projects(field="track", op="eq", value="Hardware") == ["Arm"]
    assert projects(field="track", op="is_null", value=True) == ["Bot", "Cam"]
    assert projects(field="gallery_blocked", op="eq", value=True) == ["Bot"]
    assert projects(field="gallery_visible", op="eq", value=False) == ["Cam"]


def test_every_registered_field_resolves_against_the_database():
    """Registry conformance: a typo in a column path would only show up at query time."""
    _, event, organizer, client, _, base = world()
    applicants(event, ROWS[:1])
    Project.objects.create(event=event, name="P", created_by=organizer)
    sample = {
        "text": ("eq", "x"),
        "number": ("eq", 1),
        "date": ("gt", "2000-01-01"),
        "bool": ("eq", True),
        "enum": ("eq", None),
        "uuid": ("eq", "00000000-0000-4000-8000-000000000000"),
    }
    for entity in entities.entities().values():
        for field in entity.fields:
            op, value = sample[field.type]
            if field.type == "enum":
                value = field.choices[0]
            if field.filterable:
                response = ask(
                    client,
                    base,
                    entity=entity.key,
                    filter=tree(field=field.key, op=op, value=value),
                )
                assert response.status_code == 200, (entity.key, field.key, response.content)
            if field.sortable:
                response = ask(client, base, entity=entity.key, sort=field.key)
                assert response.status_code == 200, (entity.key, field.key, response.content)


def test_the_canonical_filter_text_is_stable_and_registration_is_strict():
    a = {"op": "eq", "value": "x", "field": "status"}
    b = {"field": "status", "value": "x", "op": "eq"}
    assert query.canonical(a) == query.canonical(b) == '{"field":"status","op":"eq","value":"x"}'
    with pytest.raises(ValueError):
        entities.register(
            entities.Entity(
                "bad", "Bad", (), lambda e, u: None, (entities.Field("x", "weird", "x", "X"),)
            )
        )
    with pytest.raises(ValueError):
        entities.register(
            entities.Entity(
                "bad", "Bad", (), lambda e, u: None, (entities.Field("x", "enum", "x", "X"),)
            )
        )


def test_the_legacy_applications_endpoint_is_unchanged():
    workspace, event, _, client, _, _ = world()
    applicants(event, ROWS)
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/applications/"
    assert len(client.get(url).json()) == 5
    assert {r["username"] for r in client.get(url + "?status=waitlisted").json()} == {"cyd", "dee"}


def test_search_matches_every_word_in_any_search_field_and_combines_with_the_filter():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)
    assert names(ask(client, base, search="berlin")) == [
        "cyd",
        "dee",
    ]  # case-insensitive, in a note
    assert names(ask(client, base, search="berlin too")) == ["dee"]  # every word must match
    assert names(ask(client, base, search="ADA")) == ["ada"]  # in the username
    assert names(ask(client, base, search="compilers ada")) == ["ada"]  # words in different fields
    both = ask(
        client, base, search="berlin", filter=tree(field="status", op="eq", value="waitlisted")
    )
    assert names(both) == ["cyd", "dee"] and both.json()["total"] == 2
    none = ask(client, base, search="berlin", filter=tree(field="status", op="eq", value="pending"))
    assert names(none) == [] and none.json()["total"] == 0
    assert ask(client, base, search="berlin").json()["search"] == "berlin"
    assert ask(client, base).json()["search"] == ""
    # wildcards are text, not patterns
    assert names(ask(client, base, search="b%")) == []
    # the catalogue says which keys are searched
    applications = next(e for e in client.get(base).json() if e["key"] == "applications")
    assert applications["search_fields"] == ["username", "note", "decided_by"]


@pytest.mark.parametrize(
    "value, fragment",
    [
        ("a", "at least 2"),
        ("ab cd ef gh ij kl", "at most 5"),
        ("x" * 201, "limited to 200"),
    ],
)
def test_bad_search_is_400_and_names_the_word(value, fragment):
    _, event, _, client, _, base = world()
    applicants(event, ROWS)
    response = ask(client, base, search=value)
    assert response.status_code == 400
    (key, messages) = next(iter(response.json().items()))
    assert key.startswith("search") and fragment in messages[0]


def test_an_entity_without_search_fields_says_so_and_search_cannot_widen_rows():
    _, event, _, client, judge, base = world()
    applicants(event, ROWS)
    entities.register(
        entities.Entity(
            key="nosearch",
            label="No search",
            roles=("organizer",),
            base=lambda event, user: EventApplication.objects.filter(event=event),
            fields=(entities.Field("note", entities.TEXT, "note", "Note"),),
        )
    )
    try:
        refused = ask(client, base, entity="nosearch", search="berlin")
        assert refused.status_code == 400 and "cannot be searched" in str(refused.json())
        assert ask(client, base, entity="nosearch").status_code == 200  # unchanged without search
    finally:
        entities._ENTITIES.pop("nosearch", None)
    # a judge is refused before any search runs
    assert ask(judge, base, search="berlin").status_code == 403


def test_search_fields_must_be_registered_text_fields():
    with pytest.raises(ValueError, match="registered text field"):
        entities.register(
            entities.Entity(
                key="bad",
                label="Bad",
                roles=(),
                base=lambda event, user: None,
                fields=(entities.Field("n", entities.NUMBER, "n", "N"),),
                search_fields=("n",),
            )
        )


def test_sort_puts_empty_values_last_in_both_directions_and_is_stable():
    _, event, _, client, _, base = world()
    applicants(event, ROWS)  # only the two waitlisted rows have a waitlist position
    up = ask(client, base, sort="waitlist_position,username")
    assert names(up) == ["cyd", "dee", "ada", "ben", "eve"]
    down = ask(client, base, sort="-waitlist_position,username")
    assert names(down) == [
        "dee",
        "cyd",
        "ada",
        "ben",
        "eve",
    ]  # empty still last, ties by the next key
    # three keys are allowed, four are refused with the key named
    assert ask(client, base, sort="status,username,created_at").status_code == 200
    refused = ask(client, base, sort="status,username,created_at,waitlist_position")
    assert refused.status_code == 400 and "sort" in refused.json()
    # the same request twice reads the same order (primary key breaks the last tie)
    assert names(ask(client, base, sort="status")) == names(ask(client, base, sort="status"))
