"""Create a disposable acceptance-identity lifecycle on a seeded test stack."""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

BASE = os.environ.get("DEMO_BASE_URL", "http://localhost:8080/api/v1").rstrip("/")
COOKIES = {
    "organizer": "acceptance-organizer",
    "participant": "acceptance-participant",
    "judge": "acceptance-judge-a",
}


def call(method, path, actor=None, data=None, expected=200):
    headers = {}
    if actor:
        headers["Cookie"] = f"session={COOKIES[actor]}"
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    request = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            status = response.status
            result = json.load(response)
    except urllib.error.HTTPError as error:
        status = error.code
        result = error.read().decode()
    if status != expected:
        sys.exit(f"{method} {path}: expected {expected}, got {status}: {result}")
    return result


workspace = call("GET", "/accounts/me/", "organizer")["memberships"][0]["workspace"]
root = f"/workspaces/{workspace}"
now = datetime.now(UTC)
name = "Release rehearsal " + now.strftime("%Y%m%d%H%M%S")
event = call(
    "POST",
    root + "/events/",
    "organizer",
    {
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "starts_at": (now - timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(days=1)).isoformat(),
        "is_public": True,
    },
    201,
)
event_id = event["public_id"]
root += f"/events/{event_id}"
stage = call("POST", root + "/stages/", "organizer", {"name": "Finals", "is_initial": True}, 201)
stage_id = stage["public_id"]
call("POST", root + "/status/", "organizer", {"status": "open"})
project = call("POST", root + "/projects/", "participant", {"name": "Rehearsal project"}, 201)
project_id = project["public_id"]
submission = root + f"/projects/{project_id}/submissions/{stage_id}/"
draft = call(
    "PUT",
    submission,
    "participant",
    {"draft_payload": {"notes": "Ready for judging"}, "draft_revision": 0},
)
assert draft["draft_revision"] == 1
receipt = call("POST", submission + "finalize/", "participant", {"draft_revision": 1}, 201)[
    "receipt"
]
plan = call(
    "POST",
    root + f"/stages/{stage_id}/evaluation-plans/",
    "organizer",
    {
        "name": "Panel",
        "results_visible_to_participants": True,
        "draft_criteria": [
            {"id": "impact", "name": "Impact", "weight": 1, "min_score": 0, "max_score": 10}
        ],
    },
    201,
)
plan_root = root + f"/stages/{stage_id}/evaluation-plans/{plan['public_id']}/"
call("POST", plan_root + "publish-rubric/", "organizer", {}, 201)
ballot = call(
    "POST",
    plan_root + "ballots/",
    "judge",
    {"project": project_id, "responses": [{"criterion_id": "impact", "score": 8}]},
    201,
)
run = call("POST", plan_root + "normalization-runs/", "organizer", {}, 201)
call("POST", plan_root + "publish-results/", "organizer", {"normalization_run": run["public_id"]})
award = call(
    "POST",
    root + "/awards/",
    "organizer",
    {
        "name": "Winner",
        "selection_source": "evaluation",
        "evaluation_plan": plan["public_id"],
        "winner_count": 1,
    },
    201,
)
award_root = root + f"/awards/{award['public_id']}/"
call("POST", award_root + "winners/", "organizer", {"project": project_id}, 201)
call("POST", award_root + "publish/", "organizer", {})
public = call("GET", f"/events/{event_id}/awards/")
assert any(item["public_id"] == award["public_id"] for item in public)
print(
    json.dumps(
        {
            "event": event_id,
            "project": project_id,
            "receipt": receipt,
            "ballot": ballot["public_id"],
            "award": award["public_id"],
            "public_awards": len(public),
        }
    )
)
