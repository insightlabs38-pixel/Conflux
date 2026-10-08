"""PD-F006-B01-T91: the CLI runs the entity query the application lists use, read-only."""

import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit

import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from projects.models import Project
from workspaces.models import Membership, Role, Workspace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sdks" / "python"))
from conflux_sdk import ConfluxClient, cli  # noqa: E402

pytestmark = pytest.mark.django_db


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


def setup(monkeypatch, role=Role.ORGANIZER):
    user = User.objects.create_user(username="cli-entities")
    workspace = Workspace.objects.create(name="CLI", slug="cli")
    Membership.objects.create(user=user, workspace=workspace, role=role)
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    for name in ("Robot arm", "Garden app"):
        Project.objects.create(event=event, name=name, created_by=user)
    monkeypatch.setenv("CONFLUX_SESSION_TOKEN", Session.issue(user).token)
    monkeypatch.delenv("CONFLUX_BEARER_TOKEN", raising=False)
    seen = []

    def opener(request):
        parts = urlsplit(request.full_url)
        seen.append((request.method, parts.path, parts.query))
        response = Client().generic(
            request.method,
            parts.path + ("?" + parts.query if parts.query else ""),
            HTTP_COOKIE=request.get_header("Cookie", ""),
        )
        if response.status_code >= 400:
            raise HTTPError(
                parts.path, response.status_code, "Failed", {}, io.BytesIO(response.content)
            )
        return Response(response)

    def factory(url, **kwargs):
        return ConfluxClient(url, **{**kwargs, "opener": opener})

    prefix = ["--base-url", "http://127.0.0.1:8093", "--workspace", str(workspace.public_id)]
    return event, prefix, factory, seen


def test_entities_list_and_query_send_only_reads_with_the_same_parameters(monkeypatch, capsys):
    event, prefix, factory, seen = setup(monkeypatch)
    assert (
        cli.main([*prefix, "entities", "list", str(event.public_id)], client_factory=factory) == 0
    )
    catalogue = json.loads(capsys.readouterr().out)
    assert {e["key"] for e in catalogue} >= {"projects", "applications"}
    assert next(e for e in catalogue if e["key"] == "projects")["search_fields"]

    code = cli.main(
        [
            *prefix,
            "entities",
            "query",
            str(event.public_id),
            "projects",
            "--search",
            "robot",
            "--sort=-name",
            "--columns",
            "name",
            "--limit",
            "5",
        ],
        client_factory=factory,
    )
    page = json.loads(capsys.readouterr().out)
    assert code == 0 and page["total"] == 1 and page["rows"][0]["name"] == "Robot arm"
    assert page["search"] == "robot" and page["sort"] == ["-name"]
    assert {method for method, _, _ in seen} == {"GET"}  # nothing is ever written
    query = dict(part.split("=") for part in seen[-1][2].split("&"))
    assert query == {"search": "robot", "sort": "-name", "columns": "name", "limit": "5"}


def test_a_refusal_prints_the_server_message_and_exits_nonzero(monkeypatch, capsys):
    event, prefix, factory, _ = setup(monkeypatch)
    code = cli.main(
        [*prefix, "entities", "query", str(event.public_id), "projects", "--search", "a"],
        client_factory=factory,
    )
    err = capsys.readouterr().err
    assert code == 1 and "400" in err and "search" in err
    missing = cli.main(
        [*prefix, "entities", "query", str(event.public_id), "nothing"], client_factory=factory
    )
    assert missing == 1 and "404" in capsys.readouterr().err


def test_a_role_that_may_not_query_gets_the_servers_refusal(monkeypatch, capsys):
    event, prefix, factory, _ = setup(monkeypatch, role=Role.PARTICIPANT)
    code = cli.main(
        [*prefix, "entities", "query", str(event.public_id), "projects"], client_factory=factory
    )
    assert code == 1 and "403" in capsys.readouterr().err


def test_group_and_subgroup_are_the_same_parameters_as_the_route(monkeypatch, capsys):
    event, prefix, factory, seen = setup(monkeypatch)
    code = cli.main(
        [
            *prefix,
            "entities",
            "query",
            str(event.public_id),
            "projects",
            "--group",
            "gallery_visible",
        ],
        client_factory=factory,
    )
    page = json.loads(capsys.readouterr().out)
    assert code == 0 and page["group"] == "gallery_visible" and page["rows"] == []
    assert [g["count"] for g in page["groups"]] == [2]
    assert "group=gallery_visible" in seen[-1][2]
