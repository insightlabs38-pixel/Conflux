from decimal import Decimal

import pytest
from awards.models import Award, PrizeComponent, PrizePackage, SelectionSource
from django.core.exceptions import ValidationError
from evaluations.models import EvaluationPlan
from events.models import Event, Track
from stages.models import Stage
from workspaces.models import Workspace

pytestmark = pytest.mark.django_db


def test_award_selection_is_independent_and_event_scoped():
    workspace = Workspace.objects.create(name="Awards", slug="awards")
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    track = Track.objects.create(event=event, name="Hardware")
    foreign_track = Track.objects.create(event=other, name="Hardware")
    stage = Stage.objects.create(event=event, name="Finals")
    plan = EvaluationPlan.objects.create(stage=stage, name="Judging")
    award = Award(event=event, name="Best hardware", eligibility_track=track)
    award.full_clean()
    award.selection_source = SelectionSource.EVALUATION
    with pytest.raises(ValidationError, match="requires a plan"):
        award.full_clean()
    award.evaluation_plan = plan
    award.full_clean()
    award.eligibility_track = foreign_track
    with pytest.raises(ValidationError, match="award event"):
        award.full_clean()
    award.eligibility_track = track
    award.winner_count = 0
    with pytest.raises(ValidationError, match="positive"):
        award.full_clean()
    award.winner_count = 1
    award.save()
    assert award.evaluation_plan == plan


def test_typed_components_keep_cash_and_non_cash_separate():
    workspace = Workspace.objects.create(name="Awards", slug="awards")
    event = Event.objects.create(workspace=workspace, name="Event", slug="event")
    award = Award.objects.create(event=event, name="Winner")
    package = PrizePackage.objects.create(award=award, name="Winner package")
    cash = PrizeComponent(
        package=package,
        kind="cash",
        name="Cash",
        amount=Decimal("100.00"),
        currency="USD",
    )
    cash.full_clean()
    cash.save()
    service = PrizeComponent(package=package, kind="service", name="Mentorship")
    service.full_clean()
    service.save()
    service.amount = Decimal("1000.00")
    with pytest.raises(ValidationError, match="Only cash"):
        service.full_clean()
    cash.amount = Decimal("0")
    with pytest.raises(ValidationError, match="positive"):
        cash.full_clean()
    assert [item.kind for item in package.components.all()] == ["cash", "service"]
