# claud_통합 검증 총평

검증일: 2026-05-12  
검증 위치: `e:\ontology_edu`

## 1. 한 줄 결론

`claud_통합`은 `src_anti`의 업무 화면성과 `src_codex`의 운영형 백엔드 구조를 결합한다는 방향을 잘 따르고 있다. 현재 상태는 **통합 샘플로는 성공**, 다만 **문서 상태 동기화와 RAG 자동 평가 보강**이 다음 병목이다.

## 2. 기준 문서 대비 판단

참고한 기준:
- `req_doc_hub/평가/23-codex가 2개 소스 비교.md`
- `req_doc_hub/추적도/09_RAG_평가와_운영_설계_추적도.md`
- `req_doc_hub/추적도/10_운영형_아키텍처_확장_추적도.md`
- `claud_통합/PROGRESS.md`
- `claud_통합/README.md`
- `claud_통합/NEXT_STEPS.md`

평가:
- `23-codex`의 결론인 "화면은 src_anti, 운영형 백엔드는 src_codex" 결합 방향을 잘 반영했다.
- FastAPI 백엔드는 `src_codex`의 서비스 경계, 정책, 워크플로우, 감사 로그, Repository 구조를 비교적 충실히 이식했다.
- Next.js 프론트엔드는 대시보드, 객체 탐색, AI 질의, 워크플로우, 감사 로그, 우측 컨텍스트 패널, 사용자 전환 셀렉터를 갖춰 `src_anti`의 화면 흐름을 잘 계승했다.
- `09_RAG_평가와_운영_설계` 기준의 자동 RAG 평가는 아직 완전 구현으로 보기는 어렵다. 현재 `backend/eval/scenarios.py`는 학습 시나리오 API 검증에 가깝고, `evaluate.py` + 평가 데이터셋 + precision/accuracy/latency 지표 기반 평가는 별도로 필요하다.

## 3. 실제 검증 결과

### 3.1 백엔드 테스트

실행:

```powershell
& "C:\Users\nkchoi2\anaconda3\envs\claud_be\python.exe" -m pytest
```

결과:

```text
17 passed in 2.11s
```

판단:
- 백엔드 API 테스트와 LLM Gateway 관련 테스트는 지정 conda 환경에서 통과했다.
- 기본 `base` Python 환경에서는 `fastapi`가 없어 실패했다. README처럼 `claud_be` 환경 사용이 필요하다.

### 3.2 프론트엔드 빌드

실행:

```powershell
$env:PATH="C:\Users\nkchoi2\anaconda3\envs\claud_fe;C:\Users\nkchoi2\anaconda3\envs\claud_fe\Library\bin;$env:PATH"
& "C:\Users\nkchoi2\anaconda3\envs\claud_fe\npm.cmd" run build
```

결과:

```text
Compiled successfully
```

판단:
- Next.js 프로덕션 빌드는 성공했다.
- `conda run -n claud_fe npm run build`는 Windows 임시파일/활성화 문제로 실패했다.
- `npm.cmd`만 직접 실행하면 내부에서 `node`를 찾지 못했기 때문에, `claud_fe` 환경 경로를 PATH에 포함해야 했다.

### 3.3 학습 시나리오 검증

실행:

```powershell
$env:PYTHONUTF8='1'
& "C:\Users\nkchoi2\anaconda3\envs\claud_be\python.exe" -m eval.scenarios
```

결과:

```text
[PASS] #1 정상 승인
[PASS] #2 고위험 거부
[PASS] #3 금액 임계 분기
[PASS] #4 지역 거부
[PASS] #5 속성 마스킹

5/5 passed
```

판단:
- README의 핵심 학습 시나리오 5종은 API 기준으로 통과했다.
- 다만 기본 Windows CP949 콘솔에서는 `—`, `→` 문자가 `UnicodeEncodeError`를 일으킨다. `PYTHONUTF8=1`을 주면 정상 동작한다.

## 4. 잘된 점

1. 통합 방향이 명확하다.
   - `src_anti`의 UI 흐름과 `src_codex`의 운영형 백엔드 구조를 결합한다는 판단이 구현에 잘 반영되어 있다.

2. 백엔드 구조가 교육용 운영 아키텍처로 적합하다.
   - `AppContext`, `OntologyService`, `PolicyEngine`, `SearchService`, `RAGService`, `WorkflowService`, `AuditService`, `Repository`가 분리되어 있어 설명하기 좋다.

3. 권한과 거버넌스 학습 포인트가 살아 있다.
   - `analyst`, `finance`, `viewer`, `admin` 역할 전환으로 마스킹, 권한 거부, 액션 가능 여부 차이를 확인할 수 있다.

4. Gemini 연동과 폴백 전략이 있다.
   - `LLMGateway`가 Gemini 키를 수집하고, 실패 시 규칙 기반 응답으로 폴백한다.
   - 현재 코드에는 키 로테이션과 health stats도 포함되어 있다.

5. 테스트 기반 확인이 가능하다.
   - `pytest` 17개 통과.
   - `eval.scenarios`로 학습 시나리오 5종을 API 기준으로 확인 가능.

## 5. 주요 지적

### 5.1 PROGRESS.md의 상태 모순

`claud_통합/PROGRESS.md`는 상단에서 "Step A~E 전부 완료"라고 말하지만, 본문에는 아직 "백엔드 검증 미실시", "프론트엔드 미착수", "Step A~E 다음 작업" 내용이 남아 있다.

문제:
- 다음 세션에서 이 파일을 읽으면 현재 상태를 잘못 이해할 수 있다.
- 실제 파일 트리도 예전 상태 기준으로 남아 있어 프론트엔드와 eval 파일이 반영되지 않았다.

권장:
- 상단 완료 상태를 유지하려면 본문도 완료 기준으로 재작성한다.
- 과거 인수인계 기록은 "이전 상태" 섹션으로 접거나 삭제한다.
- 실제 검증 결과를 `17 passed`, `next build 성공`, `eval.scenarios 5/5 passed`로 갱신한다.

### 5.2 RAG 자동 평가는 아직 별도 보강 필요

`NEXT_STEPS.md`에 있는 `evaluate.py` RAG 자동 평가 항목은 아직 충족되지 않았다.

현재 상태:
- 있음: `backend/eval/scenarios.py`
- 없음: `backend/evaluate.py`
- 없음: `backend/eval/cases.json`
- 없음: object detection accuracy, retrieval precision@3, action recall, latency p50/p95, warning rate 집계

판단:
- `scenarios.py`는 좋은 회귀 검증 도구지만, `req_doc_hub/추적도/09`가 말하는 RAG 품질 평가와는 목적이 다르다.

권장:
- `evaluate.py`를 별도 생성한다.
- 최소 15~20개 평가 케이스를 JSON으로 분리한다.
- 결과를 `backend/eval/results-{timestamp}.json`으로 저장한다.
- README에 실행 방법을 추가한다.

### 5.3 Windows 콘솔 인코딩 이슈

`python -m eval.scenarios`는 기본 CP949 콘솔에서 출력 문자 때문에 실패했다.

실패 원인:
- `—`, `→` 등 일부 유니코드 문자가 CP949에서 인코딩되지 않음.

권장:
- 출력 문자열을 ASCII 위주로 바꾸거나,
- README/NEXT_STEPS에 `$env:PYTHONUTF8='1'` 설정을 명시하거나,
- `scenarios.py`에서 stdout 인코딩을 UTF-8로 재설정한다.

### 5.4 README와 NEXT_STEPS의 표현 정리 필요

README는 전반적으로 좋지만 "완료된 기능"과 "남은 보강"이 조금 섞여 보인다.

권장:
- README: 실행과 사용법 중심.
- PROGRESS: 현재 구현/검증 상태 중심.
- NEXT_STEPS: 남은 작업만 관리.
- 평가 자동화, 프론트 E2E, Postgres, JWT, OTel, Docker는 명확히 "미구현/후속"으로 유지.

## 6. 추천 우선순위

1. `PROGRESS.md` 최신화
   - 현재 가장 먼저 해야 할 문서 정리다.
   - 작업 중단 후 재개 시 혼선을 줄인다.

2. `eval.scenarios` 인코딩 이슈 수정
   - 교육/Windows 환경에서 바로 막힐 수 있는 작은 문제다.

3. `backend/evaluate.py` RAG 자동 평가 구현
   - `req_doc_hub/추적도/09` 기준의 가장 큰 미충족 항목이다.

4. Playwright 프론트 E2E 추가
   - 실제 브라우저 클릭 흐름과 UI 회귀를 자동화한다.

5. Gemini 실제 답변 품질 평가
   - 키 한도 회복 후 한국어 응답 품질, 근거 인용 정확도, 환각 여부를 확인한다.

## 7. 최종 판정

현재 `claud_통합`은 교육용 통합 콘솔로 충분히 의미 있는 상태다.

다만 "완료"라는 표현을 쓰려면 범위를 나눠야 한다.

- 통합 앱 골격: 완료
- 백엔드 테스트: 통과
- 프론트 빌드: 통과
- API 기반 학습 시나리오: 통과
- 실제 브라우저 E2E: 미완료
- RAG 품질 자동 평가: 미완료
- 운영 전환 요소(Postgres/JWT/OTel/Docker): 미완료

따라서 현 시점의 가장 정확한 표현은 다음이다.

> `claud_통합`은 src_anti와 src_codex의 장점을 결합한 교육용 통합 샘플로 성공적으로 구성되었고, 기본 검증도 통과했다. 다음 단계는 문서 상태 정합성 정리와 RAG 평가 자동화, 브라우저 E2E 보강이다.
