"""PD-F003-B03-T04: the versioning claims of the completeness contract, held against the models.

A feature keeps numbered immutable versions, a counter a writer must present, a comparison source,
or is edited in place with the audit trail as its history. The verifier reads the models, the
manifests and the comparison registry; these tests prove the claims by writing: every numbered
immutable model is claimed once, each refuses an edit and a delete once written, no code bypasses
that guard with a bulk write, a stale writer is refused by each counter, and the comparison sources
compare two real versions."""

import re
from pathlib import Path

import pytest
from core import features as ft
from core import features_versioning, version_diff
from django.apps import apps
from django.core.exceptions import ValidationError
from evaluations.models import AssignmentVersion, NormalizationRun, PairwiseRun, RubricVersion
from forms.models import FormDefinition, FormVersion
from governance.models import RulesVersion
from projects.models import Submission, SubmissionVersion

from tests.integration.test_final_archive import source

pytestmark = pytest.mark.django_db
SRC = Path(__file__).resolve().parents[2] / "src/api"


def claimed():
    found = {"immutable": {}, "counter": {}, "diff": {}}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        immutable, counters, diffs, _, _, _ = features_versioning.parse(
            feature.claims["versioning"]
        )
        for label in immutable:
            found["immutable"].setdefault(label, []).append(feature.key)
        for name in counters:
            found["counter"].setdefault((feature.model, name), []).append(feature.key)
        for name in diffs:
            found["diff"].setdefault(name, []).append(feature.key)
    return found


CLAIMED = claimed()


def test_every_numbered_immutable_model_is_claimed_once_or_named_outside():
    every = {
        m._meta.label
        for m in apps.get_models()
        if features_versioning.is_numbered(m) and features_versioning.is_immutable(m)
    }
    assert every == set(CLAIMED["immutable"]) | set(features_versioning.OUTSIDE)
    assert not set(CLAIMED["immutable"]) & set(features_versioning.OUTSIDE)
    assert all(len(owners) == 1 for kind in CLAIMED.values() for owners in kind.values())
    assert set(CLAIMED["diff"]) == set(version_diff.SOURCES)
    assert ft.check() == []


def make(label, event, plan, project):
    """One written row of each claimed version model, built from the archive suite's event."""
    if label == "forms.FormVersion":
        definition = FormDefinition.objects.create(event=event, name="Form", draft_schema={})
        return FormVersion.objects.create(definition=definition, number=1, schema={})
    if label == "evaluations.RubricVersion":
        return RubricVersion.objects.filter(plan=plan).first()
    if label == "evaluations.AssignmentVersion":
        return AssignmentVersion.objects.create(plan=plan, number=7, coverage=1, evidence={})
    if label == "evaluations.NormalizationRun":
        return NormalizationRun.objects.filter(plan=plan).first()
    if label == "evaluations.PairwiseRun":
        return PairwiseRun.objects.create(
            plan=plan, number=1, prior_games=1, iterations=1, converged=True, evidence={}
        )
    if label == "projects.SubmissionVersion":
        return SubmissionVersion.objects.filter(submission__project=project).first()
    if label == "governance.RulesVersion":
        owner = project.created_by
        return RulesVersion.objects.create(
            event=event, number=1, title="Rules", body="Be kind", created_by=owner
        )
    raise AssertionError(f"no way to build {label}")


def test_each_claimed_version_model_refuses_an_edit_and_a_delete():
    _, event, _, _, project, plan = source()
    for label in sorted(CLAIMED["immutable"]):
        row = make(label, event, plan, project)
        assert row is not None and row.pk, label
        with pytest.raises(ValidationError) as edit:
            row.save()
        assert edit.value is not None, label
        with pytest.raises(ValidationError) as delete:
            row.delete()
        assert delete.value is not None, label
        assert type(row).objects.filter(pk=row.pk).exists(), f"{label} was changed or removed"


BULK = re.compile(
    r"\b(FormVersion|RubricVersion|AssignmentVersion|NormalizationRun|PairwiseRun|SubmissionVersion"
    r"|RulesVersion)\.objects\b[^\n]*\.(update|delete|bulk_update)\("
)


def test_no_code_bypasses_the_guard_with_a_bulk_write_on_a_version_model():
    """Immutability is a rule of the model, not a database trigger: a queryset `update` or
    `delete` would slip past it, so no source file may do that (accepted residual: the database
    itself does not refuse it)."""
    offenders = []
    for path in SRC.rglob("*.py"):
        if {"migrations", "tests"} & set(path.parts) or path.name.startswith("test_"):
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if BULK.search(line):
                offenders.append(f"{path.relative_to(SRC)}:{number}")
    assert offenders == []


def test_a_stale_writer_is_refused_by_the_submission_counter():
    from projects.submissions import save_draft
    from stages.models import Stage

    from tests.integration.test_retention_privacy import world

    _, event, people, projects = world()
    event.status = "open"
    event.starts_at = event.ends_at = None
    event.save()
    stage = Stage.objects.get(event=event)
    alice, project = people["alice"], projects["alice"]
    submission = Submission.objects.get(project=project, stage=stage)
    revision = submission.draft_revision
    save_draft(project, stage, alice, payload={"notes": "first"}, revision=revision)
    submission.refresh_from_db()
    assert submission.draft_revision == revision + 1
    with pytest.raises(ValidationError, match="stale"):  # a second writer with the old revision
        save_draft(project, stage, alice, payload={"notes": "second"}, revision=revision)
    submission.refresh_from_db()
    assert submission.draft_revision == revision + 1
    assert submission.draft_payload["notes"] == "first"


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"versioning": claim})
    return ft.VERIFIERS["versioning"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_versioning.py"
    "::test_each_claimed_version_model_refuses_an_edit_and_a_delete"
)
REASON = "a reason that is long enough to be a sentence"


def real(key):
    return list(ft.FEATURES[key].claims["versioning"].refs)


def test_the_real_claims_verify_clean_and_the_report_lists_versions_counters_and_comparison():
    assert verify("form", real("form")) == []
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["form"]["facts"]["versioning"] == {
        "versions": ["forms.FormVersion"],
        "compare": ["form"],
    }
    assert row["submission"]["facts"]["versioning"]["counters"] == ["draft_revision"]
    assert row["track"]["facts"]["versioning"]["versioning"] == "edited in place"


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", ["in_place@short"], "no_reason"),
        ("form", real("form") + ["in_place@" + REASON], "both"),
        ("form", [TEST], "no_answer"),
        ("form", ["immutable:forms.FormVersion"], "no_test"),
        ("form", ["immutable:forms.FormVersion", "test:nowhere"], "test_ref"),
        ("form", real("form") + ["color:red"], "bad_ref"),
        ("form", ["immutable:forms.Nothing", TEST, "diff:form"], "model_unknown"),
        ("form", ["immutable:forms.FormDefinition", TEST, "diff:form"], "not_numbered"),
        ("form", ["immutable:forms.FormVersion"] * 2 + ["diff:form", TEST], "version_twice"),
        ("form", ["diff:form", TEST], "version_unclaimed"),
        ("form", ["immutable:forms.FormVersion", "diff:rubric", TEST], "diff_foreign"),
        ("form", ["immutable:forms.FormVersion", "diff:nothing", TEST], "diff_unknown"),
        ("form", ["immutable:forms.FormVersion", TEST], "diff_unclaimed"),
        ("form", ["in_place@" + REASON], "versions_exist"),
        ("track", ["immutable:forms.FormVersion", TEST], "not_a_child"),
        ("announcement", [TEST], "counter_unclaimed"),
        ("announcement", ["counter:nothing", "counter:version", TEST], "counter_unknown"),
        ("announcement", ["in_place@" + REASON], "counter_exists"),
        ("event", ["immutable:evaluations.RubricVersion", TEST], "not_a_child"),
        ("project", ["immutable:projects.SubmissionVersion", TEST], "not_a_child"),
        (
            "evaluation_plan",
            ["immutable:evaluations.RubricVersion", "diff:rubric", TEST],
            "version_unclaimed",
        ),
        ("stage", ["counter:version", TEST], "counter_unknown"),
        (
            "submission",
            [
                "immutable:projects.SubmissionVersion",
                TEST,
                "counter:draft_revision",
                "counter:draft_revision",
            ],
            "counter_twice",
        ),
        ("track", ["in_place@" + REASON], "ok"),
    ],
)
def test_each_versioning_failure_has_a_code(key, refs, code):
    found = codes(verify(key, refs))
    assert (not found) if code == "ok" else code in found
