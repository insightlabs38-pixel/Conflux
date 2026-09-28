#!/usr/bin/env python3
"""Keep one sequential DOGFOODHACK coding agent running."""
from __future__ import annotations

import argparse
import fcntl
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

POLL_SECONDS = 30.0
PROVIDERS = ("claude", "codex")
QUOTA_RE = re.compile(
    r"(?:rate limit|usage limit|quota|capacity|too many requests|limit reached|"
    r"out of (?:credits|usage)|overloaded)",
    re.I,
)

class Supervisor:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()
        self.state = self.repo / ".dogfood"
        self.state.mkdir(exist_ok=True)
        self.log_path = self.state / "master.log"
        self.pid_path = self.state / "master.pid"
        self.next_path = self.state / "master.next"
        self.stop_path = self.state / "master.stop"
        self.complete_path = self.state / "master.complete"
        self.stop_requested = False

    def log(self, message: str) -> None:
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {message}\n"
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(line)
        print(line, end="", flush=True)

    def acquire_lock(self) -> bool:
        self.lock_handle = (self.state / "master.lock").open("a+")
        try:
            fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock_handle.close()
            return False
        return True

    def existing_child(self) -> int | None:
        try:
            pid = int(self.pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
        except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
            return None
        # A live PID file is treated as occupied even if proc inspection is
        # unavailable or the PID has been reused. Failing closed is safer than
        # knowingly creating a second repository writer.
        return pid

    def command(self, provider: str) -> list[str]:
        override = os.environ.get(f"DOGFOOD_MASTER_{provider.upper()}_COMMAND")
        if override:
            return shlex.split(override)
        if provider == "codex":
            return [
                "codex", "exec", "--yolo", "--model", "gpt-6-sol", "--config",
                'model_reasoning_effort="medium"', "--cd", str(self.repo), "-",
            ]
        return [
            "claude", "--print", "--model", "claude-sonnet-5", "--effort", "high",
            "--permission-mode", "bypassPermissions", "--dangerously-skip-permissions",
            "--no-session-persistence", "--add-dir", str(self.repo),
        ]

    def next_first(self) -> str:
        value = (
            self.next_path.read_text(encoding="utf-8").strip()
            if self.next_path.exists()
            else "claude"
        )
        return value if value in PROVIDERS else "claude"

    def stream(self, pipe, output: list[str]) -> None:
        for raw in iter(pipe.readline, b""):
            text = raw.decode(errors="replace")
            output.append(text)
            sys.stdout.write(text)
            sys.stdout.flush()
        pipe.close()

    def run_provider(self, provider: str) -> str:
        prompt = (self.repo / "master" / "worker_prompt.md").read_bytes()
        prompt += b"\n\n" + (self.repo / "master" / "autonomous_system_prompt.md").read_bytes()
        try:
            process = subprocess.Popen(
                self.command(provider), cwd=self.repo, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
            )
        except (OSError, ValueError) as exc:
            self.log(f"provider={provider} launch-failure={exc}")
            return "launch-failure"
        self.pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
        self.log(f"provider={provider} pid={process.pid} start")
        output: list[str] = []
        reader = threading.Thread(target=self.stream, args=(process.stdout, output), daemon=True)
        reader.start()
        try:
            process.stdin.write(prompt)
            process.stdin.close()
        except BrokenPipeError:
            process.stdin.close()
        while process.poll() is None:
            if self.stop_path.exists() and not self.stop_requested:
                self.stop_requested = True
                self.log("stop-requested; current agent continues")
            time.sleep(0.2)
        reader.join()
        self.pid_path.unlink(missing_ok=True)
        code = process.returncode
        text = "".join(output)
        if code != 0 and QUOTA_RE.search(text):
            self.log(f"provider={provider} exit={code} recognized-unavailable")
            return "unavailable"
        if code == 0:
            self.log(f"provider={provider} exit=0")
            return "normal"
        self.log(f"provider={provider} exit={code} unknown-failure")
        return "failure"

    def wait_for_next_cycle(self) -> bool:
        seconds = float(os.environ.get("DOGFOOD_MASTER_POLL_SECONDS", POLL_SECONDS))
        deadline = time.monotonic() + seconds
        self.log(f"next-poll seconds={seconds:g}")
        while time.monotonic() < deadline:
            if self.stop_path.exists() or self.stop_requested or self.complete_path.exists():
                return False
            time.sleep(min(0.2, max(0.0, deadline - time.monotonic())))
        return True

    def wait_until_start(self, value: str) -> bool:
        if value in ("now", "none"):
            return True
        try:
            hour, minute = (int(part) for part in value.split(":", 1))
            now = datetime.now(UTC)
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                return True
        except (TypeError, ValueError):
            self.log(f"invalid-start-at={value}; starting now")
            return True
        self.log(f"waiting-until={target.isoformat()} UTC")
        while datetime.now(UTC) < target:
            if self.stop_path.exists() or self.stop_requested or self.complete_path.exists():
                return False
            time.sleep(min(0.2, (target - datetime.now(UTC)).total_seconds()))
        self.log("scheduled-start reached")
        return True

    def run(self, start_at: str) -> int:
        if not self.acquire_lock():
            print("master: another supervisor is already running", file=sys.stderr)
            return 2
        child = self.existing_child()
        if child is not None:
            self.log(f"active-child pid={child}; refusing to start another")
            return 2
        if self.complete_path.exists():
            self.log("complete-signal present; exiting")
            return 0
        if self.stop_path.exists():
            self.log("stop-signal present; exiting")
            return 0
        signal.signal(signal.SIGINT, self.request_stop)
        signal.signal(signal.SIGTERM, self.request_stop)
        if not self.wait_until_start(start_at):
            self.log("stopped cleanly")
            return 0
        while not self.stop_requested and not self.stop_path.exists():
            if self.complete_path.exists():
                self.log("complete-signal present; exiting")
                return 0
            first = self.next_first()
            second = "claude" if first == "codex" else "codex"
            next_first = "claude\n" if first == "codex" else "codex\n"
            self.next_path.write_text(next_first, encoding="utf-8")
            result = self.run_provider(first)
            if result == "unavailable" and not self.stop_requested and not self.stop_path.exists():
                self.run_provider(second)
            if self.stop_requested or self.stop_path.exists():
                break
            if self.complete_path.exists():
                self.log("complete-signal present; exiting")
                return 0
            if not self.wait_for_next_cycle():
                break
        self.log("stopped cleanly")
        return 0

    def request_stop(self, signum, _frame) -> None:
        if not self.stop_requested:
            self.stop_requested = True
            self.log(f"stop-requested signal={signal.Signals(signum).name}")

def stop(repo: Path) -> int:
    state = repo.resolve() / ".dogfood"
    state.mkdir(exist_ok=True)
    (state / "master.stop").touch()
    print("master: stop requested; any current agent is left running")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "stop", "resume"), nargs="?", default="run")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--start-at", default=os.environ.get("DOGFOOD_MASTER_START_AT", "10:14"),
        metavar="HH:MM|now",
    )
    args = parser.parse_args()
    if args.action == "stop":
        return stop(args.repo)
    if args.action == "resume":
        (args.repo.resolve() / ".dogfood" / "master.stop").unlink(missing_ok=True)
    return Supervisor(args.repo).run(args.start_at)

if __name__ == "__main__":
    raise SystemExit(main())
