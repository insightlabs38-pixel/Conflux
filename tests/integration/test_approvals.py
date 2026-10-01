"""PD-F002-B01-T06: approval gates through one primitive, with an independent consumer."""

from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import approvals
from core.models import ApprovalGate, ApprovalRequest
from django.db import transaction
from django.test import Client
from django.utils import timezone
from events.models import Event
from rest_framework.exceptions import PermissionDenied, ValidationError
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

DONE = []


def do_thing(event, actor, payload, *, fail=False):
    """A toy operation gated the way a real one is: inside its own transaction."""
    with transaction.atomic():
        approvals.require_approval(
            event=event,
            actor=actor,
            action="test_thing",
            payload=payload,
            summary=[f"Do the thing with {payload['n']}"],
            subject=("thing", "t1"),
        )
        if fail:
            raise RuntimeError("boom")
        DONE.append(payload["n"])


THING = approvals.ApprovalPolicy(
    "test_thing", "Doing the thing", "A toy.", deciders=(Role.ORGANIZER,)
)


@pytest.fixture(autouse=True)
def policy():
    DONE.clear()
    approvals.register_policy(THING)
    yield
    for key in [k for k in approvals.POLICIES if k.startswith("test_")]:
        approvals.POLICIES.pop(key)


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
        ("org3", Role.ORGANIZER),
        ("par", Role.PARTICIPANT),
    ):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    return {
        "workspace": workspace,
        "event": event,
        "people": people,
        "client": {name: _client(user) for name, user in people.items()},
        "base": base,
    }


def gate_on(w, action="test_thing"):
    approvals.set_gate(event=w["event"], actor=w["people"]["org"], action=action, enabled=True)


def ask(w, n=1, who="org"):
    """Try the operation as `who`; returns (the 409 body, request) or runs it."""
    try:
        do_thing(w["event"], w["people"][who], {"n": n})
    except approvals.ApprovalRequired as needed:
        response = needed.respond(w["people"][who])
        return response.data, ApprovalRequest.objects.get(
            public_id=response.data["approval"]["public_id"]
        )
    return None, None


def answer(w, request, who, decision="approve", note=""):
    return w["client"][who].post(
        w["base"] + f"approvals/{request.public_id}/decision/",
        data={"decision": decision, "note": note},
        content_type="application/json",
    )


def test_with_the_gate_off_nothing_changes(world):
    do_thing(world["event"], world["people"]["org"], {"n": 1})
    assert DONE == [1] and not ApprovalRequest.objects.exists()
    assert not AuditEvent.objects.filter(action__startswith="approval.").exists()


def test_a_gated_operation_waits_for_a_second_person_then_runs_once(world):
    gate_on(world)
    body, request = ask(world)
    assert DONE == [] and body["code"] == "approval_required"
    assert body["approval"]["status"] == "pending" and body["approval"]["summary"] == [
        "Do the thing with 1"
    ]
    assert AuditEvent.objects.filter(action="approval.requested").count() == 1
    # Asking again for the same operation finds the same request.
    _, same = ask(world, who="org2")
    assert same.pk == request.pk and ApprovalRequest.objects.count() == 1

    approved = answer(world, request, "org2", note="Looks right")
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert approved.json()["decisions"][0]["note"] == "Looks right"
    do_thing(world["event"], world["people"]["org"], {"n": 1})
    assert DONE == [1]
    request.refresh_from_db()
    assert request.status == "executed" and request.executed_at
    assert AuditEvent.objects.filter(action="approval.executed").count() == 1
    # The approval was spent: the same operation needs a new one.
    body, again = ask(world)
    assert body["code"] == "approval_required" and again.pk != request.pk


def test_an_approval_is_for_exactly_what_the_approvers_read(world):
    gate_on(world)
    _, request = ask(world, n=1)
    answer(world, request, "org2")
    _, other = ask(world, n=2)  # a different payload is a different operation
    assert DONE == [] and other.pk != request.pk
    do_thing(world["event"], world["people"]["org"], {"n": 1})
    assert DONE == [1]


def test_the_operation_rolling_back_does_not_spend_the_approval(world):
    gate_on(world)
    _, request = ask(world)
    answer(world, request, "org2")
    with pytest.raises(RuntimeError):
        do_thing(world["event"], world["people"]["org"], {"n": 1}, fail=True)
    request.refresh_from_db()
    assert request.status == "approved" and DONE == []
    do_thing(world["event"], world["people"]["org"], {"n": 1})
    assert DONE == [1]


def test_who_may_decide_and_how_often(world):
    gate_on(world)
    _, request = ask(world)
    own = answer(world, request, "org")
    assert own.status_code == 400 and "own request" in str(own.json())
    assert answer(world, request, "par").status_code == 404  # no role, no existence
    assert answer(world, request, "org", decision="maybe").status_code == 400
    assert (
        world["client"]["org2"]
        .post(
            world["base"] + f"approvals/{request.public_id}/decision/",
            data={"decision": "approve", "note": "x" * 501},
            content_type="application/json",
        )
        .status_code
        == 400
    )
    assert answer(world, request, "org2").status_code == 200
    again = answer(world, request, "org2")
    assert again.status_code == 409 and again.json()["code"] == "approval_closed"


def test_more_than_one_approval_can_be_required_and_one_rejection_ends_it(world):
    approvals.register_policy(
        approvals.ApprovalPolicy("test_two", "Two", "x", (Role.ORGANIZER,), min_approvals=2)
    )
    gate_on(world, "test_two")
    needed = ApprovalRequest.objects.create(
        workspace=world["workspace"],
        event=world["event"],
        action="test_two",
        digest="d" * 64,
        requested_by=world["people"]["org"],
        required_approvals=2,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    assert answer(world, needed, "org2").json()["status"] == "pending"
    assert answer(world, needed, "org3").json()["status"] == "approved"
    other = ApprovalRequest.objects.create(
        workspace=world["workspace"],
        event=world["event"],
        action="test_two",
        digest="e" * 64,
        requested_by=world["people"]["org"],
        required_approvals=2,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    assert answer(world, other, "org2", "reject", "No").json()["status"] == "rejected"
    assert answer(world, other, "org3").status_code == 409
    assert AuditEvent.objects.filter(action="approval.rejected").count() == 1


def test_expiry_is_enforced_on_decide_and_consume_and_by_the_sweep(world):
    gate_on(world)
    _, stale = ask(world, n=1)
    _, approved = ask(world, n=2)
    answer(world, approved, "org2")
    past = timezone.now() - timedelta(minutes=1)
    ApprovalRequest.objects.filter(pk__in=[stale.pk, approved.pk]).update(expires_at=past)

    assert (
        world["client"]["org"].get(world["base"] + f"approvals/{stale.public_id}/").json()["status"]
        == "expired"
    )  # visible as expired before the sweep
    refused = answer(world, stale, "org2")
    assert refused.status_code == 409 and "expired" in refused.json()["detail"]
    with pytest.raises(approvals.ApprovalRequired):
        do_thing(
            world["event"], world["people"]["org"], {"n": 2}
        )  # an old approval is not spendable
    assert DONE == []
    assert approvals.sweep() == 1  # the approved one; the refusal already marked the other
    assert set(ApprovalRequest.objects.values_list("status", flat=True)) == {"expired"}
    # A fresh ask after expiry opens a new pending request.
    _, fresh = ask(world, n=1)
    assert fresh.status == "pending" and fresh.pk != stale.pk


def test_a_request_can_be_withdrawn_but_not_after_it_is_used(world):
    gate_on(world)
    _, request = ask(world)
    assert (
        world["client"]["par"]
        .post(world["base"] + f"approvals/{request.public_id}/cancel/")
        .status_code
        == 404
    )
    done = world["client"]["org"].post(world["base"] + f"approvals/{request.public_id}/cancel/")
    assert done.status_code == 200 and done.json()["status"] == "cancelled"
    again = world["client"]["org"].post(world["base"] + f"approvals/{request.public_id}/cancel/")
    assert again.status_code == 409
    assert answer(world, request, "org2").status_code == 409
    _, second = ask(world)
    assert (
        world["client"]["org2"]
        .post(  # a decider may also withdraw it
            world["base"] + f"approvals/{second.public_id}/cancel/"
        )
        .json()["status"]
        == "cancelled"
    )


def test_a_preview_collects_the_need_instead_of_failing(world):
    gate_on(world)
    with transaction.atomic(), approvals.dry_run() as needed:
        do_thing(world["event"], world["people"]["org"], {"n": 1})
    assert [n["action"] for n in needed] == ["test_thing"]
    assert needed[0]["summary"] == ["Do the thing with 1"]
    assert not ApprovalRequest.objects.exists()


def test_who_sees_which_requests(world):
    gate_on(world)
    _, request = ask(world, who="org")
    ids = lambda who, q="": [  # noqa: E731
        a["public_id"] for a in world["client"][who].get(world["base"] + "approvals/" + q).json()
    ]
    assert ids("org") == ids("org2") == [str(request.public_id)]
    assert ids("par") == []
    assert (
        world["client"]["par"].get(world["base"] + f"approvals/{request.public_id}/").status_code
        == 404
    )
    detail = world["client"]["org2"].get(world["base"] + f"approvals/{request.public_id}/").json()
    assert detail["can_decide"] is True and detail["can_cancel"] is True
    mine = world["client"]["org"].get(world["base"] + f"approvals/{request.public_id}/").json()
    assert mine["can_decide"] is False  # one may not approve one's own request
    assert ids("org", "?status=pending") == [str(request.public_id)]
    assert ids("org", "?status=approved") == []
    assert world["client"]["org"].get(world["base"] + "approvals/?status=zzz").status_code == 400
    assert world["client"]["org"].get(world["base"] + "approvals/?limit=0").status_code == 400
    # A different workspace's organizer cannot reach them.
    other = Workspace.objects.create(name="O", slug="o")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    url = f"/api/v1/workspaces/{other.public_id}/events/{world['event'].public_id}/approvals/"
    assert _client(stranger).get(url).status_code == 404


def test_gates_are_listed_switched_audited_and_off_by_default(world):
    listed = world["client"]["org"].get(world["base"] + "approval-gates/").json()
    thing = next(g for g in listed if g["action"] == "test_thing")
    assert thing["enabled"] is False and thing["deciders"] == ["organizer"]
    url = world["base"] + "approval-gates/test_thing/"

    def put(who, value):
        return world["client"][who].put(
            url, data={"enabled": value}, content_type="application/json"
        )

    assert put("par", True).status_code == 403
    assert put("org", True).json()["enabled"] is True
    assert put("org", True).status_code == 200  # no change, no second audit entry
    assert AuditEvent.objects.filter(action="approval.gate_changed").count() == 1
    assert ApprovalGate.objects.get(event=world["event"], action="test_thing").enabled
    assert put("org", False).json()["enabled"] is False
    assert AuditEvent.objects.filter(action="approval.gate_changed").count() == 2
    unknown = world["client"]["org"].put(
        world["base"] + "approval-gates/nope/",
        data={"enabled": True},
        content_type="application/json",
    )
    assert unknown.status_code == 400
    assert (
        world["client"]["org"].put(url, data={}, content_type="application/json").status_code == 400
    )
    world["event"].status = "archived"
    world["event"].save()
    assert put("org", True).status_code == 400


def test_the_setting_registry_reports_the_gate(world):
    url = world["base"] + "configuration/"
    entry = next(
        s
        for s in world["client"]["org"].get(url).json()["settings"]
        if s["key"] == "approvals.message_send"
    )
    assert entry["value"] is False and entry["editable"] and entry["tier"] == "advanced"
    approvals.set_gate(
        event=world["event"], actor=world["people"]["org"], action="message_send", enabled=True
    )
    entry = next(
        s
        for s in world["client"]["org"].get(url).json()["settings"]
        if s["key"] == "approvals.message_send"
    )
    assert entry["value"] is True


def test_registration_is_strict(world):
    with pytest.raises(ValueError):
        approvals.register_policy(
            approvals.ApprovalPolicy("test_thing", "Different", "x", (Role.ADMIN,))
        )
    approvals.register_policy(THING)  # the identical one is harmless
    with pytest.raises(ValueError):
        approvals.register_policy(approvals.ApprovalPolicy("test_bad", "B", "x", ()))
    with pytest.raises(ValueError):
        approvals.require_approval(
            event=world["event"],
            actor=world["people"]["org"],
            action="nope",
            payload={},
            summary=[],
        )
    with pytest.raises(PermissionDenied):
        approvals.decide(
            ApprovalRequest.objects.create(
                workspace=world["workspace"],
                event=world["event"],
                action="test_thing",
                digest="a" * 64,
                requested_by=world["people"]["org"],
                expires_at=timezone.now() + timedelta(hours=1),
            ),
            world["people"]["par"],
            "approve",
        )
    with pytest.raises(ValidationError):
        approvals.set_gate(
            event=world["event"], actor=world["people"]["org"], action="nope", enabled=True
        )


def test_the_state_graph_only_moves_forward(world):
    gate_on(world)
    _, request = ask(world)
    answer(world, request, "org2")
    do_thing(world["event"], world["people"]["org"], {"n": 1})
    from core.approvals import ApprovalStateError

    with pytest.raises(ApprovalStateError):
        approvals.cancel(ApprovalRequest.objects.get(pk=request.pk), world["people"]["org"])
