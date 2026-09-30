import io
import json
from datetime import timedelta

import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.utils import timezone
from events.models import Event, EventStatus
from integrations.demo_scenarios import generate_demo_event
from integrations.e2e_fixtures import (
    FIXTURE_SEED_BASE,
    PROFILES,
    SLOTS,
    create_fixture,
    dispose_fixture,
    sweep_fixtures,
)
from integrations.models import DemoScenario
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def test_profiles_are_valid_generator_inputs_and_cover_spec_labels():
    # participant-05 and judge-03 are addressed by the specs; `published` cannot leave live users.
    for spec in PROFILES.values():
        assert spec["participants"] >= 5 and spec["judges"] >= 3
        assert spec["live"] == 0 or spec["checkpoint"] != "published"
    assert PROFILES["canary"]["participants"] >= 24 and PROFILES["canary"]["live"] >= 1


def test_iso_min_fixture_is_a_real_showcased_scenario_with_working_accounts():
    fx = create_fixture("iso-min", nonce=1, password="fx-pass")
    assert fx["seed"] >= FIXTURE_SEED_BASE and fx["slug"] == f"demo-hackathon-{fx['seed']}"
    event = Event.objects.get(public_id=fx["event"])
    assert str(event.workspace.public_id) == fx["workspace"]
    assert event.status == EventStatus.OPEN and event.is_public
    prefix = f"demo-hackathon-{fx['seed']}-"
    names = set(User.objects.filter(username__startswith=prefix).values_list("username", flat=True))
    assert {prefix + label for label in ("organizer", "judge-03", "participant-05")} <= names
    assert {prefix + label for label in ("mentor", "volunteer", "sponsor")} <= names  # showcase ran
    assert User.objects.get(username=prefix + "organizer").check_password("fx-pass")
    assert event.projects.count() == 4  # 6 participants, 2 live


def test_published_profile_closes_the_event():
    fx = create_fixture("iso-published", nonce=2)
    assert Event.objects.get(public_id=fx["event"]).status == EventStatus.CLOSED


def test_same_nonce_yields_distinct_isolated_fixtures_and_random_passwords():
    first = create_fixture("iso-min", nonce=3)
    second = create_fixture("iso-min", nonce=3)
    assert second["seed"] == first["seed"] + 1
    assert len({first["workspace"], second["workspace"]}) == 2
    assert len({first["event"], second["event"]}) == 2
    assert first["password"] != second["password"]
    dispose_fixture(first["slug"])
    survivor = Event.objects.get(public_id=second["event"])
    assert survivor.projects.count() == 4
    assert not Workspace.objects.filter(slug=first["slug"]).exists()
    assert not User.objects.filter(username__startswith=f"demo-hackathon-{first['seed']}-").exists()


def test_taken_seeds_are_skipped_not_reused():
    taken = FIXTURE_SEED_BASE + 4 * SLOTS
    generate_demo_event(seed=taken, participants=4, judges=2, live=1, checkpoint="submitted")
    fx = create_fixture("iso-min", nonce=4)
    assert fx["seed"] == taken + 1
    assert DemoScenario.objects.filter(seed=taken).exists()  # untouched


def test_dispose_refuses_everything_that_is_not_a_fixture():
    generate_demo_event(seed=7, participants=4, judges=2, live=1, checkpoint="submitted")
    Workspace.objects.create(name="Real", slug="real")
    for slug, needle in (
        ("demo-hackathon-7", "not an e2e fixture"),
        ("real", "not a generated scenario"),
        ("missing", "not a generated scenario"),
    ):
        with pytest.raises(ValidationError, match=needle):
            dispose_fixture(slug)
    assert Workspace.objects.filter(slug__in=["demo-hackathon-7", "real"]).count() == 2


def test_sweep_only_removes_old_fixtures():
    generate_demo_event(seed=7, participants=4, judges=2, live=1, checkpoint="submitted")
    old = create_fixture("iso-min", nonce=5)
    fresh = create_fixture("iso-min", nonce=6)
    DemoScenario.objects.filter(workspace__slug=old["slug"]).update(
        created_at=timezone.now() - timedelta(hours=3)
    )
    assert sweep_fixtures(older_than_minutes=120) == [old["slug"]]
    assert Workspace.objects.filter(slug=fresh["slug"]).exists()
    assert sweep_fixtures() == [fresh["slug"]]
    assert Workspace.objects.filter(slug="demo-hackathon-7").exists()


def test_invalid_inputs_fail_with_diagnostics():
    with pytest.raises(ValidationError, match="Use one of"):
        create_fixture("iso-huge")
    with pytest.raises(ValidationError, match="Use 0-9999"):
        create_fixture("iso-min", nonce=10_000)
    assert not DemoScenario.objects.exists()


def test_showcase_failure_leaves_no_half_built_fixture(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("showcase failed")

    monkeypatch.setattr("integrations.e2e_fixtures.call_command", boom)
    with pytest.raises(RuntimeError):
        create_fixture("iso-min", nonce=7)
    assert not DemoScenario.objects.exists() and not Workspace.objects.exists()


def test_management_command_prints_handle_and_reports_refusals():
    out = io.StringIO()
    call_command("e2e_fixture", "create", "iso-min", "--nonce", "8", stdout=out)
    handle = json.loads(out.getvalue())
    listing = io.StringIO()
    call_command("e2e_fixture", "list", stdout=listing)
    assert handle["slug"] in listing.getvalue()
    with pytest.raises(CommandError, match="not an e2e fixture"):
        generate_demo_event(seed=9, participants=4, judges=2, live=1, checkpoint="submitted")
        call_command("e2e_fixture", "dispose", "demo-hackathon-9")
    call_command("e2e_fixture", "dispose", handle["slug"], stdout=io.StringIO())
    swept = io.StringIO()
    call_command("e2e_fixture", "sweep", stdout=swept)
    assert json.loads(swept.getvalue()) == {"purged": []}
