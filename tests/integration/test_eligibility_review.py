import pytest
from accounts.models import User
from artifacts.models import Artifact
from audit.models import AuditEvent
from awards.models import Award
from awards.services import select_winner
from communications.models import MessageRecipient
from django.core.exceptions import ValidationError
from eligibility.models import EligibilityFinding, EligibilityReview
from evaluations.eligibility import eligible_projects
from evaluations.models import EvaluationPlan
from events.models import Event, Track
from participation.models import Team, TeamMembership
from projects.models import Project, ProjectMembership, Submission
from stages.models import Stage
from test_sponsor_portal import client_for
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db
JSON = "application/json"


def world():
    workspace = Workspace.objects.create(name="W", slug="w")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    stage = Stage.objects.create(event=event, name="Build", position=0)
    users = {}
    for name, role in (
        ("org", Role.ORGANIZER),
        ("alice", Role.PARTICIPANT),
        ("bob", Role.PARTICIPANT),
        ("judge", Role.JUDGE),
    ):
        users[name] = User.objects.create_user(username=name, password="x")
        Membership.objects.create(workspace=workspace, user=users[name], role=role)
    track = Track.objects.create(event=event, name="AI")
    team = Team.objects.create(event=event, name="Solo")
    TeamMembership.objects.create(team=team, user=users["alice"], role="captain")
    project = Project.objects.create(
        event=event, team=team, created_by=users["alice"], name="Mine", track=track
    )
    ProjectMembership.objects.create(project=project, user=users["alice"], role="owner")
    other = Project.objects.create(event=event, created_by=users["bob"], name="Other")
    ProjectMembership.objects.create(project=other, user=users["bob"], role="owner")
    for p in (project, other):
        Submission.objects.create(
            project=p, stage=stage, status="finalized", updated_by=p.created_by
        )
    return workspace, event, stage, users, project, other, track


def base(workspace, event):
    return f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"


def rules(client, workspace, event, **extra):
    body = {
        "min_team_size": 2,
        "max_team_size": None,
        "required_artifact_kinds": ["repository"],
        "require_finalized_submission": True,
        "require_track": True,
        "require_clearance": False,
        **extra,
    }
    return client.put(base(workspace, event) + "eligibility-rules/", body, content_type=JSON)


def path(workspace, event, project, suffix=""):
    return base(workspace, event) + f"projects/{project.public_id}/eligibility/{suffix}"


def test_rules_are_organizer_only_validated_and_audited():
    workspace, event, _, users, *_ = world()
    organizer = client_for(users["org"])
    assert rules(organizer, workspace, event).status_code == 200
    assert AuditEvent.objects.filter(action="eligibility.rules_saved").count() == 1
    for bad in (
        {"min_team_size": 3, "max_team_size": 2},
        {"required_artifact_kinds": ["nope"]},
        {"required_artifact_kinds": ["file", "file"]},
        {"unknown": 1},
    ):
        assert rules(organizer, workspace, event, **bad).status_code == 400
    for name in ("alice", "judge"):
        assert rules(client_for(users[name]), workspace, event).status_code == 403


def test_checks_open_findings_notify_and_remediation_auto_resolves():
    workspace, event, _, users, project, _, _ = world()
    organizer, alice = client_for(users["org"]), client_for(users["alice"])
    rules(organizer, workspace, event)
    review = organizer.post(path(workspace, event, project, "checks/")).json()
    assert review["status"] == "needs_remediation"
    assert {f["code"] for f in review["findings"]} == {"team_size_min", "artifact_repository"}
    assert MessageRecipient.objects.filter(user=users["alice"]).count() == 1
    assert not MessageRecipient.objects.filter(user=users["bob"]).exists()
    again = organizer.post(path(workspace, event, project, "checks/")).json()
    assert len(again["findings"]) == 2 and again["revision"] == review["revision"]
    ProjectMembership.objects.create(project=project, user=users["bob"], role="member")
    TeamMembership.objects.create(team=project.team, user=users["bob"], role="member")
    Artifact.objects.create(
        project=project,
        kind="repository",
        visibility="public",
        title="Repo",
        external_url="https://example.com/r",
        status="ready",
        created_by=users["alice"],
    )
    fixed = organizer.post(path(workspace, event, project, "checks/")).json()
    assert {f["state"] for f in fixed["findings"]} == {"resolved"}
    assert fixed["status"] == "needs_remediation"
    assert client_for(users["alice"]).get(path(workspace, event, project)).json()["status"]
    assert alice is not None


def test_participant_responds_only_on_own_open_findings_and_review_returns_to_pending():
    workspace, event, _, users, project, other, _ = world()
    organizer = client_for(users["org"])
    finding = organizer.post(
        path(workspace, event, project, "findings/"),
        {"message": "Upload proof of enrollment."},
        content_type=JSON,
    )
    assert finding.status_code == 201, finding.content
    fid = finding.json()["public_id"]
    respond = path(workspace, event, project, f"findings/{fid}/respond/")
    assert (
        client_for(users["bob"]).post(respond, {"response": "x"}, content_type=JSON).status_code
        == 404
    )
    assert client_for(users["bob"]).get(path(workspace, event, project)).status_code == 404
    assert client_for(users["judge"]).get(path(workspace, event, project)).status_code == 404
    assert organizer.post(respond, {"response": "x"}, content_type=JSON).status_code == 404
    alice = client_for(users["alice"])
    assert alice.post(respond, {"response": ""}, content_type=JSON).status_code == 400
    done = alice.post(respond, {"response": "Uploaded the PDF."}, content_type=JSON)
    assert done.status_code == 200 and done.json()["state"] == "addressed"
    assert alice.get(path(workspace, event, project)).json()["status"] == "pending"
    assert alice.post(respond, {"response": "again"}, content_type=JSON).status_code == 400
    assert EligibilityReview.objects.get(project=project).revision == 2
    assert not EligibilityReview.objects.filter(project=other).exists()


def test_clearing_needs_closed_blocking_findings_and_waivers_need_reasons():
    workspace, event, _, users, project, _, _ = world()
    organizer = client_for(users["org"])
    rules(organizer, workspace, event, min_team_size=None, required_artifact_kinds=[])
    fid = organizer.post(
        path(workspace, event, project, "findings/"), {"message": "Check ID"}, content_type=JSON
    ).json()["public_id"]
    decide = lambda **b: organizer.post(  # noqa: E731
        path(workspace, event, project, "decision/"), b, content_type=JSON
    )
    assert decide(decision="cleared").status_code == 400
    close = path(workspace, event, project, f"findings/{fid}/close/")
    assert organizer.post(close, {"state": "waived"}, content_type=JSON).status_code == 400
    assert organizer.post(close, {"state": "open"}, content_type=JSON).status_code == 400
    assert (
        organizer.post(
            close, {"state": "waived", "note": "ID seen in person"}, content_type=JSON
        ).status_code
        == 200
    )
    assert organizer.post(close, {"state": "resolved"}, content_type=JSON).status_code == 400
    cleared = decide(decision="cleared", note="ok")
    assert cleared.status_code == 200 and cleared.json()["status"] == "cleared"
    assert decide(decision="ineligible").status_code == 400
    actions = [
        e.action
        for e in AuditEvent.objects.filter(action__startswith="eligibility.").order_by("id")
    ]
    assert "eligibility.decided" in actions and "eligibility.finding_closed" in actions


def test_waived_automated_finding_is_not_reopened_and_cleared_project_regresses():
    workspace, event, _, users, project, _, _ = world()
    organizer = client_for(users["org"])
    rules(organizer, workspace, event, required_artifact_kinds=[], require_track=False,
          require_finalized_submission=False, min_team_size=2)  # fmt: skip
    review = organizer.post(path(workspace, event, project, "checks/")).json()
    fid = review["findings"][0]["public_id"]
    organizer.post(
        path(workspace, event, project, f"findings/{fid}/close/"),
        {"state": "waived", "note": "Solo allowed"},
        content_type=JSON,
    )
    cleared = organizer.post(
        path(workspace, event, project, "decision/"), {"decision": "cleared"}, content_type=JSON
    )
    assert cleared.status_code == 200
    assert len(organizer.post(path(workspace, event, project, "checks/")).json()["findings"]) == 1
    organizer.post(
        path(workspace, event, project, "findings/"), {"message": "New concern"}, content_type=JSON
    )
    assert EligibilityReview.objects.get(project=project).status == "needs_remediation"


def test_ineligible_projects_leave_judging_and_awards_and_can_be_reinstated():
    workspace, event, stage, users, project, other, _ = world()
    plan = EvaluationPlan.objects.create(stage=stage, name="Main")
    organizer = client_for(users["org"])
    assert set(eligible_projects(plan)) == {project, other}
    award = Award.objects.create(event=event, name="A", require_finalized_submission=False)
    decide = lambda p, **b: organizer.post(  # noqa: E731
        path(workspace, event, p, "decision/"), b, content_type=JSON
    )
    assert decide(project, decision="ineligible", note="Not a student").status_code == 200
    assert set(eligible_projects(plan)) == {other}
    with pytest.raises(ValidationError, match="eligibility review"):
        select_winner(award=award, project=project, actor=users["org"])
    assert (
        client_for(users["alice"]).get(path(workspace, event, project)).json()["decision_note"]
        == "Not a student"
    )
    assert decide(project, decision="pending").status_code == 200
    assert set(eligible_projects(plan)) == {project, other}
    select_winner(award=award, project=project, actor=users["org"])


def test_require_clearance_limits_judging_to_cleared_projects():
    workspace, event, stage, users, project, other, _ = world()
    plan = EvaluationPlan.objects.create(stage=stage, name="Main")
    organizer = client_for(users["org"])
    rules(
        organizer,
        workspace,
        event,
        require_clearance=True,
        min_team_size=None,
        required_artifact_kinds=[],
        require_track=False,
        require_finalized_submission=False,
    )
    assert set(eligible_projects(plan)) == set()
    organizer.post(
        path(workspace, event, project, "decision/"), {"decision": "cleared"}, content_type=JSON
    )
    assert set(eligible_projects(plan)) == {project}


def test_archived_events_freeze_reviews_and_listing_is_scoped():
    workspace, event, _, users, project, other, _ = world()
    organizer = client_for(users["org"])
    organizer.post(
        path(workspace, event, project, "findings/"), {"message": "m"}, content_type=JSON
    )
    listed = organizer.get(
        base(workspace, event) + "eligibility-reviews/?status=needs_remediation"
    ).json()
    assert [row["project"] for row in listed] == [str(project.public_id)] and listed[0][
        "open_findings"
    ] == 1
    assert (
        organizer.get(base(workspace, event) + "eligibility-reviews/?status=bogus").status_code
        == 400
    )
    assert (
        client_for(users["alice"]).get(base(workspace, event) + "eligibility-reviews/").status_code
        == 403
    )
    Event.objects.filter(pk=event.pk).update(status="archived")
    assert (
        organizer.post(
            path(workspace, event, project, "findings/"), {"message": "m"}, content_type=JSON
        ).status_code
        == 400
    )
    fid = EligibilityFinding.objects.get().public_id
    assert (
        client_for(users["alice"])
        .post(
            path(workspace, event, project, f"findings/{fid}/respond/"),
            {"response": "r"},
            content_type=JSON,
        )
        .status_code
        == 400
    )
