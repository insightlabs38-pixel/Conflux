"""Isolated settings for focused tests until the app is registered by its integration owner."""

from config.settings import *  # noqa: F403

INSTALLED_APPS = [*INSTALLED_APPS, "events"]  # noqa: F405
ROOT_URLCONF = "events.urls"
