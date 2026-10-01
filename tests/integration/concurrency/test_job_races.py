"""PD-F002-B01-T05: the job lifecycle under real concurrent transactions."""

import pytest
from accounts.models import User
from core import jobs
from core.models import Job
from events.models import Event
from test_pvs_races import race, requires_real_db
from workspaces.models import Membership, Role, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]

RUNS = []


def _once(ctx):
    RUNS.append(ctx.public_id)
    return {"ran": True}


@pytest.fixture
def world():
    RUNS.clear()
    jobs.register_kind(jobs.JobKind("test_once", "Once", _once, roles=(Role.ORGANIZER,)))
    workspace = Workspace.objects.create(name="JR", slug="jr")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="org")
    Membership.objects.create(workspace=workspace, user=user, role=Role.ORGANIZER)
    yield workspace, event, user
    jobs.KINDS.pop("test_once", None)


def test_duplicate_deliveries_run_the_handler_once(world, monkeypatch):
    monkeypatch.setattr("core.tasks.run_job.delay", lambda public_id: None)
    workspace, event, user = world
    job, _ = jobs.enqueue(kind="test_once", actor=user, workspace=workspace, event=event)
    race([lambda: jobs.run(job.public_id)] * 4)
    assert len(RUNS) == 1
    assert Job.objects.get(pk=job.pk).attempts == 1


def test_simultaneous_requests_with_one_key_create_one_job(world, monkeypatch):
    monkeypatch.setattr("core.tasks.run_job.delay", lambda public_id: None)
    workspace, event, user = world
    race(
        [
            lambda: jobs.enqueue(
                kind="test_once",
                actor=user,
                workspace=workspace,
                event=event,
                idempotency_key="same",
            )
        ]
        * 4
    )
    assert Job.objects.count() == 1


def test_a_cancel_racing_the_start_ends_in_one_consistent_state(world, monkeypatch):
    monkeypatch.setattr("core.tasks.run_job.delay", lambda public_id: None)
    workspace, event, user = world
    job, _ = jobs.enqueue(kind="test_once", actor=user, workspace=workspace, event=event)
    race(
        [
            lambda: jobs.run(job.public_id),
            lambda: jobs.cancel(Job.objects.get(pk=job.pk), user),
        ]
    )
    final = Job.objects.get(pk=job.pk)
    assert final.status in ("cancelled", "succeeded")
    assert (final.status == "succeeded") == (len(RUNS) == 1)
