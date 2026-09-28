"""Seed a production-shaped event for PVS-H02 (run with DATABASE_URL set).

    python loadtests/h02/seed.py seed   PROFILE.json [--participants N --judges N --finalized N]
    python loadtests/h02/seed.py verify PROFILE.json RESULTS.json
"""

import argparse
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from accounts.models import Session, User, digest_session_token  # noqa: E402
from audit.models import AuditEvent, DomainEvent  # noqa: E402
from community.models import Vote, VotingPlan  # noqa: E402
from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402
from django.utils import timezone  # noqa: E402
from evaluations.models import Ballot  # noqa: E402
from events.models import Event  # noqa: E402
from projects.models import (  # noqa: E402
    Project,
    ProjectMembership,
    Submission,
    SubmissionStatus,
    SubmissionVersion,
)
from stages.models import Stage  # noqa: E402
from workspaces.models import Membership, Role, Workspace  # noqa: E402

CRITERIA = [
    {"id": "impact", "name": "Impact", "weight": 2, "min_score": 0, "max_score": 10},
    {"id": "polish", "name": "Polish", "weight": 1, "min_score": 0, "max_score": 10},
]


def seed(args):
    now = timezone.now()
    workspace = Workspace.objects.create(name="Load", slug="load-h02")
    users = [User(username="h02-organizer", password="!")]
    users += [User(username=f"h02-judge-{i}", password="!") for i in range(args.judges)]
    users += [User(username=f"h02-p-{i}", password="!") for i in range(args.participants)]
    User.objects.bulk_create(users)
    users = list(User.objects.filter(username__startswith="h02-").order_by("id"))
    by_name = {u.username: u for u in users}
    organizer = by_name["h02-organizer"]
    judges = [by_name[f"h02-judge-{i}"] for i in range(args.judges)]
    parts = [by_name[f"h02-p-{i}"] for i in range(args.participants)]
    Membership.objects.bulk_create(
        [Membership(user=organizer, workspace=workspace, role=Role.ORGANIZER)]
        + [Membership(user=u, workspace=workspace, role=Role.JUDGE) for u in judges]
        + [Membership(user=u, workspace=workspace, role=Role.PARTICIPANT) for u in parts]
    )
    Session.objects.bulk_create(
        [
            Session(user=u, token_digest=digest_session_token(f"{u.username}-token"))
            for u in users
        ]
    )
    event = Event.objects.create(
        workspace=workspace,
        name="Load Hack",
        slug="load-hack",
        status="open",
        is_public=True,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
    )
    stage = Stage.objects.create(event=event, name="Build")
    Project.objects.bulk_create(
        [
            Project(
                event=event,
                name=f"Project {i} {'atlas beacon ledger'.split()[i % 3]}",
                description=f"Synthetic project {i} for load testing search and gallery.",
                created_by=u,
            )
            for i, u in enumerate(parts)
        ]
    )
    projects = list(Project.objects.filter(event=event).order_by("id"))
    ProjectMembership.objects.bulk_create(
        [ProjectMembership(project=p, user=p.created_by, role="owner") for p in projects]
    )
    fin = projects[: args.finalized]
    Submission.objects.bulk_create(
        [Submission(project=p, stage=stage, updated_by=p.created_by) for p in fin]
    )
    subs = list(Submission.objects.filter(project__in=fin))
    SubmissionVersion.objects.bulk_create(
        [
            SubmissionVersion(
                submission=s,
                number=1,
                snapshot={"draft": {"notes": "seed"}, "artifacts": [], "forms": []},
                digest=f"{s.pk:064x}",
                finalized_by=s.updated_by,
            )
            for s in subs
        ]
    )
    versions = {v.submission_id: v for v in SubmissionVersion.objects.filter(submission__in=subs)}
    for s in subs:
        s.status = SubmissionStatus.FINALIZED
        s.current_version = versions[s.pk]
    Submission.objects.bulk_update(subs, ["status", "current_version"])
    VotingPlan.objects.create(
        event=event,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(days=1),
        identity_mode="authenticated",
    )

    c = Client()
    c.cookies["session"] = "h02-organizer-token"
    base = f"/api/v1/workspaces/{workspace.public_id}/events/{event.public_id}"
    plan = c.post(
        f"{base}/stages/{stage.public_id}/evaluation-plans/",
        data={"name": "Panel", "draft_criteria": CRITERIA},
        content_type="application/json",
        HTTP_HOST="localhost",
    ).json()
    assert (
        c.post(
            f"{base}/stages/{stage.public_id}/evaluation-plans/{plan['public_id']}/publish-rubric/",
            HTTP_HOST="localhost",
        ).status_code
        == 201
    )
    profile = {
        "workspace": str(workspace.public_id),
        "event": str(event.public_id),
        "stage": str(stage.public_id),
        "plan": plan["public_id"],
        "organizer": "h02-organizer-token",
        "judges": [f"h02-judge-{i}-token" for i in range(args.judges)],
        "participants": [
            {"token": f"h02-p-{i}-token", "project": str(p.public_id)}
            for i, p in enumerate(projects)
        ],
        "finalized_projects": [str(p.public_id) for p in fin],
        "finalized": args.finalized,
    }
    Path(args.profile).write_text(json.dumps(profile))
    print(f"seeded {len(parts)} participants, {len(judges)} judges, {len(fin)} finalized")


def verify(args):
    profile = json.loads(Path(args.profile).read_text())
    res = json.loads(Path(args.results).read_text())
    ok = res["successes"]
    failures = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name, detail)
        if not cond:
            failures.append(name)

    event = Event.objects.get(public_id=profile["event"])
    ballots = Ballot.objects.filter(rubric_version__plan__public_id=profile["plan"])
    check("ballots == 201s", ballots.count() == ok["ballot"], f"{ballots.count()} vs {ok['ballot']}")
    dupes = (
        ballots.values("judge_id", "project_id").order_by().distinct().count() != ballots.count()
    )
    check("no duplicate judge/project ballots", not dupes)
    check(
        "ballot.submitted audit == ballots",
        AuditEvent.objects.filter(action="ballot.submitted").count() >= ballots.count(),
    )
    votes = Vote.objects.filter(plan__event=event)
    check("votes == 201s", votes.count() == ok["vote"], f"{votes.count()} vs {ok['vote']}")
    fin_events = DomainEvent.objects.filter(event_type="submission.finalized").count()
    versions = SubmissionVersion.objects.filter(submission__project__event=event)
    live = versions.count() - profile["finalized"]
    check("live finalizations == 201s", live == ok["finalize"], f"{live} vs {ok['finalize']}")
    check("finalize domain events == live finalizations", fin_events == live, f"{fin_events}")
    multi = (
        Submission.objects.filter(project__event=event)
        .values("id")
        .annotate(n=django.db.models.Count("versions"))
        .filter(n__gt=1)
        .count()
    )
    check("no submission has >1 version", multi == 0)
    check("no 5xx", res["server_errors"] == 0, str(res["server_errors"]))
    with connection.cursor() as cur:
        cur.execute("select count(*) from pg_stat_activity where datname=current_database()")
        print("open db connections now:", cur.fetchone()[0])
    sys.exit(1 if failures else 0)


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("seed")
s.add_argument("profile")
s.add_argument("--participants", type=int, default=400)
s.add_argument("--judges", type=int, default=30)
s.add_argument("--finalized", type=int, default=300)
v = sub.add_parser("verify")
v.add_argument("profile")
v.add_argument("results")
a = p.parse_args()
seed(a) if a.cmd == "seed" else verify(a)
