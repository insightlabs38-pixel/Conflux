import re

import pytest
from accounts.models import User
from audit.models import AuditEvent
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from events.models import Event
from projects.models import Project
from taxonomy.models import Taxonomy, TaxonomyAssignment, TaxonomyTerm
from test_sponsor_portal import client_for
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
JSON = "application/json"


def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    users = {}
    for name, role in (("org", Role.ORGANIZER), ("part", Role.PARTICIPANT), ("judge", Role.JUDGE)):
        users[name] = User.objects.create_user(username=name, password="x")
        Membership.objects.create(workspace=workspace, user=users[name], role=role)
    project = Project.objects.create(event=event, created_by=users["part"], name="P")
    return workspace, event, users, project


def urls(workspace, event):
    base = f"/api/v1/workspaces/{workspace.public_id}/"
    return base + "taxonomies/", base + f"events/{event.public_id}/taxonomy-assignments/"


def create(client, url, **extra):
    body = {
        "key": "domain",
        "name": "Domain",
        "applies_to": "project",
        "terms": [{"key": "health", "label": "Health"}, {"key": "edu", "label": "Education"}],
        **extra,
    }
    return client.post(url, body, content_type=JSON)


def test_organizers_define_taxonomies_and_others_are_denied():
    workspace, event, users, _ = world()
    taxonomies, assignments = urls(workspace, event)
    organizer = client_for(users["org"])
    created = create(organizer, taxonomies)
    assert created.status_code == 201, created.content
    assert [t["key"] for t in created.json()["terms"]] == ["health", "edu"]
    assert create(organizer, taxonomies).status_code == 400
    for name in ("part", "judge"):
        other = client_for(users[name])
        assert other.get(taxonomies).status_code == 403
        assert create(other, taxonomies, key="x").status_code == 403
        assert other.get(assignments).status_code == 403
    assert AuditEvent.objects.filter(action="taxonomy.created").count() == 1


@pytest.mark.parametrize(
    "bad",
    [
        {"key": "Bad Key"},
        {"applies_to": "team"},
        {"unknown": 1},
        {"terms": [{"key": "a", "label": "A"}, {"key": "a", "label": "B"}]},
        {"terms": [{"key": "a", "label": "A", "extra": 1}]},
        {"terms": [{"key": f"t{i}", "label": "T"} for i in range(51)]},
    ],
)
def test_taxonomy_definitions_are_validated(bad):
    workspace, event, users, _ = world()
    assert create(client_for(users["org"]), urls(workspace, event)[0], **bad).status_code == 400
    assert not Taxonomy.objects.exists()


def test_assignment_replaces_terms_validates_scope_and_is_audited():
    workspace, event, users, project = world()
    taxonomies, assignments = urls(workspace, event)
    organizer = client_for(users["org"])
    taxonomy = create(organizer, taxonomies).json()
    put = lambda terms, **kw: organizer.put(  # noqa: E731
        assignments,
        {
            "taxonomy": taxonomy["public_id"],
            "subject": {"type": "project", "id": str(project.public_id)},
            "terms": terms,
            **kw,
        },
        content_type=JSON,
    )
    assert put(["health"]).status_code == 200
    assert put(["health", "edu"]).status_code == 400
    assert put(["nope"]).status_code == 400
    assert put(["edu"]).status_code == 200
    listed = organizer.get(assignments + "?taxonomy=domain").json()
    assert listed == [
        {
            "taxonomy": "domain",
            "term": "edu",
            "subject": {"type": "project", "id": str(project.public_id)},
        }
    ]
    assert organizer.get(assignments + "?term=health").json() == []
    assert put([]).status_code == 200 and organizer.get(assignments).json() == []
    changes = [
        e.metadata for e in AuditEvent.objects.filter(action="taxonomy.assigned").order_by("id")
    ]
    assert [(c["before"], c["after"]) for c in changes] == [
        ([], ["health"]),
        (["health"], ["edu"]),
        (["edu"], []),
    ]


def test_subjects_must_belong_to_this_event_and_workspace():
    workspace, event, users, project = world()
    other_workspace = Workspace.objects.create(name="O", slug="o")
    other_event = Event.objects.create(workspace=other_workspace, name="O", slug="oe")
    foreign_project = Project.objects.create(event=other_event, created_by=users["part"], name="F")
    stranger = User.objects.create_user(username="stranger", password="x")
    taxonomies, assignments = urls(workspace, event)
    organizer = client_for(users["org"])
    project_tax = create(organizer, taxonomies).json()
    person_tax = create(
        organizer, taxonomies, key="level", name="Level", applies_to="person",
        terms=[{"key": "novice", "label": "Novice"}],
    ).json()  # fmt: skip

    def put(tax, subject, terms):
        return organizer.put(
            assignments,
            {"taxonomy": tax["public_id"], "subject": subject, "terms": terms},
            content_type=JSON,
        )

    assert (
        put(
            project_tax, {"type": "project", "id": str(foreign_project.public_id)}, ["edu"]
        ).status_code
        == 404
    )
    assert (
        put(person_tax, {"type": "person", "id": str(stranger.public_id)}, ["novice"]).status_code
        == 404
    )
    assert (
        put(
            person_tax, {"type": "person", "id": str(users["part"].public_id)}, ["novice"]
        ).status_code
        == 200
    )
    assert (
        put(
            project_tax, {"type": "person", "id": str(users["part"].public_id)}, ["edu"]
        ).status_code
        == 400
    )
    foreign_taxonomy = Taxonomy.objects.create(
        workspace=other_workspace, key="domain", name="D", applies_to="project"
    )
    assert (
        put(
            {"public_id": str(foreign_taxonomy.public_id)},
            {"type": "project", "id": str(project.public_id)},
            [],
        ).status_code
        == 404
    )


def test_event_taxonomy_and_archived_event_freeze():
    workspace, event, users, _ = world()
    taxonomies, assignments = urls(workspace, event)
    organizer = client_for(users["org"])
    tax = create(
        organizer, taxonomies, key="format", name="Format", applies_to="event",
        terms=[{"key": "hybrid", "label": "Hybrid"}],
    ).json()  # fmt: skip
    body = {"taxonomy": tax["public_id"], "subject": {"type": "event"}, "terms": ["hybrid"]}
    assert organizer.put(assignments, body, content_type=JSON).status_code == 200
    body["subject"]["id"] = str(event.public_id)
    assert organizer.put(assignments, body, content_type=JSON).status_code == 400
    del body["subject"]["id"]
    Event.objects.filter(pk=event.pk).update(status="archived")
    assert organizer.put(assignments, {**body, "terms": []}, content_type=JSON).status_code == 400
    assert len(organizer.get(assignments).json()) == 1


def test_terms_in_use_and_multiplicity_are_protected_and_delete_needs_no_assignments():
    workspace, event, users, project = world()
    taxonomies, assignments = urls(workspace, event)
    organizer = client_for(users["org"])
    tax = create(organizer, taxonomies, allows_multiple=True).json()
    detail = taxonomies + f"{tax['public_id']}/"
    organizer.put(
        assignments,
        {
            "taxonomy": tax["public_id"],
            "subject": {"type": "project", "id": str(project.public_id)},
            "terms": ["health", "edu"],
        },
        content_type=JSON,
    )
    patch = lambda body: organizer.patch(detail, body, content_type=JSON)  # noqa: E731
    assert patch({"allows_multiple": False}).status_code == 400
    assert patch({"terms": [{"key": "health", "label": "Health"}]}).status_code == 400
    renamed = patch(
        {
            "name": "Area",
            "terms": [{"key": "edu", "label": "Learning"}, {"key": "health", "label": "Health"}],
        }
    )
    assert renamed.status_code == 200 and renamed.json()["terms"][0]["label"] == "Learning"
    assert organizer.delete(detail).status_code == 400
    TaxonomyAssignment.objects.all().delete()
    assert patch({"terms": []}).status_code == 200
    assert organizer.delete(detail).status_code == 204
    assert organizer.get(detail).status_code == 404


def test_database_rejects_inconsistent_or_duplicate_assignments():
    workspace, event, users, project = world()
    taxonomy = Taxonomy.objects.create(workspace=workspace, key="d", name="D", applies_to="project")
    term = TaxonomyTerm.objects.create(taxonomy=taxonomy, key="a", label="A")
    with pytest.raises(IntegrityError), transaction.atomic():
        TaxonomyAssignment.objects.create(event=event, term=term, subject_type="project")
    TaxonomyAssignment.objects.create(
        event=event, term=term, subject_type="project", project=project
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        TaxonomyAssignment.objects.create(
            event=event, term=term, subject_type="project", project=project
        )
    other = Event.objects.create(workspace=workspace, name="E2", slug="e2")
    with pytest.raises(ValidationError):
        TaxonomyAssignment(
            event=other, term=term, subject_type="project", project=project
        ).full_clean()


def test_labels_never_influence_results_or_public_pages():
    from django.test import Client

    workspace, event, users, project = world()
    Event.objects.filter(pk=event.pk).update(is_public=True, status="open")

    def page():
        return re.sub(
            rb'csrfmiddlewaretoken" value="[^"]*',
            b"",
            Client().get(f"/e/{event.public_id}/").content,
        )

    before = page()
    taxonomy = Taxonomy.objects.create(
        workspace=workspace, key="d", name="Secret area", applies_to="event"
    )
    term = TaxonomyTerm.objects.create(taxonomy=taxonomy, key="a", label="Secret label")
    TaxonomyAssignment.objects.create(event=event, term=term, subject_type="event")
    after = page()
    assert before == after and b"Secret" not in after
