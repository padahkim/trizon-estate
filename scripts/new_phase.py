#!/usr/bin/env python3
"""
새 phase 스켈레톤 생성기.

Usage:
    python3 scripts/new_phase.py 0-mvp --steps project-setup,core-types,api-layer
    python3 scripts/new_phase.py 1-polish --steps ui-tweaks
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read_project_name() -> str:
    agent_md = ROOT / "AGENT.md"
    if not agent_md.exists():
        return "project"
    m = re.search(r"^#\s*프로젝트:\s*(.+)$", agent_md.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1).strip() if m else "project"


def read_ac_command() -> str:
    agent_md = ROOT / "AGENT.md"
    if not agent_md.exists():
        return "# AC 커맨드를 AGENT.md에 정의하고 여기 복사하세요"
    m = re.search(r"^AC:\s*(.+)$", agent_md.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1).strip() if m else "# AC 커맨드를 AGENT.md에 정의하고 여기 복사하세요"


def write_step_file(phase_dir: Path, step_num: int, step_name: str, ac: str):
    path = phase_dir / f"step{step_num}.md"
    content = f"""# Step {step_num}: {step_name}

## 읽어야 할 파일

먼저 아래 파일들을 읽고 프로젝트의 아키텍처와 설계 의도를 파악하라:

- `AGENT.md`
- `docs/ARCHITECTURE.md`
- `docs/ADR.md`
- (이전 step에서 생성/수정된 파일이 있으면 경로 명시)

## 작업

(구체적인 구현 지시를 작성하세요.
- 파일 경로, 클래스/함수 시그니처, 로직 설명
- 코드 스니펫은 인터페이스/시그니처 수준만
- 설계 의도에서 벗어나면 안 되는 CRITICAL 규칙 명시)

## Acceptance Criteria

```bash
{ac}
```

## 검증 절차

1. 위 AC 커맨드를 실행한다.
2. 아키텍처 체크리스트를 확인한다:
   - ARCHITECTURE.md 디렉토리 구조 준수
   - ADR 기술 스택 준수
   - AGENT.md CRITICAL 규칙 위반 없음
3. 결과에 따라 `phases/{phase_dir.name}/index.json`의 step 상태를 업데이트.

## 금지사항

- (이 step에서 하지 말아야 할 것. "X 하지 마라. 이유: Y" 형식)
- 기존 테스트를 깨뜨리지 마라
"""
    path.write_text(content, encoding="utf-8")


def update_top_index(phase_dir_name: str):
    top_path = ROOT / "phases" / "index.json"
    if top_path.exists():
        top = json.loads(top_path.read_text(encoding="utf-8"))
    else:
        top = {"phases": []}

    if not any(p.get("dir") == phase_dir_name for p in top["phases"]):
        top["phases"].append({"dir": phase_dir_name, "status": "pending"})
        top_path.write_text(
            json.dumps(top, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 스켈레톤 생성")
    parser.add_argument("phase_dir", help="phase 디렉토리명 (예: 0-mvp)")
    parser.add_argument(
        "--steps",
        required=True,
        help="step slug 쉼표 구분 (예: project-setup,core-types,api-layer)",
    )
    parser.add_argument("--force", action="store_true", help="기존 phase 덮어쓰기")
    args = parser.parse_args()

    phases_dir = ROOT / "phases"
    phases_dir.mkdir(exist_ok=True)

    phase_dir = phases_dir / args.phase_dir
    if phase_dir.exists() and not args.force:
        print(f"ERROR: {phase_dir}가 이미 존재합니다. --force 로 덮어쓰세요.")
        return 1
    phase_dir.mkdir(exist_ok=True)

    step_names = [s.strip() for s in args.steps.split(",") if s.strip()]
    if not step_names:
        print("ERROR: --steps가 비어있습니다.")
        return 1
    for name in step_names:
        if not SLUG_RE.match(name):
            print(f"ERROR: '{name}'은 kebab-case slug가 아닙니다.")
            return 1

    project = read_project_name()
    ac = read_ac_command()

    index = {
        "project": project,
        "phase": args.phase_dir,
        "steps": [
            {"step": i, "name": name, "status": "pending"}
            for i, name in enumerate(step_names)
        ],
    }
    (phase_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for i, name in enumerate(step_names):
        write_step_file(phase_dir, i, name, ac)

    update_top_index(args.phase_dir)

    print(f"✓ {phase_dir} 생성")
    print(f"  steps: {len(step_names)}개")
    for i, name in enumerate(step_names):
        print(f"    step{i}.md — {name}")
    print("\n각 stepN.md 를 열어 '작업' 섹션을 채운 뒤 실행:")
    print(f"  python3 scripts/execute.py {args.phase_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
