"""PD-F002-B01-T07: the first comments on one subject under real concurrent transactions."""

import pytest
from accounts.models import User
from core import threads
from core.models import Thread, ThreadComment
from events.models import Event, EventApplication
from test_pvs_races import race, requires_real_db
from workspaces.models import Membership, Role, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]


def test_simultaneous_first_comments_share_one_thread_and_all_land():
    workspace = Workspace.objects.create(name="TR", slug="tr")
    event = Event.objects.create(workspace=workspace, name="E", slug="e")
    organizers = []
    for name in ("a", "b", "c", "d"):
        user = User.objects.create_user(username=name)
        Membership.objects.create(workspace=workspace, user=user, role=Role.ORGANIZER)
        organizers.append(user)
    applicant = User.objects.create_user(username="applicant")
    application = EventApplication.objects.create(event=event, user=applicant)

    def write(user):
        def go():
            target = threads.resolve(
                event, user, "application", application.public_id, "organizers"
            )
            return threads.post(target, user, f"note from {user.username}").pk

        return go

    ids = race([write(u) for u in organizers])
    assert len(set(ids)) == 4
    assert Thread.objects.count() == 1
    assert ThreadComment.objects.count() == 4
