"""What this deployment's code provides and needs, as one inventory (EXTENSION_MANIFEST,
PD-F002-B02-T08).

Conflux has no plugin loader. Everything extensible is application source that registers into one
of the platform's registries when Django starts: page blocks, artifact validators, advancement
strategies, bulk actions, job kinds, approval policies, thread subjects, timeline providers,
entities, preview and version sources, notification categories, rich-content profiles. A
**manifest** is how a source of such code (an app) declares itself, in code:

    manifest.register_manifest(manifest.Manifest(
        id="communications", version="1.0.0", label="Communications",
        provides=(("bulk_action", "send"), ("approval_policy", "message_send")),
        requires=(("manifest", "core"),)))

Rules
- **Declared and checked against the live registries, never trusted.** A manifest's claims must
  be true (`provides` entries exist in the registry they name), every live entry must be claimed
  by exactly one manifest, ids are unique, `api_version` is one this build supports and every
  requirement resolves. `check()` reports each failure with a code; the Django system check turns
  the errors into a startup failure, so a broken or half-registered extension cannot ship quietly.
- **Read-only.** There is no loader, no runtime permission model, no way for an organizer to
  supply code, and nothing here registers or removes anything: the inventory describes what the
  deployment's source already did.
- A capability named after a registry reads its entries live (`live`); one that has no runtime
  registry (archive converters, the assignment solver) is *declared only*: it is listed and its
  requirements resolve against it, but there is nothing to verify it against.
"""

from collections.abc import Callable
from dataclasses import dataclass

API_VERSION = 1
SUPPORTED_API_VERSIONS = (1,)
MANIFEST_KIND = "manifest"  # `requires=(("manifest", "core"),)` needs that manifest to exist


@dataclass(frozen=True)
class Capability:
    """A kind of thing a deployment can provide. `live()` returns `{entry id: label}` read from the
    registry the kind is named after, or is None when the kind has no runtime registry."""

    kind: str
    label: str
    description: str
    live: Callable[[], dict[str, str]] | None = None


@dataclass(frozen=True)
class Manifest:
    id: str
    version: str
    label: str
    api_version: int = API_VERSION
    provides: tuple[tuple[str, str], ...] = ()
    requires: tuple[tuple[str, str], ...] = ()


CAPABILITIES: dict[str, Capability] = {}
MANIFESTS: dict[str, Manifest] = {}


def register_capability(capability: Capability) -> None:
    if capability.kind in CAPABILITIES and CAPABILITIES[capability.kind] != capability:
        raise ValueError(f"Capability '{capability.kind}' is already registered.")
    CAPABILITIES[capability.kind] = capability


def register_manifest(manifest: Manifest) -> None:
    if manifest.id in MANIFESTS and MANIFESTS[manifest.id] != manifest:
        raise ValueError(f"Manifest '{manifest.id}' is already registered.")
    MANIFESTS[manifest.id] = manifest


def _live() -> dict[str, dict[str, str] | None]:
    return {kind: c.live() if c.live else None for kind, c in CAPABILITIES.items()}


def problem(code, message, *, manifest=None, severity="error") -> dict:
    return {"code": code, "severity": severity, "manifest": manifest, "message": message}


def check() -> list[dict]:
    """Every way the declared manifests and the live registries disagree, in a stable order."""
    live = _live()
    problems = []
    claims: dict[tuple[str, str], list[str]] = {}
    for manifest in sorted(MANIFESTS.values(), key=lambda m: m.id):
        if not manifest.id or not manifest.version or not manifest.label:
            problems.append(
                problem(
                    "incomplete",
                    "A manifest needs an id, a version and a label.",
                    manifest=manifest.id,
                )
            )
        if manifest.api_version not in SUPPORTED_API_VERSIONS:
            problems.append(
                problem(
                    "unsupported_api_version",
                    f"Manifest api_version {manifest.api_version} is not supported "
                    f"(this build supports {', '.join(map(str, SUPPORTED_API_VERSIONS))}).",
                    manifest=manifest.id,
                )
            )
        for kind, entry in manifest.provides:
            if kind not in CAPABILITIES:
                problems.append(
                    problem(
                        "unknown_capability",
                        f"Provides '{kind}:{entry}', but there is no capability '{kind}'.",
                        manifest=manifest.id,
                    )
                )
                continue
            claims.setdefault((kind, entry), []).append(manifest.id)
            if live[kind] is not None and entry not in live[kind]:
                problems.append(
                    problem(
                        "not_registered",
                        f"Declares '{kind}:{entry}' but nothing is registered under that name.",
                        manifest=manifest.id,
                    )
                )
    for (kind, entry), owners in sorted(claims.items()):
        if len(owners) > 1:
            problems.append(
                problem(
                    "duplicate_claim",
                    f"'{kind}:{entry}' is claimed by {', '.join(owners)}.",
                    manifest=owners[0],
                )
            )
    for manifest in sorted(MANIFESTS.values(), key=lambda m: m.id):
        for kind, entry in manifest.requires:
            if kind == MANIFEST_KIND:
                found = entry in MANIFESTS
            else:
                found = (kind, entry) in claims or (
                    live.get(kind) is not None and entry in live[kind]
                )
            if not found:
                problems.append(
                    problem(
                        "unresolved_requirement",
                        f"Requires '{kind}:{entry}', which nothing provides.",
                        manifest=manifest.id,
                    )
                )
    for kind, entries in live.items():
        for entry in sorted(entries or {}):
            if (kind, entry) not in claims:
                problems.append(
                    problem(
                        "unclaimed",
                        f"'{kind}:{entry}' is registered but no manifest declares it.",
                        severity="warning",
                    )
                )
    return problems


def snapshot() -> dict:
    """The inventory a read-only admin list shows: manifests with the live state of what they
    provide, the capabilities with their live entries and owners, and the check's findings."""
    live = _live()
    owners: dict[tuple[str, str], str] = {}
    for manifest in MANIFESTS.values():
        for key in manifest.provides:
            owners.setdefault(tuple(key), manifest.id)
    manifests = []
    for manifest in sorted(MANIFESTS.values(), key=lambda m: m.id):
        provides = []
        for kind, entry in manifest.provides:
            registry = live.get(kind)
            provides.append(
                {
                    "kind": kind,
                    "id": entry,
                    "label": (registry or {}).get(entry, entry),
                    "state": "declared"
                    if registry is None
                    else "live"
                    if entry in registry
                    else "missing",
                }
            )
        manifests.append(
            {
                "id": manifest.id,
                "version": manifest.version,
                "label": manifest.label,
                "api_version": manifest.api_version,
                "provides": provides,
                "requires": [{"kind": k, "id": e} for k, e in manifest.requires],
            }
        )
    capabilities = []
    for kind, capability in sorted(CAPABILITIES.items()):
        registry = live[kind]
        # A declared-only kind has no registry to read, so its entries are what manifests declare.
        entries = (
            registry
            if registry is not None
            else {entry: entry for (k, entry) in owners if k == kind}
        )
        capabilities.append(
            {
                "kind": kind,
                "label": capability.label,
                "description": capability.description,
                "declared_only": registry is None,
                "entries": [
                    {"id": entry, "label": label, "manifest": owners.get((kind, entry))}
                    for entry, label in sorted(entries.items())
                ],
            }
        )
    findings = check()
    return {
        "api_version": API_VERSION,
        "supported_api_versions": list(SUPPORTED_API_VERSIONS),
        "manifests": manifests,
        "capabilities": capabilities,
        "problems": findings,
        "ok": not any(p["severity"] == "error" for p in findings),
    }
