import os

from django.core.asgi import get_asgi_application

from .concurrency import BoundedInflight

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = BoundedInflight(
    get_asgi_application(), int(os.environ.get("CONFLUX_MAX_INFLIGHT_REQUESTS", "12"))
)
