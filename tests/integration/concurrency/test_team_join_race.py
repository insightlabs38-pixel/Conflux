"""GCON-001/002: `join_team`'s team-size cap is the *only* place "team size
one to four" is enforced (a plain COUNT can't be a DB constraint), so it
must hold up under real concurrent joins, not just sequential ones. This
needs genuine cross-connection concurrency (two real transactions racing
against real PostgreSQL), which is why it lives here rather than in the
SQLite-backed default test run -- see the batch report for how to run it.
"""

import threading

import pytest
from accounts.models import User
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, connections
from events.models import Event
from participation.models import MAX_TEAM_SIZE, Team, TeamMembership, TeamMembershipRole
from participation.services import join_team
from workspaces.models import Workspace

requires_real_db = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Needs a real multi-connection DB: set DATABASE_URL to a PostgreSQL instance.",
)
pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]


def _setup_team_at(size):
    workspace = Workspace.objects.create(name="Race", slug="race")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    team = Team.objects.create(event=event, name="Racers")
    for n in range(size):
        member = User.objects.create_user(username=f"seed-{n}", password="unused")
        TeamMembership.objects.create(
            team=team,
            user=member,
            role=TeamMembershipRole.CAPTAIN if n == 0 else TeamMembershipRole.MEMBER,
        )
    return team


def _race_join(team, users):
    results = []
    ready = threading.Barrier(len(users))

    def attempt(user):
        close_old_connections()
        try:
            ready.wait(timeout=5)
            join_team(team, user)
            results.append("ok")
        except ValidationError:
            results.append("blocked")
        finally:
            connections.close_all()

    threads = [threading.Thread(target=attempt, args=(user,)) for user in users]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def test_concurrent_joins_never_exceed_the_team_size_cap():
    team = _setup_team_at(MAX_TEAM_SIZE - 1)
    challengers = [
        User.objects.create_user(username=f"challenger-{n}", password="unused") for n in range(3)
    ]

    results = _race_join(team, challengers)

    assert results.count("ok") == 1, (
        f"expected exactly one join to win the last slot, got {results}"
    )
    assert results.count("blocked") == 2
    assert team.memberships.count() == MAX_TEAM_SIZE


def test_concurrent_joins_of_an_already_full_team_all_fail():
    team = _setup_team_at(MAX_TEAM_SIZE)
    challengers = [
        User.objects.create_user(username=f"late-{n}", password="unused") for n in range(2)
    ]

    results = _race_join(team, challengers)

    assert results == ["blocked", "blocked"]
    assert team.memberships.count() == MAX_TEAM_SIZE
