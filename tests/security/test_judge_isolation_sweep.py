"""A judge must never receive a peer's ballot content through ANY readable route,
including the ones added after the original isolation checks.
"""

import pytest
from accounts.models import Session, User
from django.test import Client
from evaluations.models import Ballot
from integrations.demo_scenarios import generate_demo_event
from test_route_sweep import fill, handlers, routes

pytestmark = pytest.mark.django_db


def test_no_readable_route_reveals_a_peers_ballot_to_a_judge():
    event = generate_demo_event(seed=81, participants=4, judges=3)
    prefix = "demo-hackathon-81-"
    j1, j2, j3 = (User.objects.get(username=f"{prefix}judge-0{i}") for i in (1, 2, 3))
    for judge in (j2, j3):
        for index, ballot in enumerate(Ballot.objects.filter(judge=judge)):
            ballot.comment = f"PEERSECRET-{judge.username}-{index}"
            Ballot.objects.filter(pk=ballot.pk).update(comment=ballot.comment)
    peer_ballot_ids = {str(b.public_id) for b in Ballot.objects.filter(judge__in=[j2, j3])}
    stage = event.stages.get()
    plan = stage.evaluation_plans.get()
    values = {
        "workspace_public_id": event.workspace.public_id,
        "event_public_id": event.public_id,
        "stage_public_id": stage.public_id,
        "plan_public_id": plan.public_id,
        "project_public_id": event.projects.first().public_id,
        "award_public_id": event.awards.first().public_id,
        "user_public_id": j2.public_id,
    }
    client = Client(raise_request_exception=False)
    client.cookies["session"] = Session.issue(j1).token
    leaks = []
    checked = 0
    for route, entry in routes():
        if "get" not in handlers(entry) or "workspace_public_id" not in route:
            continue
        for path in {fill(route, values), fill(route, {**values, "user_public_id": j1.public_id})}:
            response = client.get(path)
            checked += 1
            body = response.content.decode(errors="replace")
            if "PEERSECRET" in body or any(pid in body for pid in peer_ballot_ids):
                leaks.append((route, response.status_code))
    assert checked > 100
    assert not leaks, leaks
