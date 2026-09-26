import pytest
from accounts.models import User
from audit.models import AuditEvent
from django.core.exceptions import ValidationError
from events.models import Event
from stages.advancement import (
    Candidate,
    EveryoneStrategy,
    ExternalResultStrategy,
    ManualStrategy,
    PassFailStrategy,
    PercentileStrategy,
    ThresholdStrategy,
    TopNPerTrackStrategy,
    TopNStrategy,
    advance_stage,
)
from stages.models import Stage, StageEntry, StageTransition
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=f"{name} Workspace", slug=name.lower())
    return Event.objects.create(workspace=workspace, name=name, slug=name.lower())


def candidates(*scores, track_ids=None):
    return [
        Candidate(subject_type="team", subject_id=f"tm_{i:02d}", score=score, track_id=tid)
        for i, (score, tid) in enumerate(
            zip(scores, track_ids or [None] * len(scores), strict=True), start=1
        )
    ]


# --- Individual strategies ----------------------------------------------


def test_manual_advances_exactly_the_selected_subjects():
    pool = candidates(1, 2, 3)
    result = ManualStrategy().select(pool, selected={("team", "tm_01"), ("team", "tm_03")})
    assert result == {("team", "tm_01"), ("team", "tm_03")}


def test_everyone_advances_the_whole_pool():
    pool = candidates(1, 2, 3)
    assert EveryoneStrategy().select(pool) == {_k(c) for c in pool}


def test_top_n_takes_the_highest_scores():
    pool = candidates(5, 9, 1, 7)
    result = TopNStrategy().select(pool, n=2)
    assert result == {("team", "tm_02"), ("team", "tm_04")}


def test_threshold_keeps_scores_at_or_above_minimum():
    pool = candidates(1, 5, 10)
    assert ThresholdStrategy().select(pool, minimum=5) == {("team", "tm_02"), ("team", "tm_03")}


def test_percentile_rounds_up_to_keep_at_least_one():
    pool = candidates(1, 2, 3, 4)
    # 25% of 4 = 1 candidate: the top scorer only.
    assert PercentileStrategy().select(pool, percentile=25) == {("team", "tm_04")}


def test_percentile_rejects_an_out_of_range_value():
    with pytest.raises(ValidationError):
        PercentileStrategy().select(candidates(1), percentile=0)
    with pytest.raises(ValidationError):
        PercentileStrategy().select(candidates(1), percentile=101)


def test_top_n_per_track_ranks_within_each_track_independently():
    pool = candidates(10, 1, 9, 2, track_ids=["trk_a", "trk_a", "trk_b", "trk_b"])
    result = TopNPerTrackStrategy().select(pool, n=1)
    assert result == {("team", "tm_01"), ("team", "tm_03")}


def test_pass_fail_keeps_only_passing_scores():
    pool = candidates(40, 60, 80)
    assert PassFailStrategy().select(pool, minimum=60) == {("team", "tm_02"), ("team", "tm_03")}


def test_external_result_records_only_the_named_advancers():
    pool = candidates(0, 0)
    result = ExternalResultStrategy().select(pool, advancing={("team", "tm_02")})
    assert result == {("team", "tm_02")}


def _k(c):
    return (c.subject_type, c.subject_id)


# --- advance_stage: persistence + audit ----------------------------------


def test_advance_stage_moves_entries_and_leaves_non_advancers_in_place():
    event = make_event()
    submission = Stage.objects.create(event=event, name="Submission", is_initial=True)
    judging = Stage.objects.create(event=event, name="Judging")
    StageTransition.objects.create(from_stage=submission, to_stage=judging)
    StageEntry.objects.create(stage=submission, subject_type="team", subject_id="tm_01")
    StageEntry.objects.create(stage=submission, subject_type="team", subject_id="tm_02")
    organizer = User.objects.create_user(username="organizer", password="unused")

    advanced = advance_stage(
        submission,
        judging,
        "top_n",
        [
            Candidate("team", "tm_01", score=10),
            Candidate("team", "tm_02", score=1),
        ],
        actor=organizer,
        params={"n": 1},
    )

    assert advanced == [{"subject_type": "team", "subject_id": "tm_01"}]
    assert not StageEntry.objects.filter(
        stage=submission, subject_type="team", subject_id="tm_01", exited_at__isnull=True
    ).exists()
    assert StageEntry.objects.filter(
        stage=judging, subject_type="team", subject_id="tm_01", exited_at__isnull=True
    ).exists()
    # tm_02 wasn't selected: still active in Submission, never touched.
    assert StageEntry.objects.filter(
        stage=submission, subject_type="team", subject_id="tm_02", exited_at__isnull=True
    ).exists()


def test_advance_stage_records_an_audited_decision():
    event = make_event()
    submission = Stage.objects.create(event=event, name="Submission", is_initial=True)
    judging = Stage.objects.create(event=event, name="Judging")
    StageTransition.objects.create(from_stage=submission, to_stage=judging)
    StageEntry.objects.create(stage=submission, subject_type="team", subject_id="tm_01")
    organizer = User.objects.create_user(username="organizer", password="unused")

    advance_stage(
        submission,
        judging,
        "everyone",
        [Candidate("team", "tm_01")],
        actor=organizer,
        params={},
    )

    event_row = AuditEvent.objects.get(action="stage.advanced")
    assert event_row.actor == organizer
    assert event_row.metadata["strategy"] == "everyone"
    assert event_row.metadata["advanced"] == [{"subject_type": "team", "subject_id": "tm_01"}]


def test_advance_stage_rejects_a_target_with_no_transition():
    event = make_event()
    submission = Stage.objects.create(event=event, name="Submission", is_initial=True)
    unreachable = Stage.objects.create(event=event, name="Unreachable")

    with pytest.raises(ValidationError):
        advance_stage(
            submission,
            unreachable,
            "everyone",
            [],
            actor=User.objects.create_user(username="organizer", password="unused"),
            params={},
        )
