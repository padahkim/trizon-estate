#!/usr/bin/env python3
"""
PreToolUse 훅 — Bash 도구 호출을 검사해 위험 명령을 차단한다.

Codex 훅은 stdin으로 JSON payload를 전달한다:
    {"tool_name": "Bash", "tool_input": {"command": "..."}}

차단 시 비영 종료 + stderr 메시지 → Codex에 피드백.
"""

import json
import re
import sys

DANGEROUS_PATTERNS = [
    # rm -rf 루트/홈 — 정확히 /, /*, ~, ~/, $HOME 만 차단. /tmp/x 같은 하위 경로는 허용.
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+(?:/|/\*|~|~/|\$HOME)(?:\s|;|&|\||$)", "rm -rf 루트/홈"),
    (r"\bgit\s+push\s+(?:--force|-f)\b", "git push --force"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
    (r"\bgit\s+clean\s+-[a-z]*f", "git clean -f"),
    (r"\bgit\s+checkout\s+--?\s*\.", "git checkout ."),
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE"),
    (r":\s*\(\s*\)\s*\{.*:\s*\|\s*:", "fork bomb"),
    (r"(?:^|\s)--no-verify(?:\s|$)", "--no-verify (훅 우회)"),
]


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0  # 스키마 변경 시 훅이 빌미가 되지 않도록 통과

    if payload.get("tool_name") not in ("Bash", "exec_command", "shell_command"):
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", tool_input.get("cmd", ""))
    if not isinstance(command, str) or not command:
        return 0

    for pattern, label in DANGEROUS_PATTERNS:
        if re.search(pattern, command, flags=re.IGNORECASE):
            print(
                f"BLOCKED: 위험한 명령어가 감지되었습니다 ({label}).\n"
                f"명령: {command}\n"
                f"사용자 확인 없이 실행할 수 없습니다.",
                file=sys.stderr,
            )
            return 2  # 훅 차단 코드

    return 0


if __name__ == "__main__":
    sys.exit(main())
