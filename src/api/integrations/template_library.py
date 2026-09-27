"""Offline starter configurations built from existing event models."""

from django.core.exceptions import ValidationError
from evaluations.models import EvaluationPlan
from events.models import Event, Track
from stages.models import ParticipationMode, Stage, StageTransition

LIBRARY = {
    "hackathon": {
        "label": "Hackathon",
        "description": "Build projects, review demos, and choose finalists.",
        "tracks": ["Software", "Hardware"],
        "stages": ["Build", "Judging", "Final"],
        "judging_stages": [1, 2],
        "criteria": [
            ("innovation", "Innovation", 1),
            ("execution", "Execution", 1),
            ("impact", "Impact", 1),
        ],
    },
    "science_fair": {
        "label": "Science fair",
        "description": "Collect research projects and evaluate their methods and findings.",
        "tracks": ["Research", "Engineering"],
        "stages": ["Submission", "Judging", "Results"],
        "judging_stages": [1],
        "criteria": [
            ("method", "Method", 2),
            ("evidence", "Evidence", 2),
            ("communication", "Communication", 1),
        ],
    },
    "grant": {
        "label": "Grant program",
        "description": "Review applications and select projects for funding.",
        "tracks": ["Research", "Community"],
        "stages": ["Application", "Panel Review", "Decision"],
        "judging_stages": [1],
        "criteria": [
            ("need", "Need", 2),
            ("feasibility", "Feasibility", 2),
            ("impact", "Impact", 1),
        ],
    },
    "demo_day": {
        "label": "Demo day",
        "description": "Prepare showcases and review live product demonstrations.",
        "tracks": ["Products", "Platforms"],
        "stages": ["Submission", "Live Demo", "Showcase"],
        "judging_stages": [1],
        "criteria": [("product", "Product", 2), ("demo", "Demo", 2), ("potential", "Potential", 1)],
    },
    "pitch_competition": {
        "label": "Pitch competition",
        "description": "Screen applicants, hear pitches, and choose finalists.",
        "tracks": ["Early Stage", "Growth"],
        "stages": ["Application", "Pitch Round", "Final"],
        "judging_stages": [1, 2],
        "criteria": [
            ("problem", "Problem", 1),
            ("solution", "Solution", 2),
            ("delivery", "Delivery", 1),
        ],
    },
}


def list_library():
    return [
        {
            "slug": slug,
            "label": spec["label"],
            "description": spec["description"],
            "tracks": spec["tracks"],
            "stages": spec["stages"],
        }
        for slug, spec in LIBRARY.items()
    ]


def instantiate_library_template(*, workspace, template_slug, name, slug):
    """Build an editable draft; the caller wraps all rows in one transaction."""
    spec = LIBRARY.get(template_slug)
    if spec is None:
        raise ValidationError({"template": "Unknown local template."})
    event = Event(
        workspace=workspace,
        name=name,
        slug=slug,
        description=spec["description"],
    )
    event.full_clean()
    event.save()

    for position, track_name in enumerate(spec["tracks"]):
        track = Track(event=event, name=track_name, position=position)
        track.full_clean()
        track.save()

    stages = []
    for position, stage_name in enumerate(spec["stages"]):
        stage = Stage(
            event=event,
            name=stage_name,
            position=position,
            is_initial=position == 0,
            participation_mode=(
                ParticipationMode.TEAM_FORMATION if position == 0 else ParticipationMode.TEAM_LOCKED
            ),
        )
        stage.full_clean()
        stage.save()
        stages.append(stage)
    for before, after in zip(stages, stages[1:]):
        transition = StageTransition(from_stage=before, to_stage=after)
        transition.full_clean()
        transition.save()

    criteria = [
        {"id": criterion_id, "name": label, "weight": weight, "min_score": 0, "max_score": 10}
        for criterion_id, label, weight in spec["criteria"]
    ]
    for index in spec["judging_stages"]:
        plan = EvaluationPlan(
            stage=stages[index],
            name=f"{stages[index].name} judging",
            draft_criteria=criteria,
        )
        plan.full_clean()
        plan.save()
    return event
