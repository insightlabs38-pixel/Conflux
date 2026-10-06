"""Verifier for the `versioning` property (PD-F003-B03-T04): how a feature keeps its history.

Records change, and what must survive the change differs: some keep numbered, immutable versions
(a published form, a rubric, a finalized submission), some keep a counter that a writer must present
so two writers cannot overwrite each other, some register with the version-comparison primitive
(VERSION_DIFF), and the rest are edited in place with the audit trail as their history. A claim is
held to the models and the registries:

- `immutable:<app.Model>` (zero or more): a model with a `number`, unique within its parent
  (a unique constraint that includes `number`), that refuses to be edited or deleted once written
  (it overrides `save` and `delete`, or is an `ImmutableMixin`), and whose parent is the feature's
  own model (a direct foreign key). Every such model that points at the feature's model must be
  claimed, so a new version model cannot be missed;
- `counter:<field>` (zero or more): an integer field of the feature's own model named for a
  version or revision, and the feature's `idempotency` claim names it as the lock that guards it.
  Every such field must be claimed;
- `diff:<source>` (zero or more): a source of the version-comparison primitive, declared as a
  `version_source` by the manifest that declares the feature;
- `in_place@<reason>`: none of the above exists for the feature, and why; its changes are audited;
- `test:<path>::<name>`: the proof, a test that writes and refuses (CI checks it exists).

A numbered immutable model whose parent is no feature of the registry is named in `OUTSIDE`
(`tests/integration/test_feature_versioning.py`, which also proves each claimed model refuses an
edit and a delete, no source bypasses that guard with a bulk write, a stale writer is refused by
the submission counter and the other locked changes are proved by the idempotency suite).
"""

import re

from django.apps import apps
from django.db import models as dj_models

from . import features, manifest
from .features import problem
from .features_extension import declaring
from .features_idempotency import parse as parse_idempotency

MIN_REASON = 20
VERSIONISH = re.compile(r"version|revision")
OUTSIDE: dict[str, str] = {}


def parse(claim):
    immutable, counters, diffs, tests, reasons, other = [], [], [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "immutable":
            immutable.append(rest)
        elif kind == "counter":
            counters.append(rest)
        elif kind == "diff":
            diffs.append(rest)
        elif kind == "test":
            tests.append(rest)
        elif head == "in_place":
            reasons.append(reason)
        else:
            other.append(ref)
    return immutable, counters, diffs, tests, reasons, other


def is_immutable(model) -> bool:
    if any(base.__name__ == "ImmutableMixin" for base in model.__mro__):
        return True
    return "save" in model.__dict__ and "delete" in model.__dict__


def is_numbered(model) -> bool:
    try:
        model._meta.get_field("number")
    except Exception:
        return False
    return any(
        isinstance(c, dj_models.UniqueConstraint) and "number" in c.fields
        for c in model._meta.constraints
    )


def points_at(model, label: str) -> bool:
    return any(
        f.is_relation and f.many_to_one and f.related_model._meta.label == label
        for f in model._meta.get_fields()
    )


def version_models(feature) -> list[str]:
    """Every numbered, immutable model whose parent is the feature's own model."""
    return sorted(
        m._meta.label
        for m in apps.get_models()
        if is_numbered(m) and is_immutable(m) and points_at(m, feature.model)
    )


def counter_fields(feature, system) -> list[str]:
    model = system.model(feature.model)
    if model is None:
        return []
    return sorted(
        f.name
        for f in model._meta.get_fields()
        if isinstance(f, dj_models.IntegerField)
        and not f.primary_key
        and not f.is_relation
        and VERSIONISH.search(f.name)
    )


def provided_sources(feature) -> set[str]:
    """The comparison sources the manifests that declare the feature provide."""
    return {
        entry
        for owner in declaring(feature)
        for kind, entry in manifest.MANIFESTS[owner].provides
        if kind == "version_source"
    }


def sources(system) -> dict:
    return dict(system.resolve("core.version_diff:SOURCES") or {})


def facts(feature, system) -> dict:
    claim = feature.claims.get("versioning")
    if claim is None or claim.state != "provided":
        return {}
    immutable, counters, diffs, _, reasons, _ = parse(claim)
    if reasons:
        return {"versioning": "edited in place", "why": reasons[0]}
    found = {}
    if immutable:
        found["versions"] = immutable
    if counters:
        found["counters"] = counters
    if diffs:
        found["compare"] = diffs
    return found


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="versioning"))

    immutable, counters, diffs, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not immutable:, counter:, diff:, test: or in_place@.")
    derived_models, derived_counters = version_models(feature), counter_fields(feature, system)
    audit = feature.claims.get("audit")
    if reasons:
        if immutable or counters or diffs or tests:
            bad("both", "A feature cannot keep versions and say it is edited in place.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why it is edited in place (a short sentence).")
        for label in derived_models:
            bad("versions_exist", f"{label} keeps immutable versions of this feature; claim it.")
        for name in derived_counters:
            bad("counter_exists", f"{feature.model}.{name} counts versions; claim it.")
        for source in sorted(provided_sources(feature)):
            bad("diff_exists", f"The manifest provides the version source '{source}'; claim it.")
        if audit is None or audit.state != "provided":
            bad("in_place_unaudited", "A feature edited in place must have its changes audited.")
        return found
    if not (immutable or counters or diffs):
        bad("no_answer", "Name its versions (immutable:, counter:, diff:) or say in_place@.")
    if not tests:
        bad("no_test", "Name the test that writes and refuses (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    seen = set()
    for label in immutable:
        if label in seen:
            bad("version_twice", f"'{label}' is claimed twice.")
        seen.add(label)
        model = system.model(label)
        if model is None:
            bad("model_unknown", f"There is no model '{label}'.")
            continue
        if not is_numbered(model):
            bad("not_numbered", f"{label} has no `number` that is unique within its parent.")
        if not is_immutable(model):
            bad("not_immutable", f"{label} can be edited or deleted after it is written.")
        if not points_at(model, feature.model):
            bad("not_a_child", f"{label} does not point at {feature.model}.")
        for other_feature in features.FEATURES.values():
            other_claim = other_feature.claims.get("versioning")
            if (
                other_feature.key != feature.key
                and other_claim is not None
                and other_claim.state == "provided"
                and label in parse(other_claim)[0]
            ):
                bad("version_shared", f"'{label}' is also claimed by '{other_feature.key}'.")
    for label in sorted(set(derived_models) - seen):
        bad("version_unclaimed", f"{label} keeps immutable versions of this feature; claim it.")
    idem = feature.claims.get("idempotency")
    locks = (
        {detail for _, _, mode, detail, _ in parse_idempotency(idem)[0] if mode == "locked"}
        if idem is not None and idem.state == "provided"
        else set()
    )
    for name in counters:
        if name not in derived_counters:
            bad("counter_unknown", f"{feature.model} has no version counter '{name}'.")
        elif f"{feature.model}.{name}" not in locks:
            bad(
                "counter_unlocked",
                f"No locked@ mode of the idempotency claim names {feature.model}.{name}.",
            )
    if len(set(counters)) != len(counters):
        bad("counter_twice", "A counter is claimed twice.")
    for name in sorted(set(derived_counters) - set(counters)):
        bad("counter_unclaimed", f"{feature.model}.{name} counts versions; claim it.")
    live = sources(system)
    provided = provided_sources(feature)
    for source in diffs:
        if source not in live:
            bad("diff_unknown", f"'{source}' is not a version-comparison source.")
        elif source not in provided:
            bad(
                "diff_foreign",
                f"The manifest that declares {feature.key} does not provide '{source}'.",
            )
    for source in sorted(provided - set(diffs)):
        bad("diff_unclaimed", f"The manifest provides the version source '{source}'; claim it.")
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "versioning")


features.register_verifier("versioning", verify, facts=facts, static=static)
