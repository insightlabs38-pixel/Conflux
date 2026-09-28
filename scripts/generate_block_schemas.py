import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/api"))
from presentation.block_types import BLOCK_TYPES  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = "export const blockTypes = " + json.dumps(BLOCK_TYPES, indent=2) + " as const;\n"
    output = subprocess.run(
        ["pnpm", "exec", "prettier", "--parser", "typescript"],
        input=source,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    ).stdout
    target = ROOT / "src/web/features/page-builder/blockSchemas.generated.ts"
    if args.check:
        if not target.exists() or target.read_text() != output:
            raise SystemExit("Block schemas are stale; run scripts/generate_block_schemas.py")
    else:
        target.write_text(output)


if __name__ == "__main__":
    main()
