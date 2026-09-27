"""Dynamic audience definitions (OPS-002): named, parameterized queries over
*live* workspace/event state, resolved fresh every time a message is
composed or sent. Nothing here is a saved mailing list -- a participant who
joins a team five minutes after "unteamed participants" was last previewed
is simply not in the audience anymore, which is the whole point of
"dynamic": stale membership is a fact about the data, not a fact this
module has to reconcile.
"""

from dataclasses import dataclass, field

from accounts.models import User
from django.core.exceptions import ValidationError
from django.db.models import Count
from evaluations.models import Assignment, Ballot, EvaluationPlan
from participation.models import Team, TeamMembership
from workspaces.models import Membership, Role


@dataclass(frozen=True)
class AudienceKind:
    key: str
    label: str
    param_names: tuple[str, ...] = field(default_factory=tuple)

    def options(self, event):
        """Choices for each declared param, for the compose UI to render."""
        if "track" in self.param_names:
            return {
                "track": [
                    {"public_id": str(t.public_id), "label": t.name}
                    for t in event.tracks.order_by("position", "id")
                ]
            }
        if "plan" in self.param_names:
            return {
                "plan": [
                    {"public_id": str(p.public_id), "label": f"{p.stage.name}: {p.name}"}
                    for p in EvaluationPlan.objects.filter(stage__event=event).select_related(
                        "stage"
                    )
                ]
            }
        return {}


def _role_members(event, *roles):
    user_ids = Membership.objects.filter(workspace=event.workspace, role__in=roles).values_list(
        "user_id", flat=True
    )
    return User.objects.filter(id__in=user_ids).order_by("username")


def _all_participants(event, params):
    return _role_members(event, Role.PARTICIPANT)


def _all_judges(event, params):
    return _role_members(event, Role.JUDGE)


def _all_organizers(event, params):
    return _role_members(event, Role.ORGANIZER, Role.ADMIN)


def _unteamed_participants(event, params):
    participants = _role_members(event, Role.PARTICIPANT)
    teamed_ids = TeamMembership.objects.filter(team__event=event).values_list("user_id", flat=True)
    return participants.exclude(id__in=teamed_ids)


def _teams_without_project(event, params):
    blocked_teams = Team.objects.filter(event=event, projects__isnull=True)
    member_ids = TeamMembership.objects.filter(team__in=blocked_teams).values_list(
        "user_id", flat=True
    )
    return User.objects.filter(id__in=member_ids).order_by("username")


def _track_participants(event, params):
    track_id = params.get("track")
    if not track_id:
        raise ValidationError({"track": "This audience requires a track."})
    track = event.tracks.filter(public_id=track_id).first()
    if track is None:
        raise ValidationError({"track": "Track not found for this event."})
    member_ids = (
        TeamMembership.objects.filter(team__event=event, team__projects__track=track)
        .values_list("user_id", flat=True)
        .distinct()
    )
    return User.objects.filter(id__in=member_ids).order_by("username")


def _judges_incomplete_assignments(event, params):
    plan_id = params.get("plan")
    if not plan_id:
        raise ValidationError({"plan": "This audience requires an evaluation plan."})
    plan = EvaluationPlan.objects.filter(stage__event=event, public_id=plan_id).first()
    if plan is None:
        raise ValidationError({"plan": "Evaluation plan not found for this event."})
    if plan.active_assignment_version_id is None:
        return User.objects.none()
    assigned = (
        Assignment.objects.filter(version=plan.active_assignment_version)
        .values("judge_id")
        .annotate(assigned_count=Count("project_id", distinct=True))
    )
    submitted = dict(
        Ballot.objects.filter(rubric_version__plan=plan)
        .values("judge_id")
        .annotate(count=Count("id"))
        .values_list("judge_id", "count")
    )
    incomplete_ids = [
        row["judge_id"]
        for row in assigned
        if submitted.get(row["judge_id"], 0) < row["assigned_count"]
    ]
    return User.objects.filter(id__in=incomplete_ids).order_by("username")


AUDIENCE_KINDS: dict[str, AudienceKind] = {
    kind.key: kind
    for kind in [
        AudienceKind("all_participants", "All participants"),
        AudienceKind("all_judges", "All judges"),
        AudienceKind("all_organizers", "All organizers"),
        AudienceKind("unteamed_participants", "Unteamed participants"),
        AudienceKind("teams_without_project", "Teams without a project"),
        AudienceKind("track_participants", "Participants in a track", ("track",)),
        AudienceKind(
            "judges_incomplete_assignments", "Judges with incomplete assignments", ("plan",)
        ),
    ]
}

_RESOLVERS = {
    "all_participants": _all_participants,
    "all_judges": _all_judges,
    "all_organizers": _all_organizers,
    "unteamed_participants": _unteamed_participants,
    "teams_without_project": _teams_without_project,
    "track_participants": _track_participants,
    "judges_incomplete_assignments": _judges_incomplete_assignments,
}


def resolve_audience(event, kind: str, params: dict | None = None):
    """Return the live `User` queryset for `kind`, or raise ValidationError
    for an unknown kind or a missing/invalid required param.
    """
    resolver = _RESOLVERS.get(kind)
    if resolver is None:
        raise ValidationError({"audience_kind": "Unknown audience kind."})
    return resolver(event, params or {})
