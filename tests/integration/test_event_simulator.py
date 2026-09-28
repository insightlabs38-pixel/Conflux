import json
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent, DomainEvent
from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from evaluations.models import EvaluationPlan, RubricVersion
from events.management.commands.simulate_event import simulate_event
from events.models import Event, EventRegistrationSettings, EventStatus, RegistrationMode
from forms.services import create_form, publish_form, save_draft
from policies.models import Action, Policy, PolicyBinding
from stages.models import Stage
from workspaces.models import Membership, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


@pytest.fixture
def scenario():
    workspace = Workspace.objects.create(name="Simulation", slug="simulation")
    event = Event.objects.create(
        workspace=workspace,
        name="Before launch",
        slug="before-launch",
        starts_at=timezone.now() + timedelta(days=7),
        ends_at=timezone.now() + timedelta(days=8),
    )
    stage = Stage.objects.create(event=event, name="Finals", is_initial=True)
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", draft_criteria=CRITERIA)
    return event, plan


def counts():
    return {model._meta.label: model.objects.count() for model in apps.get_models()}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", list(RegistrationMode.values))
def test_real_api_lifecycle_succeeds_and_every_table_rolls_back(scenario, mode):
    event, plan = scenario
    EventRegistrationSettings.objects.create(event=event, mode=mode)
    before = counts()
    original_clock = timezone.now
    callbacks = []
    with transaction.atomic():
        # An on-commit callback scheduled during replay must be discarded.
        from events.management.commands import simulate_event as module

        original_actor = module.Session.issue

        def issue(*args, **kwargs):
            transaction.on_commit(lambda: callbacks.append("committed"))
            return original_actor(*args, **kwargs)

        with patch.object(module.Session, "issue", side_effect=issue):
            report = simulate_event(event.public_id, plan.public_id)
    assert report["passed"], report
    assert report["persisted"] is False
    assert report["steps"][-1]["step"] == "read published results"
    assert len(report["result"]) == 2
    assert counts() == before
    assert not callbacks
    assert timezone.now is original_clock
    event.refresh_from_db()
    plan.refresh_from_db()
    assert event.status == EventStatus.DRAFT
    assert plan.published_normalization_run_id is None


def test_existing_published_rubric_is_reused_without_mutation(scenario):
    event, plan = scenario
    version = RubricVersion.objects.create(plan=plan, number=1, criteria=CRITERIA)
    before = counts()
    report = simulate_event(event.public_id, plan.public_id, participants=1, judges=1)
    assert report["passed"], report
    assert "publish rubric" not in [step["step"] for step in report["steps"]]
    assert counts() == before
    version.refresh_from_db()
    assert version.number == 1


@pytest.mark.parametrize(
    "blocker", ["deadline", "policy", "form", "capacity", "unsupported", "live"]
)
def test_configuration_failures_are_reported_without_retaining_side_effects(scenario, blocker):
    event, plan = scenario
    if blocker == "policy":
        policy = Policy.objects.create(event=event, name="Deny", ast={"op": "false"})
        PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)
    elif blocker == "form":
        form = create_form(event, "Application")
        save_draft(
            form, {"fields": [{"id": "pitch", "type": "text", "label": "Pitch", "required": True}]}
        )
        publish_form(form)
    elif blocker == "capacity":
        EventRegistrationSettings.objects.create(event=event, capacity=1)
    elif blocker == "unsupported":
        plan.mode = "pairwise"
        plan.save()
    else:
        event.status = EventStatus.OPEN
        event.save()
    before = counts()
    report = simulate_event(
        event.public_id,
        plan.public_id,
        at=event.ends_at + timedelta(seconds=1) if blocker == "deadline" else None,
    )
    assert not report["passed"], report
    assert report["failure"]["detail"]
    assert counts() == before
    assert not AuditEvent.objects.exists()
    assert not DomainEvent.objects.exists()
    assert not User.objects.exists()
    assert not Session.objects.exists()
    assert not Membership.objects.exists()


def test_unexpected_exception_also_rolls_back_and_restores_clock(scenario):
    event, plan = scenario
    before = counts()
    original_clock = timezone.now
    with patch(
        "events.management.commands.simulate_event.Session.issue",
        side_effect=RuntimeError("failure"),
    ):
        with pytest.raises(RuntimeError, match="failure"):
            simulate_event(event.public_id, plan.public_id)
    assert counts() == before
    assert timezone.now is original_clock


def test_command_reports_json_and_rejects_bad_options_or_cross_event_plan(scenario):
    event, plan = scenario
    output = StringIO()
    call_command("simulate_event", str(event.public_id), str(plan.public_id), stdout=output)
    assert json.loads(output.getvalue())["passed"]
    for kwargs in (
        {"participants": 0},
        {"judges": 11},
        {"at": "invalid"},
        {"at": "2026-09-28T00:00:00"},
    ):
        with pytest.raises(CommandError):
            call_command("simulate_event", str(event.public_id), str(plan.public_id), **kwargs)
    other = Event.objects.create(workspace=event.workspace, name="Other", slug="other")
    with pytest.raises(CommandError):
        call_command("simulate_event", str(other.public_id), str(plan.public_id))


@pytest.mark.parametrize("option", ["calibration_required", "prize_judging", "assigned_subset"])
def test_unsupported_plan_options_are_not_silently_changed(scenario, option):
    event, plan = scenario
    if option == "assigned_subset":
        plan.pool_strategy = option
    else:
        setattr(plan, option, True)
    plan.save()
    before = counts()
    report = simulate_event(event.public_id, plan.public_id)
    assert not report["passed"]
    assert report["steps"] == []
    assert counts() == before


def test_command_exits_unsuccessfully_with_machine_readable_blocker(scenario):
    event, plan = scenario
    output = StringIO()
    with pytest.raises(CommandError, match="Simulation blocked"):
        call_command(
            "simulate_event",
            str(event.public_id),
            str(plan.public_id),
            at=(event.ends_at + timedelta(seconds=1)).isoformat(),
            stdout=output,
        )
    report = json.loads(output.getvalue())
    assert not report["passed"] and not report["persisted"]
    assert report["failure"]["step"] == "draft submission 1"
    assert report["failure"]["status"] == 400
