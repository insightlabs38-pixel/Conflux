"""Common multi-round judging workflows an organizer can bootstrap in one
action (S20), the same "form control instead of hand-wiring" idea as
policies.presets: builds an ordinary Stage/StageTransition chain plus one
EvaluationPlan per round through the existing models -- nothing a stage
graph and an evaluation plan couldn't already express by hand.

Deliberately for a brand-new stage graph only: what round advances into
what, per-round pool assignment, prize judging, and rubric criteria stay
real organizer decisions made afterward through the existing stage/plan
endpoints, not guessed here.
"""

from django.core.exceptions import ValidationError
from stages.models import ParticipationMode, Stage, StageTransition

from .models import EvaluationPlan

PRESETS = {
    "two_round": {
        "label": "Two rounds: Screening → Final",
        "rounds": ["Screening", "Final"],
    },
    "three_round": {
        "label": "Three rounds: Screening → Semifinal → Final",
        "rounds": ["Screening", "Semifinal", "Final"],
    },
}


def apply_preset(event, preset_slug):
    """Create the preset's stage graph and one evaluation plan per stage
    for `event`. Raises ValidationError (never invents a merge) if the
    event already has stages, or if `preset_slug` is unknown.
    """
    if preset_slug not in PRESETS:
        raise ValidationError({"preset": f"Unknown preset: {preset_slug!r}"})
    if event.stages.exists():
        raise ValidationError(
            {"detail": "Workflow presets only apply to an event with no stages yet."}
        )

    stages = []
    for position, name in enumerate(PRESETS[preset_slug]["rounds"]):
        stage = Stage(
            event=event,
            name=name,
            position=position,
            is_initial=(position == 0),
            participation_mode=(
                ParticipationMode.TEAM_FORMATION if position == 0 else ParticipationMode.TEAM_LOCKED
            ),
        )
        stage.full_clean()
        stage.save()
        stages.append(stage)

    for earlier, later in zip(stages, stages[1:]):
        transition = StageTransition(from_stage=earlier, to_stage=later)
        transition.full_clean()
        transition.save()

    plans = []
    for stage in stages:
        plan = EvaluationPlan(stage=stage, name=f"{stage.name} judging")
        plan.full_clean()
        plan.save()
        plans.append(plan)

    return stages, plans
