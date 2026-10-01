"""PD-F002-B01-T05: the event archive export is the first adopter of the job primitive."""

import json

import pytest
from accounts.models import Session, User
from core import jobs
from core.models import Job
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def no_broker(monkeypatch):
    monkeypatch.setattr("core.tasks.run_job.delay", lambda public_id: None)


@pytest.fixture
def case():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="Spring Jam", slug="spring-jam")
    clients = {}
    for name, role in (("org", Role.ORGANIZER), ("par", Role.PARTICIPANT)):
        user = User.objects.create_user(username=name, password="unused")
        Membership.objects.create(user=user, workspace=workspace, role=role)
        client = Client()
        client.cookies["session"] = Session.issue(user).token
        clients[name] = client
    base = f"/api/v1/workspaces/{workspace.public_id}/"
    return {
        "base": base,
        "url": f"{base}events/{event.public_id}/archive/export-jobs/",
        "sync": f"{base}events/{event.public_id}/archive/",
        "clients": clients,
    }


def post(case, body=None, who="org", **extra):
    return case["clients"][who].post(
        case["url"], data=body or {}, content_type="application/json", **extra
    )


def test_an_export_runs_as_a_job_and_the_download_matches_the_synchronous_export(case):
    started = post(case, {"mode": "config"})
    assert started.status_code == 202, started.content
    job = started.json()
    assert job["status"] == "queued" and job["kind"] == "archive_export"
    jobs.run(job["public_id"])

    done = case["clients"]["org"].get(f"{case['base']}jobs/{job['public_id']}/").json()
    assert done["status"] == "succeeded" and done["progress"]["done"] == done["progress"]["total"]
    assert done["result"]["mode"] == "config" and done["result"]["signed"] is False
    name = done["artifacts"][0]["name"]
    assert name == "spring-jam-config-archive.json" == done["result"]["filename"]
    download = case["clients"]["org"].get(
        f"{case['base']}jobs/{job['public_id']}/artifacts/{name}/"
    )
    assert download["Content-Type"] == "application/json"
    expected = case["clients"]["org"].get(case["sync"] + "?mode=config").json()
    assert json.loads(download.content) == expected
    assert done["result"]["bytes"] == len(download.content)


def test_a_signed_export_carries_the_envelope(case, settings):
    job = post(case, {"mode": "config", "signed": True}).json()
    jobs.run(job["public_id"])
    stored = Job.objects.get(public_id=job["public_id"])
    assert stored.status == "succeeded", stored.error
    artifact = stored.artifacts.get()
    envelope = json.loads(bytes(artifact.body))
    assert {"manifest", "archive", "signature", "public_key_pem"} <= envelope.keys()
    assert artifact.name.endswith("-signed-archive.json")


def test_retrying_with_the_same_key_returns_the_job_already_started(case):
    first = post(case, {"mode": "full"}, HTTP_IDEMPOTENCY_KEY="k1")
    again = post(case, {"mode": "full"}, HTTP_IDEMPOTENCY_KEY="k1")
    assert first.status_code == 202 and again.status_code == 200
    assert first.json()["public_id"] == again.json()["public_id"]
    assert Job.objects.count() == 1
    different = post(case, {"mode": "config"}, HTTP_IDEMPOTENCY_KEY="k1")
    assert different.status_code == 400


def test_bad_input_and_missing_rights_are_refused_without_a_job(case):
    assert post(case, {"mode": "everything"}).status_code == 400
    assert post(case, who="par").status_code == 403
    assert not Job.objects.exists()


def test_cancelling_before_the_worker_starts_leaves_no_file(case):
    job = post(case, {"mode": "config"}).json()
    cancelled = case["clients"]["org"].post(f"{case['base']}jobs/{job['public_id']}/cancel/")
    assert cancelled.json()["status"] == "cancelled"
    jobs.run(job["public_id"])
    assert not Job.objects.get(public_id=job["public_id"]).artifacts.exists()
