import pytest
from django.core.exceptions import ValidationError
from events.models import Event
from stages.advancement import Candidate, advance_stage
from stages.models import ParticipationMode, Stage, StageEntry, StageTransition
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def test_default_mode_is_team_formation():
    event = make_event()
    stage = Stage.objects.create(event=event, name="Submission")
    assert stage.participation_mode == ParticipationMode.TEAM_FORMATION
    assert stage.expected_subject_type() == "team"
    assert stage.locks_team_membership is False


def test_team_locked_reports_locks_team_membership():
    event = make_event()
    stage = Stage.objects.create(
        event=event, name="Finals", participation_mode=ParticipationMode.TEAM_LOCKED
    )
    assert stage.locks_team_membership is True
    assert stage.expected_subject_type() == "team"


def test_individual_stage_expects_a_user_subject():
    event = make_event()
    stage = Stage.objects.create(
        event=event, name="Onboarding", participation_mode=ParticipationMode.INDIVIDUAL
    )
    assert stage.expected_subject_type() == "user"


def test_entering_a_team_into_an_individual_stage_is_rejected():
    event = make_event()
    stage = Stage.objects.create(
        event=event, name="Onboarding", participation_mode=ParticipationMode.INDIVIDUAL
    )
    with pytest.raises(ValidationError):
        StageEntry.objects.enter(stage, "team", "tm_01")


def test_entering_a_user_into_a_team_stage_is_rejected():
    event = make_event()
    stage = Stage.objects.create(event=event, name="Submission")
    with pytest.raises(ValidationError):
        StageEntry.objects.enter(stage, "user", "usr_01")


def test_matching_subject_type_is_accepted():
    event = make_event()
    stage = Stage.objects.create(event=event, name="Submission")
    entry = StageEntry.objects.enter(stage, "team", "tm_01")
    assert entry.stage_id == stage.pk


def test_advance_stage_rejects_a_subject_type_mismatch_with_the_target_stage():
    event = make_event()
    formation = Stage.objects.create(event=event, name="Formation", is_initial=True)
    onboarding = Stage.objects.create(
        event=event, name="Onboarding", participation_mode=ParticipationMode.INDIVIDUAL
    )
    StageTransition.objects.create(from_stage=formation, to_stage=onboarding)
    StageEntry.objects.enter(formation, "team", "tm_01")

    with pytest.raises(ValidationError):
        advance_stage(
            formation,
            onboarding,
            "everyone",
            [Candidate("team", "tm_01")],
            actor=None,
            params={},
        )
