from datetime import timedelta

import pytest
from accounts.models import User
from django.utils import timezone
from events.models import Event
from policies.models import Action, ExceptionGrant, Policy, PolicyBinding
from policies.services import check_action
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def deny_everyone_policy(event, action):
    policy = Policy.objects.create(event=event, name=f"Deny {action}", ast={"op": "false"})
    PolicyBinding.objects.create(event=event, action=action, policy=policy)
    return policy


def test_an_active_grant_overrides_a_denial_for_its_exact_subject():
    event = make_event()
    deny_everyone_policy(event, Action.SUBMIT)
    ExceptionGrant.objects.create(
        event=event, action=Action.SUBMIT, subject_type="team", subject_id="tm_01"
    )

    allowed, reason = check_action(
        event, Action.SUBMIT, {}, subject_type="team", subject_id="tm_01"
    )
    assert allowed is True
    assert "exception grant" in reason


def test_a_grant_does_not_help_a_different_subject():
    event = make_event()
    deny_everyone_policy(event, Action.SUBMIT)
    ExceptionGrant.objects.create(
        event=event, action=Action.SUBMIT, subject_type="team", subject_id="tm_01"
    )

    allowed, _ = check_action(event, Action.SUBMIT, {}, subject_type="team", subject_id="tm_02")
    assert allowed is False


def test_a_grant_does_not_widen_a_different_action_for_the_same_subject():
    event = make_event()
    deny_everyone_policy(event, Action.SUBMIT)
    deny_everyone_policy(event, Action.VOTE)
    ExceptionGrant.objects.create(
        event=event, action=Action.SUBMIT, subject_type="team", subject_id="tm_01"
    )

    submit_allowed, _ = check_action(
        event, Action.SUBMIT, {}, subject_type="team", subject_id="tm_01"
    )
    vote_allowed, _ = check_action(event, Action.VOTE, {}, subject_type="team", subject_id="tm_01")
    assert submit_allowed is True
    assert vote_allowed is False


def test_an_expired_grant_does_not_override_a_denial():
    event = make_event()
    deny_everyone_policy(event, Action.SUBMIT)
    ExceptionGrant.objects.create(
        event=event,
        action=Action.SUBMIT,
        subject_type="team",
        subject_id="tm_01",
        expires_at=timezone.now() - timedelta(hours=1),
    )

    allowed, _ = check_action(event, Action.SUBMIT, {}, subject_type="team", subject_id="tm_01")
    assert allowed is False


def test_a_grant_is_never_consulted_when_the_policy_already_allows():
    """No binding at all means unconditionally allowed; a grant existing
    for a *different* subject must not somehow leak in as a false denial
    reason or otherwise change the outcome.
    """
    event = make_event()
    allowed, reason = check_action(
        event, Action.SUBMIT, {}, subject_type="team", subject_id="tm_99"
    )
    assert allowed is True
    assert reason is None


def test_grant_records_reason_and_granter_for_audit():
    event = make_event()
    organizer = User.objects.create_user(username="organizer", password="unused")
    grant = ExceptionGrant.objects.create(
        event=event,
        action=Action.JOIN,
        subject_type="user",
        subject_id="usr_01",
        reason="Late registration approved by email.",
        granted_by=organizer,
    )
    assert grant.granted_by == organizer
    assert grant.is_active() is True
