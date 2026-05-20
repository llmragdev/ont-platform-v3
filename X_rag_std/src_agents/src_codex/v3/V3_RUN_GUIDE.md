# src_codex v3 실행 가이드

작성일: 2026-05-15

이 문서는 `src_codex` v3 개발/검증을 위한 전용 실행 가이드이다. 모든 명령은 Windows PowerShell 기준이며, 복사해서 실행할 수 있도록 절대 경로 `cd E:\...`를 포함한다.

> 현재 v3는 `src_agents\src_codex\v3` 아래에 실제 FastAPI 코드와 테스트를 포함한다. 이 가이드는 v3 구현체를 직접 실행하고 검증하는 절차를 설명한다.

## 1. 전체 실행 구성

v3 기준 권장 포트는 다음과 같다.

| 서비스 | 경로 | 포트 |
|--------|------|------|
| Gemini LLM Gateway | `E:\ontology_edu\X_rag_std\src_agents\llm_gateway` | `8010` |
| src_codex RAG API | `E:\ontology_edu\X_rag_std\src_agents\src_codex\v3` | `8020` |
| Chroma 선택 실행 시 | 외부/별도 프로세스 | `8001` |

RAG API가 Gemini API key를 직접 갖지 않는다. Gemini API key는 `llm_gateway\.env`에서만 관리한다.

## 2. LLM Gateway 실행

### 2.1. Gateway 폴더로 이동

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
```

### 2.2. 폴더 기준 conda 가상환경 생성 또는 갱신

Gateway는 `llm_gateway` 폴더 안의 `.\.conda`를 전용 가상환경으로 사용한다. 전역 conda 환경 이름을 쓰지 않는다.

처음 실행하는 경우:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
conda create --prefix .\.conda python=3.11 -y
```

가상환경 활성화:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
conda activate .\.conda
```

Python 경로 확인:

```powershell
python -c "import sys; print(sys.executable)"
```

정상 예:

```text
E:\ontology_edu\X_rag_std\src_agents\llm_gateway\.conda\python.exe
```

### 2.3. Gateway 의존성 설치

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
pip install -r requirements.txt
```

이미 환경이 있는 경우에도 같은 명령으로 의존성을 갱신한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
conda activate .\.conda
pip install -r requirements.txt
```

### 2.4. 환경 파일 준비

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
Copy-Item .env.example .env -Force
notepad .env
```

`.env`에 Gemini API key를 설정한다.

```env
GEMINI_API_KEY=your_gemini_api_key_here

# 선택
# GEMINI_EMBED_MODEL=models/gemini-embedding-001
# GEMINI_LLM_MODEL=gemini-2.5-flash-lite
```

### 2.5. Gateway 서버 실행

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
conda activate .\.conda
python -m uvicorn app.main:app --port 8010 --reload
```

가상환경을 활성화하지 않고 실행하려면:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
.\.conda\python.exe -m uvicorn app.main:app --port 8010 --reload
```

### 2.6. Gateway 상태 확인

새 PowerShell 창에서 실행한다.

```powershell
curl.exe http://localhost:8010/api/v1/health
```

Gateway는 v3 기준으로 `tenant_id`를 받는다. 기존 v2 호환을 위해 `company_id`도 보조 필드로 받을 수 있지만, v3 RAG 서버는 `tenant_id`만 전송한다.

Gateway 임베딩 확인:

```powershell
curl.exe -X POST "http://localhost:8010/api/v1/embed" `
  -H "Content-Type: application/json" `
  -d "{\"text\":\"테스트 문장\",\"tenant_id\":\"company_abc\"}"
```

## 3. src_codex RAG API 실행

### 3.1. RAG 폴더로 이동

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
```

### 3.2. conda 환경 생성 또는 갱신

RAG API도 `src_codex\v3` 폴더 안의 `.\.conda`를 전용 가상환경으로 사용한다. Gateway의 `.\.conda`와 분리한다.

처음 실행하는 경우:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
conda env create --prefix .\.conda --file environment.yml
```

이미 환경이 있는 경우:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
conda env update --prefix .\.conda --file environment.yml --prune
```

### 3.3. conda 환경 활성화

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
conda activate .\.conda
```

Python 경로 확인:

```powershell
python -c "import sys; print(sys.executable)"
```

정상 예:

```text
E:\ontology_edu\X_rag_std\src_agents\src_codex\v3\.conda\python.exe
```

## 4. RAG API 환경변수 설정

### 4.1. 로컬 JSON VectorDB + Mock LLM

Gemini Gateway 없이 빠르게 서버만 확인할 때 사용한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
$env:DATABASE_URL = "sqlite:///./storage/metadata.db"
$env:VECTOR_DB_ENGINE = "local_json"
$env:EMBEDDING_PROVIDER = "hash"
$env:LLM_PROVIDER = "mock"
```

### 4.2. Gemini Gateway 연동

Gateway를 8010 포트에서 먼저 실행한 뒤 사용한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
$env:DATABASE_URL = "sqlite:///./storage/metadata.db"
$env:VECTOR_DB_ENGINE = "local_json"
$env:EMBEDDING_PROVIDER = "gemini_http"
$env:LLM_PROVIDER = "gemini_http"
$env:LLM_GATEWAY_URL = "http://localhost:8010"
```

### 4.3. Chroma 사용 시

Chroma 서버가 별도 실행되어 있어야 한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
$env:DATABASE_URL = "sqlite:///./storage/metadata.db"
$env:VECTOR_DB_ENGINE = "chroma"
$env:CHROMA_HOST = "localhost"
$env:CHROMA_PORT = "8001"
$env:EMBEDDING_PROVIDER = "gemini_http"
$env:LLM_PROVIDER = "gemini_http"
$env:LLM_GATEWAY_URL = "http://localhost:8010"
```

## 5. RAG API 서버 실행

Gateway와 포트가 충돌하지 않도록 RAG API는 `8020` 포트를 사용한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
conda activate .\.conda
python -m uvicorn main:app --reload --port 8020
```

가상환경을 활성화하지 않고 실행하려면:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
.\.conda\python.exe -m uvicorn main:app --reload --port 8020
```

상태 확인:

```powershell
curl.exe http://localhost:8020/api/v1/health
```

Swagger UI:

```text
http://localhost:8020/docs
```

## 5.1. Alembic migration 적용

운영 DB에서는 서버 기동 전에 Alembic migration을 적용한다. 로컬 SQLite는 앱 시작 시 `Base.metadata.create_all()`로도 생성되지만, v3 표준 운영 경로는 Alembic을 기준으로 한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
conda activate .\.conda
python -m alembic upgrade head
```

## 6. v3 기준 문서 업로드 테스트

v3 완료 후에는 `X-Tenant-ID`가 필수이다. `X-Org-ID`는 선택이며, 없을 경우 v1.3 정책에 따라 관리자/일반 사용자 권한별로 처리한다.

샘플 파일 생성:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$file = "E:\ontology_edu\X_rag_std\src_agents\src_codex\v3\sample_v3.txt"
"인사 규정 문서입니다. 휴가 규정은 연 15일입니다." | Set-Content -Encoding UTF8 $file
```

팀 소유 문서 업로드:

```powershell
curl.exe -X POST "http://localhost:8020/api/v1/documents/upload" `
  -H "X-Tenant-ID: company_abc" `
  -H "X-Org-ID: 0102" `
  -F "file=@$file" `
  -F "category_mid=policy"
```

부서 공통 소유 문서 업로드:

```powershell
curl.exe -X POST "http://localhost:8020/api/v1/documents/upload" `
  -H "X-Tenant-ID: company_abc" `
  -H "X-Org-ID: 0100" `
  -F "file=@$file" `
  -F "category_mid=policy"
```

전사 공유 문서 업로드는 `org_id IS NULL` 저장 정책을 따라야 한다. 구현에서는 관리자/시스템 권한에서만 허용하는 것을 기본으로 한다.

```powershell
curl.exe -X POST "http://localhost:8020/api/v1/documents/upload" `
  -H "X-Tenant-ID: company_abc" `
  -F "file=@$file" `
  -F "category_mid=policy"
```

## 7. v3 기준 RAG 검색 테스트

### 7.1. 팀 검색

팀 검색은 팀 문서와 전사 공유 문서를 반환해야 한다.

```powershell
curl.exe -X POST "http://localhost:8020/api/v1/rag/search" `
  -H "Content-Type: application/json" `
  -H "X-Tenant-ID: company_abc" `
  -H "X-Org-ID: 0102" `
  -d "{\"query\":\"휴가 규정 알려줘\",\"top_k\":3,\"debug_mode\":true,\"filters\":{\"category_mid\":\"policy\"}}"
```

적용 필터 의미:

```text
tenant_id == "company_abc" AND (org_id == "0102" OR org_id IS NULL)
```

### 7.2. 부서 검색

부서 검색은 해당 부서 문서와 전사 공유 문서를 반환해야 한다.

```powershell
curl.exe -X POST "http://localhost:8020/api/v1/rag/search" `
  -H "Content-Type: application/json" `
  -H "X-Tenant-ID: company_abc" `
  -H "X-Org-ID: 0100" `
  -d "{\"query\":\"휴가 규정 알려줘\",\"top_k\":3,\"debug_mode\":true,\"filters\":{\"category_mid\":\"policy\"}}"
```

적용 필터 의미:

```text
tenant_id == "company_abc" AND (dept_code == "01" OR org_id IS NULL)
```

### 7.3. 전사 검색

전사 검색은 관리자/시스템 토큰에서만 허용한다. 일반 사용자는 `X-Org-ID`가 없으면 사용자 소속 `org_id`로 자동 보정되거나 403을 받아야 한다.

```powershell
curl.exe -X POST "http://localhost:8020/api/v1/rag/search" `
  -H "Content-Type: application/json" `
  -H "X-Tenant-ID: company_abc" `
  -d "{\"query\":\"휴가 규정 알려줘\",\"top_k\":3,\"debug_mode\":true,\"filters\":{\"category_mid\":\"policy\"}}"
```

## 8. v3 필수 오류 확인

`X-Tenant-ID`가 없으면 400이어야 한다.

```powershell
curl.exe -i -X POST "http://localhost:8020/api/v1/rag/search" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"휴가 규정 알려줘\",\"top_k\":3,\"debug_mode\":false,\"filters\":{\"category_mid\":\"policy\"}}"
```

기대 오류 형식:

```json
{
  "status": "error",
  "error_code": "tenant_header_required",
  "message": "X-Tenant-ID header is required",
  "data": null
}
```

## 9. v3 코드 검증

v3 구현체는 `X-Tenant-ID`를 사용한다. `X-Company-ID`는 운영 경로에서 제거되었다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
.\.conda\python.exe test_endpoints.py
```

pytest:

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
.\.conda\python.exe -m pytest -q
```

## 10. v3 완료 검증 체크리스트

v3 구현 완료 후 아래 명령이 모두 성공해야 한다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
.\.conda\python.exe -m pytest -q
```

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex\v3
.\.conda\python.exe test_endpoints.py
```

필수 확인 항목:

- `X-Tenant-ID` 누락 시 400
- `X-Company-ID` 운영 경로 제거
- Gateway 요청에 `tenant_id` 전달
- Vector metadata에 `tenant_id`, `org_id`, `dept_code`, `vector_db_id`, `created_at` 저장
- Vector metadata에 `tags` 미저장
- 팀 검색에서 팀 문서 + 전사 공유 문서 반환
- 부서 검색에서 부서 문서 + 전사 공유 문서 반환
- 타 tenant 문서 미반환
- Chroma 저장 시 `embeddings=` 명시
- PDF chunk `page_no`가 실제 페이지 번호
- worker thread에서 SQLAlchemy Session 공유 없음

## 11. 종료

각 서버 창에서 `Ctrl+C`를 눌러 종료한다.

conda 환경 비활성화:

```powershell
conda deactivate
```

