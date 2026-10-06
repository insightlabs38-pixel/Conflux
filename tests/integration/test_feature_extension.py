"""PD-F003-B03-T03: the extension claims of the completeness contract, held against the manifests.

Extension points are registrations in code, declared by each app's manifest and checked against the
live registries. A feature either offers hooks through its own app's manifest or says why none. The
verifier reads the manifests; these tests prove them: every (manifest, kind) pair is claimed by one
feature or named outside, the manifests agree with the live registries, each claimed kind has live
entries, the SDK has a typed contract for the kinds it describes, and a registration nobody declares
or a claim nobody backs is noticed."""

import pytest
from core import features as ft
from core import features_extension, manifest

pytestmark = pytest.mark.django_db


def claimed():
    found = {}
    for feature in sorted(ft.FEATURES.values(), key=lambda f: f.key):
        hooks, _, _, _ = features_extension.parse(feature.claims["extension"])
        for kind, owner in hooks:
            found.setdefault((owner, kind), []).append(feature.key)
    return found


CLAIMED = claimed()


def test_every_hook_pair_is_claimed_once_and_the_manifests_agree_with_the_live_registries():
    assert manifest.check() == []
    assert set(CLAIMED) | set(features_extension.OUTSIDE) == features_extension.pairs()
    assert not set(CLAIMED) & set(features_extension.OUTSIDE)
    assert all(len(owners) == 1 for owners in CLAIMED.values())
    assert all(len(r) >= features_extension.MIN_REASON for r in features_extension.OUTSIDE.values())
    assert ft.check() == []


def test_each_claimed_kind_has_live_entries_that_its_manifest_declares():
    live = {k: c.live() for k, c in manifest.CAPABILITIES.items() if c.live}
    for owner, kind in CLAIMED:
        declared = features_extension.entries(owner, kind)
        assert declared, (owner, kind)
        if kind in live:
            assert set(declared) <= set(live[kind]), (owner, kind)


def test_the_sdk_has_a_typed_contract_for_the_kinds_it_describes_and_says_so_in_the_report():
    typed = {k for _, k in CLAIMED if features_extension.sdk_type(k)}
    assert typed == {
        "artifact_validator",
        "assignment_strategy",
        "advancement_strategy",
        "archive_converter",
        "archive_exporter",
        "archive_importer",
    }
    row = {f["key"]: f for f in ft.report()["features"]}
    assert row["stage"]["facts"]["extension"]["hooks"][0].startswith(
        "advancement_strategy (everyone, external, manual"
    )
    assert (
        "typed in the SDK as AdvancementStrategy" in row["stage"]["facts"]["extension"]["hooks"][0]
    )
    assert "registered in code only" in row["message"]["facts"]["extension"]["hooks"][0]
    assert row["policy"]["facts"]["extension"]["extension"] == "no hook"


def test_an_entry_registered_without_a_manifest_and_a_claim_nobody_backs_are_noticed(monkeypatch):
    from artifacts import validators

    monkeypatch.setitem(validators.VALIDATORS, "hologram", lambda artifact, storage: None)
    assert [(p["code"], p["severity"]) for p in manifest.check()] == [("unclaimed", "warning")]
    monkeypatch.undo()
    assert manifest.check() == []
    own = manifest.MANIFESTS["stages"]
    emptied = manifest.Manifest(
        id=own.id,
        version=own.version,
        label=own.label,
        provides=tuple(p for p in own.provides if p[0] != "advancement_strategy"),
        requires=own.requires,
    )
    monkeypatch.setitem(manifest.MANIFESTS, "stages", emptied)
    assert "hook_empty" in {p["code"] for p in ft.check(ft.System())}


def verify(key, refs):
    base = ft.FEATURES[key]
    claim = ft.provided(*refs)
    feature = ft.Feature(base.key, base.label, base.model, base.claims | {"extension": claim})
    return ft.VERIFIERS["extension"](feature, claim, ft.System())


def codes(found):
    return {p["code"] for p in found}


TEST = (
    "test:tests/integration/test_feature_extension.py"
    "::test_every_hook_pair_is_claimed_once_and_the_manifests_agree_with_the_live_registries"
)
REASON = "a reason that is long enough to be a sentence"


def real(key):
    return list(ft.FEATURES[key].claims["extension"].refs)


def test_the_real_claims_verify_clean():
    assert verify("stage", real("stage")) == []
    assert verify("track", real("track")) == []


@pytest.mark.parametrize(
    ("key", "refs", "code"),
    [
        ("track", ["no_extension@short"], "no_reason"),
        ("stage", real("stage") + ["no_extension@" + REASON], "both"),
        ("stage", [TEST], "no_hook"),
        ("stage", ["hook:advancement_strategy=stages"], "no_test"),
        ("stage", ["hook:advancement_strategy=stages", "test:nowhere"], "test_ref"),
        ("stage", real("stage") + ["color:red"], "bad_ref"),
        ("stage", ["hook:teleport=stages", TEST], "kind_unknown"),
        ("stage", ["hook:advancement_strategy=nowhere", TEST], "manifest_unknown"),
        ("stage", ["hook:advancement_strategy=artifacts", TEST], "manifest_foreign"),
        ("stage", ["hook:artifact_validator=stages", TEST], "hook_empty"),
        ("stage", ["hook:advancement_strategy=stages"] * 2 + [TEST], "hook_twice"),
        ("stage", ["no_extension@" + REASON], "hook_exists"),
        ("artifact", ["hook:artifact_validator=artifacts", TEST], "hook_unclaimed"),
        ("project", real("project")[:1] + ["hook:thread_subject=events", TEST], "hook_shared"),
    ],
)
def test_each_extension_failure_has_a_code(key, refs, code):
    assert code in codes(verify(key, refs))
