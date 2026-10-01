"""PD-F002-B02-T04: the first choices of one person under real concurrent transactions."""

import pytest
from accounts.models import User
from core import notifications
from core.models import NotificationPreference
from test_pvs_races import race, requires_real_db
from workspaces.models import Membership, Role, Workspace

pytestmark = [pytest.mark.django_db(transaction=True), requires_real_db]


def test_simultaneous_first_choices_leave_one_row_and_one_audit_per_real_change():
    from audit.models import AuditEvent

    workspace = Workspace.objects.create(name="NR", slug="nr")
    user = User.objects.create_user(username="chooser")
    Membership.objects.create(workspace=workspace, user=user, role=Role.PARTICIPANT)

    def choose(value):
        return lambda: notifications.set_preference(user, workspace, "announcement", "email", value)

    changed = race([choose(False) for _ in range(6)])
    assert NotificationPreference.objects.filter(user=user).count() == 1
    assert changed.count(True) == 1
    assert AuditEvent.objects.filter(action="notification_preference.changed").count() == 1
    assert notifications.wants(user, workspace, "announcement", "email") is False
