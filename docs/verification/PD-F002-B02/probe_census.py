"""Read-only census for the PD-F002-B02 contract: what already exists for each shared primitive.

Run: docker compose exec -T app python manage.py shell < docs/verification/PD-F002-B02/probe_census.py
Nothing is written. Prints the schema subset in use, rich-text paths, artifact inspection kinds,
profile and preference fields, diff/version helpers, policy evidence shapes and extension registries.
"""

import re
from collections import Counter

from django.apps import apps

print("== SCHEMA_EDITOR: what already declares a schema")
from eventconfig.registry import SPECS
from presentation.block_types import BLOCK_TYPES

kinds = Counter()
for spec in SPECS:
    kinds[str(spec.schema.get("type"))] += 1
print(f"   eventconfig settings: {len(SPECS)} by schema type {dict(kinds)}")
subset = Counter()
for name, block in BLOCK_TYPES.items():
    for key in block["schema"].get("properties", {}):
        subset[block["schema"]["properties"][key]["type"]] += 1
print(f"   page block types: {len(BLOCK_TYPES)}; property types {dict(subset)}")

print("== RICH_DOC: renderers in use")
from presentation import sanitize, technical

print(f"   organizer allowlist HTML: tags={sorted(sanitize.ALLOWED_TAGS)} attrs={sanitize.ALLOWED_ATTRS}")
print(f"   participant markdown: html disabled, images disabled, tables on ({technical._markdown.options})")

print("== ARTIFACT_PREVIEW: inspection and kinds")
from artifacts import inspector
from artifacts.models import ArtifactKind

print(f"   kinds: {[k for k, _ in ArtifactKind.choices]}")
print(f"   inspector version {inspector.INSPECTOR_VERSION}; preview chars {inspector.PREVIEW_CHARS}; max bytes {inspector.MAX_INSPECT_BYTES}")

print("== NOTIFICATIONS: delivery and preferences")
for label in ("communications.Message", "communications.MessageRecipient", "accounts.UserProfile", "integrations.WebhookSubscription"):
    model = apps.get_model(label)
    print(f"   {label}: " + ", ".join(f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)))
print("   no preference or subscription model exists for people (opt-in, categories, channels)")

print("== VERSION_DIFF: what versions and diffs exist")
from audit import services

print(f"   audit.services: {[n for n in dir(services) if 'snapshot' in n or 'diff' in n]}")
versioned = [
    m.__name__ for m in apps.get_models() if any(f.name in ("version", "current_version") for f in m._meta.get_fields())
]
print(f"   models with a version field: {versioned}")

print("== POLICY_EXPLAIN: existing reason and evidence shapes")
from policies import evaluator

print(f"   policy trace: {[n for n in dir(evaluator) if 'trace' in n]}")
from eventconfig import readiness

print(f"   readiness item keys: {sorted(readiness.compute_readiness.__annotations__) or 'dict of id, severity, passed, detail, module, fix'}")

print("== AUDIT_PROVENANCE: where origin and inputs are recorded today")
from audit.models import AuditEvent

print("   AuditEvent: " + ", ".join(f.name for f in AuditEvent._meta.get_fields() if getattr(f, "concrete", False)))
print(f"   AuditEvent rows: {AuditEvent.objects.count()}")

print("== EXTENSION_MANIFEST: registries that exist")
from artifacts.validators import VALIDATORS

print(f"   BLOCK_TYPES={len(BLOCK_TYPES)} VALIDATORS={len(VALIDATORS)}")
from stages.advancement import AdvancementStrategy

print(f"   advancement strategies (subclass registry): {[c.__name__ for c in AdvancementStrategy.__subclasses__()]}")
print("   no manifest, version or capability declaration exists; extensions are deployment source")
