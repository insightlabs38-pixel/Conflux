import pytest
from django.core.management import call_command
from integrations.models import (
    FixtureJudge,
    FixtureProject,
    FixtureScore,
    FixtureScoreCriterion,
    FixtureTeam,
    FixtureTrack,
    ImportedFixture,
)

pytestmark = pytest.mark.django_db


def import_official_fixture():
    call_command("import_fixture", "fixtures/fixtures.json")


def test_import_produces_the_expected_record_counts():
    import_official_fixture()

    fixture = ImportedFixture.objects.get()
    assert fixture.event_external_id == "evt_01"
    assert fixture.event_name == "Sample Hack 2026"
    assert FixtureTrack.objects.count() == 8
    assert FixtureJudge.objects.count() == 30
    assert FixtureTeam.objects.count() == 40
    assert FixtureProject.objects.count() == 41
    assert FixtureScore.objects.count() == 126


def test_duplicate_submission_is_preserved_not_deduplicated():
    """prj_07 and prj_41 are the same team/title/repo on purpose (a deliberate
    duplicate submission per the fixture's design) — the importer must keep
    both rows rather than collapsing or rejecting the second one.
    """
    import_official_fixture()

    dry_harbour = FixtureProject.objects.filter(title="Dry Harbour")
    assert dry_harbour.count() == 2
    assert set(dry_harbour.values_list("external_id", flat=True)) == {"prj_07", "prj_41"}
    assert len({p.submitted_at for p in dry_harbour}) == 2, "distinct records, not one row twice"


def test_constant_scorer_criteria_are_not_normalized():
    """jdg_07 gave every reviewed project 4/4/4 — real fixture data, not a
    bug in the importer, and it must not get "corrected" on the way in.
    """
    import_official_fixture()

    judge = FixtureJudge.objects.get(external_id="jdg_07")
    scores = FixtureScore.objects.filter(judge=judge)
    assert scores.count() == 3
    for score in scores:
        values = set(score.criteria.values_list("value", flat=True))
        assert values == {4}


def test_reimport_replaces_rather_than_accumulates():
    import_official_fixture()
    import_official_fixture()

    assert ImportedFixture.objects.count() == 1
    assert FixtureProject.objects.count() == 41
    assert FixtureScore.objects.count() == 126


def test_score_criteria_are_stored_as_typed_child_rows_not_a_blob():
    import_official_fixture()

    score = FixtureScore.objects.filter(judge__external_id="jdg_01").first()
    criterion = score.criteria.first()
    assert isinstance(criterion, FixtureScoreCriterion)
    assert isinstance(criterion.value, int)
