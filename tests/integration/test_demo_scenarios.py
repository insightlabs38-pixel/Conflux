from datetime import UTC, datetime, timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from awards.models import AwardWinner
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from evaluations.models import Ballot, NormalizationRun
from events.models import Event, EventStatus
from integrations.demo_scenarios import generate_demo_event, purge_demo_scenario
from integrations.models import DemoScenario
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fingerprint(event):
    run = NormalizationRun.objects.get(plan__stage__event=event)
    return {
        "projects": sorted(event.projects.values_list("name", "track__name")),
        "ballots": sorted(
            (
                b.judge.username,
                b.project.name,
                tuple(r.score for r in b.responses.order_by("criterion_id")),
            )
            for b in Ballot.objects.filter(project__event=event).select_related("judge", "project")
        ),
        "winners": sorted(
            (w.award.name, w.project.name) for w in AwardWinner.objects.filter(award__event=event)
        ),
        "grand_mean": run.grand_mean,
    }


def test_same_seed_reproduces_content_and_different_seed_differs():
    first = generate_demo_event(seed=7, participants=6, judges=3)
    second_seed = generate_demo_event(seed=8, participants=6, judges=3)
    snapshot = fingerprint(first)
    purge_demo_scenario("demo-hackathon-7")
    again = generate_demo_event(seed=7, participants=6, judges=3)
    assert fingerprint(again) == snapshot
    assert fingerprint(second_seed) != snapshot


def test_scenario_is_complete_isolated_and_locked_by_default():
    real = Workspace.objects.create(name="Real", slug="real")
    real_event = Event.objects.create(workspace=real, name="Real event", slug="real-event")
    event = generate_demo_event(seed=3, participants=5, judges=3)
    assert event.workspace.slug == "demo-hackathon-3" and event.workspace != real
    assert event.status == EventStatus.CLOSED and not event.is_public
    assert Project.objects.filter(event=event).count() == 5
    assert Ballot.objects.filter(project__event=event).count() == 15
    assert AwardWinner.objects.filter(award__event=event).count() == 4
    assert all(a.published_at for a in event.awards.all())
    assert event.workspace.demo_scenario.seed == 3
    users = User.objects.filter(username__startswith="demo-hackathon-3-")
    assert users.count() == 9 and not any(u.has_usable_password() for u in users)
    assert not Session.objects.filter(user__in=users).exists()
    assert set(
        Membership.objects.filter(workspace=event.workspace).values_list("role", flat=True)
    ) == {
        Role.ORGANIZER,
        Role.PARTICIPANT,
        Role.JUDGE,
    }
    assert (
        AuditEvent.objects.filter(workspace=event.workspace, action="award.published").count() == 4
    )
    assert not Project.objects.filter(event=real_event).exists()
    assert Membership.objects.filter(workspace=real).count() == 0


def test_optional_password_makes_accounts_loginable_and_public_flag_applies():
    event = generate_demo_event(
        seed=4, participants=3, judges=2, password="training-pass", public=True
    )
    user = User.objects.get(username="demo-hackathon-4-judge-01")
    assert user.check_password("training-pass") and event.is_public


@pytest.mark.parametrize(
    "kwargs",
    [
        {"participants": 2},
        {"judges": 1},
        {"participants": 41},
        {"judges": 13},
        {"scenario": "nope"},
        {"at": datetime(2026, 1, 1)},
    ],
)
def test_invalid_requests_leave_nothing_behind(kwargs):
    with pytest.raises(ValidationError):
        generate_demo_event(**{"seed": 5, **kwargs})
    assert not Workspace.objects.exists() and not User.objects.exists()


def test_duplicate_seed_is_rejected_without_touching_existing_data():
    generate_demo_event(seed=6, participants=3, judges=2)
    before = Project.objects.count()
    with pytest.raises(ValidationError, match="purge it first"):
        generate_demo_event(seed=6, participants=3, judges=2)
    assert Project.objects.count() == before


def test_purge_removes_only_the_marked_workspace_and_its_exclusive_accounts():
    real = Workspace.objects.create(name="Real", slug="real")
    generate_demo_event(seed=9, participants=3, judges=2)
    shared = User.objects.get(username="demo-hackathon-9-judge-01")
    Membership.objects.create(workspace=real, user=shared, role=Role.JUDGE)
    with pytest.raises(ValidationError):
        purge_demo_scenario("real")
    assert Workspace.objects.filter(slug="real").exists()
    purge_demo_scenario("demo-hackathon-9")
    assert not DemoScenario.objects.exists() and not Event.objects.exists()
    assert list(User.objects.values_list("username", flat=True)) == [shared.username]
    assert Workspace.objects.filter(slug="real").exists()


def test_command_creates_lists_and_purges(capsys):
    call_command("demo_scenario", "create", "--seed", "2", "--participants", "3", "--judges", "2")
    assert '"workspace": "demo-hackathon-2"' in capsys.readouterr().out
    call_command("demo_scenario", "list")
    assert "demo-hackathon-2 3p/2j" in capsys.readouterr().out
    with pytest.raises(CommandError):
        call_command("demo_scenario", "create", "--seed", "2")
    call_command("demo_scenario", "purge", "demo-hackathon-2")
    assert not Workspace.objects.exists()
    with pytest.raises(CommandError):
        call_command("demo_scenario", "purge", "demo-hackathon-2")


def test_synthetic_clock_is_fixed_by_default_and_overridable():
    at = datetime(2027, 5, 1, 9, tzinfo=UTC)
    event = generate_demo_event(seed=10, participants=3, judges=2, at=at)
    assert event.starts_at == at - timedelta(days=1)
    assert event.projects.first().created_at == at


def test_config_archive_round_trips_evaluation_sourced_awards():
    from integrations.archive import build_archive, import_archive

    event = generate_demo_event(seed=11, participants=3, judges=2)
    archive = build_archive(event, mode="config")
    copy = import_archive(workspace=event.workspace, archive=archive, name="Copy", slug="copy")
    awards = {a.name: a.evaluation_plan.name for a in copy.awards.select_related("evaluation_plan")}
    assert awards["Grand Prize"] == "Main judging" and len(awards) == 4
