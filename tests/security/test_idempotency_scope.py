from datetime import timedelta

import pytest
from accounts.models import Session, User
from core.models import IdempotencyKey
from django.test import Client
from django.utils import timezone
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db
JSON = "application/json"


def signed_in(name):
    user = User.objects.create_user(username=name, password="x")
    client = Client(raise_request_exception=False)
    client.cookies["session"] = Session.issue(user).token
    return client


def create(client, name, key="k1", **extra):
    return client.post(
        "/api/v1/workspaces/",
        {"name": name},
        content_type=JSON,
        HTTP_IDEMPOTENCY_KEY=key,
        **extra,
    )


def test_another_callers_key_never_replays_or_blocks_your_request():
    alice, bob = signed_in("alice"), signed_in("bob")
    first = create(alice, "Shared Name")
    assert first.status_code == 201
    other = create(bob, "Shared Name")
    assert other.status_code == 409  # slug already taken by Alice, i.e. executed, not replayed
    assert other.json() != first.json()
    assert "public_id" not in other.json()
    third = create(bob, "Bob Only", key="k2")
    assert third.status_code == 201 and third.json()["name"] == "Bob Only"
    assert Workspace.objects.count() == 2
    assert create(alice, "Shared Name").json() == first.json()


def test_a_key_is_bound_to_one_method_and_path():
    alice = signed_in("alice")
    assert create(alice, "One", key="reuse").status_code == 201
    other_path = alice.post(
        "/api/v1/workspaces/",
        {"name": "One"},
        content_type=JSON,
        HTTP_IDEMPOTENCY_KEY="reuse",
        HTTP_X_ELSEWHERE="1",
    )
    assert other_path.status_code == 201
    put = alice.put(
        "/api/v1/workspaces/", {"name": "One"}, content_type=JSON, HTTP_IDEMPOTENCY_KEY="reuse"
    )
    assert put.status_code in (405, 422)
    assert Workspace.objects.count() == 1


def test_an_unfinished_duplicate_is_refused_until_it_expires_then_taken_over():
    alice = signed_in("alice")
    assert create(alice, "Slow", key="slow").status_code == 201
    record = IdempotencyKey.objects.get()
    IdempotencyKey.objects.filter(pk=record.pk).update(response_status=None, response_body=None)
    duplicate = create(alice, "Slow", key="slow")
    assert duplicate.status_code == 409 and "still being processed" in duplicate.json()["detail"]
    IdempotencyKey.objects.filter(pk=record.pk).update(
        created_at=timezone.now() - timedelta(minutes=5)
    )
    assert create(alice, "Slow", key="slow").status_code == 409  # workspace exists; ran again
    assert IdempotencyKey.objects.get().response_status == 409


def test_server_errors_are_not_cached_and_oversized_keys_are_rejected(monkeypatch):
    alice = signed_in("alice")
    from workspaces import views

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(views.Workspace.objects, "create", boom)
    assert create(alice, "Retry", key="flaky").status_code == 500
    assert not IdempotencyKey.objects.exists()
    monkeypatch.undo()
    assert create(alice, "Retry", key="flaky").status_code == 201
    assert create(alice, "X", key="k" * 191).status_code == 400
    assert create(alice, "Y", key="k" * 190).status_code == 201
