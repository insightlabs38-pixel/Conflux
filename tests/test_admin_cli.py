import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sdks/python"))
from conflux_sdk import ConfluxClient  # noqa: E402
from conflux_sdk.cli import NoRedirect, main, origin, write_result  # noqa: E402


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.example",
        "https://user:password@host",
        "https://host/path",
        "https://host/?token=x",
        "https://host/#x",
        "https://host:0",
        "https://ho\nst",
        "https://host\\path",
    ],
)
def test_cli_rejects_unsafe_origins(url):
    with pytest.raises(ValueError):
        origin(url)


def test_cli_accepts_https_and_local_plain_http_only():
    assert origin("https://host/") == "https://host"
    assert origin("http://127.0.0.1:8093") == "http://127.0.0.1:8093"
    assert origin("http://[::1]:8000") == "http://[::1]:8000"
    assert (
        NoRedirect().redirect_request(None, None, 302, "", {}, "https://external.example") is None
    )


def test_cli_export_is_private_atomic_and_never_overwrites(tmp_path):
    path = tmp_path / "archive.json"
    write_result({"name": "Café"}, str(path))
    assert json.loads(path.read_text())["name"] == "Café"
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        write_result({"changed": True}, str(path))
    assert not json.loads(path.read_text()).get("changed")
    assert list(tmp_path.iterdir()) == [path]


def test_cli_errors_redact_credentials_and_fail_before_network(monkeypatch, capsys):
    monkeypatch.setenv("CONFLUX_SESSION_TOKEN", "cli-secret")
    monkeypatch.delenv("CONFLUX_BEARER_TOKEN", raising=False)
    assert (
        main(
            ["--base-url", "http://remote.example", "whoami"],
            client_factory=lambda *a, **k: pytest.fail("network"),
        )
        == 1
    )
    monkeypatch.setenv("CONFLUX_BEARER_TOKEN", "bearer-secret")
    assert main(["--base-url", "https://host", "whoami"]) == 1
    assert "exactly one" in capsys.readouterr().err
    monkeypatch.delenv("CONFLUX_BEARER_TOKEN")

    def factory(*args, **kwargs):
        raise ValueError("cli-secret cannot be used")

    assert main(["--base-url", "https://host", "whoami"], client_factory=factory) == 1
    captured = capsys.readouterr()
    assert "cli-secret" not in captured.err and "[redacted]" in captured.err
    assert captured.out == ""


@pytest.mark.django_db
def test_cli_create_manage_export_preview_and_import_use_canonical_api(
    monkeypatch, capsys, tmp_path
):
    from urllib.parse import urlsplit

    from accounts.models import Session, User
    from django.test import Client
    from django.utils import timezone
    from events.models import Event
    from workspaces.models import Membership, Role, Workspace

    user = User.objects.create_user(username="cli-organizer")
    workspace = Workspace.objects.create(name="CLI", slug="cli")
    membership = Membership.objects.create(user=user, workspace=workspace, role=Role.ORGANIZER)
    token = Session.issue(user).token
    monkeypatch.setenv("CONFLUX_SESSION_TOKEN", token)
    monkeypatch.delenv("CONFLUX_BEARER_TOKEN", raising=False)
    seen = []

    class Response:
        def __init__(self, response):
            self.status = response.status_code
            self.body = response.content

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self):
            return self.body

    def opener(request):
        seen.append(request)
        parts = urlsplit(request.full_url)
        url = parts.path + ("?" + parts.query if parts.query else "")
        response = Client().generic(
            request.method,
            url,
            data=request.data or b"",
            content_type="application/json",
            HTTP_COOKIE=request.get_header("Cookie", ""),
            HTTP_AUTHORIZATION=request.get_header("Authorization", ""),
        )
        if response.status_code >= 400:
            raise HTTPError(url, response.status_code, "Failed", {}, io.BytesIO(response.content))
        return Response(response)

    def factory(url, **kwargs):
        kwargs["opener"] = opener
        return ConfluxClient(url, **kwargs)

    prefix = ["--base-url", "http://127.0.0.1:8093", "--workspace", str(workspace.public_id)]

    def run(*args):
        code = main([*prefix, *args], client_factory=factory)
        captured = capsys.readouterr()
        assert code == 0, captured.err
        return json.loads(captured.out) if captured.out else None

    assert run("whoami")["username"] == user.username
    created = run("events", "create", "--name", "CLI event", "--slug", "cli-event")
    event_id = created["public_id"]
    assert not created["is_public"]
    assert run("events", "list")[0]["public_id"] == event_id
    assert run("events", "get", event_id)["name"] == "CLI event"
    change = tmp_path / "update.json"
    change.write_text('{"description":"Updated"}')
    assert run("events", "update", event_id, "--input", str(change))["description"] == "Updated"
    archive = tmp_path / "event.json"
    assert run("events", "export", event_id, "--mode", "full", "--output", str(archive)) is None
    assert json.loads(archive.read_text())["mode"] == "full"
    count = Event.objects.count()
    args = ("events", "import", "--input", str(archive), "--name", "Clone", "--slug", "clone")
    run(*args)
    assert Event.objects.count() == count
    clone = run(*args, "--apply")
    assert clone["public_id"] != event_id
    assert Event.objects.count() == count + 1
    code = main([*prefix, "events", "status", event_id, "--status", "open"], client_factory=factory)
    assert code == 1 and "dates are required" in capsys.readouterr().err
    from datetime import timedelta

    change.write_text(
        json.dumps(
            {
                "starts_at": (timezone.now() + timedelta(hours=1)).isoformat(),
                "ends_at": (timezone.now() + timedelta(hours=2)).isoformat(),
            }
        )
    )
    run("events", "update", event_id, "--input", str(change))
    assert run("events", "status", event_id, "--status", "open")["status"] == "open"
    code = main([*prefix, "events", "get", str(uuid4())], client_factory=factory)
    assert code == 1 and "HTTP 404" in capsys.readouterr().err
    membership.role = Role.PARTICIPANT
    membership.save()
    code = main(
        [*prefix, "events", "create", "--name", "Denied", "--slug", "denied"],
        client_factory=factory,
    )
    assert code == 1 and "HTTP 403" in capsys.readouterr().err
    assert not Event.objects.filter(slug="denied").exists()
    bad = tmp_path / "invalid.json"
    bad.write_text("[]")
    before = len(seen)
    code = main(
        [*prefix, "events", "update", event_id, "--input", str(bad)], client_factory=factory
    )
    assert code == 1 and "JSON object" in capsys.readouterr().err
    assert len(seen) == before
    membership.role = Role.ORGANIZER
    membership.save()
    session_client = Client()
    session_client.cookies["session"] = token
    issued = session_client.post(
        f"/api/v1/workspaces/{workspace.public_id}/api-credentials/",
        {"name": "CLI reader", "allowed_actions": ["GET:event-list"]},
        content_type="application/json",
    )
    assert issued.status_code == 201
    monkeypatch.delenv("CONFLUX_SESSION_TOKEN")
    monkeypatch.setenv("CONFLUX_BEARER_TOKEN", issued.json()["token"])
    assert len(run("events", "list")) == 2
    assert seen[-1].get_header("Cookie") is None
    code = main(
        [*prefix, "events", "create", "--name", "Denied", "--slug", "denied"],
        client_factory=factory,
    )
    assert code == 1 and "HTTP 401" in capsys.readouterr().err
