import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from events.models import Event
from stages.models import Stage, StageEntry, StageTransition
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def make_event(name="Dogfood"):
    workspace = Workspace.objects.create(name=workspace_name(name), slug=slugify(name))
    return Event.objects.create(workspace=workspace, name=name, slug=slugify(name))


def workspace_name(name):
    return f"{name} Workspace"


def slugify(name):
    return name.lower().replace(" ", "-")


def make_stage(event, name):
    return Stage.objects.create(event=event, name=name)


# --- Stage/StageTransition model invariants ---------------------------------


def test_two_stages_in_the_same_event_cannot_share_a_name():
    event = make_event()
    Stage.objects.create(event=event, name="Submission")
    with pytest.raises(IntegrityError):
        Stage.objects.create(event=event, name="Submission")


def test_a_stage_cannot_transition_to_itself():
    event = make_event()
    stage = make_stage(event, "Submission")
    with pytest.raises(ValidationError):
        StageTransition(from_stage=stage, to_stage=stage).clean()


def test_a_transition_cannot_cross_events():
    event_a, event_b = make_event("A"), make_event("B")
    stage_a = make_stage(event_a, "Submission")
    stage_b = make_stage(event_b, "Judging")
    with pytest.raises(ValidationError):
        StageTransition(from_stage=stage_a, to_stage=stage_b).clean()


def test_a_direct_cycle_is_rejected():
    event = make_event()
    a = make_stage(event, "A")
    b = make_stage(event, "B")
    StageTransition.objects.create(from_stage=a, to_stage=b)
    with pytest.raises(ValidationError):
        StageTransition(from_stage=b, to_stage=a).clean()


def test_an_indirect_cycle_through_several_stages_is_rejected():
    event = make_event()
    a, b, c, d = (make_stage(event, name) for name in "ABCD")
    StageTransition.objects.create(from_stage=a, to_stage=b)
    StageTransition.objects.create(from_stage=b, to_stage=c)
    StageTransition.objects.create(from_stage=c, to_stage=d)
    with pytest.raises(ValidationError):
        StageTransition(from_stage=d, to_stage=a).clean()


def test_a_branch_with_two_outgoing_edges_is_allowed():
    event = make_event()
    submission = make_stage(event, "Submission")
    judging = make_stage(event, "Judging")
    finals = make_stage(event, "Finals")
    StageTransition.objects.create(from_stage=submission, to_stage=judging)
    StageTransition.objects.create(from_stage=submission, to_stage=finals)
    assert submission.outgoing_transitions.count() == 2


def test_a_merge_with_two_incoming_edges_is_allowed():
    event = make_event()
    track_a = make_stage(event, "Track A")
    track_b = make_stage(event, "Track B")
    finals = make_stage(event, "Finals")
    StageTransition.objects.create(from_stage=track_a, to_stage=finals)
    StageTransition.objects.create(from_stage=track_b, to_stage=finals)
    assert finals.incoming_transitions.count() == 2


def test_the_same_edge_cannot_be_created_twice():
    event = make_event()
    a = make_stage(event, "A")
    b = make_stage(event, "B")
    StageTransition.objects.create(from_stage=a, to_stage=b)
    with pytest.raises(IntegrityError):
        StageTransition.objects.create(from_stage=a, to_stage=b)


# --- StageEntry participation boundary --------------------------------------


def test_a_subject_cannot_have_two_active_stage_entries():
    event = make_event()
    a = make_stage(event, "A")
    b = make_stage(event, "B")
    StageEntry.objects.create(stage=a, subject_type="team", subject_id="tm_01")
    with pytest.raises(IntegrityError):
        StageEntry.objects.create(stage=b, subject_type="team", subject_id="tm_01")


def test_a_subject_may_re_enter_after_its_prior_entry_exits():
    event = make_event()
    a = make_stage(event, "A")
    b = make_stage(event, "B")
    first = StageEntry.objects.create(stage=a, subject_type="team", subject_id="tm_01")
    first.exited_at = first.entered_at
    first.save(update_fields=["exited_at"])

    second = StageEntry.objects.create(stage=b, subject_type="team", subject_id="tm_01")
    assert second.stage_id == b.pk


def test_different_subjects_may_be_active_in_the_same_stage():
    event = make_event()
    stage = make_stage(event, "Submission")
    StageEntry.objects.create(stage=stage, subject_type="team", subject_id="tm_01")
    StageEntry.objects.create(stage=stage, subject_type="team", subject_id="tm_02")
    assert stage.entries.count() == 2
