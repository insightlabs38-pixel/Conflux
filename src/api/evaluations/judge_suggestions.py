"""VS15: transparent, read-only judge suggestions for a pool, ranking
workspace judges who are not yet pool members by matching expertise tags
(VS14/VS13) plus their prior workload/reliability elsewhere in this
workspace -- so an organizer can decide whom to invite before assignment
ever runs. Suggests nothing structural: it never writes an invitation,
membership, or assignment (same read-only boundary as VS04's explorer).
"""

from accounts.models import User
from django.db.models import Count, F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from events.models import Track
from events.views import OrganizerView
from rest_framework.response import Response
from workspaces.models import Role

from .expertise import normalize_tag
from .models import Assignment, Ballot, EvaluationPool, JudgeExpertiseProfile
from .schema import JudgeSuggestionSchema


class PoolJudgeSuggestionsView(OrganizerView):
    @extend_schema(responses=JudgeSuggestionSchema(many=True))
    def get(self, request, workspace_public_id, event_public_id, pool_public_id):
        event = self.get_event()
        workspace = self.get_workspace()
        pool = get_object_or_404(EvaluationPool, event=event, public_id=pool_public_id)

        candidates = list(
            User.objects.filter(memberships__workspace=workspace, memberships__role=Role.JUDGE)
            .exclude(pool_memberships__pool=pool)
            .distinct()
            .order_by("username", "id")
        )
        candidate_ids = [candidate.id for candidate in candidates]

        track_names = {
            normalize_tag(name)
            for name in Track.objects.filter(event=event).values_list("name", flat=True)
        }
        tags_by_judge = dict(
            JudgeExpertiseProfile.objects.filter(
                workspace=workspace, judge_id__in=candidate_ids
            ).values_list("judge_id", "tags")
        )

        # "Prior" workload/reliability is scoped to this workspace's other
        # events -- a judge's standing record here, not this (unstaffed)
        # pool's own not-yet-existent ballots.
        ballot_rows = (
            Ballot.objects.filter(
                judge_id__in=candidate_ids,
                is_calibration=False,
                rubric_version__plan__stage__event__workspace=workspace,
            )
            .exclude(rubric_version__plan__stage__event=event)
            .values("judge_id")
            .annotate(
                ballots=Count("id"),
                events=Count("rubric_version__plan__stage__event", distinct=True),
            )
        )
        ballots_by_judge = {row["judge_id"]: row for row in ballot_rows}

        # Only each historical plan's currently active assignment version
        # counts -- immutable prior versions (e.g. pre-rebalance) would
        # otherwise double-count the same real workload (JDG-008/S04).
        assignment_rows = (
            Assignment.objects.filter(
                judge_id__in=candidate_ids,
                version=F("version__plan__active_assignment_version"),
                version__plan__stage__event__workspace=workspace,
            )
            .exclude(version__plan__stage__event=event)
            .values("judge_id")
            .annotate(assigned=Count("project", distinct=True))
        )
        assigned_by_judge = {row["judge_id"]: row["assigned"] for row in assignment_rows}

        suggestions = []
        for candidate in candidates:
            tags = tags_by_judge.get(candidate.id, [])
            matched = sorted(set(tags) & track_names)
            ballot_row = ballots_by_judge.get(candidate.id)
            ballots = ballot_row["ballots"] if ballot_row else 0
            events_judged = ballot_row["events"] if ballot_row else 0
            assigned = assigned_by_judge.get(candidate.id, 0)
            completion_rate = min(ballots / assigned, 1.0) if assigned else None
            suggestions.append(
                {
                    "judge": candidate,
                    "username": candidate.username,
                    "expertise_tags": tags,
                    "matched_tags": matched,
                    "events_judged": events_judged,
                    "ballots_completed": ballots,
                    "assignments_received": assigned,
                    "completion_rate": completion_rate,
                }
            )

        suggestions.sort(
            key=lambda s: (
                -len(s["matched_tags"]),
                -s["ballots_completed"],
                s["username"].casefold(),
            )
        )
        return Response(
            [
                {
                    "rank": index + 1,
                    "judge": str(suggestion["judge"].public_id),
                    "username": suggestion["username"],
                    "expertise_tags": suggestion["expertise_tags"],
                    "matched_tags": suggestion["matched_tags"],
                    "events_judged": suggestion["events_judged"],
                    "ballots_completed": suggestion["ballots_completed"],
                    "assignments_received": suggestion["assignments_received"],
                    "completion_rate": suggestion["completion_rate"],
                }
                for index, suggestion in enumerate(suggestions)
            ]
        )
