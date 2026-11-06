#!/usr/bin/env python3
"""
Harness 부트스트랩 — AGENT.md / docs/*.md 템플릿을 실제 프로젝트 값으로 치환한다.

Usage:
    python3 scripts/init.py                     # 대화형
    python3 scripts/init.py --name MyApp \
        --stack "Next.js 15, TypeScript" \
        --ac "npm run build && npm test"
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 템플릿 필드: (파일상대경로, 플레이스홀더 라벨 → 실제 키)
FIELDS = [
    ("name", "프로젝트명을 입력하세요"),
    ("stack", "기술 스택 (예: Next.js 15, TypeScript)"),
    ("ac", "AC 검증 커맨드 (예: npm run build && npm test)"),
]


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"{label}{suffix}: ").strip()
        if val:
            return val
        if default:
            return default
        print("  (필수 입력입니다)")


def gather(args) -> dict:
    values = {}
    for key, label in FIELDS:
        cli_val = getattr(args, key, None)
        if cli_val:
            values[key] = cli_val
        else:
            values[key] = prompt(label)
    return values


def substitute_file(path: Path, values: dict) -> bool:
    """파일에서 템플릿 플레이스홀더를 치환. 변경 여부 반환."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    original = text

    # 프로젝트명
    text = text.replace("{프로젝트명}", values["name"])

    # 기술 스택 — 첫 번째 `{프레임워크 ...}` 만 치환, 나머지는 비움
    text = re.sub(
        r"\{프레임워크[^}]*\}",
        values["stack"],
        text,
        count=1,
    )
    text = re.sub(r"\{언어[^}]*\}", "", text)
    text = re.sub(r"\{스타일링[^}]*\}", "", text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def write_agent_md(values: dict):
    path = ROOT / "AGENT.md"
    content = f"""# 프로젝트: {values['name']}

## 기술 스택
- {values['stack']}

## 아키텍처 규칙
- (프로젝트별 규칙을 추가하세요. CRITICAL 표시는 Codex가 반드시 지킬 규칙에만 사용.)

## 개발 프로세스
- 커밋 메시지는 conventional commits 형식을 따를 것 (feat:, fix:, docs:, refactor:)

## 명령어
AC: {values['ac']}
"""
    path.write_text(content, encoding="utf-8")


def write_prd(values: dict):
    path = ROOT / "docs" / "PRD.md"
    content = f"""# PRD: {values['name']}

## 목표
(이 프로젝트가 해결하려는 문제를 한 줄로 요약)

## 사용자
(누가 이 제품을 쓰는지)

## 핵심 기능
1. (기능 1)
2. (기능 2)

## MVP 제외 사항
- (안 만들 것)
"""
    path.write_text(content, encoding="utf-8")


def write_architecture(values: dict):
    path = ROOT / "docs" / "ARCHITECTURE.md"
    content = f"""# 아키텍처

## 기술 스택
{values['stack']}

## 디렉토리 구조
(프로젝트 구조를 작성하세요)

## 데이터 흐름
(데이터 흐름 설명)
"""
    path.write_text(content, encoding="utf-8")


def write_adr():
    path = ROOT / "docs" / "ADR.md"
    content = """# Architecture Decision Records

## 철학
(프로젝트 핵심 가치관 — 예: MVP 속도 최우선, 외부 의존성 최소화)

---

### ADR-001
**결정**:
**이유**:
**트레이드오프**:
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness 프로젝트 부트스트랩")
    parser.add_argument("--name", help="프로젝트명")
    parser.add_argument("--stack", help="기술 스택")
    parser.add_argument("--ac", help="AC 검증 커맨드")
    parser.add_argument("--force", action="store_true", help="기존 AGENT.md / docs 덮어쓰기")
    args = parser.parse_args()

    agent_md = ROOT / "AGENT.md"
    if agent_md.exists() and not args.force:
        text = agent_md.read_text(encoding="utf-8")
        if "{프로젝트명}" not in text:
            print("AGENT.md가 이미 초기화된 것으로 보입니다. 덮어쓰려면 --force 를 사용하세요.")
            return 1

    values = gather(args)

    (ROOT / "docs").mkdir(exist_ok=True)
    write_agent_md(values)
    write_prd(values)
    write_architecture(values)
    write_adr()

    print("\n✓ 초기화 완료")
    print(f"  프로젝트: {values['name']}")
    print(f"  스택: {values['stack']}")
    print(f"  AC: {values['ac']}")
    print("\n다음 단계:")
    print("  1. AGENT.md / docs/*.md 를 프로젝트에 맞게 추가 편집")
    print("  2. python3 scripts/new_phase.py <phase-name> 으로 첫 phase 생성")
    print("  3. python3 scripts/execute.py <phase-name> 으로 실행")
    return 0


if __name__ == "__main__":
    sys.exit(main())
