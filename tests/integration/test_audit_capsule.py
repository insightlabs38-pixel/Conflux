import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from accounts.models import User
from evaluations.models import EvaluationPlan
from integrations.demo_scenarios import generate_demo_event
from integrations.signed_archive import verify_signed_archive
from presentation.keys import public_key_pem
from projects.models import Project
from test_sponsor_portal import client_for

pytestmark = pytest.mark.django_db
SCRIPT = Path(__file__).resolve().parents[2] / "scripts/verify_capsule.py"


def world(seed=95, participants=6, judges=3):
    event = generate_demo_event(seed=seed, participants=participants, judges=judges)
    plan = EvaluationPlan.objects.get(stage__event=event)
    prefix = f"demo-hackathon-{seed}-"
    users = {
        "org": User.objects.get(username=prefix + "organizer"),
        "judge": User.objects.get(username=prefix + "judge-01"),
        "part": User.objects.get(username=prefix + "participant-01"),
        "other": User.objects.get(username=prefix + "participant-02"),
    }
    return event, plan, users


def plan_url(event, plan, suffix):
    return (
        f"/api/v1/workspaces/{event.workspace.public_id}/events/{event.public_id}/stages/"
        f"{plan.stage.public_id}/evaluation-plans/{plan.public_id}/{suffix}"
    )


def run_script(tmp_path, envelope, *extra):
    path = tmp_path / "capsule.json"
    path.write_text(json.dumps(envelope))
    key = tmp_path / "key.pem"
    key.write_text(public_key_pem())
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--public-key", str(key), *extra],
        capture_output=True,
        text=True,
    )


def test_capsule_is_signed_pseudonymous_and_verifies_offline(tmp_path):
    event, plan, users = world()
    response = client_for(users["org"]).get(plan_url(event, plan, "audit-capsule/"))
    assert response.status_code == 200
    envelope = response.json()
    verify_signed_archive(envelope)
    capsule = envelope["archive"]
    text = json.dumps(capsule)
    assert all(u.username not in text for u in User.objects.filter(username__contains="judge"))
    assert {b["judge"] for b in capsule["ballots"]} == {"J01", "J02", "J03"}
    assert len(capsule["ballots"]) == 18 and capsule["replay"]["verdict"] == "verified"
    assert [r["rank"] for r in capsule["results"]] == list(range(1, 7))
    assert {a["name"] for a in capsule["awards"]} >= {"Grand Prize"}
    done = run_script(tmp_path, envelope)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "VERIFIED" in done.stdout and "FAIL" not in done.stdout


@pytest.mark.parametrize(
    "tamper",
    ["score", "score_and_checksums", "result_order", "wrong_key", "no_key"],
)
def test_any_alteration_of_a_capsule_is_caught(tmp_path, tamper):
    event, plan, users = world(seed=96)
    envelope = client_for(users["org"]).get(plan_url(event, plan, "audit-capsule/")).json()
    forged = copy.deepcopy(envelope)
    extra = []
    if tamper == "score":
        forged["archive"]["ballots"][0]["weighted_score"] += 1
    elif tamper == "score_and_checksums":
        from integrations.signed_archive import _sha256

        forged["archive"]["ballots"][0]["weighted_score"] += 1
        forged["manifest"]["archive_sha256"] = _sha256(forged["archive"])
        forged["manifest"]["checksums"] = {k: _sha256(v) for k, v in forged["archive"].items()}
    elif tamper == "result_order":
        forged["archive"]["results"][0], forged["archive"]["results"][1] = (
            forged["archive"]["results"][1],
            forged["archive"]["results"][0],
        )
    elif tamper == "wrong_key":
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        other = (
            Ed25519PrivateKey.generate()
            .public_key()
            .public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
        (tmp_path / "other.pem").write_bytes(other)
        path = tmp_path / "capsule.json"
        path.write_text(json.dumps(envelope))
        done = subprocess.run(
            [sys.executable, str(SCRIPT), str(path), "--public-key", str(tmp_path / "other.pem")],
            capture_output=True,
            text=True,
        )
        assert done.returncode == 1 and "FAIL  signing_key" in done.stdout
        return
    elif tamper == "no_key":
        path = tmp_path / "capsule.json"
        path.write_text(json.dumps(envelope))
        done = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True
        )
        assert done.returncode == 1 and "authenticity not established" in done.stdout
        return
    done = run_script(tmp_path, forged, *extra)
    assert done.returncode == 1 and "NOT VERIFIED" in done.stdout


def test_capsule_needs_published_results_and_an_organizer():
    event, plan, users = world(seed=97, participants=4, judges=2)
    for name in ("judge", "part"):
        assert (
            client_for(users[name]).get(plan_url(event, plan, "audit-capsule/")).status_code == 403
        )
    EvaluationPlan.objects.filter(pk=plan.pk).update(published_normalization_run=None)
    assert client_for(users["org"]).get(plan_url(event, plan, "audit-capsule/")).status_code == 404


def test_explanation_is_deterministic_and_organizers_see_more_than_participants():
    event, plan, users = world(seed=98)
    project = Project.objects.get(event=event, created_by=users["part"])
    org = client_for(users["org"])
    first = org.get(plan_url(event, plan, f"explain/{project.public_id}/")).json()
    assert org.get(plan_url(event, plan, f"explain/{project.public_id}/")).json() == first
    assert first["explanation"][0].startswith(f"{project.name} ranked ")
    assert first["ballots_counted"] == 3 and len(first["judges"]) == 3 and "neighbours" in first
    assert {c["criterion"] for c in first["criteria"]} == {
        "Impact",
        "Technical depth",
        "Design and clarity",
    }
    mine = client_for(users["part"]).get(plan_url(event, plan, f"explain/{project.public_id}/"))
    assert mine.status_code == 200
    body = mine.json()
    assert "judges" not in body and "neighbours" not in body
    assert body["rank"] == first["rank"] and body["final_score"] == first["final_score"]
    others = [p for p in event.projects.all() if p != project]
    assert all(o.name not in json.dumps(body) for o in others)
    assert (
        client_for(users["other"])
        .get(plan_url(event, plan, f"explain/{project.public_id}/"))
        .status_code
        == 404
    )
    assert (
        client_for(users["judge"])
        .get(plan_url(event, plan, f"explain/{project.public_id}/"))
        .status_code
        == 403
    )


def test_participants_wait_for_visibility_and_published_results():
    event, plan, users = world(seed=99, participants=4, judges=2)
    project = Project.objects.get(event=event, created_by=users["part"])
    EvaluationPlan.objects.filter(pk=plan.pk).update(results_visible_to_participants=False)
    hidden = client_for(users["part"]).get(plan_url(event, plan, f"explain/{project.public_id}/"))
    assert hidden.status_code == 403
    unknown = "00000000-0000-4000-8000-000000000000"
    assert (
        client_for(users["org"]).get(plan_url(event, plan, f"explain/{unknown}/")).status_code
        == 404
    )
