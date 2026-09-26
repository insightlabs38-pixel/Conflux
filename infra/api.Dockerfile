FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY uv.lock pyproject.toml /tmp/deps/

# No apt packages: psycopg[binary] vendors libpq, and health checks use
# Python (below) instead of curl, so the build needs no Debian mirror access
# — consistent with the offline runtime this image serves.
RUN python -m pip install --no-cache-dir "uv==0.12.18" \
    && uv sync --frozen --directory /tmp/deps --no-dev --compile-bytecode

COPY src/api /app
COPY fixtures /app/fixtures

WORKDIR /app

# Migrate, collect static assets, then serve the ASGI application.
ENTRYPOINT ["/bin/sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]
