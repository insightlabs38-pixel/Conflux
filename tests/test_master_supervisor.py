from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

ROOT = Path(__file__).parents[1]
MASTER = ROOT / "master" / "master.py"


def make_repo(tmp: Path) -> Path:
    (tmp / "master").mkdir()
    (tmp / "master" / "worker_prompt.md").write_text("prompt\n")
    (tmp / "master" / "autonomous_system_prompt.md").write_text("autonomous\n")
    return tmp


def fake_provider(tmp: Path) -> Path:
    path = tmp / "fake-provider.py"
    path.write_text(
        textwrap.dedent("""
        import os
        from pathlib import Path
        import sys
        import time
        provider = sys.argv[1]
        log = Path(os.environ["FAKE_LOG"])
        with log.open("a") as f:
            f.write(provider + "\\n")
        quota_provider = os.environ.get("FAKE_QUOTA_PROVIDER", "codex")
        if provider == quota_provider and os.environ.get("FAKE_QUOTA") == "1":
            print("usage limit reached", flush=True)
            raise SystemExit(1)
        time.sleep(float(os.environ.get("FAKE_SLEEP", "0")))
        if os.environ.get("FAKE_COMPLETE") == "1":
            Path(os.environ["FAKE_REPO"], ".dogfood", "master.complete").touch()
    """)
    )
    return path


def run_master(repo: Path, fake: Path, log: Path, **extra: str) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(
        {
            "DOGFOOD_MASTER_START_AT": "now",
            "DOGFOOD_MASTER_POLL_SECONDS": "0.05",
            "DOGFOOD_MASTER_CODEX_COMMAND": f"{sys.executable} {fake} codex",
            "DOGFOOD_MASTER_CLAUDE_COMMAND": f"{sys.executable} {fake} claude",
            "FAKE_LOG": str(log),
            "FAKE_REPO": str(repo),
            **extra,
        }
    )
    return subprocess.Popen(
        [sys.executable, str(MASTER), "--repo", str(repo)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_for(path: Path, timeout: float = 3) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert path.exists(), f"timed out waiting for {path}"


def test_complete_signal_prevents_launch() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repo = make_repo(Path(directory))
        (repo / ".dogfood").mkdir()
        (repo / ".dogfood" / "master.complete").touch()
        log = repo / "calls"
        fake = fake_provider(repo)
        result = subprocess.run(
            [sys.executable, str(MASTER), "--repo", str(repo)],
            env={
                **os.environ,
                "DOGFOOD_MASTER_CODEX_COMMAND": f"{sys.executable} {fake} codex",
                "DOGFOOD_MASTER_CLAUDE_COMMAND": f"{sys.executable} {fake} claude",
            },
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert not log.exists()


def test_quota_falls_through_and_next_cycle_reverses() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repo = make_repo(Path(directory))
        (repo / ".dogfood").mkdir()
        log = repo / "calls"
        fake = fake_provider(repo)
        process = run_master(
            repo, fake, log, FAKE_QUOTA="1", FAKE_QUOTA_PROVIDER="claude", FAKE_COMPLETE="1"
        )
        output = process.communicate(timeout=3)[0]
        assert process.returncode == 0, output
        assert log.read_text().splitlines() == ["claude", "codex"]
        assert (repo / ".dogfood" / "master.complete").exists()
        assert (repo / ".dogfood" / "master.next").read_text() == "codex\n"


def test_stop_leaves_running_child_alive() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repo = make_repo(Path(directory))
        (repo / ".dogfood").mkdir()
        log = repo / "calls"
        fake = fake_provider(repo)
        process = run_master(repo, fake, log, FAKE_SLEEP="0.5", FAKE_COMPLETE="1")
        wait_for(repo / ".dogfood" / "master.pid")
        subprocess.run([sys.executable, str(MASTER), "stop", "--repo", str(repo)], check=True)
        output = process.communicate(timeout=3)[0]
        assert process.returncode == 0, output
        assert log.read_text().splitlines() == ["claude"]
        assert (repo / ".dogfood" / "master.complete").exists()


def test_ctrl_c_stops_supervisor_but_not_child_and_lock_blocks_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repo = make_repo(Path(directory))
        (repo / ".dogfood").mkdir()
        log = repo / "calls"
        fake = fake_provider(repo)
        process = run_master(repo, fake, log, FAKE_SLEEP="0.5", FAKE_COMPLETE="1")
        wait_for(repo / ".dogfood" / "master.pid")
        second = run_master(repo, fake, log, FAKE_SLEEP="0.5", FAKE_COMPLETE="1")
        assert second.wait(timeout=2) == 2
        process.send_signal(signal.SIGINT)
        output = process.communicate(timeout=3)[0]
        assert process.returncode == 0, output
        assert log.read_text().splitlines() == ["claude"]
        assert (repo / ".dogfood" / "master.complete").exists()
