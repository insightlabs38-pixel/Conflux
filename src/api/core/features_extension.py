"""Verifier for the `extension` property (PD-F003-B03-T03): the hooks a feature offers extenders.

Conflux has no plugin loader. What is extensible is application source that registers into one of
the platform's registries when Django starts, and each app declares what it provides in a manifest
(`core.manifest`, EXTENSION_MANIFEST) that is checked against the live registries. A feature either
offers extension points or says why it offers none, and a claim is held to the manifests:

- `hook:<kind>=<manifest>` (one or more): the capability kind exists, the manifest provides at
  least one entry of it, and the manifest is the one that declares the feature (the app that owns
  it), so a feature cannot claim another app's hooks; no (manifest, kind) pair is claimed by two
  features. The report lists the live entries of the kind and whether the platform's SDK has a typed
  contract for it (`extensions.sdk`) or the hook is registered in code only;
- `test:<path>::<name>`: the proof, a test that the manifests agree with the registries (CI checks
  it exists);
- `no_extension@<reason>`: the feature offers no extension point, and why; a feature whose hooks
  are owed is `planned` with the owning task.

A (manifest, kind) pair no feature owns is named in `OUTSIDE`
(`tests/integration/test_feature_extension.py`, which also proves every pair is claimed once, the
manifests agree with the live registries, and an unclaimed registration fails the manifest check).
"""

import importlib
import re

from . import features, manifest
from .features import problem

MIN_REASON = 20
SDK = "extensions.sdk"

# Pairs of (manifest, capability kind) that belong to an app which declares no feature of the
# registry, so no feature can own them yet.
OUTSIDE = {
    ("core", "rich_profile"): "rich-content profiles belong to the platform core, not to a feature",
    (
        "eventconfig",
        "timeline_provider",
    ): "the event timeline is declared by eventconfig, which has no feature",
    (
        "presentation",
        "page_block",
    ): "page blocks belong to the public event page, not a feature of the registry yet",
    (
        "presentation",
        "preview_surface",
    ): "the public page preview belongs to the public event page, not a registry feature yet",
}


def parse(claim):
    hooks, tests, reasons, other = [], [], [], []
    for ref in claim.refs:
        kind, _, rest = ref.partition(":")
        head, _, reason = ref.partition("@")
        if kind == "hook":
            capability, _, owner = rest.partition("=")
            hooks.append((capability, owner))
        elif kind == "test":
            tests.append(rest)
        elif head == "no_extension":
            reasons.append(reason)
        else:
            other.append(ref)
    return hooks, tests, reasons, other


def declaring(feature) -> list[str]:
    """The manifests that declare the feature (provide `feature:<key>`)."""
    return sorted(
        m.id for m in manifest.MANIFESTS.values() if ("feature", feature.key) in m.provides
    )


def alone(manifest_id: str) -> bool:
    """The manifest declares exactly one feature, so its hooks can only be that feature's."""
    return sum(1 for k, _ in manifest.MANIFESTS[manifest_id].provides if k == "feature") == 1


def entries(manifest_id: str, kind: str) -> list[str]:
    found = manifest.MANIFESTS.get(manifest_id)
    return sorted(e for k, e in found.provides if k == kind) if found else []


def sdk_type(kind: str) -> str | None:
    """The typed contract the SDK offers for a capability kind (`artifact_validator` is
    `ArtifactValidator`), or None when the hook is registered in code only."""
    try:
        exported = importlib.import_module(SDK).__all__
    except (ImportError, AttributeError):
        return None
    name = "".join(part.title() for part in kind.split("_"))
    return next((n for n in (name, name + "Type") if n in exported), None)


def pairs() -> set[tuple[str, str]]:
    """Every (manifest, kind) the deployment provides other than the features themselves."""
    return {(m.id, k) for m in manifest.MANIFESTS.values() for k, _ in m.provides if k != "feature"}


def unclaimed_hooks(feature, claimed: set[tuple[str, str]]) -> list[str]:
    """The hooks of the manifests that declare the feature which no feature of them claims. An app
    with one feature owns every hook it provides; an app with several has them assigned by claim,
    so the first of its features reports the ones nobody claims."""
    found = []
    for owner in declaring(feature):
        mine = sorted(f.key for f in features.FEATURES.values() if owner in declaring(f))
        if feature.key != mine[0]:
            continue
        others = {
            (o, k)
            for f in features.FEATURES.values()
            if owner in declaring(f)
            and f.key != feature.key
            and f.claims["extension"].state == "provided"
            for k, o in parse(f.claims["extension"])[0]
        }
        for kind in sorted({k for k, _ in manifest.MANIFESTS[owner].provides} - {"feature"}):
            if (owner, kind) not in others | claimed and (owner, kind) not in OUTSIDE:
                found.append(f"The manifest '{owner}' provides '{kind}'; no feature claims it.")
    return found


def facts(feature, system) -> dict:
    claim = feature.claims.get("extension")
    if claim is None or claim.state != "provided":
        return {}
    hooks, _, reasons, _ = parse(claim)
    if reasons:
        return {"extension": "no hook", "why": reasons[0]}
    rows = []
    for kind, owner in hooks:
        typed = sdk_type(kind)
        rows.append(
            f"{kind} ({', '.join(entries(owner, kind))}): "
            f"{'typed in the SDK as ' + typed if typed else 'registered in code only'}"
        )
    return {"hooks": rows}


def verify(feature, claim, system) -> list[dict]:
    found = []

    def bad(code, message):
        found.append(problem(code, message, feature=feature.key, prop="extension"))

    hooks, tests, reasons, other = parse(claim)
    for ref in other:
        bad("bad_ref", f"'{ref}' is not hook:<kind>=<manifest>, test: or no_extension@.")
    owners = declaring(feature)
    if reasons:
        if hooks or tests:
            bad("both", "A feature cannot offer hooks and say it offers none.")
        if len(reasons) > 1 or len(reasons[0].strip()) < MIN_REASON:
            bad("no_reason", "Say once why it offers no extension point (a short sentence).")
        for owner in owners:
            if alone(owner):  # an app with one feature owns every hook it provides
                for kind in sorted(
                    {k for k, _ in manifest.MANIFESTS[owner].provides} - {"feature"}
                ):
                    if (owner, kind) not in OUTSIDE:
                        bad("hook_exists", f"The manifest '{owner}' provides '{kind}'; claim it.")
        for message in unclaimed_hooks(feature, set()):
            bad("hook_unclaimed", message)
        return found
    if not hooks:
        bad("no_hook", "Name each hook (hook:<kind>=<manifest>) or say why none (no_extension@).")
    if hooks and not tests:
        bad("no_test", "Name the test that checks the manifests (test:<path>::<name>).")
    for ref in tests:
        if not re.fullmatch(r"tests/[\w./-]+\.py::test_\w+", ref):
            bad("test_ref", f"'{ref}' is not a test (tests/<file>.py::test_<name>).")
    seen = set()
    for kind, owner in hooks:
        if (kind, owner) in seen:
            bad("hook_twice", f"'{kind}' of '{owner}' is claimed twice.")
        seen.add((kind, owner))
        if kind not in manifest.CAPABILITIES:
            bad("kind_unknown", f"'{kind}' is not a capability kind.")
            continue
        if owner not in manifest.MANIFESTS:
            bad("manifest_unknown", f"There is no manifest '{owner}'.")
            continue
        if owner not in owners:
            bad("manifest_foreign", f"'{owner}' does not declare the feature '{feature.key}'.")
        if not entries(owner, kind):
            bad("hook_empty", f"The manifest '{owner}' provides no '{kind}'.")
        for other_feature in features.FEATURES.values():
            other_claim = other_feature.claims.get("extension")
            if (
                other_feature.key != feature.key
                and other_claim is not None
                and other_claim.state == "provided"
                and (kind, owner) in parse(other_claim)[0]
            ):
                bad(
                    "hook_shared",
                    f"'{kind}' of '{owner}' is also claimed by '{other_feature.key}'.",
                )
    for message in unclaimed_hooks(feature, {(owner, kind) for kind, owner in hooks}):
        bad("hook_unclaimed", message)
    return found


def static(feature, claim, root) -> list[dict]:
    return features.static_test_refs(feature, claim, root, "extension")


features.register_verifier("extension", verify, facts=facts, static=static)
