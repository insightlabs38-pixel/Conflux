import json
from pathlib import Path

import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from workspaces.models import Membership, Role, Workspace

EXAMPLES = Path(__file__).resolve().parents[2] / "src/web/features/api-explorer/examples.json"


def test_explorer_examples_match_live_json_contract():
    response = Client().get("/api/v1/schema/?format=json")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.oai.openapi+json"
    paths = response.json()["paths"]
    for example in json.loads(EXAMPLES.read_text()):
        assert example["method"] in paths[example["path"]]
        if "body" in example:
            assert (
                "application/json"
                in paths[example["path"]][example["method"]]["requestBody"]["content"]
            )


@pytest.mark.django_db
def test_seeded_event_request_obeys_authorization_and_creates_real_event():
    seed = next(example for example in json.loads(EXAMPLES.read_text()) if "body" in example)
    workspace = Workspace.objects.create(name="Explorer", slug="explorer")
    url = seed["path"].replace("{workspace_public_id}", str(workspace.public_id))
    assert Client().post(url, seed["body"], content_type="application/json").status_code == 401
    assert not Event.objects.exists()
    user = User.objects.create_user(username="explorer")
    membership = Membership.objects.create(user=user, workspace=workspace, role=Role.PARTICIPANT)
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    assert client.post(url, seed["body"], content_type="application/json").status_code == 403
    membership.role = Role.ORGANIZER
    membership.save()
    response = client.post(url, seed["body"], content_type="application/json")
    assert response.status_code == 201
    event = Event.objects.get(public_id=response.json()["public_id"])
    assert event.name == seed["body"]["name"]
    assert not event.is_public
    detail = url + f"{event.public_id}/"
    assert client.get(detail).json()["public_id"] == str(event.public_id)
