from datetime import timedelta

import pytest
from accounts.models import Session, User
from audit.models import AuditEvent
from django.test import Client
from django.utils import timezone
from evaluations.models import (
    Assignment,
    AssignmentVersion,
    Ballot,
    ConflictOfInterest,
    NormalizationRun,
)
from events.models import Event
from governance.models import ResultCorrection, SubmissionReceipt
from policies.models import Action, ExceptionGrant, Policy, PolicyBinding, TemporalGate
from policies.services import base_facts, check_action
from presentation.records import verify_record
from projects.services import create_project
from projects.submissions import finalize_submission, save_draft
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def client_for(user):
    result = Client()
    result.cookies["session"] = Session.issue(user).token
    return result


def user(name, workspace, role):
    account = User.objects.create_user(username=name)
    Membership.objects.create(workspace=workspace, user=account, role=role)
    return account


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="G", slug="g")
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="E",
        slug="e",
        status="open",
        is_public=True,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
    )
    stage = Stage.objects.create(event=event, name="Build")
    org_a = user("org-a", workspace, Role.ORGANIZER)
    org_b = user("org-b", workspace, Role.ORGANIZER)
    judge = user("judge", workspace, Role.JUDGE)
    judge2 = user("judge2", workspace, Role.JUDGE)
    member = user("member", workspace, Role.PARTICIPANT)
    other = user("other", workspace, Role.PARTICIPANT)
    project = create_project(event, member, "Mine")
    other_project = create_project(event, other, "Theirs")
    return dict(
        workspace=workspace,
        event=event,
        stage=stage,
        org_a=org_a,
        org_b=org_b,
        judge=judge,
        judge2=judge2,
        member=member,
        other=other,
        project=project,
        other_project=other_project,
    )


def base(w):
    return f"/api/v1/workspaces/{w['workspace'].public_id}/events/{w['event'].public_id}/"


def post(client, url, data=None):
    return client.post(url, data or {}, content_type="application/json")


def make_plan(w):
    c = client_for(w["org_a"])
    url = f"{base(w)}stages/{w['stage'].public_id}/evaluation-plans/"
    plan_id = post(c, url, {"name": "Panel", "draft_criteria": CRITERIA}).json()["public_id"]
    assert post(c, f"{url}{plan_id}/publish-rubric/").status_code == 201
    return url + f"{plan_id}/", plan_id


def submit_ballot(w, plan_url, judge, project, score=5):
    r = post(
        client_for(judge),
        plan_url + "ballots/",
        {
            "project": str(project.public_id),
            "responses": [{"criterion_id": "impact", "score": score}],
        },
    )
    assert r.status_code == 201, r.content
    return r


def new_run(w, plan_url):
    r = post(client_for(w["org_a"]), plan_url + "normalization-runs/")
    assert r.status_code == 201, r.content
    return r.json()["public_id"]


# Rules


def test_rules_are_versioned_immutable_and_acknowledged_per_version(world):
    w = world
    assert client_for(w["member"]).get(base(w) + "rules/").json()["current"] is None
    assert (
        post(client_for(w["member"]), base(w) + "rules/", {"title": "T", "body": "B"}).status_code
        == 403
    )
    org = client_for(w["org_a"])
    assert post(org, base(w) + "rules/", {"title": "Rules", "body": "v1"}).json()["number"] == 1
    member = client_for(w["member"])
    view = member.get(base(w) + "rules/").json()
    assert view["current"]["body"] == "v1" and view["acknowledged"] is False
    assert post(member, base(w) + "rules/acknowledge/", {"number": 2}).status_code == 400
    assert post(member, base(w) + "rules/acknowledge/", {"number": 1}).status_code == 201
    assert post(member, base(w) + "rules/acknowledge/").status_code == 200
    assert AuditEvent.objects.filter(action="rules.acknowledged").count() == 1
    pending = org.get(base(w) + "rules/acknowledgements/").json()
    assert [a["user"] for a in pending["acknowledged"]] == ["member"]
    assert pending["pending"] == ["other"]
    post(org, base(w) + "rules/", {"title": "Rules", "body": "v2"})
    assert member.get(base(w) + "rules/").json()["acknowledged"] is False
    assert member.get(base(w) + "rules/1/").json()["body"] == "v1"
    assert client_for(w["member"]).get(base(w) + "rules/acknowledgements/").status_code == 403


# Publication approval and correction history


def published_world(w):
    plan_url, plan_id = make_plan(w)
    submit_ballot(w, plan_url, w["judge"], w["project"], 4)
    submit_ballot(w, plan_url, w["judge"], w["other_project"], 8)
    return plan_url, plan_id, new_run(w, plan_url)


def test_publication_approval_needs_a_second_organizer_and_records_corrections(world):
    w = world
    plan_url, plan_id, run_1 = published_world(w)
    org_a, org_b = client_for(w["org_a"]), client_for(w["org_b"])
    settings_url = base(w) + "governance/settings/"
    assert (
        org_a.put(
            settings_url, {"require_publication_approval": True}, content_type="application/json"
        ).status_code
        == 200
    )
    direct = post(org_a, plan_url + "publish-results/", {"normalization_run": run_1})
    assert direct.status_code == 400

    requests_url = base(w) + "result-publication-requests/"
    created = post(org_a, requests_url, {"plan": plan_id, "normalization_run": run_1})
    assert created.status_code == 201
    request_id = created.json()["public_id"]
    assert (
        post(org_a, requests_url, {"plan": plan_id, "normalization_run": run_1}).status_code == 400
    )
    assert post(org_a, f"{requests_url}{request_id}/approve/").status_code == 400
    approved = post(org_b, f"{requests_url}{request_id}/approve/", {"note": "ok"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert post(org_b, f"{requests_url}{request_id}/approve/").status_code == 400
    assert client_for(w["member"]).get(plan_url + "results/").status_code in (403, 404)
    assert org_a.get(plan_url + "results/").status_code == 200
    assert not ResultCorrection.objects.exists()

    submit_ballot(w, plan_url, w["judge2"], w["project"], 9)
    run_2 = new_run(w, plan_url)
    no_reason = post(org_a, requests_url, {"plan": plan_id, "normalization_run": run_2})
    assert no_reason.status_code == 400
    again = post(
        org_a, requests_url, {"plan": plan_id, "normalization_run": run_2, "reason": "Late ballot"}
    )
    rejected = post(org_b, f"{requests_url}{again.json()['public_id']}/reject/", {"note": "no"})
    assert rejected.json()["status"] == "rejected"
    assert not ResultCorrection.objects.exists()
    again = post(
        org_a, requests_url, {"plan": plan_id, "normalization_run": run_2, "reason": "Late ballot"}
    )
    assert (
        post(org_a, f"{requests_url}{again.json()['public_id']}/cancel/").json()["status"]
        == "cancelled"
    )
    third = post(
        org_a, requests_url, {"plan": plan_id, "normalization_run": run_2, "reason": "Late ballot"}
    )
    post(org_b, f"{requests_url}{third.json()['public_id']}/approve/")
    correction = ResultCorrection.objects.get()
    assert correction.reason == "Late ballot" and correction.run.number == 2
    assert AuditEvent.objects.filter(action="results.corrected").count() == 1

    assert org_a.get(base(w) + "result-corrections/").json()[0]["reason"] == "Late ballot"
    assert client_for(w["member"]).get(base(w) + "result-corrections/").json() == []
    assert Client().get(f"/api/v1/events/{w['event'].public_id}/result-corrections/").json() == []


def test_corrections_become_visible_once_results_are_visible_to_participants(world):
    w = world
    plan_url, plan_id, run_1 = published_world(w)
    org = client_for(w["org_a"])
    assert post(org, plan_url + "publish-results/", {"normalization_run": run_1}).status_code == 200
    assert not ResultCorrection.objects.exists()
    submit_ballot(w, plan_url, w["judge2"], w["project"], 2)
    run_2 = new_run(w, plan_url)
    assert (
        post(
            org, plan_url + "publish-results/", {"normalization_run": run_2, "reason": "Recount"}
        ).status_code
        == 200
    )
    from evaluations.models import EvaluationPlan

    EvaluationPlan.objects.filter(public_id=plan_id).update(results_visible_to_participants=True)
    public = Client().get(f"/api/v1/events/{w['event'].public_id}/result-corrections/").json()
    assert [(c["previous_run"], c["run"], c["reason"]) for c in public] == [(1, 2, "Recount")]
    assert "score" not in str(public)
    assert client_for(w["member"]).get(base(w) + "result-corrections/").json() == public
    Event.objects.filter(pk=w["event"].pk).update(is_public=False)
    assert (
        Client().get(f"/api/v1/events/{w['event'].public_id}/result-corrections/").status_code
        == 404
    )


def test_correction_rows_are_immutable(world):
    w = world
    plan_url, _, run_1 = published_world(w)
    org = client_for(w["org_a"])
    post(org, plan_url + "publish-results/", {"normalization_run": run_1})
    submit_ballot(w, plan_url, w["judge2"], w["project"], 2)
    post(org, plan_url + "publish-results/", {"normalization_run": new_run(w, plan_url)})
    correction = ResultCorrection.objects.get()
    correction.reason = "edited"
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        correction.save()
    with pytest.raises(ValidationError):
        correction.delete()


# Receipts


def test_finalize_issues_an_immutable_signed_receipt_verifiable_by_anyone(world):
    w = world
    save_draft(w["project"], w["stage"], w["member"], payload={"notes": "hi"}, revision=0)
    _, version, _ = finalize_submission(w["project"], w["stage"], w["member"], revision=1)
    assert SubmissionReceipt.objects.get(version=version).token
    url = f"{base(w)}projects/{w['project'].public_id}/submissions/{w['stage'].public_id}/receipt/"
    member = client_for(w["member"])
    body = member.get(url).json()
    claims = verify_record(body["token"])
    assert claims["kind"] == "submission_receipt"
    assert claims["subject"]["digest"] == version.digest
    assert claims["subject"]["version"] == 1
    assert member.get(url).json()["token"] == body["token"]
    verified = (
        Client()
        .post("/api/v1/records/verify/", {"token": body["token"]}, content_type="application/json")
        .json()
    )
    assert verified["valid"] is True
    assert client_for(w["other"]).get(url).status_code == 404
    assert client_for(w["org_a"]).get(url).status_code == 200
    receipt = SubmissionReceipt.objects.get()
    receipt.token = "x"
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        receipt.save()


def test_receipt_is_issued_on_demand_for_a_pre_existing_version(world):
    w = world
    save_draft(w["project"], w["stage"], w["member"], payload={}, revision=0)
    _, version, _ = finalize_submission(w["project"], w["stage"], w["member"], revision=1)
    SubmissionReceipt.objects.filter(version=version)._raw_delete(SubmissionReceipt.objects.db)
    url = f"{base(w)}projects/{w['project'].public_id}/submissions/{w['stage'].public_id}/receipt/"
    assert client_for(w["member"]).get(url).status_code == 200
    assert SubmissionReceipt.objects.filter(version=version).count() == 1


# Assignment accept/decline


def assign(w, plan_id, pairs):
    from evaluations.models import EvaluationPlan

    plan = EvaluationPlan.objects.get(public_id=plan_id)
    version = AssignmentVersion.objects.create(plan=plan, number=1, coverage=1)
    for judge, project in pairs:
        Assignment.objects.create(version=version, judge=judge, project=project)
    plan.active_assignment_version = version
    plan.save()
    return plan


def test_judge_accepts_or_declines_and_a_decline_becomes_a_recusal(world):
    w = world
    plan_url, plan_id = make_plan(w)
    assign(w, plan_id, [(w["judge"], w["project"]), (w["judge"], w["other_project"])])
    judge = client_for(w["judge"])
    rows = judge.get(plan_url + "my-assignments/").json()
    assert {r["status"] for r in rows} == {"pending"}
    keep = f"{plan_url}my-assignments/{w['project'].public_id}/respond/"
    drop = f"{plan_url}my-assignments/{w['other_project'].public_id}/respond/"
    assert post(judge, keep, {"status": "maybe"}).status_code == 400
    assert post(judge, keep, {"status": "accepted"}).status_code == 200
    assert post(judge, drop, {"status": "declined"}).status_code == 400
    assert (
        post(judge, drop, {"status": "declined", "reason": "Conflict of schedule"}).status_code
        == 200
    )
    coi = ConflictOfInterest.objects.get(judge=w["judge"], project=w["other_project"])
    assert coi.reason.startswith("Declined assignment:")
    assert post(judge, drop, {"status": "accepted"}).status_code == 400
    blocked = post(
        judge,
        plan_url + "ballots/",
        {
            "project": str(w["other_project"].public_id),
            "responses": [{"criterion_id": "impact", "score": 3}],
        },
    )
    assert blocked.status_code == 400 and not Ballot.objects.exists()
    summary = client_for(w["org_a"]).get(plan_url + "assignment-responses/").json()
    assert summary["counts"] == {"pending": 0, "accepted": 1, "declined": 1}
    assert summary["declined"][0]["reason"] == "Conflict of schedule"
    assert client_for(w["judge2"]).get(plan_url + "my-assignments/").json() == []
    assert post(client_for(w["judge2"]), keep, {"status": "accepted"}).status_code == 400
    assert client_for(w["member"]).get(plan_url + "my-assignments/").status_code == 403
    assert client_for(w["judge"]).get(plan_url + "assignment-responses/").status_code == 403


def test_a_judge_cannot_decline_after_submitting_a_ballot(world):
    w = world
    plan_url, plan_id = make_plan(w)
    assign(w, plan_id, [(w["judge"], w["project"])])
    submit_ballot(w, plan_url, w["judge"], w["project"])
    url = f"{plan_url}my-assignments/{w['project'].public_id}/respond/"
    assert (
        post(client_for(w["judge"]), url, {"status": "declined", "reason": "x"}).status_code == 400
    )
    assert not ConflictOfInterest.objects.exists()


# Deadline-exception requests


def closed_gate_policy(w):
    gate = TemporalGate.objects.create(
        event=w["event"], name="submissions", closes_at=timezone.now() - timedelta(minutes=1)
    )
    policy = Policy.objects.create(
        event=w["event"],
        name="Window",
        ast={"op": "eq", "fact": "gate_open:submissions", "value": True},
    )
    PolicyBinding.objects.create(event=w["event"], action=Action.SUBMIT, policy=policy)
    return gate


def allowed(w):
    return check_action(
        w["event"],
        Action.SUBMIT,
        base_facts(w["event"]),
        subject_type="project",
        subject_id=str(w["project"].public_id),
    )[0]


def test_exception_request_feeds_a_bounded_exception_grant(world):
    w = world
    closed_gate_policy(w)
    assert allowed(w) is False
    member, org = client_for(w["member"]), client_for(w["org_a"])
    url = f"{base(w)}projects/{w['project'].public_id}/exception-requests/"
    assert post(member, url, {}).status_code == 400
    created = post(member, url, {"reason": "Wi-Fi outage"})
    assert created.status_code == 201
    assert post(member, url, {"reason": "again"}).status_code == 400
    assert client_for(w["other"]).get(url).status_code == 404
    assert post(client_for(w["other"]), url, {"reason": "steal"}).status_code == 404
    request_id = created.json()["public_id"]
    decide = f"{base(w)}exception-requests/{request_id}/"
    assert (
        post(member, decide + "approve/", {"expires_at": "2099-01-01T00:00:00Z"}).status_code == 403
    )
    assert post(org, decide + "approve/", {}).status_code == 400
    past = (timezone.now() - timedelta(hours=1)).isoformat()
    assert post(org, decide + "approve/", {"expires_at": past}).status_code == 400
    far = (timezone.now() + timedelta(days=30)).isoformat()
    assert post(org, decide + "approve/", {"expires_at": far}).status_code == 400
    assert not ExceptionGrant.objects.exists() and allowed(w) is False
    soon = (timezone.now() + timedelta(hours=2)).isoformat()
    approved = post(org, decide + "approve/", {"expires_at": soon, "note": "granted"})
    assert approved.json()["status"] == "approved"
    grant = ExceptionGrant.objects.get()
    assert (grant.action, grant.subject_type, grant.subject_id) == (
        "submit",
        "project",
        str(w["project"].public_id),
    )
    assert allowed(w) is True
    assert post(org, decide + "approve/", {"expires_at": soon}).status_code == 400
    assert AuditEvent.objects.filter(action="exception_grant.created").count() == 1
    assert (
        org.get(f"{base(w)}exception-requests/?status=approved").json()[0]["public_id"]
        == request_id
    )


def test_exception_denial_and_cancellation_create_no_grant(world):
    w = world
    member, org = client_for(w["member"]), client_for(w["org_a"])
    url = f"{base(w)}projects/{w['project'].public_id}/exception-requests/"
    first = post(member, url, {"reason": "r"}).json()["public_id"]
    assert (
        post(org, f"{base(w)}exception-requests/{first}/reject/", {"note": "no"}).json()["status"]
        == "rejected"
    )
    second = post(member, url, {"reason": "r2"}).json()["public_id"]
    assert (
        post(client_for(w["other"]), f"{base(w)}exception-requests/{second}/cancel/").status_code
        == 404
    )
    assert (
        post(member, f"{base(w)}exception-requests/{second}/cancel/").json()["status"]
        == "cancelled"
    )
    assert not ExceptionGrant.objects.exists()


def test_a_newer_active_grant_is_honoured_even_when_an_older_one_expired(world):
    w = world
    closed_gate_policy(w)
    for delta in (-1, 2):
        ExceptionGrant.objects.create(
            event=w["event"],
            action=Action.SUBMIT,
            subject_type="project",
            subject_id=str(w["project"].public_id),
            reason="r",
            expires_at=timezone.now() + timedelta(hours=delta),
        )
    assert allowed(w) is True


def test_governance_evidence_survives_a_final_archive_round_trip(world):
    from governance.models import RulesAcknowledgement, RulesVersion
    from integrations.archive import build_archive, import_archive

    w = world
    org = client_for(w["org_a"])
    post(org, base(w) + "rules/", {"title": "Rules", "body": "v1"})
    post(client_for(w["member"]), base(w) + "rules/acknowledge/")
    save_draft(w["project"], w["stage"], w["member"], payload={"notes": "x"}, revision=0)
    _, version, _ = finalize_submission(w["project"], w["stage"], w["member"], revision=1)
    plan_url, _, run_1 = published_world(w)
    post(org, plan_url + "publish-results/", {"normalization_run": run_1})
    submit_ballot(w, plan_url, w["judge2"], w["project"], 2)
    post(
        org,
        plan_url + "publish-results/",
        {"normalization_run": new_run(w, plan_url), "reason": "Recount"},
    )

    archive = build_archive(w["event"], mode="final")
    copied = import_archive(workspace=w["workspace"], archive=archive, name="Copy", slug="copy")

    assert RulesVersion.objects.get(event=copied).body == "v1"
    assert RulesAcknowledgement.objects.get(version__event=copied).user.username == "member"
    assert ResultCorrection.objects.get(plan__stage__event=copied).reason == "Recount"
    receipt = SubmissionReceipt.objects.get(version__submission__project__event=copied)
    assert verify_record(receipt.token)["subject"]["digest"] == version.digest
