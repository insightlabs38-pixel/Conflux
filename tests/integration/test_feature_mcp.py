"""PD-F003-B02-T05: the MCP claims of the completeness contract, held against the tool catalogue.

The adapter's tools are existing routes called with the credential's own authority. The verifier
reads the catalogue and the permission matrix; these tests prove the claims through the real
endpoint: every tool is claimed by exactly one feature or named as outside the registry, and each
claimed tool succeeds with a credential limited to its own route and is refused without it."""

import pytest
from audit.models import AuditEvent
from core import features as ft
from core import features_mcp
from mcp_adapter import tools as catalogue

from tests.integration.test_mcp_adapter import MCP, credential, tool, world  # noqa: F401

pytestmark = pytest.mark.django_db


def claimed():
    found = {}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        names, _, _, _ = features_mcp.parse(feature.claims["mcp"])
        for name in names:
            found.setdefault(name, []).append(feature.key)
    return found


CLAIMED = claimed()


def test_every_mcp_tool_is_claimed_by_exactly_one_feature_or_named_as_outside():
    assert set(catalogue.BY_NAME) == set(CLAIMED) | set(features_mcp.OUTSIDE)
    assert all(len(owners) == 1 for owners in CLAIMED.values())
    assert not set(CLAIMED) & set(features_mcp.OUTSIDE)
    assert all(len(r) >= features_mcp.MIN_REASON for r in features_mcp.OUTSIDE.values())
    owned = set().union(*(features_mcp.feature_routes(f) for f in ft.FEATURES.values()))
    for name in features_mcp.OUTSIDE:  # an outside tool calls a route no feature claims
        assert catalogue.BY_NAME[name].url_name not in owned, name


def test_the_registry_is_clean_with_the_mcp_claims():
    assert ft.check() == []


ARGUMENTS = {
    "list_stages": lambda w: {},
    "list_my_projects": lambda w: {},
    "get_project": lambda w: {"project_id": str(w["project"].public_id)},
    "list_announcements": lambda w: {},
    "create_announcement": lambda w: {"title": "Hello", "body": "Doors open"},
}


def test_each_claimed_tool_reaches_its_own_route_with_a_credential_limited_to_it(world):  # noqa: F811
    assert set(ARGUMENTS) == set(CLAIMED)
    w = world
    for name, arguments in ARGUMENTS.items():
        spec = catalogue.BY_NAME[name]
        owner = w["participant"] if name in ("list_my_projects", "get_project") else None
        allowed = credential(w, [f"POST:{MCP}", spec.action], owner=owner)
        result = tool(w, allowed, name, arguments(w))["result"]
        assert result["isError"] is False, (name, result)
        other = next(t for t in catalogue.TOOLS if t.action != spec.action)
        limited = credential(w, [f"POST:{MCP}", other.action], owner=owner)
        refused = tool(w, limited, name, arguments(w))
        assert "error" in refused or refused["result"]["isError"] is True, name
    called = AuditEvent.objects.filter(action="mcp.tool_called").values_list("metadata", flat=True)
    assert {m["tool"] for m in called if m["status"] < 300} >= set(ARGUMENTS)


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"mcp": claim})
    return ft.VERIFIERS["mcp"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_mcp.py"
    "::test_every_mcp_tool_is_claimed_by_exactly_one_feature_or_named_as_outside"
)


def test_the_real_claims_verify_clean_and_the_report_lists_the_tools():
    assert (
        verify("announcement", ("tool:list_announcements", "tool:create_announcement", TEST)) == []
    )
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["announcement"]["facts"]["mcp"]["tools"] == [
        "list_announcements (read): GET announcement-list",
        "create_announcement (write): POST announcement-list",
    ]
    assert row["track"]["facts"]["mcp"]["mcp"] == "no tool"


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", ("no_mcp@short",), "no_reason"),
        (
            "stage",
            ("tool:list_stages", TEST, "no_mcp@an agent has nothing to do here at all"),
            "both",
        ),
        ("stage", (TEST,), "no_tool"),
        ("stage", ("tool:list_stages",), "no_test"),
        ("stage", ("tool:list_stages", "test:nowhere"), "test_ref"),
        ("stage", ("tool:list_stages", TEST, "color:red"), "bad_ref"),
        ("stage", ("tool:teleport", TEST), "tool_unknown"),
        ("stage", ("tool:list_stages", "tool:list_stages", TEST), "tool_twice"),
        ("stage", ("tool:list_my_projects", TEST), "tool_foreign"),
        ("stage", (TEST,), "tool_unclaimed"),
        ("track", ("tool:list_stages", TEST), "tool_foreign"),
        ("track", ("no_mcp@a reason long enough to be a sentence",), "ok"),
        ("stage", ("no_mcp@a reason long enough to be a sentence",), "mcp_exists"),
    ],
)
def test_each_mcp_failure_has_a_code(key, refs, code):
    found = codes(verify(key, refs))
    assert (not found) if code == "ok" else code in found


def test_a_tool_may_not_be_claimed_by_two_features():
    found = codes(
        verify("project", ("tool:list_stages", "tool:list_my_projects", "tool:get_project", TEST))
    )
    assert {"tool_shared", "tool_foreign"} <= found


def test_a_write_tool_must_reach_an_audited_role_gated_route(monkeypatch):
    audit = ft.FEATURES["announcement"].claims["audit"]
    stripped = ft.provided(*[r for r in audit.refs if "announcement-list:POST" not in r])
    base = ft.FEATURES["announcement"]
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"audit": stripped})
    claim = ft.provided("tool:list_announcements", "tool:create_announcement", TEST)
    assert "write_unaudited" in codes(ft.VERIFIERS["mcp"](feature, claim, ft.System()))
