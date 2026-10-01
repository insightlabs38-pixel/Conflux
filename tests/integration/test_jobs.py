"""PD-F002-B01-T05: durable background jobs through one primitive, with an independent consumer."""

import json
from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import jobs
from core.models import Job, JobLog
from django.test import Client
from django.utils import timezone
from events.models import Event
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class CountParams(serializers.Serializer):
    upto = serializers.IntegerField(min_value=1, max_value=50)


def _count(ctx):
    upto = ctx.params["upto"]
    for index in range(upto):
        ctx.checkpoint()
        ctx.progress(index + 1, upto, f"Counted {index + 1}")
    ctx.log("done")
    ctx.artifact("count.txt", "text/plain", "\n".join(str(i) for i in range(upto)))
    return {"counted": upto}


COUNT = jobs.JobKind(
    "test_count", "Count", _count, roles=(Role.ORGANIZER,), params=CountParams, timeout=60
)


@pytest.fixture(autouse=True)
def kinds():
    jobs.register_kind(COUNT)
    yield
    for key in [k for k in jobs.KINDS if k.startswith("test_")]:
        jobs.KINDS.pop(key)


@pytest.fixture
def sent(monkeypatch):
    sent = []
    monkeypatch.setattr("core.tasks.run_job.delay", lambda public_id: sent.append(public_id))
    return sent


def _client(user):
    c = Client()
    c.cookies["session"] = Session.issue(user).token
    return c


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    people = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("org2", Role.ORGANIZER),
        ("par", Role.PARTICIPANT),
    ):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        people[name] = user
    people["outsider"] = User.objects.create_user(username="out", password="unused")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    base = f"/api/v1/workspaces/{workspace.public_id}/"
    return {
        "workspace": workspace,
        "event": event,
        "people": people,
        "client": {name: _client(user) for name, user in people.items()},
        "base": base,
    }


def start(w, upto=3, who="org", key=""):
    return jobs.enqueue(
        kind="test_count",
        actor=w["people"][who],
        workspace=w["workspace"],
        event=w["event"],
        params={"upto": upto},
        idempotency_key=key,
    )


def get(w, who, path):
    return w["client"][who].get(w["base"] + path)


def test_enqueue_audits_and_hands_the_job_to_a_worker_only_after_commit(
    world, sent, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        job, created = start(world)
        assert sent == []  # not before the transaction is durable
    assert created and job.status == "queued" and job.params == {"upto": 3}
    assert sent == [str(job.public_id)]
    assert AuditEvent.objects.filter(action="job.requested", target_id=str(job.public_id)).exists()


def test_a_job_runs_with_progress_logs_result_and_a_downloadable_output(world, sent):
    job, _ = start(world, upto=4)
    done = jobs.run(job.public_id)
    assert done.status == "succeeded" and done.result == {"counted": 4}
    assert done.attempts == 1 and done.started_at and done.finished_at
    assert (done.progress_done, done.progress_total) == (4, 4)
    body = get(world, "org", f"jobs/{job.public_id}/").json()
    assert body["status"] == "succeeded" and body["label"] == "Count"
    assert body["progress"] == {"done": 4, "total": 4, "message": "Counted 4"}
    assert body["logs"][0]["message"] == "done"
    assert body["artifacts"] == [{"name": "count.txt", "content_type": "text/plain", "size": 7}]
    download = get(world, "org", f"jobs/{job.public_id}/artifacts/count.txt/")
    assert download.status_code == 200 and download.content == b"0\n1\n2\n3"
    assert "attachment" in download["Content-Disposition"]
    assert download["X-Content-Type-Options"] == "nosniff"
    assert get(world, "org", f"jobs/{job.public_id}/artifacts/nope.txt/").status_code == 404
    assert AuditEvent.objects.filter(action="job.succeeded").count() == 1


def test_a_second_delivery_does_not_run_the_job_again(world, sent):
    job, _ = start(world)
    jobs.run(job.public_id)
    again = jobs.run(job.public_id)
    assert again.attempts == 1 and AuditEvent.objects.filter(action="job.succeeded").count() == 1
    assert jobs.run("00000000-0000-4000-8000-000000000000") is None


def test_failures_show_what_the_user_can_act_on_and_hide_internals(world, sent):
    def invalid(ctx):
        raise ValidationError({"mode": ["Pick a mode."]})

    def broken(ctx):
        raise RuntimeError("secret connection string postgres://u:p@h/db")

    jobs.register_kind(jobs.JobKind("test_invalid", "Invalid", invalid, roles=(Role.ORGANIZER,)))
    jobs.register_kind(jobs.JobKind("test_broken", "Broken", broken, roles=(Role.ORGANIZER,)))
    results = {}
    for kind in ("test_invalid", "test_broken"):
        job, _ = jobs.enqueue(
            kind=kind,
            actor=world["people"]["org"],
            workspace=world["workspace"],
            event=world["event"],
        )
        results[kind] = jobs.run(job.public_id)
    assert results["test_invalid"].status == "failed"
    assert results["test_invalid"].error["code"] == "invalid"
    assert "Pick a mode." in results["test_invalid"].error["message"]
    assert results["test_broken"].error["code"] == "internal"
    assert "postgres" not in json.dumps(results["test_broken"].error)
    assert AuditEvent.objects.filter(action="job.failed").count() == 2


def test_cancelling_a_queued_job_is_immediate_and_a_finished_job_cannot_be_cancelled(world, sent):
    job, _ = start(world)
    response = world["client"]["org"].post(world["base"] + f"jobs/{job.public_id}/cancel/")
    assert response.status_code == 200 and response.json()["status"] == "cancelled"
    assert jobs.run(job.public_id).status == "cancelled"  # a late delivery does not start it
    assert Job.objects.get(pk=job.pk).attempts == 0
    again = world["client"]["org"].post(world["base"] + f"jobs/{job.public_id}/cancel/")
    assert again.status_code == 400
    assert AuditEvent.objects.filter(action="job.cancelled").count() == 1


def test_cancelling_a_running_job_is_cooperative(world, sent):
    seen = {}

    def slow(ctx):
        ctx.progress(1, 3, "step 1")
        response = world["client"]["org"].post(world["base"] + f"jobs/{ctx.public_id}/cancel/")
        seen["status"] = response.json()["status"]
        ctx.checkpoint()
        seen["reached"] = True  # never: the checkpoint stops the handler

    jobs.register_kind(jobs.JobKind("test_slow", "Slow", slow, roles=(Role.ORGANIZER,)))
    job, _ = jobs.enqueue(
        kind="test_slow",
        actor=world["people"]["org"],
        workspace=world["workspace"],
        event=world["event"],
    )
    assert jobs.run(job.public_id).status == "cancelled"
    assert seen == {"status": "cancelling"}
    assert AuditEvent.objects.filter(action="job.cancel_requested").exists()


def test_a_job_that_finishes_despite_a_cancel_request_is_reported_as_succeeded(world, sent):
    def stubborn(ctx):
        jobs.cancel(Job.objects.get(public_id=ctx.public_id), ctx.actor)
        return {"finished": True}

    jobs.register_kind(jobs.JobKind("test_stubborn", "S", stubborn, roles=(Role.ORGANIZER,)))
    job, _ = jobs.enqueue(
        kind="test_stubborn",
        actor=world["people"]["org"],
        workspace=world["workspace"],
        event=world["event"],
    )
    assert jobs.run(job.public_id).status == "succeeded"


def test_the_same_idempotency_key_returns_the_same_job(world, sent):
    first, created = start(world, key="abc")
    second, again = start(world, key="abc")
    assert created and not again and first.pk == second.pk
    assert Job.objects.count() == 1
    with pytest.raises(ValidationError):
        start(world, upto=9, key="abc")  # same key, different input
    other, made = start(world, who="org2", key="abc")  # keys never cross people
    assert made and other.pk != first.pk


@pytest.mark.parametrize(
    "mutate,expected",
    [
        ({"kind": "nope"}, ValidationError),
        ({"params": {"upto": 0}}, ValidationError),
        ({"params": {"upto": 3, "password": "x"}}, ValidationError),
        ({"event": None}, ValidationError),
        ({"idempotency_key": "k" * 101}, ValidationError),
    ],
)
def test_bad_requests_are_refused_without_creating_a_job(world, sent, mutate, expected):
    args = {
        "kind": "test_count",
        "actor": world["people"]["org"],
        "workspace": world["workspace"],
        "event": world["event"],
        "params": {"upto": 3},
    }
    with pytest.raises(expected):
        jobs.enqueue(**{**args, **mutate})
    assert not Job.objects.exists() and not AuditEvent.objects.exists()


def test_secrets_nested_in_params_are_refused_and_roles_are_enforced(world, sent):
    from rest_framework.exceptions import PermissionDenied

    class Free(serializers.Serializer):
        options = serializers.DictField()

    jobs.register_kind(
        jobs.JobKind("test_free", "Free", lambda ctx: None, roles=(Role.ORGANIZER,), params=Free)
    )
    with pytest.raises(ValidationError):
        jobs.enqueue(
            kind="test_free",
            actor=world["people"]["org"],
            workspace=world["workspace"],
            event=world["event"],
            params={"options": {"deep": [{"API_KEY": "x"}]}},
        )
    for who in ("par", "outsider"):
        with pytest.raises(PermissionDenied):
            start(world, who=who)


def test_a_person_cannot_pile_up_unbounded_jobs(world, sent):
    for _ in range(jobs.MAX_ACTIVE_PER_USER):
        start(world)
    with pytest.raises(ValidationError):
        start(world)
    start(world, who="org2")


def test_who_sees_which_jobs(world, sent):
    mine, _ = start(world, who="org")
    theirs, _ = start(world, who="org2")
    # An organizer sees the whole workspace; a participant sees only their own (none here).
    ids = {j["public_id"] for j in get(world, "org", "jobs/").json()}
    assert ids == {str(mine.public_id), str(theirs.public_id)}
    assert get(world, "par", "jobs/").json() == []
    assert get(world, "par", f"jobs/{mine.public_id}/").status_code == 404
    assert get(world, "par", f"jobs/{mine.public_id}/artifacts/x/").status_code == 404
    assert (
        world["client"]["par"].post(world["base"] + f"jobs/{mine.public_id}/cancel/").status_code
        == 404
    )
    assert get(world, "outsider", "jobs/").status_code == 403
    assert Client().get(world["base"] + "jobs/").status_code in (401, 403)
    # Another workspace's organizer cannot reach this one's jobs.
    other = Workspace.objects.create(name="O", slug="o")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    assert (
        _client(stranger).get(f"/api/v1/workspaces/{other.public_id}/jobs/{mine.public_id}/")
    ).status_code == 404


def test_the_list_filters_and_pages(world, sent):
    first, _ = start(world)
    jobs.run(first.public_id)
    start(world)
    start(world)
    page = get(world, "org", "jobs/?limit=2")
    assert len(page.json()) == 2 and page["X-Total-Count"] == "3"
    assert [j["status"] for j in get(world, "org", "jobs/?status=succeeded").json()] == [
        "succeeded"
    ]
    assert len(get(world, "org", f"jobs/?event={world['event'].public_id}").json()) == 3
    assert get(world, "org", "jobs/?kind=other").json() == []
    assert get(world, "org", "jobs/?event=zzz").status_code == 400
    assert get(world, "org", "jobs/?limit=0").status_code == 400


def test_a_requester_who_lost_the_role_does_not_get_the_work_done(world, sent):
    job, _ = start(world)
    Membership.objects.filter(user=world["people"]["org"]).delete()
    done = jobs.run(job.public_id)
    assert done.status == "failed" and done.error["code"] == "forbidden"


def test_oversized_or_secret_results_fail_the_job_instead_of_being_stored(world, sent):
    jobs.register_kind(
        jobs.JobKind("test_big", "Big", lambda ctx: {"x": "y" * 70000}, roles=(Role.ORGANIZER,))
    )
    jobs.register_kind(
        jobs.JobKind("test_leaky", "Leaky", lambda ctx: {"api_key": "k"}, roles=(Role.ORGANIZER,))
    )
    for kind in ("test_big", "test_leaky"):
        job, _ = jobs.enqueue(
            kind=kind,
            actor=world["people"]["org"],
            workspace=world["workspace"],
            event=world["event"],
        )
        done = jobs.run(job.public_id)
        assert done.status == "failed" and done.error["code"] == "unsafe_result"
        assert done.result is None


def test_the_log_keeps_the_newest_lines_only(world, sent):
    def chatty(ctx):
        for index in range(jobs.MAX_LOG_LINES + 5):
            ctx.log(f"line {index}")

    jobs.register_kind(jobs.JobKind("test_chatty", "C", chatty, roles=(Role.ORGANIZER,)))
    job, _ = jobs.enqueue(
        kind="test_chatty",
        actor=world["people"]["org"],
        workspace=world["workspace"],
        event=world["event"],
    )
    jobs.run(job.public_id)
    lines = list(JobLog.objects.filter(job=job).values_list("message", flat=True))
    assert len(lines) == jobs.MAX_LOG_LINES
    assert lines[0] == "line 5" and lines[-1] == f"line {jobs.MAX_LOG_LINES + 4}"


def test_the_sweep_ends_jobs_that_stopped_reporting_and_resends_lost_ones(world, sent):
    stale, _ = start(world)
    Job.objects.filter(pk=stale.pk).update(
        status="running", heartbeat_at=timezone.now() - timedelta(seconds=120)
    )
    fresh, _ = start(world)
    Job.objects.filter(pk=fresh.pk).update(status="running", heartbeat_at=timezone.now())
    cancelling, _ = start(world)
    Job.objects.filter(pk=cancelling.pk).update(
        status="cancelling", heartbeat_at=timezone.now() - timedelta(seconds=120)
    )
    lost, _ = start(world)
    Job.objects.filter(pk=lost.pk).update(created_at=timezone.now() - timedelta(minutes=5))
    recent, _ = start(world)
    sent.clear()
    assert jobs.sweep() == {"ended": 2, "redispatched": 1}
    assert Job.objects.get(pk=stale.pk).error["code"] == "timeout"
    assert Job.objects.get(pk=stale.pk).status == "failed"
    assert Job.objects.get(pk=fresh.pk).status == "running"
    assert Job.objects.get(pk=cancelling.pk).status == "cancelled"
    assert sent == [str(lost.public_id)] and recent.status == "queued"


def test_the_state_graph_only_moves_forward(world, sent):
    job, _ = start(world)
    jobs.run(job.public_id)
    finished = jobs._finish(job.pk, "failed", error={"code": "x", "message": "x"})
    assert finished.status == "succeeded"  # a finished job never changes again


def test_registration_is_strict(world):
    other = jobs.JobKind("test_count", "Different", _count)
    with pytest.raises(ValueError):
        jobs.register_kind(other)
    jobs.register_kind(COUNT)  # the identical registration is harmless
