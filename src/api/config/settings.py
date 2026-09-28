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
# Extra browser origins allowed to make cookie-authenticated writes (same-origin always is).
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Seeds the Ed25519 keypair that signs publicly verifiable records
# (REC-002): deterministic from the seed so records stay verifiable across
# restarts without persisting key material anywhere. Runtime deployments
# must supply their own; rotating it invalidates every previously issued
# record's signature (there is no key-rotation/multi-key support in v1).
RECORD_SIGNING_KEY_SEED = os.environ["RECORD_SIGNING_KEY_SEED"]
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]

# Optional OpenID Connect sign-in. Everything is off unless OIDC_ISSUER is set, and the
# provider is only contacted when someone signs in, never at startup, so the stack still
# boots and runs fully offline with built-in password authentication.
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "").strip().rstrip("/")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")
OIDC_REDIRECT_URI = os.environ.get("OIDC_REDIRECT_URI", "")
OIDC_SCOPES = os.environ.get("OIDC_SCOPES", "openid email profile")
OIDC_PROVIDER_NAME = os.environ.get("OIDC_PROVIDER_NAME", "Single sign-on")
OIDC_ALLOWED_EMAIL_DOMAINS = [
    domain.strip().lower()
    for domain in os.environ.get("OIDC_ALLOWED_EMAIL_DOMAINS", "").split(",")
    if domain.strip()
]
OIDC_AUTO_CREATE_USERS = os.environ.get("OIDC_AUTO_CREATE_USERS", "1") == "1"
# Linking an unknown provider identity to an existing local account by email is a takeover
# vector if the provider does not verify addresses, so it is opt-in.
OIDC_LINK_BY_VERIFIED_EMAIL = os.environ.get("OIDC_LINK_BY_VERIFIED_EMAIL", "0") == "1"
OIDC_DEFAULT_WORKSPACE_SLUG = os.environ.get("OIDC_DEFAULT_WORKSPACE_SLUG", "")
OIDC_ALLOW_INSECURE_HTTP = os.environ.get("OIDC_ALLOW_INSECURE_HTTP", "0") == "1"

# Extra hosts whose stream URLs may be framed on the public agenda (YouTube and Vimeo are built in).
EMBED_HOSTS = [h.strip() for h in os.environ.get("CONFLUX_EMBED_HOSTS", "").split(",") if h.strip()]

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
    "awards",
    "stages",
    "policies",
    "participation",
    "projects",
    "forms",
    "artifacts",
    "presentation",
    "evaluations",
    "community",
    "communications",
    "taxonomy",
    "eligibility",
    "deliberation",
    "onsite",
    "mentorship",
    "governance",
    "mcp_adapter",
    "portfolio",
    "continuation",
]

MIDDLEWARE = [
    "presentation.middleware.PublicationCacheMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
]

# Presentation (C-B12): the public gallery/event/project pages must show real
# content in the raw HTTP response with no JS execution (the acceptance
# checker, and any similarly plain crawler, only ever does that). Those
# routes are server-rendered Django templates rather than the React SPA.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        # VS23: the language-switcher form needs `request.path` to redirect
        # back to the current page after `set_language`; still deliberately
        # minimal otherwise (no messages/auth/debug processors).
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

# Serves the same design tokens/component CSS the React app uses (single
# source of truth in src/web/styles), so server-rendered pages match it.
STATICFILES_DIRS = [BASE_DIR.parent / "web" / "styles"]
# The built single-page app (image builds bake it in at /web/dist), collected under
# /static/app/; absent in a bare source checkout, which serves only the API and
# server-rendered pages.
_WEB_DIST = Path(os.environ.get("CONFLUX_WEB_DIST", "/web/dist"))
if _WEB_DIST.is_dir():
    STATICFILES_DIRS.append(("app", _WEB_DIST))

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
CELERY_BEAT_SCHEDULE = {
    "process-webhooks": {
        "task": "integrations.tasks.process_webhooks",
        "schedule": 30.0,
    },
    "dispatch-reminders": {
        "task": "communications.tasks.dispatch_due_reminders",
        "schedule": 30.0,
    },
}

# Generic S3 adapter settings; RustFS is the default local object store.
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
S3_PUBLIC_ENDPOINT_URL = os.environ.get("S3_PUBLIC_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "conflux-artifacts")

# Communications (OPS-003): console output is the offline-safe default --
# organizer/participant messages always land in the in-app inbox regardless
# of this setting, and outbound email is a convenience on top, never the
# only copy. A real deployment sets DJANGO_EMAIL_BACKEND to the SMTP
# backend plus EMAIL_HOST/EMAIL_PORT/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD/
# EMAIL_USE_TLS to relay through a local or hosted SMTP server.
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Conflux <no-reply@conflux.local>")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# Presentation i18n (VS23): only the public site's own template chrome is
# translated (organizer-authored content -- project names, block config
# text -- is user data, not app UI, and stays as entered). LocaleMiddleware
# picks a language from `Accept-Language` or the `django_language` cookie
# `set_language` sets; templates render {% trans %} strings from
# LOCALE_PATHS, and Django localizes {{ event.starts_at }}-style output to
# the active locale automatically once USE_I18N is on.
USE_I18N = True
LANGUAGE_CODE = "en-us"
LANGUAGES = [("en", "English"), ("es", "Español")]
LOCALE_PATHS = [BASE_DIR / "locale"]

# Identity/authorization spine (C-B02): custom User carries a stable public ID.
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "core.schema.ConfluxAutoSchema",
    "DEFAULT_PARSER_CLASSES": [
        "core.parsers.ObjectJSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Conflux API",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "ENUM_NAME_OVERRIDES": {
        "EventStatus": "events.models.EventStatus",
        "TaxonomySubjectType": "taxonomy.models.SubjectType",
        "LocationKind": "onsite.models.LocationKind",
        "EventQuestionStatus": "communications.models.EventQuestion.Status",
        "CandidateQueueStatus": ["pending", "drafted", "submitted"],
        "BulkOperationAction": ["assign", "advance", "extend", "move", "send"],
        "ActionEnum": "policies.models.Action",
        "BasePrizeKind": "events.models.BasePrize.Kind",
        "COIRelationshipKind": "evaluations.models.COIRelationshipKind",
        "COIRuleKind": "evaluations.models.COIRuleKind",
        "ProjectCOIAttributeKind": ["institution", "domain"],
    },
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"
