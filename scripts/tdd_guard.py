#!/usr/bin/env python3
"""Codex PreToolUse: require an existing test before editing implementation.

Based on jha0313/finsight's scripts/hooks/{codex-tdd-guard,tdd-guard}.sh.
Checks file presence only; it does not prove a failing test or test coverage.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

SOURCE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx")
PATCH_PATH = re.compile(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$", re.MULTILINE)


def edited_paths(tool_input: dict) -> list[str]:
    direct = tool_input.get("file_path")
    if isinstance(direct, str) and direct:
        return [direct]
    command = tool_input.get("command", "")
    if isinstance(command, list):
        command = "\n".join(part for part in command if isinstance(part, str))
    if not isinstance(command, str):
        return []
    return [path.rstrip("\r") for path in PATCH_PATH.findall(command)]


def requires_test(path: Path) -> bool:
    if path.suffix not in SOURCE_EXTENSIONS:
        return False
    if any(part in {"tests", "__tests__", "types", ".codex", ".claude", "workflows"} for part in path.parts):
        return False
    if path.suffix == ".py":
        return not (path.name.startswith("test_") or path.name == "__init__.py")
    if path.stem.endswith((".test", ".spec", ".config")) or path.name.endswith(".d.ts"):
        return False
    if path.stem == "types":
        return False
    # Match the reference guard's Next.js entry-point exemptions.
    return not (path.suffix in {".ts", ".tsx"} and path.stem in {
        "layout", "page", "loading", "error", "not-found",
    })


def has_test(source: Path, root: Path) -> bool:
    if source.suffix == ".py":
        names = [f"test_{source.stem}.py"]
    else:
        names = [f"{source.stem}.{kind}{ext}"
                 for kind in ("test", "spec") for ext in SOURCE_EXTENSIONS[1:]]
    relative = source.relative_to(root)
    directories = {
        source.parent, source.parent / "__tests__",
        root / "src" / "__tests__", root / "tests", root / "tests" / relative.parent,
    }
    if source.parent != root:
        directories.add(source.parent.parent / "__tests__")
    if relative.parts[0] == "src":
        directories.add(root / "tests" / Path(*relative.parts[1:]).parent)
    return any((directory / name).is_file() for directory in directories for name in names)


def project_root(cwd: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=cwd,
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return cwd


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in {"apply_patch", "Edit", "Write"}:
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    paths = edited_paths(tool_input)
    if not paths:
        return 0
    cwd = Path(payload.get("cwd") or Path.cwd()).resolve()
    root = project_root(cwd)
    for name in paths:
        source = (cwd / name).resolve()
        try:
            relative = source.relative_to(root)
        except ValueError:
            continue
        if requires_test(relative) and not has_test(source, root):
            example = f"test_{source.stem}.py" if source.suffix == ".py" else f"{source.stem}.test{source.suffix}"
            reason = (
                f"TDD GUARD: '{relative}'에 대응하는 테스트 파일이 없습니다. "
                f"구현 코드를 편집하기 전에 테스트 파일을 먼저 작성하세요. (예: {example})"
            )
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}, ensure_ascii=False))
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
