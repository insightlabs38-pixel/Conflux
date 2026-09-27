import pytest
from accounts.models import Session, User
from artifacts.models import ArtifactValidation
from artifacts.services import create_external_artifact
from django.test import Client
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_api(kind="repository", url="https://github.com/octo/demo"):
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    artifact = create_external_artifact(
        project, user, kind=kind, visibility="public", title="Repo", url=url
    )
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    base = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
        f"projects/{project.public_id}/artifacts/{artifact.public_id}/"
    )
    return client, artifact, base


def test_check_evidence_records_ci_evidence_without_touching_status(monkeypatch):
    client, artifact, base = setup_api()
    status_before = artifact.status
    monkeypatch.setattr("artifacts.validators.pinned_get", lambda host, address, path: 200)
    monkeypatch.setattr(
        "artifacts.validators.github_evidence",
        lambda owner, repo: "license: MIT; HEAD commit abc123.",
    )

    response = client.post(base + "check-evidence/")
    assert response.status_code == 200
    body = response.json()
    assert len(body["ci_evidence"]) == 1
    assert body["ci_evidence"][0]["outcome"] == "ok"
    assert "MIT" in body["ci_evidence"][0]["detail"]

    artifact.refresh_from_db()
    assert artifact.status == status_before  # unchanged: CI evidence never gates status
    assert (
        ArtifactValidation.objects.filter(artifact=artifact, validator="submission_ci").count() == 1
    )


def test_check_evidence_reports_a_non_200_as_a_warning(monkeypatch):
    client, artifact, base = setup_api()
    monkeypatch.setattr("artifacts.validators.pinned_get", lambda host, address, path: 404)

    response = client.post(base + "check-evidence/")
    assert response.json()["ci_evidence"][0]["outcome"] == "warning"
    assert "404" in response.json()["ci_evidence"][0]["detail"]


def test_check_evidence_records_gitlab_evidence_for_a_gitlab_repository(monkeypatch):
    client, artifact, base = setup_api(url="https://gitlab.com/octo/demo")
    monkeypatch.setattr("artifacts.validators.pinned_get", lambda host, address, path: 200)
    monkeypatch.setattr(
        "artifacts.validators.gitlab_evidence",
        lambda owner, repo: "license: mit; HEAD commit abc123.",
    )

    response = client.post(base + "check-evidence/")
    assert response.status_code == 200
    detail = response.json()["ci_evidence"][0]["detail"]
    assert "mit" in detail


def test_check_evidence_only_calls_github_for_github_repository_urls(monkeypatch):
    client, artifact, base = setup_api(kind="live_url", url="https://demo.example.com/app")
    called = {"github": False}

    def fake_pinned_get(host, address, path):
        assert host == "demo.example.com"
        return 200

    def fake_github_evidence(owner, repo):
        called["github"] = True
        return "should not be called"

    monkeypatch.setattr("artifacts.validators.pinned_get", fake_pinned_get)
    monkeypatch.setattr("artifacts.validators.github_evidence", fake_github_evidence)

    response = client.post(base + "check-evidence/")
    assert response.status_code == 200
    assert called["github"] is False
    assert "license" not in response.json()["ci_evidence"][0]["detail"]


def test_check_evidence_is_blocked_for_a_private_or_malformed_url(monkeypatch):
    client, artifact, base = setup_api(kind="live_url", url="https://localhost:9999/app")
    # No mocking needed: validate_destination itself rejects a non-public host.
    response = client.post(base + "check-evidence/")
    assert response.json()["ci_evidence"][0]["outcome"] == "blocked"


def test_check_evidence_rejects_a_non_link_artifact_kind():
    workspace = Workspace.objects.create(name="W2", slug="w2")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member2", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    from artifacts.models import Artifact

    artifact = Artifact.objects.create(
        project=project, created_by=user, kind="file", visibility="participant", title="File"
    )
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    base = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
        f"projects/{project.public_id}/artifacts/{artifact.public_id}/"
    )
    response = client.post(base + "check-evidence/")
    assert response.status_code == 400
