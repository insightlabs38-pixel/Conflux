"""Django settings for the Conflux API.

Bootstrap used SQLite for isolated local checks. RT-001 composes the offline
runtime: PostgreSQL is the authoritative database, Valkey serves disposable
cache/broker data, and the RustFS object store is reachable through the
generic S3 settings below. Local non-Compose checks still default to SQLite.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]

ROOT_URLCONF = "config.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core",
    "accounts.apps.AccountsConfig",
    "workspaces",
    "audit",
    "events",
    "integrations",
    "stages",
    "policies",
    "participation",
    "projects",
    "forms",
    "artifacts",
    "presentation",
    "evaluations",
    "community",
]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

# Presentation (C-B12): the public gallery/event/project pages must show real
# content in the raw HTTP response with no JS execution (the acceptance
# checker, and any similarly plain crawler, only ever does that). Those
# routes are server-rendered Django templates rather than the React SPA.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

# Serves the same design tokens/component CSS the React app uses (single
# source of truth in src/web/styles), so server-rendered pages match it.
STATICFILES_DIRS = [BASE_DIR.parent / "web" / "styles"]

# Compose and deployed runtimes provide DATABASE_URL; the default keeps
# bootstrap-style local checks (pytest, manage.py check) working without it.
if "DATABASE_URL" in os.environ:
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=0)}
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }

# Valkey is disposable cache/broker state only; never authoritative.
VALKEY_URL = os.environ.get("VALKEY_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = VALKEY_URL
CELERY_RESULT_BACKEND = VALKEY_URL

# Generic S3 adapter settings; RustFS is the default local object store.
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
S3_PUBLIC_ENDPOINT_URL = os.environ.get("S3_PUBLIC_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "conflux-artifacts")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# Identity/authorization spine (C-B02): custom User carries a stable public ID.
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "core.schema.ConfluxAutoSchema",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Conflux API",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "ENUM_NAME_OVERRIDES": {
        "EventStatus": "events.models.EventStatus",
        "CandidateQueueStatus": ["pending", "drafted", "submitted"],
    },
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"
