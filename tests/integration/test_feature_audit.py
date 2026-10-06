"""PD-F003-B01-T04: the audit claims of the completeness contract, held against real requests.

Every feature claims, per writing route and method, the audit action it records
(`write:<route>:<METHOD>=<action>`). This file sends each of those changes through the API as the
role that may make it and reads the audit row it left: the declared action, the workspace, the
actor and the target, and no secret. A change that is refused leaves no audit row, and an audit row
is written in the same transaction as the change it documents."""

import json
from datetime import timedelta

import pytest
from accounts.models import Session, User
from artifacts.models import Artifact, ArtifactStatus
from audit.models import AuditEvent
from core import features as ft
from core import features_audit
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from events.models import Announcement, Event, EventApplication, Track
from participation.models import Team, TeamInvite, TeamMembership, TeamMembershipRole
from projects.models import Project
from projects.services import create_project
from projects.submissions import finalize_submission, save_draft
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


class FakeStorage:
    def ensure_bucket(self):
        pass

    def presign_put(self, key, content_type, artifact_id, expires):
        self.key = key
        self.info = {
            "ContentLength": 4,
            "ContentType": content_type,
            "Metadata": {"artifact-id": artifact_id},
        }
        return "https://upload.example.com/signed"

    def head(self, key):
        return self.info


def declared():
    """(feature, route, METHOD, action) for every claimed change."""
    found = []
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        writes, _ = features_audit.parse(feature.claims["audit"])
        found += [(feature.key, route, method, action) for route, method, action, _ in writes]
    return found


DECLARED = declared()


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def user(name):
    return User.objects.create_user(username=name, password="unused")


@pytest.fixture
def world(monkeypatch):
    storage = FakeStorage()
    monkeypatch.setattr("artifacts.services.S3Storage", lambda: storage)
    monkeypatch.setattr("artifacts.validators.S3Storage", lambda: storage)
    workspace = Workspace.objects.create(name="W", slug="w")
    now = timezone.now()
    event = Event.objects.create(
        workspace=workspace,
        name="E",
        slug="e",
        status="open",
        starts_at=now - timedelta(days=2),
        ends_at=now + timedelta(days=1),
    )
    people = {}
    for name, role in (
        ("organizer", Role.ORGANIZER),
        ("alice", Role.PARTICIPANT),
        ("bob", Role.PARTICIPANT),
        ("carol", Role.PARTICIPANT),
    ):
        people[name] = user(name)
        Membership.objects.create(workspace=workspace, user=people[name], role=role)
    return {
        "workspace": workspace,
        "event": event,
        "people": people,
        "storage": storage,
        "project": create_project(event, people["alice"], "Mine"),
        "stage": Stage.objects.create(event=event, name="Build"),
    }


def where(world, **extra):
    return {
        "workspace_public_id": world["workspace"].public_id,
        "event_public_id": world["event"].public_id,
        **extra,
    }


def finalized(world, notes="First"):
    project, stage, alice = world["project"], world["stage"], world["people"]["alice"]
    artifact = Artifact.objects.create(
        project=project,
        created_by=alice,
        kind="repository",
        visibility="public",
        title="Repo",
        external_url="https://example.com/repo",
        status=ArtifactStatus.READY,
    )
    save_draft(
        project, stage, alice, payload={"notes": notes, "artifact_ids": [str(artifact.public_id)]},
        revision=0,
    )  # fmt: skip
    finalize_submission(project, stage, alice, revision=1)


def uploaded(world):
    """An uploaded artifact the member can validate (the same path the upload API takes)."""
    client = client_for(world["people"]["alice"])
    base = reverse(
        "artifact-upload-intent", kwargs=where(world, project_public_id=world["project"].public_id)
    )
    issued = client.post(
        base,
        {"kind": "file", "visibility": "participant", "title": "Deck", "byte_size": 4,
         "content_type": "application/pdf"},
        content_type="application/json",
    ).json()  # fmt: skip
    complete = reverse(
        "artifact-upload-complete",
        kwargs=where(
            world,
            project_public_id=world["project"].public_id,
            artifact_public_id=issued["artifact"]["public_id"],
            intent_public_id=issued["intent"],
        ),
    )
    client.post(complete, {}, content_type="application/json")
    return issued["artifact"]["public_id"]


def team_of(world, *names):
    team = Team.objects.create(event=world["event"], name="Team A")
    for i, name in enumerate(names):
        role = TeamMembershipRole.CAPTAIN if i == 0 else TeamMembershipRole.MEMBER
        TeamMembership.objects.create(team=team, user=world["people"][name], role=role)
    return team


# Each scenario returns (who acts, url keyword arguments, body). What a change needs first (a draft
# event to delete, a finalized submission to reopen) is made with the ORM so that the request under
# test is the only thing that writes.
def scenarios(world):
    w, event, project = world, world["event"], world["project"]
    project_kw = where(w, project_public_id=project.public_id)
    stage_kw = where(w, stage_public_id=w["stage"].public_id)

    def track():
        return Track.objects.create(event=event, name="AI")

    def announcement():
        return Announcement.objects.create(
            event=event, title="Hi", body="There", posted_by=w["people"]["organizer"]
        )

    def plan():
        from evaluations.models import EvaluationPlan

        return EvaluationPlan.objects.create(stage=w["stage"], name="Plan")

    def applicant():
        return EventApplication.objects.create(event=event, user=user("applicant"))

    def draft_event():
        return Event.objects.create(workspace=w["workspace"], name="Old", slug="old")

    def award():
        from awards.models import Award

        return Award.objects.create(
            event=event, name="Best", selection_source="manual", winner_count=1,
            require_finalized_submission=False,
        )  # fmt: skip

    def winner(a):
        from awards.models import AwardWinner

        return AwardWinner.objects.create(
            award=a, project=project, selected_by=w["people"]["organizer"], source="manual"
        )

    return {
        ("event-list", "POST"): lambda: (
            "organizer", {"workspace_public_id": w["workspace"].public_id},
            {"name": "E2", "slug": "e2"},
        ),
        ("event-detail", "PATCH"): lambda: ("organizer", where(w), {"name": "Renamed"}),
        ("event-detail", "DELETE"): lambda: (
            "organizer", where(w, event_public_id=draft_event().public_id), None,
        ),
        ("event-status", "POST"): lambda: ("organizer", where(w), {"status": "closed"}),
        ("track-list", "POST"): lambda: ("organizer", where(w), {"name": "AI"}),
        ("track-detail", "PATCH"): lambda: (
            "organizer", where(w, track_public_id=track().public_id), {"name": "AI 2"},
        ),
        ("track-detail", "DELETE"): lambda: (
            "organizer", where(w, track_public_id=track().public_id), None,
        ),
        ("event-application-decide", "POST"): lambda: (
            "organizer", where(w, application_public_id=applicant().public_id),
            {"decision": "approved"},
        ),
        ("announcement-list", "POST"): lambda: (
            "organizer", where(w), {"title": "Hello", "body": "World"},
        ),
        ("announcement-detail", "DELETE"): lambda: (
            "organizer", where(w, announcement_public_id=announcement().public_id), None,
        ),
        ("announcement-review", "POST"): lambda: (
            "organizer", where(w, source_public_id=announcement().public_id),
            {"version": 1, "status": "hidden", "note": "Wrong details"},
        ),
        ("webhook-list", "POST"): lambda: (
            "organizer", {"workspace_public_id": w["workspace"].public_id},
            {"url": "https://example.com/hook", "event_types": ["project.created"]},
        ),
        ("webhook-detail", "PATCH"): lambda: _webhook(w),
        ("award-list", "POST"): lambda: (
            "organizer", where(w),
            {"name": "Best", "selection_source": "manual", "winner_count": 1,
             "require_finalized_submission": False},
        ),
        ("award-publish", "POST"): lambda: _publish(w, award, winner),
        ("stage-list", "POST"): lambda: ("organizer", where(w), {"name": "Pitch"}),
        ("stage-detail", "PATCH"): lambda: ("organizer", stage_kw, {"name": "Build 2"}),
        ("stage-detail", "DELETE"): lambda: (
            "organizer",
            where(w, stage_public_id=Stage.objects.create(event=event, name="Spare").public_id),
            None,
        ),
        ("policy-list", "POST"): lambda: (
            "organizer", where(w), {"name": "Open", "ast": {"op": "true"}},
        ),
        ("policy-detail", "PATCH"): lambda: _policy(w, {"name": "Open 2"}),
        ("policy-detail", "DELETE"): lambda: _policy(w, None),
        ("form-list", "POST"): lambda: ("organizer", where(w), {"name": "Intake"}),
        ("form-detail", "PUT"): lambda: _form(w),
        ("evaluation-plan-list", "POST"): lambda: ("organizer", stage_kw, {"name": "Rubric"}),
        ("evaluation-plan-detail", "PATCH"): lambda: (
            "organizer", {**stage_kw, "plan_public_id": plan().public_id}, {"name": "Rubric 2"},
        ),
        ("evaluation-plan-detail", "DELETE"): lambda: (
            "organizer", {**stage_kw, "plan_public_id": plan().public_id}, None,
        ),
        ("message-list-create", "POST"): lambda: (
            "organizer", where(w),
            {"subject": "Welcome", "body": "Good luck", "audience_kind": "all_participants"},
        ),
        ("project-list", "POST"): lambda: ("bob", where(w), {"name": "Another"}),
        ("project-detail", "PATCH"): lambda: ("alice", project_kw, {"description": "Better"}),
        ("submission-detail", "PUT"): lambda: (
            "alice", {**project_kw, "stage_public_id": w["stage"].public_id},
            {"draft_payload": {"notes": "Draft"}, "draft_revision": 0},
        ),
        ("submission-finalize", "POST"): lambda: _finalize(w),
        ("submission-reopen", "POST"): lambda: _reopen(w),
        ("artifact-list", "POST"): lambda: (
            "alice", project_kw,
            {"kind": "repository", "visibility": "public", "title": "Repo",
             "external_url": "https://example.com/repo"},
        ),
        ("artifact-upload-intent", "POST"): lambda: (
            "alice", project_kw,
            {"kind": "file", "visibility": "participant", "title": "Deck", "byte_size": 4,
             "content_type": "application/pdf"},
        ),
        ("artifact-validate", "POST"): lambda: (
            "alice", {**project_kw, "artifact_public_id": uploaded(w)}, None,
        ),
        ("my-team", "POST"): lambda: ("bob", where(w), {"name": "Team B"}),
        ("my-team-leave", "POST"): lambda: _leave(w),
        ("my-team-transfer-captain", "POST"): lambda: _transfer(w),
        ("my-team-invite-list", "POST"): lambda: _invite(w),
        ("team-invite-redeem", "POST"): lambda: _redeem(w),
    }  # fmt: skip


def _webhook(w):
    from integrations.models import WebhookSubscription

    sub = WebhookSubscription.objects.create(
        workspace=w["workspace"], url="https://example.com/hook", event_types=["project.created"]
    )
    return (
        "organizer",
        {"workspace_public_id": w["workspace"].public_id, "subscription_public_id": sub.public_id},
        {"enabled": False},
    )


def _publish(w, award, winner):
    a = award()
    winner(a)
    return "organizer", where(w, award_public_id=a.public_id), {}


def _policy(w, body):
    from policies.models import Policy

    policy = Policy.objects.create(event=w["event"], name="Open", ast={"op": "true"})
    return "organizer", where(w, policy_public_id=policy.public_id), body


def _form(w):
    from forms.models import FormDefinition

    form = FormDefinition.objects.create(
        event=w["event"], name="Intake", draft_schema={"fields": []}
    )
    return "organizer", where(w, form_public_id=form.public_id), {"schema": {"fields": []}}


def _finalize(w):
    from artifacts.models import Artifact as A

    A.objects.create(
        project=w["project"], created_by=w["people"]["alice"], kind="repository",
        visibility="public", title="Repo", external_url="https://example.com/repo",
        status=ArtifactStatus.READY,
    )  # fmt: skip
    artifact = A.objects.get()
    save_draft(
        w["project"], w["stage"], w["people"]["alice"],
        payload={"notes": "Done", "artifact_ids": [str(artifact.public_id)]}, revision=0,
    )  # fmt: skip
    return (
        "alice",
        where(w, project_public_id=w["project"].public_id, stage_public_id=w["stage"].public_id),
        {"draft_revision": 1},
    )


def _reopen(w):
    finalized(w)
    return (
        "organizer",
        where(w, project_public_id=w["project"].public_id, stage_public_id=w["stage"].public_id),
        {"reason": "wrong demo link"},
    )


def _leave(w):
    team_of(w, "alice", "bob")
    return "bob", where(w), None


def _transfer(w):
    team_of(w, "alice", "bob")
    return "alice", where(w), {"user": str(w["people"]["bob"].public_id)}


def _invite(w):
    team_of(w, "alice")
    return "alice", where(w), {"max_uses": 2}


def _redeem(w):
    team = team_of(w, "alice")
    invite = TeamInvite.objects.create(team=team, created_by=w["people"]["alice"], max_uses=1)
    return "carol", where(w), {"token": invite.token}


def send(world, route, method, who, kwargs, body):
    from core.features import System

    wanted = {part for _, part in System().converters(route)}
    url = reverse(route, kwargs={k: v for k, v in kwargs.items() if k in wanted})
    data = json.dumps(body) if body is not None else None
    return client_for(world["people"][who]).generic(
        method, url, data or "", content_type="application/json"
    )


def secrets_in(value):
    """Every value stored under a key that names a secret or a token."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str) and any(w in key for w in ("secret", "token")):
                found.append(item)
            found += secrets_in(item)
    elif isinstance(value, list):
        for item in value:
            found += secrets_in(item)
    return found


# --- the claims against real requests ---------------------------------------------------------


def test_every_declared_change_has_a_scenario_and_no_scenario_is_extra(world):
    assert {(route, method) for _, route, method, _ in DECLARED} == set(scenarios(world))
    assert len(DECLARED) == len({(r, m) for _, r, m, _ in DECLARED}) >= 40


@pytest.mark.parametrize(
    ("key", "route", "method", "action"),
    DECLARED,
    ids=[f"{k}:{r}:{m}" for k, r, m, _ in DECLARED],
)
def test_each_declared_change_records_its_audit_action(world, key, route, method, action):
    who, kwargs, body = scenarios(world)[(route, method)]()
    before = AuditEvent.objects.count()
    response = send(world, route, method, who, kwargs, body)
    assert response.status_code in (200, 201, 204), (route, method, response.content[:300])
    rows = list(AuditEvent.objects.order_by("id")[before:])
    mine = [row for row in rows if row.action == action]
    assert mine, f"{method} {route} recorded {[r.action for r in rows]}, not {action}"
    row = mine[0]
    assert row.workspace_id == world["workspace"].id
    assert row.actor == world["people"][who]
    assert row.target_type and row.target_id
    text = json.dumps(row.metadata)
    payload = response.json() if response.content else {}
    for secret in secrets_in(payload) + secrets_in(body or {}):
        assert secret not in text, f"{action} carries a secret"
    assert "whsec_" not in text and "upload.example.com" not in text


@pytest.mark.parametrize(
    ("key", "route", "method", "action"),
    DECLARED,
    ids=[f"{k}:{r}:{m}" for k, r, m, _ in DECLARED],
)
def test_a_refused_change_leaves_no_audit_row(world, key, route, method, action):
    who, kwargs, body = scenarios(world)[(route, method)]()
    intruder = user("intruder")  # a stranger to the workspace
    world["people"]["intruder"] = intruder
    before = AuditEvent.objects.count()
    response = send(world, route, method, "intruder", kwargs, body)
    assert response.status_code in (401, 403, 404)
    assert AuditEvent.objects.count() == before


def test_an_invalid_change_is_refused_and_leaves_no_audit_row(world):
    cases = [
        ("track-list", "POST", {"name": ""}),
        ("stage-list", "POST", {"name": ""}),
        ("form-list", "POST", {"name": ""}),
        ("announcement-list", "POST", {"title": "", "body": ""}),
    ]
    before = AuditEvent.objects.count()
    for route, method, body in cases:
        response = send(world, route, method, "organizer", where(world), body)
        assert response.status_code == 400, route
    assert AuditEvent.objects.count() == before


def test_deciding_an_application_twice_audits_once_and_the_second_is_refused(world):
    application = EventApplication.objects.create(event=world["event"], user=user("applicant"))
    kwargs = where(world, application_public_id=application.public_id)
    first = send(
        world, "event-application-decide", "POST", "organizer", kwargs, {"decision": "approved"}
    )
    again = send(
        world, "event-application-decide", "POST", "organizer", kwargs, {"decision": "rejected"}
    )
    assert (first.status_code, again.status_code) == (200, 400)
    rows = AuditEvent.objects.filter(action="application.decided")
    assert rows.count() == 1
    assert rows[0].metadata["decision"] == "approved"
    assert rows[0].metadata["applicant_id"] == str(application.user.public_id)


def test_the_audit_row_and_the_change_commit_or_roll_back_together(world, monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("the audit write failed")

    monkeypatch.setattr("projects.services.record_mutation", boom)
    with pytest.raises(RuntimeError):
        create_project(world["event"], world["people"]["bob"], "Doomed")
    assert not Project.objects.filter(name="Doomed").exists()
    monkeypatch.setattr("participation.services.record_mutation", boom)
    with pytest.raises(RuntimeError):
        from participation.services import create_team

        create_team(world["event"], "Doomed", world["people"]["bob"])
    assert not Team.objects.filter(name="Doomed").exists()


def test_the_invite_token_is_never_written_to_the_audit_log(world):
    who, kwargs, body = _invite(world)
    response = send(world, "my-team-invite-list", "POST", who, kwargs, body)
    assert response.status_code == 201
    token = response.json()["token"]
    redeemed = send(world, "team-invite-redeem", "POST", "carol", where(world), {"token": token})
    assert redeemed.status_code == 201
    logged = json.dumps(list(AuditEvent.objects.values_list("metadata", flat=True)))
    assert token not in logged
    actions = set(AuditEvent.objects.values_list("action", flat=True))
    assert {"team.invite_created", "team.invite_redeemed", "team.member_joined"} <= actions
