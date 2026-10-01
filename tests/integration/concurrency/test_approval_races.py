"""PD-F002-B01-T06: approvals under real concurrent transactions."""

from datetime import timedelta

import pytest
from accounts.models import User
from core import approvals
from core.models import ApprovalRequest
from django.db import transaction
from django.utils import timezone
from events.models import Event
from test_pvs_races import race, requires_real_db
from workspaces.models import Membership, Role, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]

DONE = []


def thing(event, actor):
    with transaction.atomic():
        approvals.require_approval(
            event=event, actor=actor, action="test_race", payload={"n": 1}, summary=["x"]
        )
        DONE.append(1)


@pytest.fixture
def world():
    DONE.clear()
    approvals.register_policy(
        approvals.ApprovalPolicy("test_race", "R", "x", (Role.ORGANIZER,), min_approvals=2)
    )
    workspace = Workspace.objects.create(name="AR", slug="ar")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    users = {}
    for name in ("a", "b", "c"):
        users[name] = User.objects.create_user(username=name)
        Membership.objects.create(workspace=workspace, user=users[name], role=Role.ORGANIZER)
    approvals.set_gate(event=event, actor=users["a"], action="test_race", enabled=True)
    yield event, users
    approvals.POLICIES.pop("test_race", None)


def _approved(event, users):
    request = ApprovalRequest.objects.create(
        workspace=event.workspace,
        event=event,
        action="test_race",
        digest=approvals.digest_of("test_race", ("", ""), {"n": 1}),
        requested_by=users["a"],
        required_approvals=1,
        status="approved",
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return request


def test_one_approval_is_spent_once_under_a_race(world):
    event, users = world
    request = _approved(event, users)

    def attempt():
        try:
            thing(event, users["a"])
            return "ran"
        except approvals.ApprovalRequired:
            return "held"

    outcomes = race([attempt] * 4)
    assert sorted(outcomes) == ["held", "held", "held", "ran"]
    assert DONE == [1]
    request.refresh_from_db()
    assert request.status == "executed"


def test_simultaneous_asks_for_one_operation_share_one_pending_request(world):
    event, users = world

    def ask():
        try:
            thing(event, users["a"])
        except approvals.ApprovalRequired as needed:
            return needed.respond(users["a"]).data["approval"]["public_id"]

    ids = race([ask] * 4)
    assert len(set(ids)) == 1 and ApprovalRequest.objects.count() == 1


def test_two_approvers_at_once_reach_exactly_one_approval(world):
    event, users = world
    try:
        thing(event, users["a"])
    except approvals.ApprovalRequired as needed:
        request = ApprovalRequest.objects.get(
            public_id=needed.respond(users["a"]).data["approval"]["public_id"]
        )
    race(
        [
            lambda: approvals.decide(request, users["b"], "approve"),
            lambda: approvals.decide(request, users["c"], "approve"),
        ]
    )
    request.refresh_from_db()
    assert request.status == "approved" and request.decisions.count() == 2
