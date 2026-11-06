#!/usr/bin/env python3
"""
Phase 정합성 검증기.

Usage:
    python3 scripts/validate_phase.py <phase-dir>
    python3 scripts/validate_phase.py --all

검사 항목:
- phases/<phase>/index.json 스키마 (project, phase, steps)
- step 번호 0부터 연속
- step name kebab-case slug
- status 값 유효
- 각 step마다 step{N}.md 파일 존재
- step{N}.md 에 Acceptance Criteria 블록 존재
- phases/index.json에 등록되어 있는지
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_STATUSES = {"pending", "completed", "error", "blocked"}


class Issue:
    def __init__(self, phase: str, level: str, message: str):
        self.phase = phase
        self.level = level  # "error" | "warn"
        self.message = message

    def render(self) -> str:
        icon = "✗" if self.level == "error" else "⚠"
        return f"  {icon} [{self.phase}] {self.message}"


def validate_phase(phase_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    name = phase_dir.name

    index_path = phase_dir / "index.json"
    if not index_path.exists():
        issues.append(Issue(name, "error", f"{index_path} 없음"))
        return issues

    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        issues.append(Issue(name, "error", f"index.json 파싱 실패: {e}"))
        return issues

    for key in ("project", "phase", "steps"):
        if key not in index:
            issues.append(Issue(name, "error", f"index.json에 '{key}' 필드 없음"))

    steps = index.get("steps", [])
    if not isinstance(steps, list) or not steps:
        issues.append(Issue(name, "error", "steps가 비어있거나 배열이 아님"))
        return issues

    for i, step in enumerate(steps):
        if step.get("step") != i:
            issues.append(
                Issue(name, "error", f"steps[{i}].step 값 불일치 (expected {i}, got {step.get('step')})")
            )
        slug = step.get("name", "")
        if not SLUG_RE.match(slug):
            issues.append(Issue(name, "error", f"step {i} name '{slug}'은 kebab-case 아님"))
        status = step.get("status")
        if status not in VALID_STATUSES:
            issues.append(Issue(name, "error", f"step {i} status '{status}' 유효하지 않음"))

        step_md = phase_dir / f"step{i}.md"
        if not step_md.exists():
            issues.append(Issue(name, "error", f"step{i}.md 없음"))
            continue

        text = step_md.read_text(encoding="utf-8")
        if "## Acceptance Criteria" not in text and "## AC" not in text:
            issues.append(Issue(name, "warn", f"step{i}.md 에 Acceptance Criteria 섹션 없음"))

    # top-level 등록 여부
    top_path = ROOT / "phases" / "index.json"
    if top_path.exists():
        try:
            top = json.loads(top_path.read_text(encoding="utf-8"))
            if not any(p.get("dir") == name for p in top.get("phases", [])):
                issues.append(Issue(name, "warn", "phases/index.json에 등록되지 않음"))
        except json.JSONDecodeError:
            issues.append(Issue("_top_", "error", "phases/index.json 파싱 실패"))

    return issues


def iter_phase_dirs() -> Iterable[Path]:
    phases = ROOT / "phases"
    if not phases.is_dir():
        return []
    return sorted(p for p in phases.iterdir() if p.is_dir())


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 정합성 검증")
    parser.add_argument("phase_dir", nargs="?", help="검증할 phase 디렉토리명")
    parser.add_argument("--all", action="store_true", help="모든 phase 검증")
    args = parser.parse_args()

    if args.all:
        targets = list(iter_phase_dirs())
        if not targets:
            print("phases/ 디렉토리에 phase가 없습니다.")
            return 0
    elif args.phase_dir:
        targets = [ROOT / "phases" / args.phase_dir]
        if not targets[0].is_dir():
            print(f"ERROR: {targets[0]} 없음")
            return 1
    else:
        parser.print_help()
        return 1

    all_issues: list[Issue] = []
    for phase_dir in targets:
        all_issues.extend(validate_phase(phase_dir))

    if not all_issues:
        print(f"✓ 검증 통과 ({len(targets)} phase)")
        return 0

    errors = [i for i in all_issues if i.level == "error"]
    warns = [i for i in all_issues if i.level == "warn"]

    for issue in all_issues:
        print(issue.render())

    print(f"\nerror: {len(errors)}, warn: {len(warns)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
