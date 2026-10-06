"""PD-F003-B03-T02: the privacy claims of the completeness contract, held against a real subject.

The privacy service exports, erases or retains a person's rows in an event. A feature either says
what becomes of its data about a person or says it holds none. The verifier reads the service's
buckets and the models; these tests prove the claims by exporting and erasing a real subject: the
export lists exactly the buckets the service has, erased rows are gone and only that person's,
retained evidence is kept and reported, private files are purged, and a person who only acted in a
role (an organizer who decided or posted) leaves what they decided in place."""

import pytest
from accounts.models import User
from artifacts.models import Artifact, ArtifactStatus
from core import features as ft
from core import features_privacy
from events.models import EventApplication
from integrations import privacy
from participation.models import Team, TeamMembership
from projects.models import Project, ProjectMembership, Submission, SubmissionVersion

from tests.integration.test_retention_privacy import FakeStorage, label, world

pytestmark = pytest.mark.django_db


def claimed():
    found = {kind: {} for kind in features_privacy.KINDS}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        buckets, _, _, _, _ = features_privacy.parse(feature.claims["privacy"])
        for kind, names in buckets.items():
            for name in names:
                found[kind].setdefault(name, []).append(feature.key)
    return found


CLAIMED = claimed()


def test_every_bucket_of_the_privacy_service_is_claimed_by_exactly_one_feature_or_named_outside():
    table = features_privacy.service_buckets(ft.System())
    for kind, names in CLAIMED.items():
        assert {n for n, (k, _) in table.items() if k == kind} == set(names) | {
            n for n in features_privacy.OUTSIDE if table[n][0] == kind
        }, kind
        assert all(len(owners) == 1 for owners in names.values())
    assert not {n for names in CLAIMED.values() for n in names} & set(features_privacy.OUTSIDE)
    assert ft.check() == []


def test_the_export_lists_exactly_the_buckets_the_service_has():
    _, event, people, _ = world()
    exported = privacy.export_subject(event, people["alice"], actor=people["organizer"])
    table = features_privacy.service_buckets(ft.System())
    assert set(exported["data"]) == {n for n, (k, _) in table.items() if k == "erased"}
    assert set(exported["retained_data"]) == {n for n, (k, _) in table.items() if k == "retained"}


WORLD_BUCKETS = (
    "event_applications",
    "comments",
    "person_labels",
    "team_memberships",
    "project_memberships",
    "submissions",
    "submission_versions",
)


def counts(event, person):
    return {
        **{n: q.count() for n, q in privacy._personal(event, person).items()},
        **{n: q.count() for n, q in privacy._retained(event, person).items()},
    }


def test_a_real_subject_is_exported_and_erased_as_every_claim_says(monkeypatch):
    _, event, people, projects = world()
    monkeypatch.setattr(privacy, "S3Storage", lambda: FakeStorage())
    label(event, people["alice"])
    label(event, people["bob"])
    team = Team.objects.create(event=event, name="Mixed")
    TeamMembership.objects.create(team=team, user=people["alice"])
    TeamMembership.objects.create(team=team, user=people["bob"])
    before_alice, before_bob = counts(event, people["alice"]), counts(event, people["bob"])
    for name in WORLD_BUCKETS:
        assert before_alice[name] > 0, f"the subject has no {name} row to prove it with"
    privacy.erase_subject(
        event, people["alice"], actor=people["organizer"], apply=True, storage=FakeStorage()
    )
    after_alice, after_bob = counts(event, people["alice"]), counts(event, people["bob"])
    assert after_bob == before_bob  # another person's rows are never touched
    for name in CLAIMED["erased"]:
        assert after_alice[name] == 0, f"{name} was not erased"
    for name in CLAIMED["retained"]:
        assert after_alice[name] == before_alice[name], f"{name} was not kept"
    # fates of the person columns
    assert not EventApplication.objects.filter(user=people["alice"]).exists()  # application.user
    kept = Project.objects.get(name="alice")
    assert kept.created_by == people["alice"]  # project.created_by: retained
    assert Submission.objects.get(project=kept).updated_by == people["alice"]  # submission
    assert SubmissionVersion.objects.filter(submission__project=kept).count() == 1
    assert ProjectMembership.objects.filter(project=kept, user=people["alice"]).exists()
    private = Artifact.objects.get(project=kept, title="private")
    assert private.status == ArtifactStatus.PURGED and private.created_by == people["alice"]
    assert Artifact.objects.get(project=kept, title="shown").status == "ready"


def test_a_person_who_only_acted_in_a_role_leaves_what_they_decided_in_place():
    """application.decided_by, announcement.posted_by and message.sent_by are `staff` fates."""
    _, event, people, _ = world()
    decided = EventApplication.objects.filter(user=people["bob"]).first()
    decided.decided_by = people["organizer"]
    decided.save()
    privacy.erase_subject(
        event, people["organizer"], actor=people["organizer"], apply=True, storage=FakeStorage()
    )
    decided.refresh_from_db()
    assert decided.decided_by == people["organizer"]
    assert EventApplication.objects.filter(user=people["bob"]).exists()
    assert User.objects.filter(pk=people["organizer"].pk).exists()


def test_erasing_one_event_leaves_the_same_person_in_another_untouched():
    from events.models import Event

    workspace, event, people, _ = world()
    other = Event.objects.create(workspace=workspace, name="Other", slug="other")
    EventApplication.objects.create(event=other, user=people["alice"], note="elsewhere")
    privacy.erase_subject(
        event, people["alice"], actor=people["organizer"], apply=True, storage=FakeStorage()
    )
    assert EventApplication.objects.filter(event=other, user=people["alice"]).exists()


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"privacy": claim})
    return ft.VERIFIERS["privacy"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_privacy.py"
    "::test_a_real_subject_is_exported_and_erased_as_every_claim_says"
)
REASON = "a reason that is long enough to be a sentence"


def real(key):
    return list(ft.FEATURES[key].claims["privacy"].refs)


def test_the_real_claims_verify_clean_and_the_report_lists_fates():
    assert verify("application", real("application")) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    facts = row["application"]["facts"]["privacy"]
    assert facts["erased"] == ["event_applications"]
    assert facts["people"] == ["user: erased", "decided_by: staff"]
    assert row["track"]["facts"]["privacy"]["privacy"] == "no personal data"
    assert row["artifact"]["facts"]["privacy"]["purged"] == ["private_artifacts"]


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", ["no_personal_data@short"], "no_reason"),
        ("track", ["no_personal_data@" + REASON, "erased:comments"], "both"),
        ("announcement", ["no_personal_data@" + REASON], "personal_exists"),
        ("application", ["no_personal_data@" + REASON], "personal_exists"),
        ("track", [TEST], "no_answer"),
        ("team", ["retained:team_memberships"], "no_test"),
        ("team", ["retained:team_memberships", "test:nowhere"], "test_ref"),
        ("team", ["retained:team_memberships", TEST, "color:red"], "bad_ref"),
        ("team", ["retained:nothing", TEST], "bucket_unknown"),
        ("team", ["erased:team_memberships", TEST], "bucket_kind"),
        ("team", ["retained:team_memberships", "retained:team_memberships", TEST], "bucket_twice"),
        ("track", ["retained:team_memberships", TEST], "bucket_foreign"),
        ("project", ["retained:team_memberships", TEST], "bucket_shared"),
        (
            "application",
            [r for r in real("application") if "event_applications" not in r],
            "bucket_unclaimed",
        ),
        ("announcement", [TEST], "person_unclaimed"),
        (
            "announcement",
            ["person:nothing=staff@" + REASON, "person:posted_by=staff@" + REASON, TEST],
            "person_unknown",
        ),
        (
            "announcement",
            ["person:posted_by=staff@" + REASON, "person:posted_by=staff@" + REASON, TEST],
            "person_twice",
        ),
        ("announcement", ["person:posted_by=gone@" + REASON, TEST], "person_fate"),
        ("announcement", ["person:posted_by=erased", TEST], "person_unbacked"),
        ("announcement", ["person:posted_by=staff@short", TEST], "no_reason"),
    ],
)
def test_each_privacy_failure_has_a_code(key, refs, code):
    assert code in codes(verify(key, refs))


def test_judging_evidence_appeals_eligibility_and_message_receipts_follow_their_claims(monkeypatch):
    """The buckets a plain event does not hold: built here so no claim is proved on zero rows."""
    from communications.models import MessageRecipient
    from communications.services import create_inbox_message
    from django.db import transaction
    from eligibility.models import EligibilityFinding, EligibilityReview
    from evaluations.models import Appeal, EvaluationPlan, PairwiseComparison
    from stages.models import Stage

    from tests.integration.test_event_analytics import judging

    workspace, event, people, projects = world()
    monkeypatch.setattr(privacy, "S3Storage", lambda: FakeStorage())
    stage = Stage.objects.get(event=event)
    plan, judges = judging(
        {"event": event, "workspace": workspace, "actor": people["organizer"]},
        stage,
        [projects["alice"], projects["bob"]],
    )
    low, high = sorted([projects["alice"], projects["bob"]], key=lambda p: p.pk)
    PairwiseComparison.objects.create(
        plan=plan, judge=judges[0], project_a=low, project_b=high, winner=low
    )
    appeal_plan = EvaluationPlan.objects.create(
        stage=stage, name="appeals", candidate_type="project"
    )
    Appeal.objects.create(
        plan=appeal_plan, project=projects["alice"], submitted_by=people["alice"], body="unfair"
    )
    review = EligibilityReview.objects.create(project=projects["alice"], status="open")
    EligibilityFinding.objects.create(
        review=review, code="manual", severity="blocking", message="m", responded_by=people["alice"]
    )
    with transaction.atomic():
        create_inbox_message(
            event=event,
            actor=people["organizer"],
            subject="Hello",
            body="Welcome",
            audience_kind="all_participants",
            audience_params={},
        )
    assert MessageRecipient.objects.filter(user=people["alice"]).exists()

    for person, buckets in (
        (judges[0], ("ballots", "assignments", "pairwise_comparisons")),
        (people["alice"], ("appeals", "eligibility_responses")),
    ):
        before = counts(event, person)
        for name in buckets:
            assert before[name] > 0, f"{person.username} has no {name} row to prove it with"
        privacy.erase_subject(
            event, person, actor=people["organizer"], apply=True, storage=FakeStorage()
        )
        after = counts(event, person)
        for name in buckets:  # retained evidence is kept, and the report says so
            assert after[name] == before[name], name
    assert counts(event, people["alice"])["message_receipts"] == 0  # erased with the person
    assert MessageRecipient.objects.filter(user=people["bob"]).exists()


def test_the_report_names_buckets_and_fates_and_never_a_person(django_assert_num_queries):
    """The report is derived from the code: it holds no subject, note, name or file key."""
    import json

    _, event, people, _ = world()
    label(event, people["alice"])
    with django_assert_num_queries(0):
        text = json.dumps(ft.report())
    for private in ("alice", "bob", "alice note", "alice bio", "k/alice", str(event.public_id)):
        assert private not in text, private
    assert "event_applications" in text and "team_memberships" in text


def test_erasing_twice_is_a_no_op_and_the_second_report_still_names_what_is_kept(monkeypatch):
    """A replayed erasure removes nothing more, keeps the evidence and records its own audit row."""
    _, event, people, _ = world()
    monkeypatch.setattr(privacy, "S3Storage", lambda: FakeStorage())
    first = privacy.erase_subject(
        event, people["alice"], actor=people["organizer"], apply=True, storage=FakeStorage()
    )
    second = privacy.erase_subject(
        event, people["alice"], actor=people["organizer"], apply=True, storage=FakeStorage()
    )
    assert (
        first["erased"]["event_applications"] == 1 and second["erased"]["event_applications"] == 0
    )
    assert second["erased"]["private_artifacts"]["purge"] == 0
    assert second["retained"] == first["retained"] and second["retained_reason"]
