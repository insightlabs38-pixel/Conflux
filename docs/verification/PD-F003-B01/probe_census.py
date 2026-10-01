"""Read-only census for PD-F003-B01-T00: how complete is each domain feature across the surfaces?

Run: docker compose exec -T app python manage.py shell < docs/verification/PD-F003-B01/probe_census.py
Nothing is written. It prints, for the domain models, which ones have a stable public id, a
lifecycle field, an owner event and a REST surface, and what each surface (audit, webhook, search,
bulk, MCP, CLI, Event-as-Code, archive, analytics, privacy) currently covers.
"""

import re
from pathlib import Path

from django.apps import apps
from django.urls import get_resolver

PLATFORM = {"accounts", "audit", "workspaces", "core", "config", "contenttypes", "sessions", "auth"}
SRC = Path("/app")
if not (SRC / "audit").exists():
    SRC = Path("src/api")

models = []
for model in apps.get_models():
    label = model._meta.app_label
    if label in PLATFORM or label in {"admin", "django_celery_beat", "django_celery_results"}:
        continue
    names = {f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)}
    lifecycle = sorted(names & {"status", "state", "is_active", "published_at", "closed_at", "archived_at", "revoked_at", "deleted_at", "decided_at", "locked_at", "finalized_at"})
    models.append(
        {
            "label": f"{label}.{model.__name__}",
            "public_id": "public_id" in names,
            "event": "event" in names,
            "lifecycle": lifecycle,
            "created_at": "created_at" in names,
            "version": bool(names & {"version", "number"}),
        }
    )
print("== domain models:", len(models))
print("   with public_id:", sum(m["public_id"] for m in models))
print("   event-owned:", sum(m["event"] for m in models))
print("   with a lifecycle field:", sum(bool(m["lifecycle"]) for m in models))
print("   public_id AND event AND lifecycle:", sum(m["public_id"] and m["event"] and bool(m["lifecycle"]) for m in models))
by_app = {}
for m in models:
    by_app.setdefault(m["label"].split(".")[0], []).append(m)
for app, rows in sorted(by_app.items()):
    print(f"   {app}: {len(rows)} models, {sum(r['public_id'] for r in rows)} with public_id, {sum(bool(r['lifecycle']) for r in rows)} with lifecycle")
print("   without public_id:", ", ".join(m["label"] for m in models if not m["public_id"]))

print("== REST")
patterns = []


def walk(resolver, prefix=""):
    for p in resolver.url_patterns:
        if hasattr(p, "url_patterns"):
            walk(p, prefix + str(p.pattern))
        else:
            patterns.append(prefix + str(p.pattern))


walk(get_resolver())
api = [p for p in patterns if p.startswith("api/v1/")]
print("   url patterns under api/v1:", len(api))
named = sum(1 for p in api if "<uuid:" in p)
print("   addressed by a public uuid:", named)
integer_ids = [p for p in api if "<int:" in p or "<pk>" in p]
print("   addressed by an integer id:", len(integer_ids), integer_ids[:5])

print("== audit")
actions = set()
for path in SRC.rglob("*.py"):
    if "migrations" in path.parts or path.name.startswith("test"):
        continue
    text = path.read_text()
    actions |= set(re.findall(r"record_mutation\([^)]*?action=\"([a-z_.]+)\"", text, flags=re.S))
    actions |= set(re.findall(r"\baction=\"([a-z_]+\.[a-z_.]+)\"", text))
print("   distinct audit actions in code:", len(actions))
roots = {}
for action in actions:
    roots.setdefault(action.split(".")[0], set()).add(action)
print("   by subject:", {k: len(v) for k, v in sorted(roots.items())})

print("== idempotency")
users = [str(p.relative_to(SRC)) for p in SRC.rglob("*.py") if "idempotency" in p.read_text() and "migrations" not in p.parts and not p.name.startswith("test")]
print("   modules referencing core.idempotency or an Idempotency-Key:", sorted(users))

print("== registries (shared primitives)")
from core import approvals, entities, jobs, manifest, notifications, preview_context, previews, rich, threads, timeline, version_diff  # noqa: E402
from communications import bulk  # noqa: E402

for name, registry in {
    "entities": entities.entities(), "bulk actions": bulk.ACTIONS, "job kinds": jobs.KINDS,
    "approval policies": approvals.POLICIES, "thread subjects": threads.SUBJECTS,
    "timeline providers": timeline.PROVIDERS, "preview sources": previews.SOURCES,
    "version sources": version_diff.SOURCES, "notification categories": notifications.CATEGORIES,
    "rich profiles": rich.PROFILES, "preview surfaces": preview_context.SURFACES,
}.items():
    print(f"   {name}: {sorted(registry)}")
print("   manifest capabilities:", len(manifest.snapshot()["capabilities"]), "manifests:", [m["id"] for m in manifest.snapshot()["manifests"]])

print("== webhook event types emitted")
types = set()
for path in SRC.rglob("*.py"):
    if "migrations" in path.parts or path.name.startswith("test"):
        continue
    types |= set(re.findall(r"event_type=\"([a-z_]+\.[a-z_.]+)\"", path.read_text()))
print("   distinct:", len(types), sorted(types))

print("== MCP tools")
from mcp_adapter import tools  # noqa: E402

print("   read:", sorted(t.name for t in tools.TOOLS if t.method == "GET"))
print("   write:", sorted(t.name for t in tools.TOOLS if t.method != "GET"))

print("== Event-as-Code and archive")
from integrations import eventascode  # noqa: E402

print("   event-as-code sections:", list(eventascode.SECTIONS))
try:
    from integrations import final_archive_schema as fas

    tops = [n for n in dir(fas) if n.isupper()]
    print("   final archive schema constants:", tops[:12])
except Exception as error:  # noqa: BLE001
    print("   final archive schema: unreadable", error)

print("== analytics and privacy")
analytics = sorted({p for p in api if "analytic" in p or "agreement" in p or "workload" in p})
print("   analytics-like endpoints:", analytics)
privacy = sorted({p for p in api if "privacy" in p or "retention" in p or "erasure" in p})
print("   privacy endpoints:", privacy)

print("== SDK and CLI")
import json  # noqa: E402

spec = Path("/app/docs/api/openapi.yaml")
print("   openapi present in container:", spec.exists())

print("== authorization (permission matrix)")
from core.permission_matrix import build_permission_matrix  # noqa: E402

matrix = build_permission_matrix()
kinds = {}
for row in matrix:
    kinds[row["access"]] = kinds.get(row["access"], 0) + 1
print("   entries:", len(matrix), "by access:", kinds, "unrecognized:", sum(r["unrecognized"] for r in matrix))
print("   unknown:", [f"{r['method']} {r['path']}" for r in matrix if r["access"] == "unknown"][:8])

print("== list endpoints: paginated or bare")
from core import pagination  # noqa: E402

print("   pagination helpers:", [n for n in dir(pagination) if not n.startswith("_")][:12])
