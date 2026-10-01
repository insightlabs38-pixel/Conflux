"""PD-F002-B01-T04: other apps add bulk actions without editing the planner; receipts read."""

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from audit.services import record_mutation
from communications import bulk
from communications.models import BulkReceipt
from django.test import Client
from events.models import Event
from projects.models import Project
from rest_framework import serializers
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class HideParams(serializers.Serializer):
    projects = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=100)


def _hide(event, actor, op):
    rows = list(
        Project.objects.select_for_update().filter(
            event=event, public_id__in=op["params"]["projects"]
        )
    )
    if len(rows) != len(op["params"]["projects"]):
        from django.core.exceptions import ValidationError

        raise ValidationError("One or more targets are unavailable in this event.")
    for project in rows:
        project.gallery_visible = False
        project.save(update_fields=["gallery_visible", "updated_at"])
        record_mutation(
            actor=actor,
            workspace=event.workspace,
            action="project.gallery_hidden",
            target=project,
        )
    return {"projects": sorted(str(p.public_id) for p in rows)}, len(rows)


HIDE = bulk.BulkAction("hide_projects", "Hide from the gallery", _hide, params=HideParams)


@pytest.fixture
def registered():
    bulk.register_action(HIDE)
    yield HIDE
    bulk.ACTIONS.pop("hide_projects", None)


@pytest.fixture
def case():
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Reg", slug="reg")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    projects = [
        Project.objects.create(event=event, name=f"P{i}", created_by=organizer) for i in range(3)
    ]

    def client(user):
        c = Client()
        c.cookies["session"] = Session.issue(user).token
        return c

    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/operations/bulk/"
    return {
        "workspace": workspace,
        "event": event,
        "projects": projects,
        "organizer": organizer,
        "client": client(organizer),
        "judge": client(judge),
        "url": base,
        "receipts": base + "receipts/",
    }


def hide_op(projects):
    return {"action": "hide_projects", "params": {"projects": [str(p.public_id) for p in projects]}}


def post(c, ops, token=None, client=None):
    data = {"operations": ops, **({"preview_token": token} if token else {})}
    return (client or c["client"]).post(c["url"], data=data, content_type="application/json")


def test_a_registered_action_previews_applies_and_replays_like_a_built_in(case, registered):
    ops = [hide_op(case["projects"][:2])]
    preview = post(case, ops)
    assert preview.status_code == 200, preview.content
    body = preview.json()
    assert body["applied"] is False and body["effects"][0]["action"] == "hide_projects"
    # A preview changes nothing and leaves no receipt or audit behind.
    assert Project.objects.filter(gallery_visible=False).count() == 0
    assert not BulkReceipt.objects.exists() and not AuditEvent.objects.exists()

    applied = post(case, ops, body["preview_token"])
    assert applied.status_code == 200, applied.content
    assert applied.json()["applied"] is True
    assert Project.objects.filter(gallery_visible=False).count() == 2
    assert BulkReceipt.objects.count() == 1
    assert set(AuditEvent.objects.values_list("action", flat=True)) == {
        "project.gallery_hidden",
        "operations.bulk_applied",
    }
    # Retrying the same token replays the saved result and does not repeat the work.
    again = post(case, ops, body["preview_token"])
    assert again.json() == applied.json()
    assert AuditEvent.objects.filter(action="project.gallery_hidden").count() == 2


def test_a_registered_action_can_be_mixed_with_built_ins_and_rolls_back_together(case, registered):
    ops = [
        hide_op(case["projects"][:1]),
        {
            "action": "move",
            "projects": ["00000000-0000-4000-8000-000000000000"],
            "track": "00000000-0000-4000-8000-000000000001",
        },
    ]
    response = post(case, ops)
    assert response.status_code == 400
    assert Project.objects.filter(gallery_visible=False).count() == 0


@pytest.mark.parametrize(
    "op",
    [
        {"action": "hide_projects"},  # params are required
        {"action": "hide_projects", "params": {"projects": []}},
        {"action": "hide_projects", "params": {"projects": ["x"]}},
        {
            "action": "hide_projects",
            "params": {"projects": ["00000000-0000-4000-8000-000000000000"], "extra": 1},
        },
        {
            "action": "hide_projects",
            "projects": ["00000000-0000-4000-8000-000000000000"],
        },  # flat fields
        {"action": "move", "params": {"a": 1}},  # a built-in takes its own flat fields
        {"action": "nonsense"},
    ],
)
def test_bad_operations_are_refused_without_writes(case, registered, op):
    response = post(case, [op])
    assert response.status_code == 400, response.content
    assert not BulkReceipt.objects.exists() and not AuditEvent.objects.exists()


def test_an_unregistered_action_is_unknown_and_registration_is_strict(case):
    assert post(case, [hide_op(case["projects"])]).status_code == 400
    bulk.register_action(HIDE)
    try:
        bulk.register_action(HIDE)  # the same registration again is harmless
        other = bulk.BulkAction("hide_projects", "Different", _hide, params=HideParams)
        with pytest.raises(ValueError):
            bulk.register_action(other)
    finally:
        bulk.ACTIONS.pop("hide_projects", None)
    assert set(bulk.ACTIONS) == {"assign", "advance", "extend", "move", "send"}


def test_receipts_are_listed_newest_first_and_readable_in_full(case, registered):
    first = post(case, [hide_op(case["projects"][:1])])
    token = first.json()["preview_token"]
    post(case, [hide_op(case["projects"][:1])], token)
    second_ops = [hide_op(case["projects"][1:2])]
    post(case, second_ops, post(case, second_ops).json()["preview_token"])

    listed = case["client"].get(case["receipts"])
    assert listed.status_code == 200, listed.content
    rows = listed.json()
    assert len(rows) == 2 and listed["X-Total-Count"] == "2"
    assert rows[0]["created_at"] >= rows[1]["created_at"]
    assert rows[0]["actions"] == ["hide_projects"] and rows[0]["actor"] == "org"
    assert "effects" not in rows[0]
    page = case["client"].get(case["receipts"], {"limit": 1, "offset": 1}).json()
    assert [r["public_id"] for r in page] == [rows[1]["public_id"]]
    assert case["client"].get(case["receipts"], {"limit": 0}).status_code == 400

    detail = case["client"].get(f"{case['receipts']}{rows[0]['public_id']}/").json()
    assert detail["effects"][0]["action"] == "hide_projects"
    assert detail["effects"][0]["projects"] == [str(case["projects"][1].public_id)]


def test_receipts_are_organizer_only_and_event_scoped(case, registered):
    post(
        case,
        [hide_op(case["projects"][:1])],
        post(case, [hide_op(case["projects"][:1])]).json()["preview_token"],
    )
    receipt = BulkReceipt.objects.get()
    assert case["judge"].get(case["receipts"]).status_code == 403
    assert Client().get(case["receipts"]).status_code in (401, 403)
    other = Event.objects.create(workspace=case["workspace"], name="O", slug="o")
    foreign = case["receipts"].replace(str(case["event"].public_id), str(other.public_id))
    assert case["client"].get(foreign).json() == []
    assert case["client"].get(f"{foreign}{receipt.public_id}/").status_code == 404
    assert case["judge"].get(f"{case['receipts']}{receipt.public_id}/").status_code == 403
