from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from events.models import Event
from policies.models import Action, Policy, PolicyBinding, TemporalGate
from policies.services import base_facts, check_action
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def test_a_gate_with_no_bounds_is_always_open():
    event = make_event()
    gate = TemporalGate.objects.create(event=event, name="submissions")
    assert gate.status() == "open"
    assert gate.is_open() is True


def test_a_gate_before_its_open_time_is_not_yet_open():
    event = make_event()
    future = timezone.now() + timedelta(days=1)
    gate = TemporalGate.objects.create(event=event, name="voting", opens_at=future)
    assert gate.status() == "not_yet_open"
    assert gate.is_open() is False


def test_a_gate_past_its_close_time_is_closed():
    event = make_event()
    past = timezone.now() - timedelta(days=1)
    gate = TemporalGate.objects.create(event=event, name="submissions", closes_at=past)
    assert gate.status() == "closed"
    assert gate.is_open() is False


def test_a_gate_between_its_bounds_is_open():
    event = make_event()
    gate = TemporalGate.objects.create(
        event=event,
        name="submissions",
        opens_at=timezone.now() - timedelta(days=1),
        closes_at=timezone.now() + timedelta(days=1),
    )
    assert gate.status() == "open"


def test_closes_at_must_be_after_opens_at():
    event = make_event()
    now = timezone.now()
    gate = TemporalGate(event=event, name="bad", opens_at=now, closes_at=now - timedelta(days=1))
    with pytest.raises(ValidationError):
        gate.full_clean()


def test_status_accepts_an_explicit_clock_rather_than_only_the_server_clock():
    """Server time is authoritative for the default; passing `at` explicitly
    is how a caller re-checks against a fixed instant without depending on
    wall-clock drift between two calls in the same request.
    """
    event = make_event()
    opens = timezone.now() + timedelta(hours=1)
    gate = TemporalGate.objects.create(event=event, name="voting", opens_at=opens)
    assert gate.status(at=opens - timedelta(minutes=1)) == "not_yet_open"
    assert gate.status(at=opens + timedelta(minutes=1)) == "open"


# --- base_facts / check_action integration ----------------------------------


def test_base_facts_exposes_gate_open_status_and_the_server_clock():
    event = make_event()
    TemporalGate.objects.create(
        event=event, name="submissions", closes_at=timezone.now() - timedelta(days=1)
    )
    facts = base_facts(event)
    assert facts["gate_open:submissions"] is False
    assert "now" in facts


def test_a_policy_can_gate_on_a_temporal_gate_via_base_facts():
    event = make_event()
    TemporalGate.objects.create(
        event=event, name="submissions", closes_at=timezone.now() - timedelta(days=1)
    )
    policy = Policy.objects.create(
        event=event,
        name="Submissions window",
        ast={"op": "eq", "fact": "gate_open:submissions", "value": True},
    )
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)

    allowed, reason = check_action(event, Action.SUBMIT, base_facts(event))
    assert allowed is False
    assert "Submissions window" in reason
