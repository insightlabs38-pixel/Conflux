"""Event format presets (PD-F001-B01): the one place where a format's real defaults are declared.

A preset is a versioned, declarative bundle: what a good event of this format looks like before the
organizer adds what only they know (real dates, judges, prize amounts). Applying one is
`services.create_event_from_preset`, which writes ordinary domain rows; nothing here is a runtime
setting. Raising `version` is how a preset changes: events record the `(key, version)` they started
from, so earlier events keep an accurate baseline.
"""

from dataclasses import dataclass
from datetime import timedelta

from artifacts.models import ArtifactKind
from events.models import RegistrationMode


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    weight: int
    min_score: int = 0
    max_score: int = 10

    def as_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "weight": self.weight,
            "min_score": self.min_score,
            "max_score": self.max_score,
        }


@dataclass(frozen=True)
class Preset:
    key: str
    version: int
    label: str
    description: str
    duration: timedelta
    registration_mode: str
    min_team_size: int
    max_team_size: int
    required_artifact_kinds: tuple
    stages: tuple
    judging_stages: tuple  # indexes into `stages`
    criteria: tuple
    # Tracks only when the format itself has them; an organizer adds their own otherwise.
    tracks: tuple = ()
    require_finalized_submission: bool = True

    @property
    def duration_days(self):
        return max(1, round(self.duration / timedelta(days=1)))


PRESETS = {
    preset.key: preset
    for preset in (
        Preset(
            key="hackathon",
            version=1,
            label="Hackathon",
            description="Build projects, review demos, and choose finalists.",
            duration=timedelta(days=2),
            registration_mode=RegistrationMode.OPEN,
            min_team_size=1,
            max_team_size=5,
            required_artifact_kinds=(ArtifactKind.REPOSITORY,),
            stages=("Build", "Judging", "Final"),
            judging_stages=(1, 2),
            criteria=(
                Criterion("innovation", "Innovation", 1),
                Criterion("execution", "Execution", 1),
                Criterion("impact", "Impact", 1),
            ),
        ),
        Preset(
            key="science_fair",
            version=1,
            label="Science fair",
            description="Collect research projects and evaluate their methods and findings.",
            duration=timedelta(days=2),
            registration_mode=RegistrationMode.OPEN,
            min_team_size=1,
            max_team_size=4,
            required_artifact_kinds=(ArtifactKind.DOCUMENT,),
            stages=("Submission", "Judging", "Results"),
            judging_stages=(1,),
            criteria=(
                Criterion("method", "Method", 2),
                Criterion("evidence", "Evidence", 2),
                Criterion("communication", "Communication", 1),
            ),
        ),
        Preset(
            key="grant",
            version=1,
            label="Grant program",
            description="Review applications and select projects for funding.",
            duration=timedelta(days=28),
            registration_mode=RegistrationMode.APPLICATION,
            min_team_size=1,
            max_team_size=8,
            required_artifact_kinds=(ArtifactKind.DOCUMENT,),
            stages=("Application", "Panel Review", "Decision"),
            judging_stages=(1,),
            criteria=(
                Criterion("need", "Need", 2),
                Criterion("feasibility", "Feasibility", 2),
                Criterion("impact", "Impact", 1),
            ),
        ),
        Preset(
            key="demo_day",
            version=1,
            label="Demo day",
            description="Prepare showcases and review live product demonstrations.",
            duration=timedelta(days=1),
            registration_mode=RegistrationMode.APPLICATION,
            min_team_size=1,
            max_team_size=10,
            required_artifact_kinds=(ArtifactKind.LIVE_URL,),
            stages=("Submission", "Live Demo", "Showcase"),
            judging_stages=(1,),
            criteria=(
                Criterion("product", "Product", 2),
                Criterion("demo", "Demo", 2),
                Criterion("potential", "Potential", 1),
            ),
        ),
        Preset(
            key="pitch_competition",
            version=1,
            label="Pitch competition",
            description="Screen applicants, hear pitches, and choose finalists.",
            duration=timedelta(days=1),
            registration_mode=RegistrationMode.APPLICATION,
            min_team_size=1,
            max_team_size=5,
            required_artifact_kinds=(ArtifactKind.DOCUMENT,),
            stages=("Application", "Pitch Round", "Final"),
            judging_stages=(1, 2),
            criteria=(
                Criterion("problem", "Problem", 1),
                Criterion("solution", "Solution", 2),
                Criterion("delivery", "Delivery", 1),
            ),
        ),
    )
}


def get_preset(key):
    return PRESETS.get(key)


def baseline(preset):
    """The registry values a preset starts an event with (only keys the preset defines)."""
    return {
        "event.description": preset.description,
        "registration.mode": str(preset.registration_mode),
        "team.min_size": preset.min_team_size,
        "team.max_size": preset.max_team_size,
        "submission.required_artifact_kinds": [
            str(kind) for kind in preset.required_artifact_kinds
        ],
        "submission.require_finalized": preset.require_finalized_submission,
        "dates.duration_hours": round(preset.duration / timedelta(hours=1), 2),
    }
