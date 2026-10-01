"""PD-F002-B02-T07: provenance envelopes on audit rows and job results, and their two adopters."""

import hashlib
import json
from datetime import UTC, datetime

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import jobs, provenance, version_diff
from core.models import Job
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

# --- the pure functions -----------------------------------------------------------------------


def test_canonical_json_and_its_digest_do_not_depend_on_key_order_or_machine():
    one = {"b": [1, 2, {"y": 1, "x": 2}], "a": "é✓"}
    two = {"a": "é✓", "b": [1, 2, {"x": 2, "y": 1}]}
    assert provenance.canonical(one) == provenance.canonical(two)
    assert provenance.canonical(one) == '{"a":"é✓","b":[1,2,{"x":2,"y":1}]}'.encode()
    assert provenance.digest({"a": 1}) == hashlib.sha256(b'{"a":1}').hexdigest()
    assert (
        provenance.digest({"a": 1})
        == "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )
    assert provenance.digest([1, 2]) != provenance.digest([2, 1])  # lists keep their order
    with pytest.raises(ValueError):
        provenance.canonical({"x": float("nan")})
    with pytest.raises(TypeError):
        provenance.canonical({"x": object()})


@pytest.fixture
def person(db):
    return User.objects.create_user(username="ada", password="unused")


def test_an_envelope_names_who_what_and_under_which_rules(person):
    at = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
    made = provenance.envelope(
        by=person,
        source_kind="config_history",
        source_id="abc",
        summary="Restored 2 fields.",
        refs=[{"kind": "event", "id": "e1", "label": "Spring"}, {"kind": "stage", "id": 7}],
        rules=("restore_before_values", 1),
        at=at,
    )
    assert made == {
        "version": 1,
        "by": {"public_id": str(person.public_id), "username": "ada"},
        "at": "2026-10-01T10:00:00Z",
        "source": {"kind": "config_history", "id": "abc"},
        "inputs": {
            "digest": None,
            "refs": [
                {"kind": "event", "id": "e1", "label": "Spring"},
                {"kind": "stage", "id": "7"},
            ],
        },
        "rules": {"name": "restore_before_values", "version": 1},
        "output": None,
        "summary": "Restored 2 fields.",
        "changes": None,
    }
    assert provenance.problems(made) == []
    assert json.loads(json.dumps(made)) == made  # plain JSON all the way down


def test_the_system_can_be_the_actor_and_a_digest_exists_only_when_inputs_are_given(person):
    system = provenance.envelope(by=None, source_kind="sweep", source_id="x", summary="s")
    assert system["by"] is None and system["inputs"]["digest"] is None
    with_inputs = provenance.envelope(
        by=person, source_kind="k", source_id="x", summary="s", inputs={"b": 1, "a": [2]}
    )
    assert with_inputs["inputs"]["digest"] == provenance.digest({"a": [2], "b": 1})


def test_everything_is_bounded_text_and_no_content_is_stored(person):
    made = provenance.envelope(
        by=person,
        source_kind="k" * 200,
        source_id="i" * 200,
        summary="s" * 900,
        refs=[
            {"kind": "r", "id": str(i), "label": "l" * 500, "body": "secret text"}
            for i in range(40)
        ],
        rules=("n" * 300, 2),
    )
    assert len(made["summary"]) == provenance.MAX_SUMMARY
    assert len(made["inputs"]["refs"]) == provenance.MAX_REFS
    assert all(
        len(r["label"]) == provenance.MAX_LABEL and set(r) == {"kind", "id", "label"}
        for r in made["inputs"]["refs"]
    )
    assert len(made["source"]["kind"]) == 60 and len(made["rules"]["name"]) == 80
    assert "secret text" not in json.dumps(made)


def test_changes_are_counted_from_a_version_diff():
    diff = version_diff.diff_json(
        {"a": 1, "b": 2, "l": [{"id": "x"}]}, {"a": 5, "c": 3, "l": [{"id": "x"}, {"id": "y"}]}
    )
    assert provenance.changes_of(diff) == {
        "total": 4, "added": 2, "removed": 1, "changed": 1, "moved": 0,
    }  # fmt: skip
    assert provenance.changes_of(version_diff.diff_text("a", "b")) is None
    assert provenance.changes_of(None) is None


def test_a_downloaded_file_is_checked_offline_against_its_record(person):
    data = b'{"event":"x"}'
    made = provenance.envelope(
        by=person, source_kind="export", source_id="1", summary="s",
        output=provenance.describe_output("a.json", data),
    )  # fmt: skip
    assert made["output"] == {
        "name": "a.json",
        "bytes": 13,
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    assert provenance.verify_output(made, data) is True
    assert provenance.verify_output(made, data + b" ") is False
    assert provenance.verify_output({"output": None}, data) is False
    assert provenance.verify_output({}, data) is False


def test_attach_keeps_the_rest_of_the_metadata_and_problems_names_what_is_wrong():
    made = provenance.envelope(by=None, source_kind="k", source_id="1", summary="s")
    assert provenance.attach({"event_id": "e"}, made) == {"event_id": "e", "provenance": made}
    assert provenance.attach(None, made) == {"provenance": made}
    assert provenance.problems("nope") == ["Not an object."]
    broken = {**made, "source": {"kind": "k"}, "inputs": {}, "output": {"sha256": "x"}}
    del broken["rules"]
    assert provenance.problems(broken) == [
        "Missing rules.",
        "The source needs a kind and an id.",
        "The inputs need a list of references.",
        "An output needs a SHA-256.",
    ]


def test_an_independent_feature_records_provenance_on_its_own_audit_row(person, db):
    """A feature outside integrations and audit needs the two functions and the audit call."""
    from audit.services import record_mutation
    from django.db import transaction

    workspace = Workspace.objects.create(name="W", slug="w")
    with transaction.atomic():
        record_mutation(
            actor=person,
            workspace=workspace,
            action="report.generated",
            metadata=provenance.attach(
                {"kind": "weekly"},
                provenance.envelope(
                    by=person,
                    source_kind="report",
                    source_id="weekly-1",
                    summary="Weekly report.",
                    inputs={"week": "2026-W40", "events": ["a", "b"]},
                    rules=("weekly_report", 3),
                ),
            ),
        )
    row = AuditEvent.objects.get(action="report.generated")
    assert provenance.problems(row.metadata["provenance"]) == []
    assert row.metadata["provenance"]["inputs"]["digest"] == provenance.digest(
        {"events": ["a", "b"], "week": "2026-W40"}
    )


# --- adopter 1: the archive export job ----------------------------------------------------------


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world(db, monkeypatch):
    monkeypatch.setattr("core.tasks.run_job.delay", lambda public_id: None)
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="Spring Jam", slug="spring-jam")
    org = User.objects.create_user(username="org", password="unused")
    Membership.objects.create(user=org, workspace=workspace, role=Role.ORGANIZER)
    return {
        "workspace": workspace, "event": event, "org": org, "client": client_for(org),
        "base": f"/api/v1/workspaces/{workspace.public_id}/",
    }  # fmt: skip


def run_export(world, **body):
    started = world["client"].post(
        f"{world['base']}events/{world['event'].public_id}/archive/export-jobs/",
        data=body,
        content_type="application/json",
    )
    assert started.status_code == 202
    jobs.run(started.json()["public_id"])
    return Job.objects.get(public_id=started.json()["public_id"])


def test_an_export_says_what_it_was_made_from_and_the_file_matches_its_digest(world):
    job = run_export(world, mode="config")
    assert job.status == "succeeded", job.error
    made = job.result["provenance"]
    assert provenance.problems(made) == []
    assert made["by"]["username"] == "org" and made["source"] == {
        "kind": "archive_export", "id": str(job.public_id),
    }  # fmt: skip
    assert made["inputs"]["refs"] == [
        {"kind": "event", "id": str(world["event"].public_id), "label": "Spring Jam"}
    ]
    assert (
        made["rules"]["name"] == "event_archive"
        and made["rules"]["version"] == job.result["format_version"]
    )
    assert made["summary"] == "Config archive of Spring Jam."
    artifact = job.artifacts.get()
    assert made["output"] == {
        "name": artifact.name,
        "bytes": artifact.size,
        "sha256": hashlib.sha256(bytes(artifact.body)).hexdigest(),
    }
    assert provenance.verify_output(made, bytes(artifact.body)) is True
    # What the person downloads is exactly what the record describes.
    download = world["client"].get(
        f"{world['base']}jobs/{job.public_id}/artifacts/{artifact.name}/"
    )
    assert provenance.verify_output(made, download.content) is True
    # The job's own audit row keeps the same envelope.
    audit = AuditEvent.objects.get(action="job.succeeded")
    assert audit.metadata["provenance"] == made and audit.metadata["kind"] == "archive_export"


def test_a_signed_export_is_described_by_the_bytes_that_were_downloaded(world):
    job = run_export(world, mode="config", signed=True)
    made = job.result["provenance"]
    assert made["summary"] == "Config archive of Spring Jam, signed."
    assert provenance.verify_output(made, bytes(job.artifacts.get().body)) is True


def test_a_job_kind_that_gives_no_provenance_is_unchanged(world):
    from core import jobs as j

    j.register_kind(
        j.JobKind("test_plain", "Plain", lambda ctx: {"ok": True}, roles=(Role.ORGANIZER,))
    )
    try:
        job, _ = j.enqueue(
            kind="test_plain",
            actor=world["org"],
            workspace=world["workspace"],
            event=world["event"],
            params={},
        )
        j.run(job.public_id)
        audit = AuditEvent.objects.get(action="job.succeeded")
        assert "provenance" not in audit.metadata and Job.objects.get(pk=job.pk).result == {
            "ok": True
        }
    finally:
        j.KINDS.pop("test_plain", None)


# --- adopter 2: restoring a configuration change ------------------------------------------------


def test_a_restore_records_where_it_came_from_and_what_it_changed(world):
    base = f"{world['base']}events/{world['event'].public_id}/"
    client = world["client"]
    client.patch(base, {"name": "Spring Jam 2"}, content_type="application/json")
    history = (
        f"/api/v1/audit/{world['workspace'].public_id}/events"
        f"/{world['event'].public_id}/config-history/"
    )
    change = client.get(history).json()[0]
    assert change["provenance"] is None  # an ordinary edit has no envelope
    restored = client.post(f"{history}{change['public_id']}/restore/")
    assert restored.status_code == 200
    entries = client.get(history).json()
    entry = entries[0]
    assert entry["action"].endswith(".restored")
    made = entry["provenance"]
    assert provenance.problems(made) == []
    assert made["by"]["username"] == "org" and made["source"] == {
        "kind": "config_history", "id": change["public_id"],
    }  # fmt: skip
    assert made["rules"] == {"name": "restore_before_values", "version": 1}
    assert made["changes"] == {"total": 1, "added": 0, "removed": 0, "changed": 1, "moved": 0}
    assert {r["kind"] for r in made["inputs"]["refs"]} == {"audit_event", "event"}
    assert made["summary"].startswith("Restored 1 field of Event")
    assert Event.objects.get(pk=world["event"].pk).name == "Spring Jam"
    row = AuditEvent.objects.get(public_id=entry["public_id"])
    assert row.metadata["restored_from"] == change["public_id"] == made["source"]["id"]
