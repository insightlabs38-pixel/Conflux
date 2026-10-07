"""PD-F002-B03-T90: cross-cutting proofs for the preview-context primitive.

The behavior is proved next to the primitive (docs/verification/PD-F002-B03/MATRIX.md). This file
proves what only holds across the platform: the registry and inventory agree with the code, every
kind of caller is refused or admitted as intended, a preview leaves no trace, and nothing outside
the endpoint can be steered by a context.
"""

import json
import pathlib
import re

import pytest
import yaml
from accounts.models import Session, User
from audit.models import AuditEvent
from core import manifest, preview_context
from django.test import Client
from events.models import Event
from forms.models import FormDefinition, FormVersion
from forms.services import create_form, publish_form, save_draft
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "api"


def test_the_primitive_registry_marks_the_owner_implemented():
    document = yaml.safe_load(
        (ROOT / "docs/product-depth-v3/PRIMITIVE_REGISTRY.yaml").read_text(encoding="utf-8")
    )
    state = {
        p["id"]: p["status"]
        for p in document["primitives"]
        if p["owner_task"].startswith("PD-F002-B03")
    }
    assert state == {"PREVIEW_CONTEXT": "IMPLEMENTED"}


def test_the_surfaces_are_exactly_what_production_registers_and_the_inventory_agrees():
    assert set(preview_context.SURFACES) == {"form", "page"}
    page = preview_context.SURFACES["page"]  # the public page, with an unsaved appearance as input
    assert page.version_source is None and page.roles == () and page.input_schema
    form = preview_context.SURFACES["form"]
    assert form.version_source == "form" and form.roles == (
        "participant",
        "judge",
        "organizer",
        "public",
    )
    snapshot = manifest.snapshot()
    kinds = {
        c["kind"]: {e["id"]: e["manifest"] for e in c["entries"]} for c in snapshot["capabilities"]
    }
    assert kinds["preview_surface"] == {"form": "forms", "page": "presentation"}
    assert snapshot["ok"] is True and snapshot["problems"] == []


def test_no_context_is_read_by_a_header_cookie_session_or_a_domain_write():
    """The context is the body of one endpoint; nothing elsewhere reads it."""
    allowed = {
        "core/manifest_core.py", "core/preview_context.py", "core/preview_context_views.py",
        "core/urls.py", "forms/preview.py", "presentation/preview.py",
    }  # fmt: skip
    readers = {
        str(p.relative_to(SRC))
        for p in SRC.rglob("*.py")
        if "preview_context" in p.read_text()
        and "migrations" not in p.parts
        and not p.name.startswith("test_")
    }
    assert readers == allowed
    for p in SRC.rglob("*.py"):
        if "migrations" in p.parts or p.name.startswith("test_"):
            continue
        text = p.read_text()
        assert not re.search(
            r"META\[.HTTP_X_PREVIEW|X-Preview|preview_as_user|session\[.preview", text
        ), p


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    foreign = Workspace.objects.create(name="F", slug="f")
    people = {}
    for name, role in (("org", Role.ORGANIZER), ("admin", Role.ADMIN), ("par", Role.PARTICIPANT),
                       ("judge", Role.JUDGE), ("sponsor", Role.SPONSOR)):  # fmt: skip
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["stranger"] = User.objects.create_user(username="stranger", password="unused")
    Membership.objects.create(user=people["stranger"], workspace=foreign, role=Role.ORGANIZER)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    definition = create_form(event, "Application")
    save_draft(definition, {"fields": [{"id": "pitch", "type": "text", "label": "Pitch",
                                        "visible_to": ["participant", "organizer"]}]})  # fmt: skip
    publish_form(definition)
    clients = {}
    for name, user in people.items():
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        clients[name] = client
    return {
        "event": event, "definition": definition, "client": clients, "anonymous": Client(),
        "url": f"/api/v1/workspaces/{workspace.public_id}/preview-as/form/",
        "ref": {"event": str(event.public_id), "form": str(definition.public_id)},
    }  # fmt: skip


def post(client, world, **body):
    body.setdefault("ref", world["ref"])
    return client.post(world["url"], data=json.dumps(body), content_type="application/json")


def test_only_organizers_and_admins_are_admitted_and_everyone_else_is_refused(world):
    for who in ("org", "admin"):
        assert post(world["client"][who], world).status_code == 200, who
    for who in ("par", "judge", "sponsor", "stranger"):
        assert (
            post(world["client"][who], world, context={"role": "organizer"}).status_code == 403
        ), who
    assert post(world["anonymous"], world).status_code in (401, 403)


def test_asking_to_preview_as_a_role_never_changes_what_the_caller_may_do(world):
    """Previewing as an organizer from a participant account is still the participant's request."""
    participant = world["client"]["par"]
    assert post(participant, world, context={"role": "organizer"}).status_code == 403
    assert participant.put(
        world["url"].replace(
            "preview-as/form/",
            f"events/{world['event'].public_id}/forms/{world['definition'].public_id}/",
        ),
        data=json.dumps({"schema": {"fields": []}}),
        content_type="application/json",
    ).status_code in (403, 404)
    world["definition"].refresh_from_db()
    assert world["definition"].draft_schema["fields"]  # unchanged


def test_a_preview_leaves_no_trace(world):
    before = (
        AuditEvent.objects.count(),
        FormDefinition.objects.count(),
        FormVersion.objects.count(),
    )
    for role in (None, "participant", "judge", "organizer", "public"):
        context = {"role": role} if role else {}
        response = post(world["client"]["org"], world, context=context)
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert (
        AuditEvent.objects.count(),
        FormDefinition.objects.count(),
        FormVersion.objects.count(),
    ) == before
    org = world["client"]["org"]
    for method in ("get", "put", "patch", "delete"):
        assert getattr(org, method)(world["url"]).status_code == 405


def test_a_forged_context_is_data_and_never_authority(world):
    org = world["client"]["org"]
    for context in (
        {"role": "admin"}, {"role": "../../organizer"}, {"as": "root"}, {"role": ["participant"]},
        {"at": "9999-01-01T00:00:00Z"}, {"version": "draft", "at": "2027-01-01T00:00:00Z"},
    ):  # fmt: skip
        response = post(org, world, context=context)
        assert response.status_code == 400, context
        assert all(key.startswith("context") for key in response.json())
    assert post(org, world, context="organizer").status_code == 400
    assert post(org, world, context=None).status_code == 200
