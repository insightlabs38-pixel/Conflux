"""FX-004: the vendored checker must stay untampered, and the committed
acceptance-report.txt must actually say what it claims.
"""

import hashlib
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# scripts/vendor/dogfood_run.py is supposed to be a byte-identical copy of
# the official spec's run.py — never hand-edited. This pins that promise:
# a deliberate upstream update should update the hash in the same commit,
# but an accidental edit shouldn't sneak past review.
VENDORED_CHECKER_SHA256 = "aa98963841bc8e18e8e5d76f0499697c093dd3c0055f9d73a459f592f4dcf09d"


def test_vendored_checker_is_untampered():
    checker = REPO_ROOT / "scripts" / "vendor" / "dogfood_run.py"
    digest = hashlib.sha256(checker.read_bytes()).hexdigest()
    assert digest == VENDORED_CHECKER_SHA256


def test_committed_report_is_all_pass_and_matches_claimed_tiers():
    with open(REPO_ROOT / ".dogfood.toml", "rb") as f:
        claimed = tomllib.load(f)["tiers"]["claimed"]

    lines = (REPO_ROOT / "acceptance-report.txt").read_text().splitlines()
    check_lines = [line for line in lines if line[:2] in ("T1", "T2", "T3", "T4")]
    assert len(check_lines) == 7, "official checker must retain its seven T1/T2 assertions"
    assert {line[:2] for line in check_lines} == {"T1", "T2"}
    assert all(line.rstrip().endswith("PASS") for line in check_lines), (
        "a stale or failing check is committed to acceptance-report.txt"
    )

    summary = next(line for line in lines if line.startswith("claimed "))
    assert claimed == ["T1", "T2", "T3", "T4"]
    assert summary == f"claimed {' '.join(claimed)}, verified T1 T2"
    assert "note: claimed but not verified: T3 T4" in lines
    readme = (REPO_ROOT / "README.md").read_text()
    assert "T3/T4 are evaluated manually" in readme
    assert "dogfood-extended.txt" in readme
