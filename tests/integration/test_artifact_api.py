import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class FakeStorage:
    def ensure_bucket(self):
        pass

    def presign_put(self, key, content_type, artifact_id, expires):
        self.key = key
        self.info = {
            "ContentLength": 4,
            "ContentType": content_type,
            "Metadata": {"artifact-id": artifact_id},
        }
        return "https://upload.example.com/signed"

    def head(self, key):
        assert key == self.key
        return self.info


def setup_api():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    user = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)
    project = create_project(event, user, "Project")
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    base = (
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
        f"projects/{project.public_id}/artifacts/"
    )
    return client, base


def test_upload_api_completes_and_filters_private_evidence(monkeypatch):
    storage = FakeStorage()
    monkeypatch.setattr("artifacts.services.S3Storage", lambda: storage)
    client, base = setup_api()
    issued = client.post(
        base + "upload-intents/",
        {
            "kind": "file",
            "visibility": "participant",
            "title": "Deck",
            "byte_size": 4,
            "content_type": "application/pdf",
        },
        content_type="application/json",
    )
    assert issued.status_code == 201
    artifact_id = issued.json()["artifact"]["public_id"]
    intent_id = issued.json()["intent"]
    assert issued.json()["upload"]["mode"] == "single"
    complete = client.post(
        base + f"{artifact_id}/upload-intents/{intent_id}/complete/",
        {},
        content_type="application/json",
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "uploaded"
    secret = client.post(
        base + "upload-intents/",
        {
            "kind": "secret",
            "visibility": "judge",
            "title": "Private",
            "byte_size": 4,
            "content_type": "application/pdf",
        },
        content_type="application/json",
    )
    assert secret.status_code == 201
    assert [item["public_id"] for item in client.get(base).json()] == [artifact_id]
    assert client.get(base + secret.json()["artifact"]["public_id"] + "/").status_code == 404


def test_external_artifact_api_rejects_bad_url_and_nonmember():
    client, base = setup_api()
    assert (
        client.post(
            base,
            {
                "kind": "repository",
                "visibility": "public",
                "title": "Repo",
                "external_url": "javascript:alert(1)",
            },
            content_type="application/json",
        ).status_code
        == 400
    )
    created = client.post(
        base,
        {
            "kind": "repository",
            "visibility": "public",
            "title": "Repo",
            "external_url": "https://example.com/repo",
        },
        content_type="application/json",
    )
    assert created.status_code == 201
    outsider = User.objects.create_user(username="outsider", password="unused")
    client.cookies["session"] = Session.issue(outsider).token
    assert client.get(base).status_code in (401, 403)
