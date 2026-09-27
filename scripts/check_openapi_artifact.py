import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKED_SCHEMA = ROOT / "docs/api/openapi.yaml"


def main():
    with tempfile.TemporaryDirectory() as directory:
        generated = Path(directory) / "openapi.yaml"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "src/api/manage.py"),
                "spectacular",
                "--validate",
                "--fail-on-warn",
                "--file",
                str(generated),
            ],
            cwd=ROOT,
            check=True,
        )
        if generated.read_bytes() != CHECKED_SCHEMA.read_bytes():
            raise SystemExit(
                "docs/api/openapi.yaml is stale; regenerate it with manage.py spectacular."
            )


if __name__ == "__main__":
    main()
