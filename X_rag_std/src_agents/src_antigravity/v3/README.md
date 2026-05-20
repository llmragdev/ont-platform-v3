# Antigravity v3 실행 및 REST API 테스트 가이드

본 가이드는 `RAG_표준_설계_v1.3`이 적용된 Antigravity v3를 기동하고, 자동화된 REST API 테스트를 수행하는 방법을 설명합니다.

---

## 1. 환경 준비 및 의존성 설치

먼저 터미널(명령 프롬프트 또는 PowerShell)을 열고 v3 디렉토리로 이동하여 필요한 패키지를 설치합니다.

```powershell
# 1. v3 디렉토리로 이동
cd E:\ontology_edu\X_rag_std\src_agents\src_antigravity\v3

# 2. 가상환경 활성화 (기존 v2 환경이 있다면 그대로 사용 가능)
conda activate ./env

# 3. v3 전용 필수 패키지 설치 (PDF/Docx 파싱용)
pip install pypdf python-docx
```

---

## 2. LLM Gateway 기동 (사전 준비)

RAG 검색 및 임베딩을 위해 LLM Gateway가 먼저 실행되어 있어야 합니다.

```powershell
# 1. LLM Gateway 디렉토리로 이동
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway

# 2. Gateway 서버 실행 (기본 8010 포트)
python main.py
```

---

## 3. API 서버 기동

서버를 기동하여 REST API 요청을 받을 준비를 합니다.

```powershell
# v3 디렉토리 내에서 실행
uvicorn main:app --reload --port 8000
```
*   서버가 정상 기동되면 `http://127.0.0.1:8000`에서 API를 호출할 수 있습니다.
*   **Swagger UI 확인**: `http://127.0.0.1:8000/docs`

---

## 3. 자동화된 REST API 테스트 수행

서버가 띄워진 상태에서(혹은 별도로) `pytest`를 통해 표준 준수 여부를 자동 테스트합니다. 
`pytest`는 내부적으로 FastAPI의 `TestClient`를 사용하여 실제 HTTP 요청을 시뮬레이션합니다.

```powershell
# 새 터미널을 열고 v3 디렉토리로 이동
cd E:\ontology_edu\X_rag_std\src_agents\src_antigravity\v3

# 가상환경 활성화
conda activate ./env

# 테스트 실행 (테넌트 격리, 계층 검색, 메타데이터 CRUD 포함)
pytest test_v3_standard.py -v
```

---

## 4. 주요 API 수동 테스트 (Curl 예시)

Swagger 대신 터미널에서 직접 호출해보고 싶을 때 사용하세요.

### 4.1. 프로젝트 생성 (멀티테넌트)
```powershell
curl -X POST "http://127.0.0.1:8000/api/v1/meta/projects" `
     -H "X-Tenant-ID: my_company" `
     -H "Content-Type: application/json" `
     -d "{\"project_code\": \"PROJ01\", \"project_name\": \"신규 프로젝트\"}"
```

### 4.2. 문서 업로드 (부서/팀 지정)
```powershell
curl -X POST "http://127.0.0.1:8000/api/v1/documents/upload" `
     -H "X-Tenant-ID: my_company" `
     -H "X-Org-ID: 0102" `
     -F "file=@sample.pdf" `
     -F "category_mid=manual"
```

---

## 5. v3 아키텍처 특징 (v1.3 표준)
*   **Strict Header**: `X-Tenant-ID` 누락 시 즉시 400 에러를 반환합니다.
*   **Hierarchical Search**: 팀(0102) 검색 시 해당 팀 문서와 전사 공유 문서를 함께 검색합니다.
*   **Composite Keys**: DB 레벨에서 테넌트와 프로젝트 코드를 복합키로 관리하여 데이터 충돌을 방지합니다.
*   **Thread Safety**: 비동기 파이프라인 실행 시 독립된 DB 세션을 사용하여 안정성을 확보했습니다.
