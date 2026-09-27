import itertools

import pytest
from accounts.models import User
from evaluations.models import EvaluationPlan, NormalizationRun
from evaluations.results import ranked_results
from events.models import Event
from projects.models import Project
from stages.models import Stage
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db

_counter = itertools.count()


def make_plan_and_run(evidence, *, tie_breaks=None):
    organizer = User.objects.create_user(username=f"organizer{next(_counter)}", password="unused")
    workspace = Workspace.objects.create(name="W", slug=f"w{next(_counter)}")
    event = Event.objects.create(workspace=workspace, name="Hack", slug="hack")
    stage = Stage.objects.create(event=event, name="Finals")
    projects = {
        name: Project.objects.create(event=event, name=name, created_by=organizer)
        for name in evidence
    }
    plan = EvaluationPlan.objects.create(stage=stage, name="Panel", tie_breaks=tie_breaks or {})
    run = NormalizationRun.objects.create(
        plan=plan,
        number=1,
        ridge_lambda=1.0,
        iterations=1,
        converged=True,
        grand_mean=5.0,
        evidence={
            "projects": {
                str(projects[name].id): {"raw": scores["raw"], "final": scores["final"]}
                for name, scores in evidence.items()
            }
        },
    )
    return plan, run, projects


def test_ranks_by_final_score_descending():
    plan, run, projects = make_plan_and_run(
        {"Best": {"raw": 8, "final": 9}, "Worst": {"raw": 3, "final": 2}}
    )
    results = ranked_results(plan, run)
    assert [r.project_id for r in results] == [projects["Best"].id, projects["Worst"].id]
    assert [r.rank for r in results] == [1, 2]


def test_exact_ties_broken_by_organizer_tie_break_then_project_id():
    plan, run, projects = make_plan_and_run(
        {"A": {"raw": 5, "final": 5.0}, "B": {"raw": 5, "final": 5.0}}
    )
    # B wins the tie via an explicit organizer override.
    plan.tie_breaks = {str(projects["B"].id): 0, str(projects["A"].id): 1}
    plan.save()
    results = ranked_results(plan, run)
    assert [r.project_id for r in results] == [projects["B"].id, projects["A"].id]


def test_ties_with_no_override_fall_back_to_project_id_deterministically():
    plan, run, projects = make_plan_and_run(
        {"A": {"raw": 5, "final": 5.0}, "B": {"raw": 5, "final": 5.0}}
    )
    first = ranked_results(plan, run)
    second = ranked_results(plan, run)
    assert [r.project_id for r in first] == [r.project_id for r in second]
    assert [r.project_id for r in first] == sorted(p.id for p in projects.values())


def test_rejects_a_normalization_run_from_a_different_plan():
    plan_a, run_a, _ = make_plan_and_run({"A": {"raw": 1, "final": 1}})
    plan_b, _, _ = make_plan_and_run({"A": {"raw": 1, "final": 1}})
    with pytest.raises(ValueError, match="does not belong"):
        ranked_results(plan_b, run_a)
