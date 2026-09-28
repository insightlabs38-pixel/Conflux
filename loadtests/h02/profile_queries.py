"""Per-endpoint query counts and slowest SQL against the seeded H02 database.

    DATABASE_URL=... python loadtests/h02/profile_queries.py PROFILE.json
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import CaptureQueriesContext  # noqa: E402

P = json.load(open(sys.argv[1]))
W, E, S, PL = P["workspace"], P["event"], P["stage"], P["plan"]
B = f"/api/v1/workspaces/{W}/events/{E}"
PLAN = f"{B}/stages/{S}/evaluation-plans/{PL}"
part = P["participants"][P["finalized"] + 5]
proj = P["finalized_projects"][0]
cases = [
    ("health", None, "GET", "/api/v1/health/", None),
    ("gallery", None, "GET", f"/api/v1/events/{E}/gallery/", None),
    ("search", None, "GET", f"/api/v1/events/{E}/search/?q=atlas", None),
    ("sub_list", part["token"], "GET", f"{B}/projects/{part['project']}/submissions/", None),
    ("autosave", part["token"], "PUT", f"{B}/projects/{part['project']}/submissions/{S}/",
     {"draft_payload": {"notes": "x"}, "draft_revision": 0}),
    ("finalize", part["token"], "POST", f"{B}/projects/{part['project']}/submissions/{S}/finalize/",
     {"draft_revision": 1}),
    ("judge_events", P["judges"][1], "GET", f"/api/v1/workspaces/{W}/judge-events/", None),
    ("ballot_list", P["judges"][1], "GET", f"{PLAN}/ballots/", None),
    ("ballot_draft_put", P["judges"][1], "PUT", f"{PLAN}/ballots/{proj}/draft/",
     {"responses": {"impact": 3}}),
    ("ballot_submit", P["judges"][1], "POST", f"{PLAN}/ballots/",
     {"project": proj, "responses": [{"criterion_id": "impact", "score": 5},
                                      {"criterion_id": "polish", "score": 5}]}),
    ("progress", P["organizer"], "GET", f"{PLAN}/progress/", None),
    ("vote", part["token"], "POST", f"{B}/voting/votes/", {"project": proj}),
    ("vote_results", P["organizer"], "GET", f"{B}/voting/results/", None),
]
for name, tok, method, path, body in cases:
    c = Client()
    if tok:
        c.cookies["session"] = tok
    kw = {"HTTP_HOST": "localhost", "content_type": "application/json"}
    if body is not None:
        kw["data"] = json.dumps(body)
    with CaptureQueriesContext(connection) as ctx:
        t = time.perf_counter()
        r = getattr(c, method.lower())(path, **kw)
        ms = (time.perf_counter() - t) * 1000
    sql = sorted(ctx.captured_queries, key=lambda q: -float(q["time"]))
    print(f"{name:18} {r.status_code} {len(ctx):4} queries  {ms:7.1f} ms  "
          f"db={sum(float(q['time']) for q in ctx.captured_queries) * 1000:6.1f} ms  "
          f"bytes={len(r.content)}")
    if len(ctx) > 25 or "-v" in sys.argv:
        for q in sql[:2]:
            print("   ", q["time"], q["sql"][:170])
