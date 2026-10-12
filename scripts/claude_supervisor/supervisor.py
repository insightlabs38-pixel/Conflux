#!/usr/bin/env python3
"""Claude-only supervisor for the Conflux Product Depth v3 continuous agent.

Schedule (America/New_York): first window starts 2026-09-30 02:50 EDT and a new
window opens every 5 hours after that until 2026-10-01 13:30 EDT. In each window
a headless Claude session runs the continuous prompt until it hits the usage
limit; the supervisor then sleeps until the next window boundary instead of
exiting. Session output is logged; a stop file ends the supervisor cleanly.

Usage:
  python3 scripts/claude_supervisor/supervisor.py            # run in foreground
  python3 scripts/claude_supervisor/supervisor.py --duration-hours 25
  nohup python3 scripts/claude_supervisor/supervisor.py &    # or detached
  touch .claude-supervisor/stop                              # stop (kills session)
  python3 scripts/claude_supervisor/supervisor.py --dry-run  # print schedule/command
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".claude-supervisor"
PROMPT = ROOT / "docs/product-depth-v3/prompts/CONTINUOUS_SINGLE_AGENT_PROMPT.md"

MODEL = "claude-sonnet-5-5"
EFFORT = "high"
WINDOW = timedelta(hours=5)
FIRST_START = datetime(2026, 9, 30, 2, 50, tzinfo=TZ)
HARD_END = datetime(2026, 10, 1, 13, 30, tzinfo=TZ)
STOP_STARTING_AT: datetime | None = None

RAPID_EXIT_SECONDS = 120   # a session shorter than this counts as a rapid exit
RAPID_EXIT_LIMIT = 3       # this many in a row -> wait for the next window
RETRY_DELAY = 60

LIMIT_RE = re.compile(
    r"usage limit|limit reached|rate[ _-]?limit|hit your limit|limit will reset|"
    r"quota|too many requests|overloaded_error|\b429\b|resets? (?:at|in) ",
    re.IGNORECASE,
)

QUESTIONS_FILE = STATE / "QUESTIONS.md"
HEADLESS_ADDENDUM = f"""\
You are running headless and unattended under a supervisor. No human is watching \
and nobody can answer prompts. Never ask the user a question and never wait for \
input: an interactive prompt would crash the session. Do not use the AskUserQuestion tool.
When you would normally ask a question or need a decision, instead append an entry to \
{QUESTIONS_FILE} (UTC timestamp, task id, the question, options considered, and the \
conservative default you chose), then follow the prompt's own escalation and stop \
conditions: proceed on the safest default that cannot cause irreversible harm, or \
select other eligible work. If usage limits interrupt you, that is expected; the \
supervisor will restart you later, so keep repository state, receipts and checkpoints \
current at all times."""


def log(msg: str) -> None:
    line = f"{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S %Z')} {msg}"
    print(line, flush=True)
    with (STATE / "supervisor.log").open("a") as fh:
        fh.write(line + "\n")


def slots() -> list[datetime]:
    out, t = [], FIRST_START
    while t < HARD_END and (STOP_STARTING_AT is None or t < STOP_STARTING_AT):
        out.append(t)
        t += WINDOW
    return out


def next_slot_after(now: datetime) -> datetime | None:
    return next((s for s in slots() if s > now), None)


def sleep_until(target: datetime, stop_file: Path) -> bool:
    """Sleep until target; return False if the stop file appeared."""
    while True:
        if stop_file.exists():
            return False
        left = (target - datetime.now(TZ)).total_seconds()
        if left <= 0:
            return True
        time.sleep(min(left, 30))


def build_cmd() -> list[str]:
    return [
        "claude", "-p",
        "--model", MODEL,
        "--effort", EFFORT,
        "--dangerously-skip-permissions",
        "--disallowedTools", "AskUserQuestion",
        "--append-system-prompt", HEADLESS_ADDENDUM,
        "--output-format", "stream-json",
        "--verbose",
    ]


def run_session(stop_file: Path) -> tuple[str, float]:
    """Run one headless session. Returns (outcome, seconds); outcome is one of
    limit | clean | error | stopped | deadline."""
    ts = datetime.now(TZ).strftime("%Y%m%dT%H%M%S")
    out_path = STATE / "sessions" / f"{ts}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    limit_seen = False
    result_error = False
    with PROMPT.open("rb") as prompt, out_path.open("wb") as raw:
        proc = subprocess.Popen(
            build_cmd(), cwd=ROOT, stdin=prompt, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        log(f"session started pid={proc.pid} log={out_path.relative_to(ROOT)}")

        def kill() -> None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=30)
            except Exception:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    pass

        import selectors
        sel = selectors.DefaultSelector()
        sel.register(proc.stdout, selectors.EVENT_READ)
        buf = b""
        outcome = None
        while outcome is None:
            if stop_file.exists():
                kill(); outcome = "stopped"; break
            if datetime.now(TZ) >= HARD_END:
                kill(); outcome = "deadline"; break
            if sel.select(timeout=5):
                chunk = os.read(proc.stdout.fileno(), 65536)
                if chunk:
                    raw.write(chunk); raw.flush()
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    for ln in lines:
                        lo, re_ = scan_line(ln)
                        limit_seen |= lo
                        result_error |= re_
                    continue
            if proc.poll() is not None:
                break
        if outcome is None:
            for ln in buf.split(b"\n"):
                lo, re_ = scan_line(ln)
                limit_seen |= lo
                result_error |= re_
            rc = proc.wait()
            if limit_seen:
                outcome = "limit"
            elif rc == 0 and not result_error:
                outcome = "clean"
            else:
                outcome = "error"
            log(f"session exited rc={rc} outcome={outcome}")
    return outcome, time.time() - start


def scan_line(line: bytes) -> tuple[bool, bool]:
    """Return (limit_hit, error_result) for one output line."""
    text = line.decode("utf-8", "replace").strip()
    if not text:
        return False, False
    try:
        ev = json.loads(text)
    except ValueError:
        return bool(LIMIT_RE.search(text)), False  # plain-text CLI error
    if not isinstance(ev, dict):
        return False, False
    kind = ev.get("type")
    if kind == "result" and ev.get("is_error"):
        blob = json.dumps(ev.get("result", "")) + str(ev.get("subtype", ""))
        return bool(LIMIT_RE.search(blob)), True
    if kind == "rate_limit_event":
        info = ev.get("rate_limit_info") or {}
        return info.get("status") == "rejected", False
    if kind == "assistant" and ev.get("error"):
        return bool(LIMIT_RE.search(str(ev.get("error")) + text[:2000])), False
    return False, False


def main() -> int:
    global FIRST_START, HARD_END, STOP_STARTING_AT
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--duration-hours",
        type=float,
        help="start now and stop after this many hours, opening windows every five hours",
    )
    ap.add_argument(
        "--hard-end",
        help="local America/New_York deadline (ISO local datetime); terminate active session then",
    )
    ap.add_argument(
        "--stop-starting-at",
        help="local America/New_York cutoff (ISO local datetime); do not launch a window then or later",
    )
    ap.add_argument(
        "--start-now",
        action="store_true",
        help="anchor the first five-hour window at the current time",
    )
    args = ap.parse_args()

    if args.duration_hours is not None:
        if args.duration_hours <= 0:
            ap.error("--duration-hours must be positive")
        FIRST_START = datetime.now(TZ)
        HARD_END = FIRST_START + timedelta(hours=args.duration_hours)
    if args.start_now:
        FIRST_START = datetime.now(TZ)
    if args.hard_end:
        HARD_END = datetime.fromisoformat(args.hard_end).replace(tzinfo=TZ)
    if args.stop_starting_at:
        STOP_STARTING_AT = datetime.fromisoformat(args.stop_starting_at).replace(tzinfo=TZ)

    if args.dry_run:
        for s in slots():
            print("window start:", s.strftime("%a %Y-%m-%d %H:%M %Z"))
        print("hard end:    ", HARD_END.strftime("%a %Y-%m-%d %H:%M %Z"))
        print("prompt:      ", PROMPT, "(exists)" if PROMPT.exists() else "(MISSING)")
        print("command:     ", " ".join(build_cmd()[:12]), "... < prompt")
        return 0

    STATE.mkdir(exist_ok=True)
    (STATE / ".gitignore").write_text("*\n")
    lock = (STATE / "lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another supervisor is already running", file=sys.stderr)
        return 1
    stop_file = STATE / "stop"
    if not PROMPT.exists():
        print(f"missing prompt: {PROMPT}", file=sys.stderr)
        return 1
    if stop_file.exists():
        stop_file.unlink()

    log(f"supervisor start pid={os.getpid()} model={MODEL} effort={EFFORT} "
        f"end={HARD_END.isoformat()}")
    # Wait for the first window if we are early.
    if datetime.now(TZ) < FIRST_START:
        log(f"waiting for first window at {FIRST_START.isoformat()}")
        if not sleep_until(FIRST_START, stop_file):
            log("stop file seen; exiting"); return 0

    rapid = 0
    while True:
        now = datetime.now(TZ)
        if now >= HARD_END:
            log("hard end reached; exiting"); return 0
        if stop_file.exists():
            log("stop file seen; exiting"); return 0

        outcome, secs = run_session(stop_file)
        if outcome in ("stopped", "deadline"):
            log(f"{outcome}; exiting"); return 0

        rapid = rapid + 1 if secs < RAPID_EXIT_SECONDS and outcome != "limit" else 0
        if outcome == "limit" or rapid >= RAPID_EXIT_LIMIT:
            nxt = next_slot_after(datetime.now(TZ))
            if nxt is None:
                log("no further windows before hard end; exiting"); return 0
            why = "usage limit" if outcome == "limit" else f"{rapid} rapid exits"
            log(f"{why}; sleeping until next window {nxt.isoformat()}")
            rapid = 0
            if not sleep_until(nxt, stop_file):
                log("stop file seen; exiting"); return 0
        else:
            log(f"outcome={outcome}; restarting in {RETRY_DELAY}s")
            if not sleep_until(datetime.now(TZ) + timedelta(seconds=RETRY_DELAY), stop_file):
                log("stop file seen; exiting"); return 0


if __name__ == "__main__":
    sys.exit(main())
