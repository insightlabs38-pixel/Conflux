import pytest
from events.models import Event
from policies.models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from policies.services import base_facts, explain_action
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def test_an_unbound_action_explains_itself_without_a_policy_name():
    event = make_event()
    decision = explain_action(event, Action.SUBMIT, {})
    assert decision.allowed is True
    assert decision.policy_name is None
    assert "allowed" in decision.explain().lower()


def test_a_denied_action_names_the_policy_in_its_explanation():
    event = make_event()
    policy = Policy.objects.create(event=event, name="Organizers only", ast={"op": "false"})
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)

    decision = explain_action(event, Action.SUBMIT, {})
    assert decision.allowed is False
    assert decision.policy_name == "Organizers only"
    assert "Organizers only" in decision.explain()


def test_an_exception_grant_is_named_in_the_explanation():
    event = make_event()
    policy = Policy.objects.create(event=event, name="Closed", ast={"op": "false"})
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)
    ExceptionGrant.objects.create(
        event=event,
        action=Action.SUBMIT,
        subject_type="team",
        subject_id="tm_01",
        reason="Approved late entry.",
    )

    decision = explain_action(event, Action.SUBMIT, {}, subject_type="team", subject_id="tm_01")
    assert decision.allowed is True
    assert decision.exception_grant_reason == "Approved late entry."
    assert "Approved late entry." in decision.explain()


def test_gate_facts_are_captured_in_the_evidence_without_being_persisted():
    event = make_event()
    TemporalGate.objects.create(event=event, name="submissions", closes_at=None)
    facts = base_facts(event)

    decision = explain_action(event, Action.SUBMIT, facts)

    assert decision.gate_facts == {"gate_open:submissions": True}
    # Nothing about this call writes a row anywhere: the evidence exists
    # only as this return value.
    assert Policy.objects.count() == 0
