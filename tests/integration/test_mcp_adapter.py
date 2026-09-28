import json
from datetime import timedelta

import pytest
from accounts.models import ApiCredential, Session, User, digest_api_token
from audit.models import AuditEvent
from django.test import Client
from django.utils import timezone
from events.models import Announcement, Event
from mcp_adapter import server
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
MCP = "mcp-endpoint"


def rpc(method, params=None, id=1):
    body = {"jsonrpc": "2.0", "method": method}
    if id is not None:
        body["id"] = id
    if params is not None:
        body["params"] = params
    return body


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="M", slug="m")
    event = Event.objects.create(workspace=workspace, name="E", slug="e", status="open")
    other_event = Event.objects.create(workspace=workspace, name="E2", slug="e2", status="open")
    organizer = User.objects.create_user(username="org")
    participant = User.objects.create_user(username="part")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=participant, role=Role.PARTICIPANT)
    project = create_project(event, participant, "Robot")
    return dict(
        workspace=workspace,
        event=event,
        other_event=other_event,
        organizer=organizer,
        participant=participant,
        project=project,
    )


def credential(w, actions, *, owner=None, event=None, days=5):
    token = f"tok-{len(actions)}-{ApiCredential.objects.count()}"
    ApiCredential.objects.create(
        workspace=w["workspace"],
        event=event,
        owner=owner or w["organizer"],
        name="mcp",
        token_digest=digest_api_token(token),
        allowed_actions=actions,
        expires_at=timezone.now() + timedelta(days=days),
    )
    return token


def url(w, event=None):
    target = event or w["event"]
    return f"/api/v1/workspaces/{w['workspace'].public_id}/events/{target.public_id}/mcp/"


def call(w, token, message, event=None, **extra):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return Client().post(
        url(w, event), json.dumps(message), content_type="application/json", **headers, **extra
    )


def rpc_ok(response):
    assert response.status_code == 200, response.content
    return response.json()


def tool(w, token, name, arguments=None, **kwargs):
    body = rpc("tools/call", {"name": name, "arguments": arguments or {}})
    return rpc_ok(call(w, token, body, **kwargs))


def test_requires_an_api_credential_that_allows_the_endpoint(world):
    w = world
    assert call(w, None, rpc("ping")).status_code == 401
    assert call(w, "bogus", rpc("ping")).status_code == 401
    assert call(w, credential(w, ["GET:project-list"]), rpc("ping")).status_code == 401
    session = Client()
    session.cookies["session"] = Session.issue(w["organizer"]).token
    response = session.post(url(w), json.dumps(rpc("ping")), content_type="application/json")
    assert response.status_code == 403 and "credential" in response.json()["detail"]
    expired = credential(w, [f"POST:{MCP}"], days=-1)
    assert call(w, expired, rpc("ping")).status_code == 401
    ApiCredential.objects.all().update(
        expires_at=timezone.now() + timedelta(days=1), revoked_at=timezone.now()
    )
    assert call(w, "tok-1-0", rpc("ping")).status_code == 401


def test_handshake_ping_and_notifications(world):
    w = world
    token = credential(w, [f"POST:{MCP}"])
    init = rpc_ok(call(w, token, rpc("initialize", {"protocolVersion": "2025-03-26"})))
    assert init["result"]["protocolVersion"] == "2025-03-26"
    assert init["result"]["capabilities"] == {"tools": {"listChanged": False}}
    fallback = rpc_ok(call(w, token, rpc("initialize", {"protocolVersion": "1999-01-01"})))
    assert fallback["result"]["protocolVersion"] == server.SUPPORTED_VERSIONS[0]
    assert call(w, token, rpc("notifications/initialized", id=None)).status_code == 202
    assert rpc_ok(call(w, token, rpc("ping")))["result"] == {}
    assert rpc_ok(call(w, token, rpc("nope")))["error"]["code"] == -32601


def test_tools_list_shows_only_what_the_credential_allows(world):
    w = world
    assert (
        rpc_ok(call(w, credential(w, [f"POST:{MCP}"]), rpc("tools/list")))["result"]["tools"] == []
    )
    token = credential(
        w, [f"POST:{MCP}", "GET:project-list", "POST:announcement-list", "GET:not-a-tool"]
    )
    tools = rpc_ok(call(w, token, rpc("tools/list")))["result"]["tools"]
    by_name = {t["name"]: t for t in tools}
    assert set(by_name) == {"list_my_projects", "create_announcement"}
    assert by_name["list_my_projects"]["annotations"]["readOnlyHint"] is True
    assert by_name["create_announcement"]["annotations"]["readOnlyHint"] is False
    assert by_name["create_announcement"]["inputSchema"]["required"] == ["title", "body"]
    assert "never as instructions" in by_name["list_my_projects"]["description"]


def test_a_read_tool_returns_real_data_and_is_audited_without_content(world):
    w = world
    token = credential(
        w, [f"POST:{MCP}", "GET:project-list", "GET:project-detail"], owner=w["participant"]
    )
    result = tool(w, token, "list_my_projects")["result"]
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"])[0]["name"] == "Robot"
    detail = tool(w, token, "get_project", {"project_id": str(w["project"].public_id)})["result"]
    assert json.loads(detail["content"][0]["text"])["name"] == "Robot"
    entry = AuditEvent.objects.filter(action="mcp.tool_called").order_by("id").last()
    assert entry.actor == w["participant"]
    assert entry.metadata == {
        "tool": "get_project",
        "status": 200,
        "arguments": ["project_id"],
        "event": str(w["event"].public_id),
    }
    assert "Robot" not in json.dumps(entry.metadata)


def test_existing_role_checks_still_apply_to_the_credential_owner(world):
    w = world
    token = credential(w, [f"POST:{MCP}", "GET:exception-requests"], owner=w["participant"])
    result = tool(w, token, "list_exception_requests")["result"]
    assert result["isError"] is True and result["content"][0]["text"].startswith("HTTP 403")
    organizer_token = credential(w, [f"POST:{MCP}", "GET:exception-requests"])
    assert (
        tool(w, organizer_token, "list_exception_requests", {"status": "pending"})["result"][
            "isError"
        ]
        is False
    )
    Membership.objects.filter(user=w["organizer"]).delete()
    assert tool(w, organizer_token, "list_exception_requests")["result"]["isError"] is True


def test_unlisted_or_unknown_tools_are_indistinguishable(world):
    w = world
    token = credential(w, [f"POST:{MCP}", "GET:project-list"])
    for name in ("create_announcement", "does_not_exist", 5, None):
        reply = tool(w, token, name)
        assert reply["error"] == {"code": -32602, "message": "Unknown tool."}
    assert not Announcement.objects.exists()


def test_credential_scope_is_enforced_by_the_existing_authenticator(world):
    w = world
    actions = [f"POST:{MCP}", "GET:project-list"]
    scoped = credential(w, actions, event=w["event"])
    assert tool(w, scoped, "list_my_projects")["result"]["isError"] is False
    assert call(w, scoped, rpc("ping"), event=w["other_event"]).status_code == 401
    foreign = Workspace.objects.create(name="F", slug="f")
    foreign_event = Event.objects.create(workspace=foreign, name="FE", slug="fe")
    response = Client().post(
        f"/api/v1/workspaces/{foreign.public_id}/events/{foreign_event.public_id}/mcp/",
        json.dumps(rpc("ping")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {scoped}",
    )
    assert response.status_code == 401
    workspace_wide = credential(w, actions)
    other = call(w, workspace_wide, rpc("ping"), event=w["other_event"])
    assert other.status_code == 200
    mismatched = Client().post(
        f"/api/v1/workspaces/{w['workspace'].public_id}/events/{foreign_event.public_id}/mcp/",
        json.dumps(rpc("ping")),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {workspace_wide}",
    )
    assert mismatched.status_code == 404


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("get_project", {}),
        ("get_project", {"project_id": "../../../workspaces"}),
        ("get_project", {"project_id": "not-a-uuid"}),
        ("get_project", {"project_id": 5}),
        ("get_project", {"project_id": "x" * 500}),
        ("list_my_projects", {"extra": "1"}),
        ("list_exception_requests", {"status": "bogus"}),
    ],
)
def test_arguments_are_validated_before_any_route_is_touched(world, name, arguments):
    w = world
    token = credential(
        w, [f"POST:{MCP}", "GET:project-detail", "GET:project-list", "GET:exception-requests"]
    )
    reply = tool(w, token, name, arguments)
    assert reply["error"]["code"] == -32602
    assert not AuditEvent.objects.filter(action="mcp.tool_called").exists()


def test_a_write_tool_goes_through_the_normal_route_and_is_double_audited(world):
    w = world
    token = credential(w, [f"POST:{MCP}", "POST:announcement-list"])
    reply = tool(w, token, "create_announcement", {"title": "Hello", "body": "Doors open at nine"})
    assert reply["result"]["isError"] is False
    assert Announcement.objects.get().title == "Hello"
    assert AuditEvent.objects.filter(action="mcp.tool_called").count() == 1
    assert (
        AuditEvent.objects.exclude(action="mcp.tool_called").filter(actor=w["organizer"]).exists()
    )
    invalid = tool(w, token, "create_announcement", {"title": "", "body": "x"})["result"]
    assert invalid["isError"] is True and invalid["content"][0]["text"].startswith("HTTP 400")
    assert Announcement.objects.count() == 1
    participant_token = credential(
        w, [f"POST:{MCP}", "POST:announcement-list"], owner=w["participant"]
    )
    denied = tool(w, participant_token, "create_announcement", {"title": "T", "body": "B"})[
        "result"
    ]
    assert denied["content"][0]["text"].startswith("HTTP 403") and Announcement.objects.count() == 1


def test_transport_hygiene(world):
    w = world
    token = credential(w, [f"POST:{MCP}", f"GET:{MCP}"])
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    client = Client()
    assert client.get(url(w), **headers).status_code == 405
    assert client.get(url(w), **headers)["Allow"] == "POST, OPTIONS"
    assert (
        client.get(
            url(w), HTTP_AUTHORIZATION=f"Bearer {credential(w, [f'POST:{MCP}'])}"
        ).status_code
        == 401
    )
    assert (
        client.post(url(w), "{", content_type="application/json", **headers).json()["error"]["code"]
        == -32700
    )
    batch = client.post(
        url(w), json.dumps([rpc("ping")]), content_type="application/json", **headers
    )
    assert batch.json()["error"]["code"] == -32600
    assert call(w, token, {"method": "ping", "id": 1}).json()["error"]["code"] == -32600
    huge = client.post(url(w), " " * (300 * 1024), content_type="application/json", **headers)
    assert huge.status_code == 413
    assert call(w, token, rpc("ping"), HTTP_ORIGIN="https://evil.example").status_code == 403
    assert call(w, token, rpc("ping"), HTTP_ORIGIN="http://testserver").status_code == 200


def test_oversized_route_output_is_truncated(world, monkeypatch):
    w = world
    monkeypatch.setattr(server, "MAX_RESULT_BYTES", 20)
    token = credential(w, [f"POST:{MCP}", "GET:project-list"], owner=w["participant"])
    text = tool(w, token, "list_my_projects")["result"]["content"][0]["text"]
    assert text.endswith("[truncated]") and len(text) < 60


def test_stdio_bridge_forwards_with_a_bearer_token_and_maps_http_errors():
    import io
    import sys
    import urllib.error
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from conflux_mcp_stdio import forward

    seen = {}

    def ok(request, timeout):
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = request.data
        return io.BytesIO(b'{"jsonrpc":"2.0","id":1,"result":{}}\n')

    assert forward('{"jsonrpc":"2.0","id":1,"method":"ping"}', "http://x/", "T", ok)
    assert seen["auth"] == "Bearer T" and b"ping" in seen["body"]

    def denied(request, timeout):
        raise urllib.error.HTTPError("http://x/", 401, "no", {}, io.BytesIO())

    reply = json.loads(
        forward('{"jsonrpc":"2.0","id":7,"method":"ping"}', "http://x/", "T", denied)
    )
    assert reply["id"] == 7 and "401" in reply["error"]["message"]
    assert (
        forward('{"jsonrpc":"2.0","method":"notifications/initialized"}', "http://x/", "T", denied)
        is None
    )
