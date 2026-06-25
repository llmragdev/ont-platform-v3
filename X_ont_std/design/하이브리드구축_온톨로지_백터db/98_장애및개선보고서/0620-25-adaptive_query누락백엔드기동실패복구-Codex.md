# 0620-25 adaptive_query 누락으로 인한 백엔드 기동 실패 복구

**작성일:** 2026-06-20  
**작성자:** Codex  
**대상:** ont_platform v5 backend  
**상태:** 코드 복구 완료, 프로세스 재시작 필요

---

## 1. 장애 현상

백엔드 재시작 중 다음 오류로 ASGI 앱 로딩이 실패했다.

```text
ImportError: cannot import name 'adaptive_query' from 'app.api'
Location: app/main.py line 460
```

`app/main.py`는 다음 라우터를 import하고 있었다.

```python
from app.api import adaptive_query
app.include_router(adaptive_query.router)
```

하지만 실제 디렉터리에 `adaptive_query.py` 파일이 없었다.

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\app\api\adaptive_query.py
```

---

## 2. 원인

SSE 질의 엔드포인트 구현 파일이 누락되어 백엔드 import 단계에서 실패했다.

영향 범위:

- 백엔드 앱 기동 실패
- `/api/v1/projects/{project_id}/query/stream` SSE 질의 API 사용 불가
- 프론트 질의 탭 사용 불가

---

## 3. 조치

`adaptive_query.py`를 재작성 복구했다.

복구된 기능:

- `APIRouter(prefix="/api/v1/projects/{project_id}/query")`
- `GET /stream`
- EventSource 호환 SSE 스트리밍
- RAG 검색 연동
- Ontology 검색 연동
- Reranker fallback
- Mock 출처 제거 상태 유지
- 온톨로지 역할 질문 구조화 답변
- `coverage_check` 메타데이터 반환
- EventSource 헤더 제약 대응용 project scoped context

---

## 4. 검증

문법 검증:

```powershell
python -m py_compile app\api\adaptive_query.py app\main.py
```

결과:

```text
PASS
```

앱 import 검증:

```powershell
@'
import app.main
print('IMPORT_OK')
'@ | python -
```

결과:

```text
IMPORT_OK
```

---

## 5. 현재 프로세스 상태

`netstat` 확인 결과 8001 포트는 열려 있으나, 실제 앱 child process가 정상 응답하지 않고 reloader 프로세스만 남은 상태로 보인다.

```text
127.0.0.1:8001 LISTENING 32728
```

HTTP 확인:

```text
/docs timeout
/api/v1/projects/.../query/stream timeout
```

따라서 코드 복구 후 백엔드 프로세스의 깨끗한 재시작이 필요하다.

---

## 6. 다음 조치

1. 현재 백엔드 터미널에서 `Ctrl + C`
2. 백엔드 재시작
3. `/docs` 응답 확인
4. SSE 질의 API 확인
5. UI에서 RAG/Ontology 탭 확인

---

## 7. 최종 판단

코드 수준의 import 장애는 복구 완료다.

남은 작업은 런타임 프로세스 재시작 및 UI/SSE 재검증이다.
