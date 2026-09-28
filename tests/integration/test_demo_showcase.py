import pytest
from continuation.models import ProjectContinuation
from django.core.management import call_command
from events.models import Event
from governance.models import RulesAcknowledgement
from integrations.demo_scenarios import generate_demo_event, purge_demo_scenario
from onsite.models import AgendaSession, ProjectLocation
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def test_showcase_is_idempotent_deterministic_and_purgeable():
    event = generate_demo_event(seed=41, participants=12, judges=3)
    slug = event.workspace.slug
    call_command("demo_showcase", slug)
    snapshot = (
        [(s.title, s.starts_at) for s in AgendaSession.objects.filter(event=event)],
        ProjectLocation.objects.filter(project__event=event).count(),
        ProjectContinuation.objects.filter(project__event=event).count(),
        RulesAcknowledgement.objects.filter(version__event=event).count(),
        [(b.kind, b.position) for b in event.page.blocks.all()],
    )
    assert len(snapshot[0]) == 4 and snapshot[1] == 6 and snapshot[2] == 2 and snapshot[3] == 8
    assert [k for k, _ in snapshot[4]] == ["hero", "tracks", "gallery", "results", "announcements"]
    call_command("demo_showcase", slug)
    again = (
        [(s.title, s.starts_at) for s in AgendaSession.objects.filter(event=event)],
        ProjectLocation.objects.filter(project__event=event).count(),
        ProjectContinuation.objects.filter(project__event=event).count(),
        RulesAcknowledgement.objects.filter(version__event=event).count(),
        [(b.kind, b.position) for b in event.page.blocks.all()],
    )
    assert again == snapshot
    purge_demo_scenario(slug)
    assert not Workspace.objects.filter(slug=slug).exists()
    assert not Event.objects.filter(pk=event.pk).exists()
    assert not AgendaSession.objects.exists() and not ProjectContinuation.objects.exists()


def test_showcase_refuses_ordinary_workspaces():
    from django.core.management.base import CommandError

    Workspace.objects.create(name="Real", slug="real")
    with pytest.raises(CommandError):
        call_command("demo_showcase", "real")
