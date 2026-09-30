"""Suite-wide test configuration.

Password hashing is the dominant cost of this suite: Django's default PBKDF2 hasher spends
~0.28 s per hash and the tests create and verify hundreds of throwaway users (measured in
docs/verification/PD-B02/PROFILE.md: ~73% of CPU). Tests use a fast hasher instead. Production
settings are not touched, and tests/security/test_password_hashing_fidelity.py proves the
configured production hasher is still strong and still works end to end.
"""

import pytest
from django.test import override_settings

FAST_TEST_PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(scope="session", autouse=True)
def _fast_password_hasher():
    with override_settings(PASSWORD_HASHERS=FAST_TEST_PASSWORD_HASHERS):
        yield


@pytest.fixture(scope="module", autouse=True)
def _no_committed_rows_leak_between_modules(request):
    """Fail the module that leaves committed workspace/user rows behind.

    Test data is normally rolled back per test. Module-scoped fixtures that commit (via
    django_db_blocker.unblock) must clean up, otherwise tests in other modules that share the
    worker's database fail depending on how xdist schedules modules (see PD-B02-T03).
    """
    yield
    module_items = [i for i in request.session.items if i.getparent(pytest.Module) is request.node]
    if not any(
        item.get_closest_marker("django_db") or {"db", "transactional_db"} & set(item.fixturenames)
        for item in module_items
    ):
        return
    from django.db import connection

    name = str(connection.settings_dict["NAME"])
    if not (name.startswith("test_") or "memory" in name):
        return  # test DB never set up on this worker; never inspect a real database
    blocker = request.getfixturevalue("django_db_blocker")
    from accounts.models import User
    from django.db.utils import DatabaseError
    from workspaces.models import Workspace

    try:
        with blocker.unblock():
            leaked = {
                "workspaces": list(Workspace.objects.values_list("slug", flat=True)[:5]),
                "users": list(User.objects.values_list("username", flat=True)[:5]),
            }
    except DatabaseError:
        return  # this worker never created the test database, so nothing could have been committed
    assert not any(leaked.values()), (
        f"{request.module.__name__} left committed rows behind: {leaked}. "
        "Clean up module-scoped committed fixtures in their teardown."
    )
