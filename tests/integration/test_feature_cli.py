"""PD-F003-B02-T04: the CLI claims of the completeness contract, held against the command table.

The CLI is a thin client of the generated Python SDK: `COMMANDS` maps each command to the
operation(s) it calls. The verifier reads that table in CI; these tests prove it against the API:
every command is claimed by exactly one feature or named as outside the registry, and each claimed
command sends the request its operation describes through the real API."""

import io
import json
import sys
from datetime import timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit

import pytest
from accounts.models import Session, User
from core import features as ft
from core import features_cli
from django.test import Client
from django.utils import timezone
from events.models import Event
from workspaces.models import Membership, Role, Workspace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdks/python"))
from conflux_sdk import ConfluxClient, cli  # noqa: E402
from conflux_sdk.generated import OPERATIONS  # noqa: E402

pytestmark = pytest.mark.django_db


def claimed():
    found = {}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        commands, _, _, _ = features_cli.parse(feature.claims["cli"])
        for command in commands:
            found.setdefault(command, []).append(feature.key)
    return found


CLAIMED = claimed()


def test_every_cli_command_is_claimed_by_exactly_one_feature_or_named_as_outside():
    assert set(cli.COMMANDS) == set(CLAIMED) | set(features_cli.OUTSIDE)
    assert all(len(owners) == 1 for owners in CLAIMED.values())
    assert not set(CLAIMED) & set(features_cli.OUTSIDE)
    assert all(len(reason) >= features_cli.MIN_REASON for reason in features_cli.OUTSIDE.values())
    system = ft.System()
    owned = set()
    for feature in ft.FEATURES.values():
        owned |= features_cli.own_operations(feature, system)
    for command in features_cli.OUTSIDE:  # an outside command touches no feature's operation
        assert not set(cli.COMMANDS[command]) & owned, command


def test_every_command_calls_generated_operations():
    for command, operations in cli.COMMANDS.items():
        assert operations and set(operations) <= set(OPERATIONS), command


def test_the_ci_check_reads_the_real_tree_clean():
    assert ft.check() == []
    assert [p for p in ft.check_static(ROOT) if p["property"] == "cli"] == []


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


def test_each_claimed_command_sends_the_request_its_operation_describes(monkeypatch, tmp_path):
    user = User.objects.create_user(username="cli-claims")
    workspace = Workspace.objects.create(name="CLI claims", slug="cli-claims")
    Membership.objects.create(user=user, workspace=workspace, role=Role.ORGANIZER)
    monkeypatch.setenv("CONFLUX_SESSION_TOKEN", Session.issue(user).token)
    monkeypatch.delenv("CONFLUX_BEARER_TOKEN", raising=False)
    seen = []

    def opener(request):
        seen.append((request.method, urlsplit(request.full_url).path))
        parts = urlsplit(request.full_url)
        response = Client().generic(
            request.method,
            parts.path + ("?" + parts.query if parts.query else ""),
            data=request.data or b"",
            content_type="application/json",
            HTTP_COOKIE=request.get_header("Cookie", ""),
            HTTP_AUTHORIZATION=request.get_header("Authorization", ""),
        )
        if response.status_code >= 400:
            raise HTTPError(parts.path, response.status_code, "Failed", {}, io.BytesIO(b"{}"))
        return Response(response)

    def factory(url, **kwargs):
        return ConfluxClient(url, **{**kwargs, "opener": opener})

    prefix = ["--base-url", "http://127.0.0.1:8093", "--workspace", str(workspace.public_id)]

    def expect(command, event=None):
        ((method, path),) = seen
        operation = OPERATIONS[cli.COMMANDS[command][0]]
        route = operation["path"].replace("{workspace_public_id}", str(workspace.public_id))
        route = route.replace("{event_public_id}", str(event)) if event else route
        assert (method, path) == (operation["method"], route), command

    change = tmp_path / "change.json"
    change.write_text(json.dumps({"description": "Changed"}))
    assert (
        cli.main(
            [*prefix, "events", "create", "--name", "C", "--slug", "c"], client_factory=factory
        )
        == 0
    )
    expect("events create")
    seen.clear()
    event = Event.objects.get(slug="c")
    event.starts_at = timezone.now() + timedelta(hours=1)
    event.ends_at = timezone.now() + timedelta(hours=2)
    event.save()
    arguments = {
        "events list": ("events", "list"),
        "events get": ("events", "get", str(event.public_id)),
        "events update": ("events", "update", str(event.public_id), "--input", str(change)),
        "events status": ("events", "status", str(event.public_id), "--status", "open"),
    }
    assert set(arguments) | {"events create"} == set(CLAIMED)
    for command, args in arguments.items():
        assert cli.main([*prefix, *args], client_factory=factory) == 0, command
        expect(command, None if command == "events list" else event.public_id)
        seen.clear()


def verify(refs, key="event"):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, {"cli": claim})
    return ft.VERIFIERS["cli"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_cli.py::test_every_cli_command_calls_generated_operations"
)


def test_the_real_claims_verify_clean_and_the_report_lists_the_commands():
    assert verify(("command:events list", TEST)) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["event"]["facts"]["cli"]["commands"][0] == "conflux-admin events list"
    assert row["track"]["facts"]["cli"]["cli"] == "no command"


@pytest.mark.parametrize(
    ("refs", "code"),
    [
        (("no_cli@short",), "no_reason"),
        (("command:events list", TEST, "no_cli@the CLI has nothing for this feature"), "both"),
        ((TEST,), "no_command"),
        (("command:events list",), "no_test"),
        (("command:events list", "test:nowhere"), "test_ref"),
        (("command:Events List", TEST), "command_shape"),
        (("command:events list", "command:events list", TEST), "command_twice"),
        (("command:events list", TEST, "color:red"), "bad_ref"),
    ],
)
def test_each_cli_failure_has_a_code(refs, code):
    assert code in codes(verify(refs))


def test_a_claimed_command_may_not_be_shared_with_another_feature():
    assert "command_shared" in codes(verify(("command:events list", TEST), key="track"))


EVENTS = "get_api_v1_workspaces_workspace_public_id_events"
DETAIL = "get_api_v1_workspaces_workspace_public_id_events_event_public_id"


def tree(tmp_path, commands, operations=(EVENTS, DETAIL)):
    package = tmp_path / "sdks/python/conflux_sdk"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "cli.py").write_text(f"COMMANDS = {commands!r}\n")
    (package / "generated.py").write_text(f"OPERATIONS = {dict.fromkeys(operations, {})!r}\n")


@pytest.mark.parametrize(
    ("commands", "refs", "operations", "expected"),
    [
        ({"events list": (EVENTS,)}, ("command:events list",), (EVENTS,), set()),
        (
            {"events list": (EVENTS,)},
            ("command:events show",),
            (EVENTS,),
            {"command_missing", "command_unclaimed"},
        ),
        ({"events list": (EVENTS,)}, ("command:events list",), (), {"op_not_generated"}),
        (
            {"whoami": ("get_api_v1_accounts_me",)},
            ("command:whoami",),
            ("get_api_v1_accounts_me",),
            {"command_foreign"},
        ),
        (
            {"events list": (EVENTS,), "events get": (DETAIL,)},
            ("command:events list",),
            (EVENTS, DETAIL),
            {"command_unclaimed"},
        ),
        ({"events list": (EVENTS,)}, ("no_cli@the CLI has nothing"), (EVENTS,), {"cli_exists"}),
    ],
)
def test_the_ci_check_holds_each_command_to_the_feature_and_the_client(
    tmp_path, commands, refs, operations, expected
):
    tree(tmp_path, commands, operations)
    refs = (refs,) if isinstance(refs, str) else refs
    claim = ft.provided(*refs)
    feature = ft.Feature("event", "Event", "events.Event", ft.FEATURES["event"].claims)
    found = features_cli.static(feature, claim, tmp_path)
    assert {p["code"] for p in found} - {"test_file", "test_name"} == expected


def test_the_ci_check_reports_an_unreadable_table(tmp_path):
    claim = ft.provided("command:events list")
    feature = ft.FEATURES["event"]
    assert "table_unreadable" in codes(features_cli.static(feature, claim, tmp_path))
