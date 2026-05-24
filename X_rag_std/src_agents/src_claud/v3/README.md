# src_claud v3

**RAG 표준 설계 v1.6 기준** — 기본 개발 가이드(v1.1.docx) 구현체

본 프로젝트는 엔터프라이즈 RAG 시스템의 기본 구현을 제공합니다.
- 멀티테넌트 격리 (`tenant_id` 필수)
- 계층적 지식 공유 (`org_id` 선택)
- 문서 업로드 → 벡터 DB 저장 → RAG 검색의 전체 흐름
- ChromaDB / 로컬 JSON 벡터DB 지원

## 환경 설치

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
conda create --prefix ./env python=3.11 -y
conda activate ./env
pip install -r requirements.txt
```

## 기동 순서

### 1. ChromaDB 서버 (운영 시)

```bash
pip install chromadb
chroma run --host localhost --port 8001
```

### 2. LLM Gateway

```bash
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
uvicorn app.main:app --port 8010 --reload
```

### 3. RAG 서버

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
set EMBEDDING_PROVIDER=gemini_http
set LLM_PROVIDER=gemini_http
set LLM_GATEWAY_URL=http://localhost:8010
set VECTOR_DB_ENGINE=chroma
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
uvicorn app.main:app --port 8000 --reload
```

API 문서: http://localhost:8000/docs

## 필수 헤더

모든 요청에 `X-Tenant-ID` 헤더 필수 — 누락 시 400 반환.

```
X-Tenant-ID: company_abc       # 필수
X-Org-ID: 0102                 # 선택 (없으면 관리자/전사 범위 검색)
```

## org_id 계층 검색 정책

| X-Org-ID | 검색 범위 |
|----------|-----------|
| 없음 | 해당 tenant 전체 |
| `0102` (팀) | `org_id == "0102"` OR `org_id == ""` (전사 공유) |
| `0100` (부서장) | `dept_code == "01"` OR `org_id == ""` (전사 공유) |

**구현 노트 — `org_id=""` sentinel**  
표준 설계 문서는 전사 공유 문서를 `org_id IS NULL`로 표기하지만, ChromaDB metadata는 `None`을 지원하지 않는다.  
따라서 Vector DB 저장 시 `org_id = org_id or ""` 로 정규화해 빈 문자열을 sentinel로 사용한다.  
RDBMS(`wc_project_rag_doc.org_id`)에는 `NULL`이 그대로 저장된다 — 계층이 다른 매체임에 주의.

## 벡터DB 엔진 선택

| 환경변수 | 값 | 동작 |
|----------|-----|------|
| `VECTOR_DB_ENGINE` | `local_json` (기본) | JSON 파일 저장 — ChromaDB 불필요 |
| `VECTOR_DB_ENGINE` | `chroma` | ChromaDB HTTP 연결 |
| `CHROMA_HOST` | `localhost` (기본) | ChromaDB 호스트 |
| `CHROMA_PORT` | `8001` (기본) | ChromaDB 포트 |

---

## 테스트 데이터 정의

본 구현체는 다중 프로젝트/조직 테스트를 위해 다음 데이터를 하드코딩으로 지원합니다.

### 테넌트 & 조직

```
tenant_id: "company_abc"  (고정)
```

**org_id 계층 코드** (`{DD}{TT}` 형식)

| org_id | 설명 | 검색 범위 |
|--------|------|---------|
| (없음) | 전사 범위 | 전체 tenant 문서 |
| `"0100"` | 영업부 전체 | 영업부 + 전사 공유 |
| `"0101"` | 영업부 1팀 | 0101팀 + 0100(부서) + 전사 |
| `"0102"` | 영업부 2팀 | 0102팀 + 0100(부서) + 전사 |
| `"0200"` | HR부 전체 | HR부 + 전사 공유 |
| `"0201"` | HR부 1팀 | 0201팀 + 0200(부서) + 전사 |
| `""` (빈 문자열) | 전사 공유 | 모든 조직에서 검색 가능 |

### 프로젝트 & 카테고리

| project_code | category_large | category_mid | vector_db_id | 설명 |
|--------------|----------------|--------------|--------------|------|
| `HR001` | 인사 | 채용 | `vdb_hr_recruit_01` | 채용 공고 및 지원자 정보 |
| `HR002` | 인사 | 급여 | `vdb_hr_payroll_01` | 급여 규정 및 계산 기준 |
| `POLICY001` | 규정 | 취업규칙 | `vdb_policy_01` | 취업 규칙 및 복리후생 |
| `TECH001` | 기술 | ontology | `vdb_ontology_01` | 온톨로지 표준 및 가이드 |

### 테스트 시나리오 예시

**시나리오 1: HR001 프로젝트에 채용 공고 업로드 (팀 단위)**
```
X-Tenant-ID: company_abc
X-Org-ID: 0101  (영업부 1팀)

POST /api/v1/documents/upload
- file: recruitment_2026.pdf
- category_large: "인사"
- category_mid: "채용"
- project_code: "HR001"
```

**시나리오 2: 검색 (조직별 권한 검증)**
```
부서장(0100) 검색 시:
- 영업부 전체 + 전사 공유 문서 모두 조회

팀원(0102) 검색 시:
- 0102팀 + 부서(0100) + 전사 공유만 조회
```

**시나리오 3: 전사 공유 문서 업로드**
```
X-Tenant-ID: company_abc
X-Org-ID: (없음 또는 요청 제외)

org_id=""로 저장 → 모든 조직에서 검색 가능
```

---

## API 엔드포인트 개요

### RAG 검색
- `POST /api/v1/rag/search` — 일반 검색 (동기)
- `POST /api/v1/rag/search/stream` — SSE 스트리밍 검색

### 문서 관리
- `POST /api/v1/documents/upload` — 문서 업로드
- `GET /api/v1/documents` — 문서 목록 조회
- `GET /api/v1/documents/{doc_id}` — 문서 상태 조회
- `PUT /api/v1/documents/{doc_id}` — 문서 재업로드
- `DELETE /api/v1/documents/{doc_id}` — 문서 삭제

### 벡터DB 관리 (관리자)
- `GET /api/v1/admin/vector-dbs` — 벡터 DB 목록 조회
- `POST /api/v1/admin/index-swap` — Index Swap 실행

**자세한 내용**: 기동 후 http://localhost:8000/docs 에서 Swagger 문서 확인

---

## 테스트

### AI Lab 6개 PDF 업로드 자동화

QA 통합테스트 전 사전 준비로 `E:\ai_lab_SIT\target_doc`의 NLP PDF 6개를 v3 RAG 서버에 업로드할 수 있다.

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
python upload_automation_target6.py
```

자세한 절차는 `upload_automation_target6.md`를 참고한다.

### 단위 테스트 (자동 실행)

서버 기동 불필요 — TestClient + 인메모리 DB + hash/mock 프로바이더로 독립 실행.

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v3
pytest tests/ -v
```

**결과**: 28개 테스트 중 24개 통과 (멀티테넌트, org_id 계층, E2E 모두 ✅)

### 통합 테스트 (AI Lab 실제 데이터)

ai_lab의 실제 PDF 파일(NLP, 국방 관련 8개)을 사용한 통합테스트:

```bash
# 1. 서버 기동 (로컬 모드)
set VECTOR_DB_ENGINE=local_json
uvicorn app.main:app --port 8000 --reload

# 2. 다른 터미널에서 통합테스트 실행
python integration_test_ailab.py
```

**테스트 단계**:
1. **업로드** — 8개 PDF를 프로젝트별로 분류 후 업로드
2. **확인** — 저장된 문서 목록 조회
3. **검색** — 온톨로지, NLP, AI 등 키워드로 RAG 검색
4. **요약** — 성공/실패 통계

**테스트 데이터**:
- 경로: `zz-ai lab 통합테스트/rag_target_files/`
- 파일: 8개 실제 PDF (NLP, 국방)
- 프로젝트: TECH001 (기술), POLICY001 (규정)
- 조직: 0100 (영업부), 0200 (HR부)

### 테스트 커버리지

- ✅ 멀티테넌트 격리 (X-Tenant-ID 필수 검증)
- ✅ org_id 계층 검색 (OR 조건)
- ✅ 문서 업로드 → 벡터 저장 → 검색 전체 흐름
- ✅ 에러 처리 (400, 404, 500)

---

## 구현 참고

| 항목 | 문서 |
|------|------|
| 기본 개발 가이드 | `RAG 개발 가이드_v1.1.docx` |
| 상세 설계 참고 | `RAG_표준_설계_v1.6.md` |
| 테스트 데이터 | 본 문서 "테스트 데이터 정의" 섹션 |
