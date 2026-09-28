"""PVS11 invariants under real concurrent transactions."""

from datetime import timedelta

import pytest
from accounts.models import User
from django.utils import timezone
from events.models import Event
from governance.models import DeadlineExceptionRequest, RulesAcknowledgement, RulesVersion
from policies.models import ExceptionGrant
from projects.services import create_project
from test_pvs_races import JSON, base, client_for, race, requires_real_db
from workspaces.models import Membership, Role, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]


@pytest.fixture
def world():
    workspace = Workspace.objects.create(name="GR", slug="gr")
    event = Event.objects.create(workspace=workspace, name="E", slug="e", status="open")
    users = {}
    for name, role in [
        ("org-a", Role.ORGANIZER),
        ("org-b", Role.ORGANIZER),
        ("member", Role.PARTICIPANT),
    ]:
        users[name] = User.objects.create_user(username=name)
        Membership.objects.create(workspace=workspace, user=users[name], role=role)
    return event, users, create_project(event, users["member"], "P")


def test_simultaneous_duplicate_exception_requests_yield_one_pending(world):
    event, users, project = world
    member = client_for(users["member"])
    url = base(event) + f"projects/{project.public_id}/exception-requests/"
    codes = race([lambda: member.post(url, {"reason": "r"}, content_type=JSON).status_code] * 4)
    assert sorted(codes) == [201, 400, 400, 400]
    assert DeadlineExceptionRequest.objects.count() == 1


def test_two_organizers_approving_one_request_create_exactly_one_grant(world):
    event, users, project = world
    created = client_for(users["member"]).post(
        base(event) + f"projects/{project.public_id}/exception-requests/",
        {"reason": "r"},
        content_type=JSON,
    )
    url = base(event) + f"exception-requests/{created.json()['public_id']}/approve/"
    body = {"expires_at": (timezone.now() + timedelta(hours=2)).isoformat()}
    calls = [
        (lambda c=client_for(users[name]): c.post(url, body, content_type=JSON).status_code)
        for name in ("org-a", "org-b")
    ]
    assert sorted(race(calls)) == [200, 400]
    assert ExceptionGrant.objects.count() == 1


def test_simultaneous_acknowledgements_and_rule_publications_stay_consistent(world):
    event, users, _ = world
    org_a, org_b = client_for(users["org-a"]), client_for(users["org-b"])
    payload = {"title": "R", "body": "b"}
    codes = race(
        [
            lambda: org_a.post(base(event) + "rules/", payload, content_type=JSON).status_code,
            lambda: org_b.post(base(event) + "rules/", payload, content_type=JSON).status_code,
        ]
    )
    assert codes == [201, 201]
    assert sorted(RulesVersion.objects.values_list("number", flat=True)) == [1, 2]
    member = client_for(users["member"])
    ack_url = base(event) + "rules/acknowledge/"
    acks = race([lambda: member.post(ack_url, {}, content_type=JSON).status_code] * 4)
    assert sorted(acks) == [200, 200, 200, 201]
    assert RulesAcknowledgement.objects.count() == 1
