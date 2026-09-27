import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.assignment import compute_assignment
from evaluations.coi import conflict_pairs, is_conflicted
from evaluations.models import (
    COIRule,
    ConflictOfInterest,
    EvaluationPlan,
    EvaluationPool,
    EvaluationPoolStrategy,
    JudgeCOIRelationship,
    PoolMembership,
)
from evaluations.optimization import compute_assignment_optimized
from events.models import Event
from participation.models import Team, TeamMembership
from projects.models import Project, ProjectMembership, ProjectMembershipRole, Submission
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db

CRITERIA = [{"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}]


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def post_json(client, url, data):
    return client.post(url, data=data, content_type="application/json")


def fixture():
    owner = User.objects.create_user(username="owner", password="unused")
    judges = [User.objects.create_user(username=f"judge{i}", password="unused") for i in range(3)]
    workspace = Workspace.objects.create(name="COI", slug="coi")
    Membership.objects.create(workspace=workspace, user=owner, role=Role.ORGANIZER)
    for judge in judges:
        Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    pool = EvaluationPool.objects.create(event=event, name="Pool")
    for judge in judges:
        PoolMembership.objects.create(pool=pool, judge=judge)
    projects = []
    for i in range(2):
        project = Project.objects.create(event=event, name=f"Project {i}", created_by=owner)
        Submission.objects.create(project=project, stage=stage, updated_by=owner)
        projects.append(project)
    plan = EvaluationPlan.objects.create(
        stage=stage,
        name="Final",
        pool=pool,
        pool_strategy=EvaluationPoolStrategy.ASSIGNED_SUBSET,
        draft_criteria=CRITERIA,
    )
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    plan_url = f"{base}stages/{stage.public_id}/evaluation-plans/{plan.public_id}/"
    return event, plan, owner, judges, projects, base, plan_url


def test_self_declared_institution_and_domain_block_both_assignment_solvers_and_ballots():
    event, plan, owner, judges, projects, base, plan_url = fixture()
    organizer = client_for(owner)
    judge = client_for(judges[0])
    project = projects[0]
    for kind, value in (("institution", "Acme University"), ("domain", "Acme.Example")):
        response = post_json(
            organizer,
            base + "coi-project-attributes/",
            {"project": str(project.public_id), "kind": kind, "value": value},
        )
        assert response.status_code == 201, response.content
        response = post_json(
            judge,
            base + "coi-relationships/",
            {"kind": kind, "value": value.upper()},
        )
        assert response.status_code == 201, response.content
        assert response.json()["value"] == value.casefold()
    assert is_conflicted(event.id, judges[0].id, project.id)
    assert not is_conflicted(event.id, judges[1].id, project.id)
    progress = organizer.get(plan_url + "progress/")
    assert progress.status_code == 200
    assert progress.json()["conflict_count"] == 1
    assert (judges[0].id, project.id) not in {
        (pair.judge_id, pair.project_id) for pair in compute_assignment(plan, coverage=2)
    }
    assert (judges[0].id, project.id) not in {
        (pair.judge_id, pair.project_id) for pair in compute_assignment_optimized(plan, coverage=2)
    }
    assert organizer.post(plan_url + "publish-rubric/").status_code == 201
    ballot = post_json(
        judge,
        plan_url + "ballots/",
        {"project": str(project.public_id), "responses": [{"criterion_id": "impact", "score": 8}]},
    )
    assert ballot.status_code == 400


def test_team_membership_rule_and_explicit_team_relationship():
    event, plan, owner, judges, projects, base, _ = fixture()
    team = Team.objects.create(event=event, name="Team")
    projects[0].team = team
    projects[0].save(update_fields=["team"])
    TeamMembership.objects.create(team=team, user=judges[0])
    assert is_conflicted(event.id, judges[0].id, projects[0].id)
    owner_client = client_for(owner)
    response = owner_client.put(
        base + "coi-rules/",
        data={"kind": "team_membership", "enabled": False},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert not is_conflicted(event.id, judges[0].id, projects[0].id)
    assert COIRule.objects.get(event=event, kind="team_membership").enabled is False

    response = post_json(
        client_for(judges[0]),
        base + "coi-relationships/",
        {"kind": "team", "team": str(team.public_id)},
    )
    assert response.status_code == 201, response.content
    assert is_conflicted(event.id, judges[0].id, projects[0].id)
    assert JudgeCOIRelationship.objects.count() == 1
    assert not is_conflicted(event.id, judges[0].id, projects[1].id)


def test_creator_and_project_membership_rules_do_not_disable_direct_recusals():
    event, _, owner, judges, projects, base, _ = fixture()
    assert is_conflicted(event.id, owner.id, projects[0].id)
    ProjectMembership.objects.create(
        project=projects[0], user=judges[0], role=ProjectMembershipRole.CONTRIBUTOR
    )
    assert is_conflicted(event.id, judges[0].id, projects[0].id)
    client = client_for(owner)
    for kind in ("project_creator", "project_membership"):
        response = client.put(
            base + "coi-rules/",
            data={"kind": kind, "enabled": False},
            content_type="application/json",
        )
        assert response.status_code == 200
    assert not is_conflicted(event.id, owner.id, projects[0].id)
    assert not is_conflicted(event.id, judges[0].id, projects[0].id)
    ConflictOfInterest.objects.create(
        event=event, judge=judges[0], project=projects[0], declared_by=owner
    )
    assert is_conflicted(event.id, judges[0].id, projects[0].id)
    assert (judges[0].id, projects[0].id) in conflict_pairs(event.id)


def test_relationship_api_scopes_self_declarations_and_rejects_invalid_targets():
    event, _, owner, judges, projects, base, _ = fixture()
    judge = client_for(judges[0])
    other_judge = client_for(judges[1])
    organizer = client_for(owner)
    path = base + "coi-relationships/"
    assert (
        post_json(
            judge,
            path,
            {"judge": str(judges[1].public_id), "kind": "domain", "value": "example.org"},
        ).status_code
        == 403
    )
    assert post_json(judge, path, {"kind": "team", "value": "example.org"}).status_code == 400
    assert post_json(judge, path, {"kind": "domain", "value": ""}).status_code == 400
    assert post_json(judge, path, {"kind": "domain", "value": "not a domain"}).status_code == 400
    assert post_json(judge, path, {"kind": "domain", "value": "example.org"}).status_code == 201
    assert post_json(judge, path, {"kind": "domain", "value": "EXAMPLE.ORG"}).status_code == 400
    assert len(judge.get(path).json()) == 1
    assert other_judge.get(path).json() == []
    assert len(organizer.get(path).json()) == 1
    assert judge.get(base + "coi-project-attributes/").status_code == 403
    assert judge.get(base + "coi-rules/").status_code == 403

    other_event = Event.objects.create(workspace=event.workspace, name="Other", slug="other")
    other_team = Team.objects.create(event=other_event, name="Foreign")
    assert (
        post_json(judge, path, {"kind": "team", "team": str(other_team.public_id)}).status_code
        == 404
    )
    assert (
        post_json(
            organizer,
            base + "coi-project-attributes/",
            {"project": str(projects[0].public_id), "kind": "team", "value": "x"},
        ).status_code
        == 400
    )


def test_only_organizer_can_remove_recorded_relationships_and_attributes():
    event, _, owner, judges, projects, base, _ = fixture()
    organizer = client_for(owner)
    judge = client_for(judges[0])
    relationship = post_json(
        judge,
        base + "coi-relationships/",
        {"kind": "institution", "value": "Lab"},
    ).json()
    attribute = post_json(
        organizer,
        base + "coi-project-attributes/",
        {"project": str(projects[0].public_id), "kind": "institution", "value": "Lab"},
    ).json()
    assert is_conflicted(event.id, judges[0].id, projects[0].id)
    relationship_url = base + f"coi-relationships/{relationship['public_id']}/"
    attribute_url = base + f"coi-project-attributes/{attribute['public_id']}/"
    assert judge.delete(relationship_url).status_code == 403
    assert judge.delete(attribute_url).status_code == 403
    assert organizer.delete(attribute_url).status_code == 204
    assert not is_conflicted(event.id, judges[0].id, projects[0].id)
    assert organizer.delete(relationship_url).status_code == 204


def test_relationship_conflict_blocks_pairwise_comparison_too():
    _, plan, owner, judges, projects, base, plan_url = fixture()
    plan.mode = "pairwise"
    plan.pool_strategy = EvaluationPoolStrategy.ALL_JUDGES
    plan.save(update_fields=["mode", "pool_strategy"])
    assert (
        post_json(
            client_for(owner),
            base + "coi-project-attributes/",
            {"project": str(projects[0].public_id), "kind": "domain", "value": "lab.example"},
        ).status_code
        == 201
    )
    assert (
        post_json(
            client_for(judges[0]),
            base + "coi-relationships/",
            {"kind": "domain", "value": "lab.example"},
        ).status_code
        == 201
    )
    comparison = {
        "project_a": str(projects[0].public_id),
        "project_b": str(projects[1].public_id),
        "winner": str(projects[0].public_id),
    }
    path = plan_url + "pairwise/comparisons/"
    assert post_json(client_for(judges[0]), path, comparison).status_code == 400
    assert post_json(client_for(judges[1]), path, comparison).status_code == 201
