import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from events.models import Event
from policies.models import Action, Policy, PolicyBinding
from policies.services import check_action
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def test_a_malformed_ast_is_rejected_at_save_time():
    event = make_event()
    policy = Policy(event=event, name="Bad", ast={"op": "shell_exec"})
    with pytest.raises(ValidationError):
        policy.full_clean()


def test_a_well_formed_ast_saves():
    event = make_event()
    policy = Policy(
        event=event, name="Organizers only", ast={"op": "eq", "fact": "role", "value": "organizer"}
    )
    policy.full_clean()
    policy.save()
    assert Policy.objects.count() == 1


def test_a_binding_cannot_reference_a_policy_from_another_event():
    event_a, event_b = make_event("A"), make_event("B")
    policy = Policy.objects.create(event=event_b, name="P", ast={"op": "true"})
    binding = PolicyBinding(event=event_a, action=Action.SUBMIT, policy=policy)
    with pytest.raises(ValidationError):
        binding.clean()


def test_only_one_binding_per_action_per_event():
    event = make_event()
    p1 = Policy.objects.create(event=event, name="P1", ast={"op": "true"})
    p2 = Policy.objects.create(event=event, name="P2", ast={"op": "false"})
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=p1)
    with pytest.raises(IntegrityError):
        PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=p2)


# --- check_action ------------------------------------------------------


def test_an_unbound_action_is_allowed_by_default():
    event = make_event()
    allowed, reason = check_action(event, Action.SUBMIT, {})
    assert allowed is True
    assert reason is None


def test_a_bound_action_is_gated_by_its_policy():
    event = make_event()
    policy = Policy.objects.create(
        event=event, name="Organizers only", ast={"op": "eq", "fact": "role", "value": "organizer"}
    )
    PolicyBinding.objects.create(event=event, action=Action.ADVANCE, policy=policy)

    allowed, reason = check_action(event, Action.ADVANCE, {"role": "organizer"})
    assert allowed is True
    assert reason is None

    denied, reason = check_action(event, Action.ADVANCE, {"role": "participant"})
    assert denied is False
    assert "Organizers only" in reason


def test_a_bound_action_fails_closed_on_a_missing_fact():
    event = make_event()
    policy = Policy.objects.create(
        event=event, name="Needs role", ast={"op": "eq", "fact": "role", "value": "organizer"}
    )
    PolicyBinding.objects.create(event=event, action=Action.VOTE, policy=policy)

    allowed, reason = check_action(event, Action.VOTE, {})  # no "role" fact supplied
    assert allowed is False
    assert reason is not None
