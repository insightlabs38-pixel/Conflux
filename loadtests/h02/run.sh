#!/usr/bin/env bash
# Reset the H02 database, seed it, serve it with uvicorn, drive the mixed load, verify integrity.
#   WORKERS=2 SECONDS_=60 SCALE=1 loadtests/h02/run.sh OUT_PREFIX
# Needs a PostgreSQL reachable at $PGURL_BASE (default: the compose db on :15432).
set -euo pipefail
cd "$(dirname "$0")/../.."
out=${1:-/tmp/h02}
base=${PGURL_BASE:-postgres://conflux:conflux@localhost:15432}
export DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-analytics-test-only}
export RECORD_SIGNING_KEY_SEED=${RECORD_SIGNING_KEY_SEED:-0000000000000000000000000000000000000000000000000000000000000001}
export DJANGO_DEBUG=1 DATABASE_URL=$base/conflux_h02
psql_admin() { docker exec "${PG_CONTAINER:-confluxh00-db-1}" psql -U conflux -q -d postgres -c "$1"; }
psql_admin "drop database if exists conflux_h02 with (force)"
psql_admin "create database conflux_h02"
.venv/bin/python src/api/manage.py migrate --noinput >/dev/null
.venv/bin/python loadtests/h02/seed.py seed "$out-profile.json" ${SEED_ARGS:-}
(cd src/api && exec ../../.venv/bin/uvicorn config.asgi:application --host 127.0.0.1 --port 18100 \
  --workers "${WORKERS:-2}" --log-level warning) > "$out-uvicorn.log" 2>&1 &
srv=$!
trap 'kill $srv 2>/dev/null || true' EXIT
for _ in $(seq 40); do curl -sf -H 'Host: localhost' http://127.0.0.1:18100/api/v1/health/ >/dev/null && break; sleep 0.5; done
(while sleep 1; do docker exec "${PG_CONTAINER:-confluxh00-db-1}" psql -U conflux -d postgres -Atc \
  "select count(*) from pg_stat_activity where datname='conflux_h02'"; done > "$out-conns.txt" 2>/dev/null) &
sampler=$!
trap 'kill $srv $sampler 2>/dev/null || true' EXIT
python3 loadtests/h02/mixed_load.py "$out-profile.json" "$out-results.json" \
  --seconds "${SECONDS_:-60}" --scale "${SCALE:-1}"
kill $sampler 2>/dev/null || true
echo "peak db connections: $(sort -n "$out-conns.txt" | tail -1)"
.venv/bin/python loadtests/h02/seed.py verify "$out-profile.json" "$out-results.json"
