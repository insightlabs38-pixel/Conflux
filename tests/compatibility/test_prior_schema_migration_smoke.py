"""UPG-005: once a prior *released* schema/fixture exists to migrate from,
this is where its regression smoke test belongs -- load that fixture's
database dump, run `manage.py migrate`, and assert the upgraded schema
still reads back the expected known records.

There is only one released version so far (see docs/operations/
UPGRADES.md), so there is nothing to migrate from yet. This is
intentionally a real, collected (not silently skipped-and-forgotten) skip:
it fails loudly with a clear reason if the fixture ever goes missing
without this test being filled in, rather than staying silent forever.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason=(
        "No prior released schema exists yet to smoke-test an upgrade from "
        "(see docs/operations/UPGRADES.md, 'Prior-schema migration smoke fixture')."
    )
)


def test_upgrading_from_the_prior_released_schema_preserves_known_records():
    raise NotImplementedError("Fill in once a prior released schema/fixture exists.")
