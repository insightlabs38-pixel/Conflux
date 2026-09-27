"""GCON-001: a duplicate vote or ballot must be impossible under real
concurrent contention, not just impossible when called sequentially. Vote
and Ballot rely on a DB unique constraint plus an IntegrityError catch
(never a row lock -- uniqueness is what the constraint is for), so this
proves that pairing actually holds up against two real transactions
racing on real PostgreSQL, not two sequential calls in one connection.
"""

import threading
from datetime import timedelta

import pytest
from accounts.models import User
from community.models import VotingPlan
from community.voting import cast_authenticated_vote
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from django.utils import timezone
from evaluations.models import EvaluationPlan, RubricVersion
from evaluations.rubric import clean_criteria
from events.models import Event
from projects.models import Project
from stages.models import Stage
from workspaces.models import Membership, Role, Workspace

requires_real_db = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Needs a real multi-connection DB: set DATABASE_URL to a PostgreSQL instance.",
)
pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]


def _race(callables):
    results = []
    ready = threading.Barrier(len(callables))

    def run(fn):
        close_old_connections()
        try:
            ready.wait(timeout=5)
            fn()
            results.append("ok")
        except (ValidationError, IntegrityError):
            results.append("blocked")
        finally:
            connections.close_all()

    threads = [threading.Thread(target=run, args=(fn,)) for fn in callables]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def test_concurrent_identical_votes_never_double_cast():
    workspace = Workspace.objects.create(name="VoteRace", slug="vote-race")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    voter = User.objects.create_user(username="voter", password="unused")
    Membership.objects.create(workspace=workspace, user=voter, role=Role.PARTICIPANT)
    project = Project.objects.create(event=event, created_by=voter, name="Project")
    now = timezone.now()
    plan = VotingPlan.objects.create(
        event=event, opens_at=now - timedelta(hours=1), closes_at=now + timedelta(hours=1)
    )

    def attempt():
        cast_authenticated_vote(plan, voter, project)

    results = _race([attempt, attempt, attempt])

    assert results.count("ok") == 1, f"expected exactly one vote to win, got {results}"
    assert results.count("blocked") == 2
    assert plan.votes.filter(voter_key=f"user:{voter.public_id}").count() == 1


def test_concurrent_identical_ballots_never_double_submit():
    from evaluations.models import Ballot

    workspace = Workspace.objects.create(name="BallotRace", slug="ballot-race")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    judge = User.objects.create_user(username="judge", password="unused")
    Membership.objects.create(workspace=workspace, user=judge, role=Role.JUDGE)
    creator = User.objects.create_user(username="creator", password="unused")
    project = Project.objects.create(event=event, created_by=creator, name="Project")
    stage = Stage.objects.create(event=event, name="Finals")
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    rubric = RubricVersion.objects.create(
        plan=plan,
        number=1,
        criteria=clean_criteria(
            [{"id": "c1", "name": "C1", "weight": 1, "min_score": 0, "max_score": 10}]
        ),
    )

    def attempt():
        with transaction.atomic():
            Ballot.objects.create(rubric_version=rubric, judge=judge, project=project)

    results = _race([attempt, attempt])

    ok_count = sum(1 for r in results if r == "ok")
    # Ballot creation raises IntegrityError (a plain db.Error), not
    # ValidationError, on the losing side of the race -- catch that too.
    assert ok_count == 1, f"expected exactly one ballot to win, got {results}"
    assert Ballot.objects.filter(rubric_version=rubric, judge=judge, project=project).count() == 1
