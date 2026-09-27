"""Vote tallies with a hidden-until-release gate (COM-005): a public vote
count published mid-vote is itself a way to sway the remaining electorate,
so nobody outside the organizer sees anything before the organizer
explicitly publishes, and even then only once voting has actually closed.
"""

from django.db.models import Count

from .models import Vote


def tally(plan):
    counts = (
        Vote.objects.filter(plan=plan)
        .values("project_id")
        .annotate(votes=Count("id"))
        .order_by("-votes", "project_id")
    )
    return [{"project_id": row["project_id"], "votes": row["votes"]} for row in counts]


def results_visible_to(plan, *, is_organizer: bool) -> bool:
    if is_organizer:
        return True
    return plan.results_published_at is not None and plan.has_closed()
