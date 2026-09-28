from datetime import UTC, datetime, timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactKind, ArtifactStatus, ArtifactVisibility
from audit.models import AuditEvent
from community.models import Comment
from django.core.management import call_command
from django.test import Client
from evaluations.models import Appeal, EvaluationPlan
from events.models import Event, EventApplication, ParticipantCheckIn
from integrations import privacy
from integrations.models import EventRetentionPolicy
from participation.models import MarketplaceProfile
from presentation.models import SavedPublicSearch
from projects.models import Project, ProjectMembership, Submission, SubmissionVersion
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
ENDED = datetime(2026, 1, 2, tzinfo=UTC)


class FakeStorage:
    def __init__(self, fail=False):
        self.deleted, self.fail = [], fail

    def delete(self, key):
        if self.fail:
            raise OSError("storage down")
        self.deleted.append(key)


def user(name):
    return User.objects.create_user(username=name, password="unused")


def artifact(project, owner, title, visibility, key):
    return Artifact.objects.create(
        project=project,
        kind=ArtifactKind.DOCUMENT,
        visibility=visibility,
        status=ArtifactStatus.READY,
        title=title,
        object_key=key,
        byte_size=3,
        sha256="b" * 64,
        created_by=owner,
    )


def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(
        workspace=workspace, name="E", slug="e", starts_at=ENDED - timedelta(days=1), ends_at=ENDED
    )
    stage = Stage.objects.create(event=event, name="Build", position=0)
    people = {}
    for name, role in (
        ("organizer", Role.ORGANIZER),
        ("alice", Role.PARTICIPANT),
        ("bob", Role.PARTICIPANT),
    ):
        people[name] = user(name)
        Membership.objects.create(workspace=workspace, user=people[name], role=role)
    projects = {}
    for name in ("alice", "bob"):
        project = Project.objects.create(event=event, name=name, created_by=people[name])
        ProjectMembership.objects.create(project=project, user=people[name], role="owner")
        submission = Submission.objects.create(
            project=project, stage=stage, updated_by=people[name]
        )
        SubmissionVersion.objects.create(
            submission=submission, number=1, snapshot={}, digest="a" * 64, finalized_by=people[name]
        )
        projects[name] = project
        EventApplication.objects.create(event=event, user=people[name], note=f"{name} note")
        MarketplaceProfile.objects.create(event=event, user=people[name], bio=f"{name} bio")
        SavedPublicSearch.objects.create(event=event, owner=people[name], name="mine")
        ParticipantCheckIn.objects.create(
            event=event, participant=people[name], checked_in_by=people["organizer"]
        )
        Comment.objects.create(project=projects[name], author=people[name], body=f"{name} says")
        artifact(project, people[name], "private", ArtifactVisibility.PARTICIPANT, f"k/{name}/1")
        artifact(project, people[name], "shown", ArtifactVisibility.PUBLIC, f"k/{name}/pub")
    return workspace, event, people, projects


def client_for(person):
    client = Client()
    client.cookies["session"] = Session.issue(person).token
    return client


def base(event):
    return f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/privacy/"


def test_subject_export_is_scoped_audited_and_lists_retained_evidence():
    _, event, people, _ = world()
    url = base(event) + f"subjects/{people['alice'].public_id}/export/"
    response = client_for(people["organizer"]).post(url)
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["data"]["event_applications"][0]["note"] == "alice note"
    assert body["data"]["comments"][0]["body"] == "alice says"
    assert len(body["retained_data"]["submission_versions"]) == 1
    assert "bob" not in str(body)
    assert {a["title"] for a in body["artifacts"]} == {"private", "shown"}
    assert AuditEvent.objects.filter(action="privacy.subject_exported").count() == 1


@pytest.mark.parametrize("actor", ["alice", "bob"])
def test_only_organizers_reach_privacy_endpoints(actor):
    _, event, people, _ = world()
    other = client_for(people[actor])
    subject = people["alice"].public_id
    for method, path in (
        ("post", f"subjects/{subject}/export/"),
        ("post", f"subjects/{subject}/erase/"),
        ("post", "retention/run/"),
        ("get", "retention-policy/"),
        ("put", "retention-policy/"),
    ):
        assert getattr(other, method)(base(event) + path).status_code == 403
        assert getattr(Client(), method)(base(event) + path).status_code in (401, 403)
    assert Comment.objects.count() == 2 and Artifact.objects.count() == 4


def test_foreign_and_unrelated_subjects_are_not_found():
    _, event, people, _ = world()
    outsider = user("outsider")
    other_workspace = Workspace.objects.create(name="X", slug="x")
    other_event = Event.objects.create(workspace=other_workspace, name="O", slug="o")
    organizer = client_for(people["organizer"])
    assert organizer.post(base(event) + f"subjects/{outsider.public_id}/erase/").status_code == 404
    unknown = "00000000-0000-4000-8000-000000000000"
    assert organizer.post(base(event) + f"subjects/{unknown}/export/").status_code == 404
    foreign = (
        f"/api/v1/workspaces/{other_workspace.public_id}/events/{other_event.public_id}/privacy/"
    )
    assert organizer.post(
        foreign + f"subjects/{people['alice'].public_id}/export/"
    ).status_code in (403, 404)


def test_erasure_previews_then_deletes_only_that_person_and_retains_evidence(monkeypatch):
    _, event, people, projects = world()
    storage = FakeStorage()
    monkeypatch.setattr(privacy, "S3Storage", lambda: storage)
    client = client_for(people["organizer"])
    url = base(event) + f"subjects/{people['alice'].public_id}/erase/"
    preview = client.post(url, {}, content_type="application/json").json()
    assert preview["applied"] is False and preview["erased"]["comments"] == 1
    assert preview["retained"]["submission_versions"] == 1
    assert EventApplication.objects.count() == 2 and not storage.deleted
    applied = client.post(url, {"apply": True}, content_type="application/json")
    assert applied.status_code == 200, applied.content
    assert applied.json()["erased"]["private_artifacts"]["purge"] == 1
    for model in (
        EventApplication,
        MarketplaceProfile,
        SavedPublicSearch,
        ParticipantCheckIn,
        Comment,
    ):
        assert model.objects.count() == 1
    assert Comment.objects.get().project == projects["bob"]
    private = Artifact.objects.get(project=projects["alice"], title="private")
    assert (private.status, private.object_key, private.sha256) == (
        ArtifactStatus.PURGED,
        "",
        "b" * 64,
    )
    assert storage.deleted == ["k/alice/1"]
    assert Artifact.objects.get(project=projects["alice"], title="shown").status == "ready"
    assert Artifact.objects.get(project=projects["bob"], title="private").object_key == "k/bob/1"
    assert SubmissionVersion.objects.count() == 2
    audit = AuditEvent.objects.get(action="privacy.subject_erased")
    assert "alice" not in str(audit.metadata) and audit.target_id == str(people["alice"].public_id)


def test_storage_failure_keeps_key_for_retry_and_never_resurrects():
    _, event, people, projects = world()
    failing = FakeStorage(fail=True)
    report = privacy.erase_subject(
        event, people["alice"], actor=people["organizer"], apply=True, storage=failing
    )
    assert report["erased"]["private_artifacts"]["purge"] == 1
    stuck = Artifact.objects.get(project=projects["alice"], title="private")
    assert stuck.status == ArtifactStatus.PURGED and stuck.object_key == "k/alice/1"
    from artifacts.validators import validate_artifact

    validate_artifact(stuck, storage=FakeStorage())
    stuck.refresh_from_db()
    assert stuck.status == ArtifactStatus.PURGED
    healthy = FakeStorage()
    assert privacy.complete_purges(event, storage=healthy) == 1
    assert healthy.deleted == ["k/alice/1"]
    stuck.refresh_from_db()
    assert stuck.object_key == ""
    assert privacy.complete_purges(event, storage=healthy) == 0


def test_pending_appeal_holds_evidence_until_decided():
    _, event, people, projects = world()
    plan = EvaluationPlan.objects.create(
        stage=Stage.objects.get(event=event), name="p", candidate_type="project"
    )
    appeal = Appeal.objects.create(
        plan=plan, project=projects["alice"], submitted_by=people["alice"], body="unfair"
    )
    storage = FakeStorage()
    report = privacy.erase_subject(
        event, people["alice"], actor=people["organizer"], apply=True, storage=storage
    )
    assert report["erased"]["private_artifacts"] == {"purge": 0, "held_for_pending_appeals": 1}
    assert not storage.deleted
    assert report["retained"]["appeals"] == 1 and Appeal.objects.filter(pk=appeal.pk).exists()


def test_retention_policy_is_validated_audited_and_waits_for_window(monkeypatch):
    _, event, people, _ = world()
    Event.objects.filter(pk=event.pk).update(ends_at=datetime.now(UTC) + timedelta(days=1))
    storage = FakeStorage()
    monkeypatch.setattr(privacy, "S3Storage", lambda: storage)
    client = client_for(people["organizer"])
    url = base(event) + "retention-policy/"
    assert client.get(url).json()["participant_data_days"] is None
    for bad in (
        {},
        {"participant_data_days": -1, "private_artifact_days": None},
        {"participant_data_days": 1, "private_artifact_days": 1, "extra": 1},
    ):
        assert client.put(url, bad, content_type="application/json").status_code == 400
    ok = {"participant_data_days": 30, "private_artifact_days": 60}
    assert client.put(url, ok, content_type="application/json").status_code == 200
    assert AuditEvent.objects.filter(action="privacy.retention_policy_saved").count() == 1
    run = base(event) + "retention/run/"
    early = client.post(run, {"apply": True}, content_type="application/json").json()
    assert early["due"] == {"participant_data": False, "private_artifacts": False}
    assert Comment.objects.count() == 2 and not storage.deleted


def test_enforcement_windows_are_independent_and_command_previews_by_default():
    _, event, people, _ = world()
    EventRetentionPolicy.objects.create(
        event=event, participant_data_days=10, private_artifact_days=40
    )
    storage = FakeStorage()
    at_10 = ENDED + timedelta(days=10)
    preview = privacy.enforce_retention(event, at_10)
    assert preview["due"] == {"participant_data": True, "private_artifacts": False}
    assert preview["erased"]["comments"] == 2 and Comment.objects.count() == 2
    privacy.enforce_retention(event, at_10, actor=people["organizer"], apply=True, storage=storage)
    assert not Comment.objects.exists() and not EventApplication.objects.exists()
    assert Artifact.objects.filter(status=ArtifactStatus.PURGED).count() == 0
    late = ENDED + timedelta(days=40)
    privacy.enforce_retention(event, late, actor=people["organizer"], apply=True, storage=storage)
    assert sorted(storage.deleted) == ["k/alice/1", "k/bob/1"]
    assert Artifact.objects.filter(visibility="public", status="ready").count() == 2
    assert SubmissionVersion.objects.count() == 2
    again = privacy.enforce_retention(
        event, late, actor=people["organizer"], apply=True, storage=storage
    )
    assert again["erased"]["private_artifacts"]["purge"] == 0
    assert AuditEvent.objects.filter(action="privacy.retention_enforced").count() == 2
    call_command("enforce_retention")
    assert AuditEvent.objects.filter(action="privacy.retention_enforced").count() == 2
