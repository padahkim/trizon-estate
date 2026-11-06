# trizon-estate

Codex CLI로 phase → step 단위의 개발 작업을 순차 실행하는 하네스입니다.
프로젝트 규칙 주입, 이전 단계 요약 전달, 실패 재시도, 결과 저장과 Git 커밋을 처리합니다.

## 요구사항

- Python 3.10+ (테스트에는 pytest 필요)
- Codex CLI 0.167.0 이상과 로그인된 계정: `codex login`
- Git

프로젝트 기술 스택과 첫 phase는 아직 초기화하지 않았습니다.

## Codex에서 시작하기

```bash
python3 scripts/codex_cli.py
```

훅 목록과 실행 설정은 `.codex/hooks.json` 한 곳에서 관리합니다.
여기에는 `PreToolUse` 훅 두 개가 있습니다.

| 훅 | 대상 | 실행 스크립트 |
| --- | --- | --- |
| 위험 명령 검사 | `Bash` 셸 명령 | `scripts/guard.py` |
| TDD 가드 검사 | `apply_patch` / `Edit` / `Write` | `scripts/tdd_guard.py` |

실행기는 프로젝트 디렉터리를 지정하고 훅 기능을 활성화하며, Codex가 이 파일을 기본 방식으로 읽습니다.
별도 인자로 같은 훅을 다시 등록하지 않으며 사용자 설정 파일은 수정하지 않습니다.
프로젝트를 신뢰한 뒤 Codex의 `/hooks`에서 각 훅을 확인하고 신뢰해야 활성화됩니다.
훅이 변경되면 다시 검토해야 합니다. 훅 신뢰나 샌드박스를 자동으로 우회하지 않습니다.
프로젝트 안에서 일반 `codex`로 시작해도 훅 기능이 활성화되어 있고 프로젝트와 훅이 신뢰된 경우 같은 파일을 읽습니다.

프로젝트 규칙은 요청한 이름인 `AGENT.md`에 있습니다. Codex가 자동으로 읽는
`AGENTS.md`가 이 파일과 작업별 프롬프트를 안내합니다.

- 계획: Codex에 `prompts/harness.md를 읽고 첫 작업을 설계해줘`라고 요청합니다.
- 리뷰: Codex에 `prompts/review.md에 따라 변경 사항을 리뷰해줘`라고 요청합니다.

## 초기화와 실행

아래 스택과 AC는 하네스 자체를 검증하는 예시입니다. 제품을 만들기 전 프로젝트에 맞게 바꾸세요.

```bash
# 프로젝트 규칙과 설계 문서 생성
python3 scripts/init.py --name trizon-estate --stack "Python 3.10+" --ac "python3 -m pytest scripts/ -q"

# phase와 step 파일 생성
python3 scripts/new_phase.py 0-mvp --steps project-setup,core-types,api-layer

# phases/0-mvp/stepN.md의 작업 내용을 채운 뒤 검증
python3 scripts/validate_phase.py 0-mvp

# 준비된 phase 실행
python3 scripts/execute.py 0-mvp
python3 scripts/execute.py 0-mvp --push
```

`execute.py`도 같은 프로젝트 가드 설정을 전달합니다. 먼저 프로젝트 실행기에서 훅을 신뢰하세요.
각 step은 다음 방식으로 Codex를 호출하며 프롬프트를 표준 입력으로 전달합니다.

```text
codex --cd <프로젝트 경로> -c features.hooks=true --ask-for-approval never exec --sandbox workspace-write --json --color never -
```

권한 확인이 필요한 작업은 자동 승인되지 않고 Codex에 실패로 반환됩니다.
Codex는 해결에 사용자 개입이 필요하면 해당 step을 `blocked`로 기록합니다.
모델과 인증은 기존 Codex 설정을 사용합니다.

## 구조

```text
AGENTS.md                    # Codex용 프로젝트 안내
AGENT.md                     # 프로젝트 규칙과 AC
prompts/harness.md           # 작업 설계 절차와 템플릿
prompts/review.md            # 프로젝트 리뷰 절차
docs/                        # PRD / ARCHITECTURE / ADR
.codex/hooks.json            # 프로젝트 훅 목록과 실행 설정
scripts/codex_cli.py         # 프로젝트 경로와 훅 기능을 지정하는 Codex 실행기
scripts/execute.py           # phase 실행, 재시도, 결과 기록, 커밋
scripts/guard.py             # Codex 셸 명령 훅
scripts/tdd_guard.py         # 구현 편집 전 대응 테스트 파일 확인
scripts/init.py              # 프로젝트 초기화
scripts/new_phase.py         # phase 생성
scripts/validate_phase.py    # phase 정합성 검사
phases/<phase>/index.json    # step 상태
phases/<phase>/stepN.md      # step 지시문
```

## 완료 판정과 기록

Codex가 AC를 직접 실행하고 `index.json`의 해당 step 상태와 요약을 갱신합니다.
하네스는 정상 종료와 JSONL의 `turn.completed`를 모두 확인한 뒤 `completed` 상태를 인정합니다.
별도의 테스트 실행기가 AC를 다시 실행하는 구조는 아니므로 AC와 리뷰 절차를 구체적으로 작성하세요.
커밋과 선택적인 push는 하네스가 담당합니다.

`stepN-output.json`에는 종료 코드, 타임아웃 여부, JSONL 이벤트, 최종 메시지와 토큰 사용량을 저장합니다.
실패한 실행은 최대 3회 시도하며 이전 오류를 다음 프롬프트에 전달합니다. 타임아웃은 30분입니다.
결과 파일에는 프롬프트 관련 내용과 명령 출력이 포함될 수 있으며 `.gitignore`로 제외합니다.

## 복구

- `error`: 원인을 해결한 뒤 해당 step을 `pending`으로 변경하고 `error_message`를 지운 후 재실행합니다.
- `blocked`: 기록된 사유를 해결한 뒤 해당 step을 `pending`으로 변경하고 `blocked_reason`을 지운 후 재실행합니다.

작업 브랜치는 `feat-<phase>`입니다. 하네스가 `git add -A`로 커밋하므로 실행 전 작업 트리를 정리하세요.

## 가드 훅

신뢰된 훅은 `Bash`로 전달되는 Codex 셸 명령을 검사합니다.
기존 정책에 따라 루트·홈 삭제, 강제 push, hard reset, 위험한 SQL 등의 일부 패턴을 차단합니다.
이는 전체 명령을 이해하는 보안 경계가 아니며 Codex 샌드박스와 함께 사용합니다.

TDD 가드는 `apply_patch`(`Edit`·`Write` 별칭 포함)로 Python·JS·TS 소스를
추가·수정·삭제하거나 이동할 때 대응 테스트 파일이 이미 있는지 확인합니다.
예를 들어 `scripts/service.py`를 편집하려면 `scripts/test_service.py`를,
`src/service.ts`를 편집하려면 `src/service.test.ts` 또는 `src/service.spec.ts`를 먼저 만듭니다.
같은 폴더 외에 인접 `__tests__/`, `src/__tests__/`, 루트 `tests/`와
소스 디렉터리 구조를 따르는 `tests/` 경로도 확인합니다.
여러 파일을 한 번에 편집하면 모든 구현 파일을 검사하고, 테스트가 없는 파일이 있으면 전체 호출을 차단합니다.
테스트와 구현을 한 패치에 추가하면 차단되므로 테스트 파일을 별도 편집으로 먼저 저장하세요.

테스트 파일, 문서·설정·스타일, `types/`, `.d.ts`, `types.ts`, Python `__init__.py`,
Next.js 진입 파일(`page`·`layout`·`loading`·`error`·`not-found`)은 제외합니다.
`.codex/`·`.claude/`·`workflows/`의 인프라 파일도 제외합니다.
파일명 중간에 `test`나 `spec`이 들어간다는 이유만으로 구현 파일을 제외하지 않습니다.

이 훅은 **테스트 파일의 존재**를 검사합니다. 테스트 실행·실패 여부나 커버리지는 확인하지 않으므로
`AGENT.md`의 테스트 우선 작성과 실행 절차를 함께 따르세요.
셸·다른 도구로 쓰는 파일은 이 TDD 훅의 검사 대상이 아닙니다.
현재 열려 있는 세션에 자동 적용되지 않으므로,
`python3 scripts/codex_cli.py`로 새 세션을 시작하고 프로젝트와 `/hooks`의 `TDD 가드 검사`를 검토·신뢰하세요.
이후 `execute.py`도 `.codex/hooks.json`의 같은 훅 구성을 사용합니다.

참고 구현: [finsight의 Codex TDD 어댑터](https://github.com/jha0313/finsight/blob/main/scripts/hooks/codex-tdd-guard.sh),
[테스트 파일 검사 규칙](https://github.com/jha0313/finsight/blob/main/scripts/hooks/tdd-guard.sh).

## 검증

```bash
python3 -m pip install pytest
python3 -m pytest scripts/ -q
```

테스트는 실제 모델을 호출하지 않습니다. CLI 호출·이벤트 처리·실패 복구는 모의 응답과 임시 실행 파일로 검증합니다.

참고: [Codex 비대화형 실행](https://learn.chatgpt.com/docs/non-interactive-mode),
[Codex 훅 설정과 신뢰](https://learn.chatgpt.com/docs/hooks).
