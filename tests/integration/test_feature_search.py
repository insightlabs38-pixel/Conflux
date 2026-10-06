"""PD-F003-B01-T08: the search claims of the completeness contract, held against the query engine.

A feature is either a registered query entity whose fields are the declared ones, or says why not.
The verifier reads the registry and the models; these tests ask the engine over HTTP: the catalogue
offers exactly the claimed fields to exactly the roles that may read the feature, every claimed
field filters and sorts as declared, an unclaimed field is refused by name, and every entity the
platform registers belongs to a claimed feature."""

import json

import pytest
from core import entities as registry
from core import features as ft
from core import features_search
from events.models import Event
from workspaces.models import Workspace

from tests.integration.test_entity_query import ROWS, applicants, ask, world

pytestmark = pytest.mark.django_db


def claimed():
    found = {}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        got, _, _ = features_search.parse(feature.claims["search"])
        for key in got["entity"]:
            found.setdefault(key, []).append((feature.key, sorted(got["fields"][0].split(","))))
    return found


CLAIMED = claimed()


def test_every_registered_query_entity_belongs_to_exactly_one_claimed_feature():
    assert set(registry.entities()) == set(CLAIMED)
    assert all(len(owners) == 1 for owners in CLAIMED.values())
    for feature in ft.FEATURES.values():
        got, reasons, _ = features_search.parse(feature.claims["search"])
        assert bool(got["entity"]) != ("no_query" in reasons), feature.key


@pytest.mark.parametrize("key", sorted(CLAIMED))
def test_the_catalogue_offers_exactly_the_claimed_fields_to_the_roles_that_may_read(key):
    _, _, _, organizer, judge, base = world()
    offered = {e["key"]: e for e in organizer.get(base).json()}
    assert sorted(f["key"] for f in offered[key]["fields"]) == CLAIMED[key][0][1]
    assert judge.get(base).json() == []
    assert judge.get(base + f"{key}/").status_code == 403


VALUES = {"text": "a", "number": 1, "date": "2027-03-01T00:00:00Z", "bool": True, "uuid": None}


@pytest.mark.parametrize("key", sorted(CLAIMED))
def test_every_claimed_field_filters_and_sorts_as_declared(key):
    _, event, _, client, _, base = world()
    applicants(event, ROWS)
    fields = {f["key"]: f for f in client.get(base).json() and next(
        e for e in client.get(base).json() if e["key"] == key)["fields"]}  # fmt: skip
    for name, spec in fields.items():
        if spec["filterable"]:
            op = spec["operators"][0]
            value = spec["choices"][0] if spec["type"] == "enum" else VALUES.get(spec["type"])
            node = {"field": name, "op": op, "value": value}
            if op == "is_null":
                node = {"field": name, "op": "is_null", "value": True}
            response = ask(client, base, entity=key, filter=json.dumps(node))
            assert response.status_code == 200, (key, name, op, response.content[:200])
        sorted_response = ask(client, base, entity=key, sort=name)
        assert (sorted_response.status_code == 200) == bool(spec["sortable"]), (key, name)
    refused = ask(client, base, entity=key, sort="not_a_claimed_field")
    assert refused.status_code == 400 and "not_a_claimed_field" in json.dumps(refused.json())


def test_a_query_never_reaches_another_events_rows():
    workspace, event, _, client, _, base = world()
    applicants(event, ROWS[:2])
    elsewhere = Event.objects.create(
        workspace=Workspace.objects.get(pk=workspace.pk), name="Other", slug="other"
    )
    applicants(elsewhere, [("zed", "pending", "", 0)])
    names = [row["username"] for row in ask(client, base).json()["rows"]]
    assert names == ["ada", "ben"]
