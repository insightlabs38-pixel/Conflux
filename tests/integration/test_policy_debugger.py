import pytest
from accounts.models import Session, User
from django.test import Client
from events.models import Event
from policies.evaluator import is_allowed, trace_evaluate
from policies.models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from projects.services import create_project
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def setup_case():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    organizer = User.objects.create_user(username="organizer", password="unused")
    member = User.objects.create_user(username="member", password="unused")
    Membership.objects.create(workspace=workspace, user=organizer, role=Role.ORGANIZER)
    Membership.objects.create(workspace=workspace, user=member, role=Role.PARTICIPANT)
    project = create_project(event, member, "P")
    endpoint = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/policy-debug/"
    return workspace, event, organizer, member, project, endpoint


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def bound_policy(event, ast):
    policy = Policy.objects.create(event=event, name="Gate", ast=ast)
    PolicyBinding.objects.create(event=event, action=Action.SUBMIT, policy=policy)
    return policy


def test_trace_shows_values_and_short_circuited_branch():
    ast = {
        "op": "and",
        "args": [
            {"op": "eq", "fact": "gate_open:submit", "value": True},
            {"op": "eq", "fact": "missing", "value": True},
        ],
    }
    allowed, error, trace = trace_evaluate(ast, {"gate_open:submit": False})
    assert allowed is is_allowed(ast, {"gate_open:submit": False}) is False
    assert error is None
    assert trace["children"][0]["actual"] is False
    assert trace["children"][0]["result"] is False
    assert trace["children"][1]["status"] == "skipped"


def test_trace_reports_missing_fact_and_fails_closed():
    ast = {"op": "eq", "fact": "missing", "value": True}
    allowed, error, trace = trace_evaluate(ast, {})
    assert allowed is is_allowed(ast, {}) is False
    assert "Unknown fact" in error
    assert trace["status"] == "error"


def test_trace_marks_siblings_skipped_after_an_error():
    ast = {
        "op": "and",
        "args": [
            {"op": "eq", "fact": "missing", "value": True},
            {"op": "true"},
        ],
    }
    allowed, error, trace = trace_evaluate(ast, {})
    assert not allowed and "Unknown fact" in error
    assert trace["children"][0]["status"] == "error"
    assert trace["children"][1]["status"] == "skipped"


def test_debug_endpoint_shows_policy_trace_and_exact_subject_grant():
    _, event, organizer, _, project, endpoint = setup_case()
    bound_policy(event, {"op": "eq", "fact": "gate_open:missing", "value": True})
    ExceptionGrant.objects.create(
        event=event,
        action=Action.SUBMIT,
        subject_type="project",
        subject_id=str(project.public_id),
        reason="Approved correction",
        granted_by=organizer,
    )
    response = client_for(organizer).post(
        endpoint,
        {"action": "submit", "subject_type": "project", "subject_id": str(project.public_id)},
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["policy_allowed"] is False
    assert body["allowed"] is True
    assert body["exception_grant_reason"] == "Approved correction"
    assert "Unknown fact" in body["error"]
    assert body["trace"]["status"] == "error"


def test_debug_endpoint_without_binding_reports_only_policy_decision():
    _, _, organizer, _, _, endpoint = setup_case()
    response = client_for(organizer).post(
        endpoint, {"action": "award"}, content_type="application/json"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True
    assert body["policy"] is None
    assert body["trace"] is None


def test_debug_endpoint_reports_a_true_bound_policy_with_server_gate_fact():
    _, event, organizer, _, _, endpoint = setup_case()
    TemporalGate.objects.create(event=event, name="submissions")
    bound_policy(event, {"op": "eq", "fact": "gate_open:submissions", "value": True})
    response = client_for(organizer).post(
        endpoint, {"action": "submit"}, content_type="application/json"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True
    assert body["policy_allowed"] is True
    assert body["facts"]["gate_open:submissions"] is True
    assert body["trace"]["result"] is True


def test_debug_endpoint_requires_organizer_and_event_scoped_subject():
    workspace, event, organizer, member, project, endpoint = setup_case()
    request = {"action": "submit", "subject_type": "project", "subject_id": str(project.public_id)}
    assert (
        client_for(member).post(endpoint, request, content_type="application/json").status_code
        == 403
    )
    other_event = Event.objects.create(workspace=workspace, name="Other", slug="other")
    alien = create_project(other_event, member, "Alien")
    request["subject_id"] = str(alien.public_id)
    assert (
        client_for(organizer).post(endpoint, request, content_type="application/json").status_code
        == 404
    )
    assert (
        client_for(organizer)
        .post(endpoint, {"action": "invalid"}, content_type="application/json")
        .status_code
        == 400
    )
    assert (
        client_for(organizer)
        .post(
            endpoint,
            {"action": "submit", "subject_type": "team", "subject_id": str(project.public_id)},
            content_type="application/json",
        )
        .status_code
        == 400
    )
