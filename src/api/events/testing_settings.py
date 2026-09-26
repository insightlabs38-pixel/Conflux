"""Isolated settings for focused tests using events.urls as the root (no /api/v1/ prefix)."""

from config.settings import *  # noqa: F403

if "events" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, "events"]  # noqa: F405
ROOT_URLCONF = "events.urls"
