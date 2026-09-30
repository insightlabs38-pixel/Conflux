"""PD-F001-B01-T06: an event can move from its format's workflow to a custom one, step by step."""

import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import EvaluationPlan, RubricVersion
from eventconfig.models import EventProfile
from events.models import Event
from stages.models import Stage, StageTransition
from workspaces.models import Membership, Role, Workspace

pytestmark = pytest.mark.django_db


def client_for(user):
    client = Client()
    client.cookies["session"] = Session.issue(user).token
    return client


def setup(key="hackathon"):
    organizer = User.objects.create_user(username="org", password="unused")
    judge = User.objects.create_user(username="jdg", password="unused")
    workspace = Workspace.objects.create(name="Flow", slug="flow")
    Membership.objects.create(user=organizer, workspace=workspace, role=Role.ORGANIZER)
    Membership.objects.create(user=judge, workspace=workspace, role=Role.JUDGE)
    client = client_for(organizer)
    response = client.post(
        f"/api/v1/workspaces/{workspace.public_id}/event-templates/library/{key}/instantiate/",
        data={"name": "Spring", "slug": "spring"},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return workspace, client, client_for(judge), Event.objects.get(workspace=workspace)


def workflow(client, workspace, event):
    response = client.get(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/workflow/"
    )
    assert response.status_code == 200, response.content
    return response.json()


def codes(body):
    return sorted(d["code"] for d in body["differences"])


def test_a_fresh_preset_event_follows_its_format():
    workspace, client, _, event = setup()
    body = workflow(client, workspace, event)
    assert body["source"] == "preset" and body["differences"] == []
    assert body["preset"] == {"key": "hackathon", "version": 1, "label": "Hackathon"}
    assert body["stages"] == ["Build", "Judging", "Final"]
    # The same answer is queryable as a derived setting.
    config = client.get(
        f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/configuration/"
        "?key=workflow."
    ).json()
    (entry,) = config["settings"]
    assert (entry["value"], entry["source"], entry["write"]) == ("preset", "derived", None)


def test_an_event_without_a_format_has_no_baseline():
    workspace, client, _, _ = setup()
    plain = Event.objects.create(workspace=workspace, name="By hand", slug="by-hand")
    Stage.objects.create(event=plain, name="Only", is_initial=True)
    body = workflow(client, workspace, plain)
    assert body["source"] == "none" and body["preset"] is None and body["differences"] == []
    assert body["stages"] == ["Only"]


def test_customizing_changes_the_answer_step_by_step_and_reverting_restores_it():
    workspace, client, _, event = setup()
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/"
    profile = EventProfile.objects.get(event=event)

    # 1. Add a stage through the real endpoint: the first difference.
    added = client.post(
        base + "stages/",
        data={"name": "Demo", "participation_mode": "team_locked"},
        content_type="application/json",
    )
    assert added.status_code == 201, added.content
    body = workflow(client, workspace, event)
    assert body["source"] == "custom"
    assert "stage_added" in codes(body)
    assert any(d["message"] == "Stage 'Demo' was added." for d in body["differences"])

    # 2. Nothing else was touched: the format it started from is still recorded.
    profile.refresh_from_db()
    assert (profile.preset_key, profile.preset_version) == ("hackathon", 1)

    # 3. Removing the stage again returns to the format (the transition list is the format's).
    demo = Stage.objects.get(event=event, name="Demo")
    assert client.delete(base + f"stages/{demo.public_id}/").status_code in (200, 204)
    assert workflow(client, workspace, event)["source"] == "preset"


def test_each_kind_of_change_is_named():
    workspace, client, _, event = setup()
    stages = {s.name: s for s in Stage.objects.filter(event=event)}

    # Removed stage (and the transitions that went through it)
    StageTransition.objects.filter(from_stage=stages["Judging"]).delete()
    StageTransition.objects.filter(to_stage=stages["Judging"]).delete()
    body = workflow(client, workspace, event)
    assert "transitions_changed" in codes(body) and body["source"] == "custom"

    # Judging removed from a judged stage
    plan = EvaluationPlan.objects.get(stage=stages["Final"])
    # Published rubric versions are immutable and protected; the plan goes with them here.
    RubricVersion.objects.filter(plan=plan)._raw_delete(RubricVersion.objects.db)
    plan.delete()
    assert "plan_removed" in codes(workflow(client, workspace, event))

    # Judging added to an unjudged stage
    EvaluationPlan.objects.create(stage=stages["Build"], name="Build judging", draft_criteria=[])
    assert "plan_added" in codes(workflow(client, workspace, event))

    # A different starting stage
    stages["Build"].is_initial = False
    stages["Build"].save(update_fields=["is_initial"])
    assert "initial_changed" in codes(workflow(client, workspace, event))


def test_a_changed_rubric_is_named_and_a_new_version_with_the_formats_criteria_is_not_a_change():
    workspace, client, _, event = setup()
    plan = EvaluationPlan.objects.get(stage__event=event, stage__name="Judging")
    original = list(plan.current_rubric_version.criteria)
    changed = [dict(c) for c in original]
    changed[0]["weight"] = 5
    RubricVersion.objects.create(plan=plan, number=2, criteria=changed)
    assert codes(workflow(client, workspace, event)) == ["rubric_changed"]
    # Publishing the format's own criteria again is not a difference.
    RubricVersion.objects.create(plan=plan, number=3, criteria=original)
    assert workflow(client, workspace, event)["source"] == "preset"


def test_workflow_is_organizer_only_and_tenant_scoped():
    workspace, client, judge, event = setup()
    url = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}/workflow/"
    assert judge.get(url).status_code == 403
    assert Client().get(url).status_code in (401, 403)
    other = Workspace.objects.create(name="Other", slug="other")
    stranger = User.objects.create_user(username="str", password="unused")
    Membership.objects.create(user=stranger, workspace=other, role=Role.ORGANIZER)
    outsider = client_for(stranger)
    assert outsider.get(url).status_code == 403
    cross = f"/api/v1/workspaces/{other.public_id}/events/{event.public_id}/workflow/"
    assert outsider.get(cross).status_code == 404
