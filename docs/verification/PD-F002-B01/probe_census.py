"""Read-only census for PD-F002-B01-T00: what already exists for each shared primitive.

Run: docker compose exec -T app python manage.py shell < docs/verification/PD-F002-B01/probe_census.py
Nothing is written. Prints model fields and row counts of the existing near-primitives, the Celery
tasks, and the URL patterns that accept list/filter parameters.
"""

import re

from django.apps import apps
from django.urls import get_resolver

CANDIDATES = {
    "QUERY/SAVED_VIEWS": ["presentation.SavedPublicSearch", "presentation.ProjectSearchTag"],
    "BULK_PLAN": ["communications.BulkReceipt"],
    "ASYNC_JOB": ["core.IdempotencyKey", "integrations.WebhookDelivery"],
    "APPROVAL": ["policies.TemporalGate", "eligibility.EligibilityReview"],
    "THREADS": [
        "community.Comment",
        "deliberation.DeliberationNote",
        "projects.MentorNote",
        "communications.Message",
    ],
    "TIMELINE": ["onsite.AgendaSession", "policies.TemporalGate", "presentation.PublicationSchedule"],
}

print("== models")
for primitive, labels in CANDIDATES.items():
    print(f"-- {primitive}")
    for label in labels:
        try:
            model = apps.get_model(label)
        except LookupError:
            print(f"   {label}: (absent)")
            continue
        fields = ", ".join(
            f"{f.name}:{f.get_internal_type()}" + (f"->{f.related_model.__name__}" if f.is_relation else "")
            for f in model._meta.get_fields()
            if getattr(f, "concrete", False)
        )
        print(f"   {label} rows={model.objects.count()} fields=[{fields}]")

print("== celery tasks")
from config.celery import app  # noqa: E402

print(sorted(name for name in app.tasks if not name.startswith("celery.")))
print("beat:", sorted(getattr(__import__("django.conf").conf.settings, "CELERY_BEAT_SCHEDULE", {})))

print("== jobs app")
print("jobs installed:", apps.is_installed("jobs"))

print("== list endpoints with filter-like query parameters (static scan of views)")
import pathlib  # noqa: E402

root = pathlib.Path("/app") if pathlib.Path("/app/manage.py").exists() else pathlib.Path(".")
pattern = re.compile(r"query_params\.get\(\s*[\"'](\w+)[\"']")
seen = {}
for path in sorted(root.rglob("*.py")):
    if "migrations" in path.parts or "tests" in path.parts:
        continue
    params = pattern.findall(path.read_text(errors="ignore"))
    if params:
        seen[str(path.relative_to(root))] = sorted(set(params))
for file, params in seen.items():
    print(f"   {file}: {params}")
print("files with ad-hoc query parameters:", len(seen))

print("== url patterns")
patterns = [str(p.pattern) for p in get_resolver().url_patterns]
print("top-level include count:", len(patterns))
