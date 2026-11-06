---
name: harness
description: trizon-estate의 기존 프로젝트 harness로 phase를 설계하거나 준비된 phase를 실행하고, 진행 현황과 변경 사항을 확인할 때 사용한다.
---

# Harness

이 스킬은 저장소의 기존 harness 진입점이다. 모든 경로와 명령은 저장소 루트 기준이다.
새 계획·실행 체계를 만들지 말고 `AGENT.md`와 아래 작업별 절차를 따른다.

## 요청 파악

- 먼저 `AGENT.md`를 읽는다. 제품 작업을 계획하거나 리뷰할 때는 `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ADR.md`도 읽는다.
- 사용자의 자연어 요청으로 계획·실행·현황·리뷰를 선택한다. 별도의 명령 파서를 만들지 않는다.
- 추가 요청 없이 스킬만 호출하면 `phases/`의 존재 여부와 인덱스를 확인해 현재 phase·step 상태와 다음 할 일을 짧게 안내한다. phase가 없으면 첫 phase의 계획부터 시작해야 함을 알린다.
- 이 저장소에서는 superpowers 스킬이나 별도의 계획·worktree·위임·커밋 워크플로우를 사용하지 않는다.

## 계획

`prompts/harness.md`를 읽고 탐색 → 논의 → step 초안 → 승인된 계획의 파일 생성 절차를 따른다.
이미 승인된 내용은 다시 승인받지 않는다. 요구사항과 제안을 구분하고 중요한 미결정 사항을 임의 확정하지 않는다.

- 각 step은 독립 세션에서 실행할 수 있도록 관련 파일·인터페이스·제약·실행 가능한 AC를 포함한다.
- 승인된 phase는 `phases/index.json`, `phases/<phase>/index.json`, `stepN.md`로 작성한다. 필요하면 `scripts/new_phase.py`로 뼈대를 생성한다.
- 생성하거나 수정한 phase는 `python3 scripts/validate_phase.py <phase>`로 검증한다.
- 계획 요청만으로 제품 구현이나 phase 실행을 시작하지 않는다.

## 실행

사용자가 준비된 phase의 실행을 요청하면 다음 절차를 따른다.

1. 실행할 phase의 인덱스와 step 지시문을 읽는다. 대상이 모호하면 현황을 확인해 후보를 제시한다.
2. `git status --short`로 기존 변경 사항을 확인한다. 실행기는 `git add -A`로 커밋하므로 무관한 변경을 임의로 포함하거나 stash·삭제·커밋하지 않는다. 기존 변경의 처리 방식은 이미 받은 사용자 지시를 따르고, 지시가 없으면 사용자에게 확인한다.
3. `python3 scripts/validate_phase.py <phase>`를 실행하고 성공하면 `python3 scripts/execute.py <phase>`로 실행한다. 사용자가 push도 요청한 경우에만 `--push`를 붙인다.
4. 실행 결과와 완료·실패·차단된 step, 다음 조치를 요약한다. 기존 `error`·`blocked` 상태는 원인을 해결한 뒤 `README.md`의 복구 절차를 따른다.

프로젝트와 훅 신뢰는 `python3 scripts/codex_cli.py`로 시작한 세션의 `/hooks`에서 사용자가 검토한다.
샌드박스나 훅 신뢰를 우회하지 않는다. harness가 실행한 step 안에서는 실행기를 중첩 실행하거나 직접 commit·push하지 않는다.

## 현황

`phases/index.json`과 관련 `phases/<phase>/index.json`을 읽어 phase·step 상태, 완료 요약, `error_message`·`blocked_reason`과 다음 조치를 보고한다.
현황 조회만으로 파일을 변경하거나 실행을 재개하지 않는다.

## 리뷰

`prompts/review.md`를 읽고 요청받은 변경 범위를 리뷰한다. 실행한 검증과 실행하지 못한 검증을 구분해 보고한다.

## 호출 예시

```text
$harness
$harness MVP 구현을 위한 첫 phase를 설계해줘
$harness 0-mvp 실행해줘
$harness 진행 현황 알려줘
$harness 변경 사항 리뷰해줘
```
