import copy

import pytest
from accounts.models import Session, User
from django.core.exceptions import ValidationError
from django.test import Client
from events.models import Event, Track
from integrations.signed_archive import sign_archive, verify_signed_archive
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def fixture():
    owner = User.objects.create_user(username="signed-owner", password="unused")
    judge = User.objects.create_user(username="signed-judge", password="unused")
    workspace = Workspace.objects.create(name="Signed", slug="signed")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Source", slug="source")
    Track.objects.create(event=event, name="Hardware")
    owner_client = Client()
    owner_client.cookies["session"] = Session.issue(owner).token
    judge_client = Client()
    judge_client.cookies["session"] = Session.issue(judge).token
    base = f"/api/v1/workspaces/{workspace.public_id}/"
    return workspace, event, owner_client, judge_client, base


def test_signed_archive_round_trip_and_manifest():
    workspace, event, client, _, base = fixture()
    export = client.get(base + f"events/{event.public_id}/archive/signed/", {"mode": "full"})
    assert export.status_code == 200, export.content
    envelope = export.json()
    assert envelope["manifest"]["envelope_version"] == 1
    assert set(envelope["manifest"]["checksums"]) == set(envelope["archive"])
    assert verify_signed_archive(envelope) == envelope["archive"]
    assert (
        client.get(base + f"events/{event.public_id}/archive/signed/", {"mode": "bad"}).status_code
        == 400
    )
    created = client.post(
        base + "archive/signed/import/",
        {"name": "Copy", "slug": "copy", "envelope": envelope},
        content_type="application/json",
    )
    assert created.status_code == 201, created.content
    assert Event.objects.filter(workspace=workspace, slug="copy").exists()
    assert Track.objects.filter(event__slug="copy", name="Hardware").exists()


def test_signed_import_rejects_tampering_and_leaves_no_rows():
    workspace, event, client, _, base = fixture()
    envelope = client.get(base + f"events/{event.public_id}/archive/signed/").json()
    for change in ("archive", "checksum", "signature", "key"):
        tampered = copy.deepcopy(envelope)
        if change == "archive":
            tampered["archive"]["event"]["name"] = "Changed"
        elif change == "checksum":
            tampered["manifest"]["checksums"]["event"] = "0" * 64
        elif change == "signature":
            tampered["signature"] = "AAAA"
        else:
            tampered["public_key_pem"] = "invalid"
        response = client.post(
            base + "archive/signed/import/",
            {"name": "Copy", "slug": "copy", "envelope": tampered},
            content_type="application/json",
        )
        assert response.status_code == 400, (change, response.content)
    assert Event.objects.filter(workspace=workspace).count() == 1


def test_signed_archive_fails_closed_for_manifest_shape_and_trust_key():
    _, event, client, _, base = fixture()
    envelope = client.get(base + f"events/{event.public_id}/archive/signed/").json()
    with pytest.raises(ValidationError, match="not trusted"):
        verify_signed_archive(envelope, trusted_public_key_pem="other key")
    envelope["manifest"]["extra"] = "unsigned"
    with pytest.raises(ValidationError, match="manifest"):
        verify_signed_archive(envelope)


def test_valid_signature_does_not_bypass_canonical_import_validation():
    workspace, event, client, _, base = fixture()
    envelope = client.get(base + f"events/{event.public_id}/archive/signed/").json()
    archive = envelope["archive"]
    archive["format_version"] = 999
    signed = sign_archive(archive)
    response = client.post(
        base + "archive/signed/import/",
        {"name": "Copy", "slug": "copy", "envelope": signed},
        content_type="application/json",
    )
    assert response.status_code == 400, response.content
    assert Event.objects.filter(workspace=workspace).count() == 1


def test_signed_export_and_import_require_organizer():
    _, event, client, judge, base = fixture()
    export = base + f"events/{event.public_id}/archive/signed/"
    envelope = client.get(export).json()
    request = {"name": "Copy", "slug": "copy", "envelope": envelope}
    assert judge.get(export).status_code == 403
    assert Client().get(export).status_code in (401, 403)
    assert (
        judge.post(
            base + "archive/signed/import/", request, content_type="application/json"
        ).status_code
        == 403
    )
    assert Client().post(
        base + "archive/signed/import/", request, content_type="application/json"
    ).status_code in (401, 403)
