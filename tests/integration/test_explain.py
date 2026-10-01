"""PD-F002-B02-T06: one explanation shape over policy traces, readiness and consequence previews."""

import json
import pathlib
import random

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from core import explain
from django.test import Client
from events.models import Event
from policies.debugger import debug_action
from policies.evaluator import trace_evaluate
from policies.models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/fixtures/explain_cases.json").read_text())["cases"]
ADAPTERS = {
    "policy": explain.from_policy_debug,
    "readiness": lambda payload, detailed: explain.from_readiness(payload),
    "consequences": lambda payload, detailed: explain.from_consequences(payload),
}


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_the_shared_fixtures_hold(case):
    """The same file is drawn by vitest (components/ExplanationView.test.tsx) from the server."""
    got = ADAPTERS[case["adapter"]](case["input"], detailed=case["detailed"])
    assert got == case["output"]


# --- the shape itself ---------------------------------------------------------------------


def test_a_reason_and_an_explanation_are_bounded_scalar_text():
    row = explain.reason(
        "c" * 200,
        "m" * 900,
        severity="blocker",
        facts={f"k{i}": i for i in range(30)} | {"obj": {"a": [1]}, "long": "x" * 900},
        fix={"destination": "setup", "section": None},
    )
    assert len(row["code"]) == 80 and len(row["message"]) == explain.MAX_MESSAGE
    assert len(row["facts"]) == explain.MAX_FACTS and row["fix"] == {
        "destination": "setup",
        "section": None,
    }
    spread = explain.reason("c", "m", facts={"obj": {"a": [1]}, "ctl": "a\x00b", "n": None})
    assert spread["facts"] == {"obj": '{"a": [1]}', "ctl": "a�b", "n": None}
    many = explain.explanation(
        "blocked", "s", [explain.reason(f"r{i}", "m") for i in range(explain.MAX_REASONS + 5)]
    )
    assert len(many["reasons"]) == explain.MAX_REASONS and many["total"] == explain.MAX_REASONS + 5
    assert many["truncated"] is True


def test_unknown_outcomes_and_severities_are_programming_errors():
    with pytest.raises(ValueError):
        explain.explanation("maybe", "s")
    with pytest.raises(ValueError):
        explain.reason("c", "m", severity="fatal")
    assert explain.unknown("Not decided yet.") == {
        "outcome": "unknown", "summary": "Not decided yet.", "reasons": [], "total": 0,
        "truncated": False,
    }  # fmt: skip


def test_an_independent_feature_builds_an_explanation_with_no_adapter():
    """A feature outside policies and eventconfig explains its own refusal with the two builders."""
    closes = "2026-10-01T12:00:00Z"
    refused = explain.explanation(
        "blocked",
        "Voting is closed.",
        [
            explain.reason(
                "voting_closed",
                f"Voting closed at {closes}.",
                severity="blocker",
                facts={"closed_at": closes},
                fix={"destination": "results", "section": None},
            )
        ],
    )
    assert (
        refused["outcome"] == "blocked" and refused["reasons"][0]["fix"]["destination"] == "results"
    )
    assert refused == json.loads(json.dumps(refused))  # plain JSON all the way down


# --- policy adapter against the real evaluator --------------------------------------------


def leaf(op, fact, value):
    return {"op": op, "fact": fact, "value": value}


def payload_for(ast, facts, grant=None):
    allowed, error, trace = trace_evaluate(ast, facts)
    return {
        "policy": {"name": "Gate"},
        "policy_allowed": allowed,
        "allowed": allowed or grant is not None,
        "reason": None if allowed else "Denied by policy 'Gate' on action 'submit'.",
        "exception_grant_reason": grant,
        "error": error,
        "trace": trace,
    }


def random_ast(rng, depth=0):
    facts = ["a", "b", "c"]
    if depth >= 3 or rng.random() < 0.4:
        op = rng.choice(["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "true", "false"])
        if op in ("true", "false"):
            return {"op": op}
        value = [1, 2] if op in ("in", "not_in") else rng.randint(0, 3)
        return {"op": op, "fact": rng.choice(facts), "value": value}
    op = rng.choice(["and", "or", "not"])
    count = 1 if op == "not" else rng.randint(1, 3)
    return {"op": op, "args": [random_ast(rng, depth + 1) for _ in range(count)]}


def test_the_explanation_always_agrees_with_the_decision_over_random_policies():
    rng = random.Random(42)
    seen = {"blocked": 0, "allowed": 0}
    for _ in range(600):
        ast = random_ast(rng)
        facts = {k: rng.randint(0, 3) for k in "abc"}
        payload = payload_for(ast, facts)
        got = explain.from_policy_debug(payload)
        assert got == explain.from_policy_debug(payload)  # deterministic
        assert got["outcome"] == ("allowed" if payload["allowed"] else "blocked")
        blockers = [r for r in got["reasons"] if r["severity"] == "blocker"]
        assert bool(blockers) == (not payload["allowed"]), (ast, facts, got)
        seen[got["outcome"]] += 1
        hidden = explain.from_policy_debug(payload, detailed=False)
        assert hidden["outcome"] == got["outcome"]
        assert all("facts" not in r for r in hidden["reasons"])
    assert seen["blocked"] > 50 and seen["allowed"] > 50


def test_a_malformed_policy_is_explained_not_raised():
    for ast in ({"op": "wat"}, {"op": "and", "args": []}, {"op": "eq", "fact": 5}, "nope", None):
        payload = payload_for(ast, {})
        got = explain.from_policy_debug(payload)
        assert got["outcome"] == "blocked" and got["reasons"][0]["code"] == "policy_error"


def test_hidden_facts_never_appear_for_a_reader_who_may_not_see_them():
    ast = leaf("eq", "secret_score", 99)
    payload = payload_for(ast, {"secret_score": 41})
    hidden = json.dumps(explain.from_policy_debug(payload, detailed=False))
    assert "41" not in hidden and "99" not in hidden and "secret_score" not in hidden
    shown = json.dumps(explain.from_policy_debug(payload, detailed=True))
    assert "41" in shown and "99" in shown


# --- the endpoints beside their existing shapes ------------------------------------------


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


@pytest.fixture
def world(db):
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    organizer = User.objects.create_user(username="organizer", password="unused")
    member = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=member, role=Role.PARTICIPANT)
    project = create_project(event, member, "P")
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    return {
        "event": event,
        "organizer": organizer,
        "member": member,
        "project": project,
        "base": base,
    }


def bind(event, ast):
    policy = Policy.objects.create(event=event, name="Gate", ast=ast)
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)


def test_the_policy_debugger_adds_the_explanation_and_keeps_every_existing_key(world):
    TemporalGate.objects.create(event=world["event"], name="submissions")
    bind(world["event"], {"op": "eq", "fact": "gate_open:submissions", "value": False})
    audits = AuditEvent.objects.count()
    body = (
        client_for(world["organizer"])
        .post(
            world["base"] + "policy-debug/", {"action": "submit"}, content_type="application/json"
        )
        .json()
    )
    legacy = {
        "action", "subject_type", "subject_id", "checked_at", "facts", "policy", "policy_allowed",
        "allowed", "reason", "exception_grant_reason", "error", "trace",
    }  # fmt: skip
    assert set(body) == legacy | {"explanation"}
    shown = body["explanation"]
    assert shown["outcome"] == "blocked" and shown["summary"] == body["reason"]
    assert [r["code"] for r in shown["reasons"]] == ["gate_open"] and shown["reasons"][0][
        "severity"
    ] == "blocker"  # the check as written wanted the window closed, and it is open
    assert AuditEvent.objects.count() == audits
    assert shown == debug_action(world["event"], "submit")["explanation"]  # derived, stable


def test_the_policy_debugger_explains_a_grant_and_a_missing_policy(world):
    bind(world["event"], {"op": "eq", "fact": "gate_open:missing", "value": True})
    ExceptionGrant.objects.create(
        event=world["event"], action=Action.SUBMIT, subject_type="project",
        subject_id=str(world["project"].public_id), reason="Approved correction",
        granted_by=world["organizer"],
    )  # fmt: skip
    body = (
        client_for(world["organizer"])
        .post(
            world["base"] + "policy-debug/",
            {
                "action": "submit",
                "subject_type": "project",
                "subject_id": str(world["project"].public_id),
            },
            content_type="application/json",
        )
        .json()
    )
    assert body["explanation"]["outcome"] == "allowed"
    assert [r["code"] for r in body["explanation"]["reasons"]] == [
        "exception_grant",
        "policy_error",
    ]
    none = (
        client_for(world["organizer"])
        .post(world["base"] + "policy-debug/", {"action": "award"}, content_type="application/json")
        .json()
    )
    assert none["explanation"]["reasons"][0]["code"] == "no_policy"


def test_readiness_and_its_legacy_surfaces_carry_the_same_explanation(world):
    client = client_for(world["organizer"])
    canonical = client.get(world["base"] + "readiness/").json()
    legacy = client.get(world["base"] + "operations/checklist/").json()
    assert legacy == canonical
    shown = canonical["explanation"]
    open_items = [i for i in canonical["items"] if not i["passed"]]
    assert shown["total"] == len(open_items)
    assert (
        shown["outcome"]
        == {"blocked": "blocked", "warning": "needs_action", "ready": "allowed"}[
            canonical["status"]
        ]
    )
    for row in shown["reasons"]:
        item = next(i for i in open_items if i["id"] == row["code"])
        assert (
            row["message"] == item["detail"]
            and row["fix"]["destination"] == item["fix"]["destination"]
        )
    assert [r["severity"] for r in shown["reasons"]] == sorted(
        (r["severity"] for r in shown["reasons"]), key={"blocker": 0, "warning": 1}.get
    )


def test_consequence_previews_carry_the_explanation_beside_their_blockers(world):
    client = client_for(world["organizer"])
    refused = client.get(world["base"] + "consequences/?action=event.close").json()  # a draft event
    assert refused["allowed"] is False
    shown = refused["explanation"]
    assert shown["outcome"] == "blocked" and shown["summary"] == "This cannot be done right now."
    assert [r["message"] for r in shown["reasons"] if r["severity"] == "blocker"] == [
        b["message"] for b in refused["blockers"]
    ]
    allowed = client.get(world["base"] + "consequences/?action=event.delete").json()
    assert allowed["explanation"]["outcome"] == "allowed"
    codes = [r["code"] for r in allowed["explanation"]["reasons"]]
    assert "irreversible" in codes and codes[:-1] == [c["code"] for c in allowed["consequences"]]
    assert {c["code"] for c in allowed["consequences"]} <= set(codes)
    assert set(allowed) >= {"action", "title", "blockers", "consequences", "reversible"}
