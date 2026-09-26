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
    "rest_framework",
    "core",
]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

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

# Generic S3 adapter settings; RustFS is the default local object store.
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "conflux-artifacts")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"
