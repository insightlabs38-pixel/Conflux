import pytest
from awards.models import Award
from django.core.exceptions import ValidationError
from django.utils import timezone
from evaluations.models import EvaluationPlan
from events.models import Event, Track
from forms.models import FormDefinition
from integrations.archive import SECTION_KEYS, build_archive, import_archive
from policies.models import Policy, PolicyBinding, TemporalGate
from presentation.models import Page, PageBlock
from stages.models import Stage
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def build_event():
    workspace = Workspace.objects.create(name="Sections", slug="sections")
    event = Event.objects.create(workspace=workspace, name="Source", slug="source")
    track = Track.objects.create(event=event, name="Hardware")
    stage = Stage.objects.create(event=event, name="Finals", is_initial=True)
    FormDefinition.objects.create(
        event=event, stage=stage, name="Submission", draft_schema={"fields": []}
    )
    policy = Policy.objects.create(event=event, name="Open policy", ast={"op": "true"})
    PolicyBinding.objects.create(event=event, action="submit", policy=policy)
    TemporalGate.objects.create(
        event=event,
        name="window",
        opens_at=timezone.now(),
        closes_at=timezone.now() + timezone.timedelta(days=1),
    )
    Award.objects.create(event=event, name="Best hardware", eligibility_track=track)
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    plan.rubric_versions.create(
        number=1,
        criteria=[{"id": "c1", "name": "C1", "weight": 1, "min_score": 0, "max_score": 10}],
    )
    page = Page.objects.create(event=event, theme="dark")
    PageBlock.objects.create(page=page, kind="hero", config={"title": "Welcome"})
    return workspace, event


def test_evaluation_plans_and_pages_round_trip():
    workspace, event = build_event()
    archive = build_archive(event, mode="config")
    assert archive["evaluation_plans"][0]["name"] == "Judging"
    assert archive["evaluation_plans"][0]["rubric_versions"][0]["criteria"][0]["id"] == "c1"
    assert archive["pages"][0]["theme"] == "dark"
    assert archive["pages"][0]["blocks"][0]["kind"] == "hero"

    cloned = import_archive(workspace=workspace, archive=archive, name="Clone", slug="clone")
    plan = EvaluationPlan.objects.get(stage__event=cloned)
    assert plan.name == "Judging"
    assert plan.rubric_versions.get().criteria[0]["name"] == "C1"
    page = Page.objects.get(event=cloned)
    assert page.theme == "dark"
    assert page.blocks.get().kind == "hero"


def test_excluding_stages_drops_stage_transitions_and_evaluation_plans():
    _workspace, event = build_event()
    sections = [key for key in SECTION_KEYS if key != "stages"]
    archive = build_archive(event, mode="config", sections=sections)
    assert "stages" not in archive
    assert "stage_transitions" not in archive
    assert "evaluation_plans" not in archive
    assert archive["forms"][0]["stage_ref"] is None


def test_excluding_policies_drops_policy_bindings():
    _workspace, event = build_event()
    sections = [key for key in SECTION_KEYS if key != "policies"]
    archive = build_archive(event, mode="config", sections=sections)
    assert "policy_bindings" not in archive
    assert "temporal_gates" in archive  # gates are independent of policies


def test_excluding_tracks_nulls_optional_track_references():
    _workspace, event = build_event()
    sections = [key for key in SECTION_KEYS if key != "tracks"]
    archive = build_archive(event, mode="config", sections=sections)
    assert archive["awards"][0]["eligibility_track_ref"] is None
    assert "tracks" not in archive


def test_unknown_section_is_rejected():
    _workspace, event = build_event()
    with pytest.raises(ValidationError):
        build_archive(event, mode="config", sections=["not-a-real-section"])
