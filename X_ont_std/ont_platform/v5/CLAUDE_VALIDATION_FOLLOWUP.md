# Claude Code 검증 결과 후속 조치

작성일: 2026-06-11

## 1. 결론

Claude Code 검증 결과는 다음과 같이 해석한다.

- v5 frontend build와 mock simulation 구조는 대체로 확인되었다.
- Template Gallery -> clone -> Workflow Builder 자동 로드 흐름은 코드 기준으로 확인되었다.
- `/api/workflow-graphs` endpoint 존재도 확인되었다.
- 다만 v5 backend는 아직 정상 기동 검증이 완료되지 않았다.

즉, 다음 작업은 프론트 기능 추가가 아니라 v5 backend를 올바른 conda 환경에서 다시 기동하고, frontend와 실제 API 계약을 확인하는 것이다.

## 2. 핵심 문제

검증 로그에서 v5 backend 실행 중 다음 오류가 발생했다.

```text
ModuleNotFoundError: No module named 'prometheus_client'
```

하지만 `ont_platform/v5/backend/requirements.txt`에는 이미 다음 의존성이 포함되어 있다.

```text
prometheus-client>=0.20.0
```

따라서 이 문제는 requirements 누락이라기보다, backend가 conda 환경 `claud_be`가 아닌 시스템 Python으로 실행된 문제일 가능성이 높다.

검증 로그의 Python 경로:

```text
C:\Users\nkchoi2\AppData\Local\Programs\Python\Python312\...
```

정상 기준 Python 경로:

```text
C:\Users\nkchoi2\anaconda3\envs\claud_be\python.exe
```

## 3. 추가한 파일

이번 후속 조치로 v5 실행 가이드를 추가했다.

```text
ont_platform/v5/RUNBOOK.md
ont_platform/v5/scripts/start_backend.ps1
ont_platform/v5/scripts/start_frontend.ps1
```

스크립트는 잘못된 conda 환경에서 실행되면 즉시 실패하도록 구성했다.

- backend script는 `claud_be`를 요구한다.
- frontend script는 `claud_fe`를 요구한다.

## 4. Backend 재검증 방법

PowerShell 새 창에서 실행한다.

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m pip install -r requirements.txt
python -c "import sys; print(sys.executable)"
python -c "import prometheus_client; print('prometheus_client ok')"
python -m uvicorn app.main:app --reload --port 8001
```

또는 추가된 스크립트를 사용한다.

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5
.\scripts\start_backend.ps1
```

확인:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8001/api/health
```

## 5. Frontend 재검증 방법

다른 PowerShell 창에서 실행한다.

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5
.\scripts\start_frontend.ps1
```

접속:

```text
http://localhost:3002
```

## 6. Claude Code에게 다시 확인시킬 항목

1. `claud_be` 환경에서 `python -c "import sys; print(sys.executable)"`가 conda Python을 가리키는지 확인한다.
2. `python -c "import prometheus_client"`가 성공하는지 확인한다.
3. v5 backend가 `8001`에서 정상 기동되는지 확인한다.
4. `GET http://localhost:8001/api/health`가 성공하는지 확인한다.
5. v5 frontend가 `3002`에서 정상 기동되는지 확인한다.
6. Template Gallery에서 템플릿 복제 후 Workflow Builder 자동 로드가 실제 브라우저에서 되는지 확인한다.
7. `/api/workflow-graphs` 저장/조회/실행이 실제 backend와 맞는지 확인한다.

## 7. 다음 개발 우선순위

1. v5 backend 기동 문제를 conda 환경 기준으로 먼저 해결한다.
2. 프론트 mock simulation과 backend workflow run API의 경계를 정리한다.
3. GraphNodeKind가 backend runner/schema와 완전히 호환되는지 검증한다.
4. LLM Gateway `8001`과 v5 backend `8001`의 포트 역할을 분리하거나 명확히 문서화한다.
5. 실제 계정 조치 기능은 approval gate, adapter registry, audit, DLQ가 준비된 뒤 연결한다.

## 8. 2026-06-11 추가 수정: `/api/hybrid/ask` 500 오류 해결

사용자가 `claud_be` 환경에서 v5 backend를 정상 기동한 뒤 `/api/hybrid/ask` 호출 시 다음 오류가 확인되었다.

```text
TypeError: EvidenceGate.check_evidence() takes 1 positional argument but 4 were given
```

원인:

- `EvidenceGate.check_evidence()`는 v5에서 keyword-only 인자를 받도록 변경되어 있었다.
- `ask_v5()` 경로는 새 인터페이스를 사용하고 있었다.
- 기존 `/api/hybrid/ask`가 호출하는 `QueryPlannerService.ask()`와 테스트용 `ask_forced_hybrid()`는 예전 positional 호출을 유지하고 있었다.

수정 파일:

```text
ont_platform/v5/backend/app/services/query_planner.py
```

수정 내용:

- 중복 `EvidenceGate` import 제거
- 중복 `self.evidence_gate = EvidenceGate()` 초기화 제거
- `ask()`에서 `QuestionAnalyzer` 결과와 `SearchMode.AUTO`를 사용해 새 `check_evidence()` 인터페이스로 호출
- `ask_forced_hybrid()`에서 `SearchMode.HYBRID`를 사용해 새 `check_evidence()` 인터페이스로 호출
- 기존 응답 생성 로직은 유지하기 위해 `EvidenceGateResult.to_dict()`로 변환

검증:

```powershell
conda run -n claud_be python -m py_compile ont_platform\v5\backend\app\services\query_planner.py
```

결과:

```text
통과
```

실제 API 검증:

```powershell
Invoke-RestMethod -Method Post `
  -Uri 'http://localhost:8001/api/hybrid/ask' `
  -ContentType 'application/json' `
  -Body (@{ query = 'Submitted 상태의 Order를 찾아줘' } | ConvertTo-Json)
```

결과:

- 500 오류 사라짐
- 근거 없음(no_direct_evidence) 정상 응답 반환

v5 전용 endpoint도 확인했다.

```powershell
Invoke-RestMethod -Method Post `
  -Uri 'http://localhost:8001/api/v5/hybrid/ask' `
  -ContentType 'application/json' `
  -Body (@{ query = 'Submitted 상태의 Order를 찾아줘'; search_mode = 'auto' } | ConvertTo-Json)
```

결과:

- 정상 응답 반환

주의:

- PowerShell 출력에서 한글 응답이 깨져 보일 수 있으나, 이는 콘솔 인코딩 표시 문제일 가능성이 높다.
- API 자체는 500이 아닌 정상 JSON을 반환한다.

## 9. 2026-06-11 추가 수정: RDF mapping endpoint 404 해결

사용자 로그에서 다음 요청이 404로 확인되었다.

```text
GET /api/ontology/mapping-candidates?external_uri=entity%3Aproject-alpha&external_label=Project%20Alpha 404 Not Found
```

해석:

- `/api/hybrid/ask`는 200으로 정상화되었다.
- 위 404는 백엔드 변경 때문이 아니라, v5 frontend RDF mapping panel이 기대하는 endpoint가 v5 backend에 아직 없어서 발생했다.
- frontend는 이미 catch fallback으로 mock 후보를 보여주고 있었지만, 백엔드 로그에는 404가 계속 남는 상태였다.

수정 파일:

```text
ont_platform/v5/backend/app/main.py
```

추가한 endpoint:

```text
GET  /api/ontology/mapping-candidates
POST /api/ontology/mappings
```

검증:

```powershell
conda run -n claud_be python -m py_compile ont_platform\v5\backend\app\main.py
```

결과:

```text
통과
```

실제 API 검증:

```powershell
Invoke-RestMethod -Method Get `
  -Uri 'http://localhost:8001/api/ontology/mapping-candidates?external_uri=entity%3Aproject-alpha&external_label=Project%20Alpha'
```

결과:

- 404 사라짐
- mapping candidate JSON 반환

저장 endpoint도 확인했다.

```powershell
Invoke-RestMethod -Method Post `
  -Uri 'http://localhost:8001/api/ontology/mappings' `
  -ContentType 'application/json' `
  -Body (@{
    externalUri='entity:project-alpha'
    externalLabel='Project Alpha'
    internalEntityId='entity:project-alpha'
    internalLabel='Project Alpha'
    relationshipType='skos:closeMatch'
    confidence=0.91
    comment='verification'
    approvalStatus='pending'
  } | ConvertTo-Json)
```

결과:

- mapping rule JSON 반환
- tenant/project ontology storage 아래 `ontology_mappings.json`에 저장

결론:

- 이 건은 frontend 수정 없이 backend API 계약을 맞추는 방식으로 해결했다.
- 나중에 실제 추천 로직을 붙일 때는 현재 demo candidate 로직을 ontology search/vector similarity 기반으로 교체하면 된다.

## 10. 2026-06-12 추가 수정: Hybrid Query 예시 데이터 입력

문제:

- `Submitted 상태인 Order를 찾아줘` 질의가 빈 저장소에서는 `온톨로지 0건`, `벡터 0건`으로 반환되었다.
- 예시 질문 버튼만으로는 실제 ontology 근거가 생성되지 않기 때문에 사용자는 기능이 동작하지 않는 것처럼 느낄 수 있다.

수정 방향:

- Hybrid Query 화면에 `예시 데이터 입력` 버튼을 추가했다.
- 버튼 클릭 시 backend seed API를 호출해 `ORDER` 예시 엔티티를 생성한다.
- 질문 입력창에는 `Submitted 상태인 Order를 찾아줘`를 자동 입력한다.
- 검색 범위는 `order-example` 문서로 자동 선택한다.

수정 파일:

```text
ont_platform/v5/backend/app/main.py
ont_platform/v5/backend/app/services/query_planner.py
ont_platform/v5/backend/app/repositories/ontology.py
ont_platform/v5/frontend/src/lib/api.ts
ont_platform/v5/frontend/src/components/HybridQuery.tsx
```

추가 backend API:

```text
POST /api/ontology/examples/order-submitted
```

생성 데이터:

- `ORDER` entity type
- `status`, `amount`, `customer`, `owner`, `submitted_at` properties
- `order-1001`: `status=Submitted`
- `order-1002`: `status=Submitted`
- `order-1003`: `status=Approved`

추가 backend 보정:

- `Submitted 상태인 Order를 찾아줘`를 `FILTER` intent로 분류하도록 보강
- `Order + Submitted/Approved/...` 패턴을 `status` property filter로 변환
- `ontology_mappings.json`처럼 list 형태의 보조 JSON 파일이 ontology document 스캔 중 오류를 만들지 않도록 repository에서 non-dict JSON을 skip

검증:

```powershell
C:\Users\nkchoi2\anaconda3\envs\claud_be\python.exe -m py_compile app\repositories\ontology.py app\services\query_planner.py app\main.py
```

결과:

```text
통과
```

실제 API 검증:

```powershell
Invoke-RestMethod -Method Post -Uri 'http://localhost:8001/api/ontology/examples/order-submitted'
```

이후:

```powershell
POST http://localhost:8001/api/hybrid/ask
body: { "query": "Submitted 상태인 Order를 찾아줘", "doc_ids": ["order-example"] }
```

결과:

- `intent`: `filter`
- `ontology_hits`: `2`
- `results`: `order-1001`, `order-1002`

결론:

- 이제 사용자가 Hybrid Query 화면에서 `예시 데이터 입력`을 누른 뒤 질의하면 실제 온톨로지 근거 2건이 반환된다.
