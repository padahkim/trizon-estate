#!/usr/bin/env python3
"""Start Codex in the project and enable its native .codex/hooks.json config."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def codex_command(root: Path) -> list[str]:
    return [
        "codex",
        "--cd", str(root.resolve()),
        "-c", "features.hooks=true",
    ]


def main() -> int:
    try:
        return subprocess.run(codex_command(ROOT) + sys.argv[1:], cwd=ROOT).returncode
    except FileNotFoundError:
        print("ERROR: Codex CLI를 설치하고 `codex login`을 실행하세요.", file=sys.stderr)
        return 127


if __name__ == "__main__":
    sys.exit(main())
