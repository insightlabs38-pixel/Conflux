#!/usr/bin/env python3
"""Verify a Conflux judging audit capsule offline.

    verify_capsule.py capsule.json --public-key record-key.pem

Checks the archive checksums and Ed25519 signature, recomputes every ballot's
weighted score from its responses and the published rubric, re-solves the
normalization from the capsule's own ballots, and confirms the published
ranking and award evidence agree. Needs only Python, `cryptography` and this
repository's pure `evaluations/normalization.py`; no server or database.
Exit status 0 means verified.
"""

import argparse
import base64
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-6


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_solver():
    path = ROOT / "src/api/evaluations/normalization.py"
    spec = importlib.util.spec_from_file_location("capsule_normalization", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolves annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def close(a, b):
    return a == b or (a is not None and b is not None and math.isclose(a, b, abs_tol=TOLERANCE))


def weighted(criteria, scores):
    used = [c for c in criteria if c["id"] in scores]
    total = sum(c["weight"] for c in used)
    return sum(c["weight"] * scores[c["id"]] for c in used) / total if total else None


def verify(envelope, public_key_pem=None):
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    capsule = envelope.get("archive")
    manifest = envelope.get("manifest")
    if not isinstance(capsule, dict) or not isinstance(manifest, dict):
        return [{"name": "format", "ok": False, "detail": "Not a signed capsule envelope."}]
    check("format", capsule.get("kind") == "judging-audit-capsule")
    check("archive_checksum", manifest.get("archive_sha256") == sha256(capsule))
    sections = manifest.get("checksums", {})
    check(
        "section_checksums",
        set(sections) == set(capsule) and all(sha256(capsule[k]) == v for k, v in sections.items()),
    )
    if public_key_pem:
        key = serialization.load_pem_public_key(public_key_pem.encode())
        raw = key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        check("signing_key", hashlib.sha256(raw).hexdigest() == manifest.get("signing_key_sha256"))
        try:
            signature = base64.urlsafe_b64decode(envelope["signature"])
            key.verify(signature, canonical(manifest))
            check("signature", True)
        except (InvalidSignature, KeyError, ValueError):
            check("signature", False, "Signature does not match the manifest.")
    else:
        check("signature", False, "No public key supplied; authenticity not established.")

    criteria = {}
    for version in capsule["plan"]["rubric_versions"]:
        criteria[version["number"]] = version["criteria"]
    latest = criteria[max(criteria)]
    ballots = capsule["ballots"]
    bad = []
    for ballot in ballots:
        scores = {r["criterion_id"]: r["score"] for r in ballot["responses"]}
        rubric = [{"id": r["criterion_id"], "weight": r["weight"]} for r in ballot["responses"]]
        expected = weighted(rubric, scores)
        if not close(expected, ballot["weighted_score"]):
            bad.append(ballot["ballot"])
    check("ballot_scores", not bad, f"recomputed differently: {bad}" if bad else "")
    check("rubric_present", bool(latest))

    solver = load_solver()
    run = capsule["run"]
    observations = [(b["judge"], b["project"], b["weighted_score"]) for b in ballots]
    result = solver.estimate_judge_effects(observations, ridge_lambda=run["ridge_lambda"])
    check("grand_mean", close(result.grand_mean, run["grand_mean"]))
    bad = [
        j
        for j, effect in run["judge_effects"].items()
        if not close(effect, result.judge_effects.get(j))
    ]
    check("judge_effects", not bad, f"differ for {bad}" if bad else "")
    adjusted_bad = [
        b["ballot"]
        for b in ballots
        if not close(
            b["adjusted_score"], solver.adjusted_score(result, b["judge"], b["weighted_score"])
        )
    ]
    check("adjusted_scores", not adjusted_bad)
    finals = {p: solver.project_final_score(result, p) for p in {b["project"] for b in ballots}}
    raws = {p: solver.raw_mean_score(observations, p) for p in finals}
    results = capsule["results"]
    check(
        "result_scores",
        all(
            close(r["final"], finals.get(r["project"])) and close(r["raw"], raws.get(r["project"]))
            for r in results
        ),
    )
    ordered = all(
        results[i]["final"] > results[i + 1]["final"]
        or (
            results[i]["final"] == results[i + 1]["final"]
            and (results[i]["tie_break"] or 0) <= (results[i + 1]["tie_break"] or 0)
        )
        for i in range(len(results) - 1)
    )
    ranks = [r["rank"] for r in results]
    check("ranking_order", ordered and ranks == list(range(1, len(results) + 1)))
    unexplained = [
        f"{award['name']}: {winner['project']}"
        for award in capsule["awards"]
        for winner in award["winners"]
        if (winner["evidence"].get("rank") or 0) > award["winner_count"]
        and not winner["override_reason"]
    ]
    check("award_evidence", not unexplained, str(unexplained) if unexplained else "")
    replayed = capsule["replay"]["verdict"] == "verified"
    check(
        "replay_recorded", replayed, "" if replayed else "The server's replay reported a mismatch."
    )
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("capsule")
    parser.add_argument("--public-key", help="PEM public key published by the issuing server")
    args = parser.parse_args(argv)
    envelope = json.loads(Path(args.capsule).read_text(encoding="utf-8"))
    pem = Path(args.public_key).read_text() if args.public_key else None
    checks = verify(envelope, pem)
    for c in checks:
        print(
            f"{'PASS' if c['ok'] else 'FAIL'}  {c['name']}"
            + (f"  {c['detail']}" if c["detail"] else "")
        )
    verified = all(c["ok"] for c in checks)
    print("VERIFIED" if verified else "NOT VERIFIED")
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())
