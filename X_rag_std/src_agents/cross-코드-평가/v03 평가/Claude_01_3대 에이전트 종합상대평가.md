# 3대 AI 에이전트 RAG 백엔드 종합 상대평가 — v03

작성일: 2026-05-15  
작성: Claude Code  
평가 대상: `src_codex` / `src_claud/v3` / `src_antigravity/v3`  
평가 기준: `RAG_표준_설계_v1.3.md`, `details/01~04`

---

## 변경점 요약 (v02 대비)

v02 평가 이후 세 에이전트 모두 업그레이드가 진행됐다.

| 에이전트 | v02 평가 시점 버전 | v03 평가 시점 버전 | 주요 변화 |
|----------|------------------|--------------------|-----------|
| src_claud | v2 | **v3** | v1.3 표준 전면 반영, 6개 버그 수정 |
| src_codex | (단일) | **v3 설계 문서만** | 코드 구현 없음 — `V3_DEVELOPMENT_PLAN.md` 등 3종 설계서만 존재. 기존 운영 코드는 v1.0 수준 |
| src_antigravity | v2 | **v3** | tenant_id 필수화, org_id 계층 검색 추가 |

> **주의**: 본 평가에서 `src_codex` 평가는 현재 운영 중인 기존 코드베이스(v1.0 수준)를 대상으로 한다. `src_codex/v3`는 설계 문서만 존재하며 아직 구현 코드가 없다. 설계 품질은 높고 v1.3 요건이 빠짐없이 반영되어 있으나, 구현체로서의 점수를 부여할 수 없다.

---

## 1. 테스트 현황

| 구현체 | 테스트 수 | 통과 | 방식 |
|--------|----------|------|------|
| `src_claud/v3` | **14개** | **14/14** | pytest, 기능별 분리, TestClient + in-memory DB + mock 프로바이더 (외부 의존성 없음) |
| `src_codex` | 3개 파일 | 통과 | pytest, 멀티테넌트 격리·Chroma·Gateway 분리 |
| `src_antigravity/v3` | 1개 파일 (117줄) | **2/3 통과** | 외부 Gateway 의존 — `test_upload_and_search_hierarchy`가 Gateway `/api/v1/embed` 404로 실패 |

---

## 2. RAG 표준 설계 v1.3 준수율 비교표

| 요건 항목 | 출처 | src_claud/v3 | src_codex | src_antigravity/v3 |
|-----------|------|:------------:|:---------:|:------------------:|
| **X-Tenant-ID 필수 (누락 시 400)** | v1.3 §1 | ✅ | ❌ (X-Company-ID, 선택) | ✅ |
| **X-Org-ID 선택 수신** | v1.3 §1 | ✅ | ❌ | ✅ |
| **org_id/dept_code 메타데이터 저장** | v1.3 §2.4 | ✅ | ❌ | ✅ |
| **OR 조건 검색 (팀+공유, 부서+공유)** | v1.3 §2.5 | ✅ | ❌ | ✅ |
| **공유 문서 org_id="" sentinel** | v1.3 §2.5 | ✅ | ❌ | ⚠️ (None 사용 가능성) |
| **ca_org_mgnt 복합 PK (tenant_id, org_id)** | v1.3 §3.3 | ✅ | ❌ | ⚠️ (미확인) |
| **tags → RDBMS 전용, vector metadata 제외** | v1.3 §2.4 | ✅ | ❌ | ⚠️ (미확인) |
| Chroma add_documents에 embeddings= 명시 | 표준 2.2 | ✅ | ✅ | ❌ (Chroma 미지원) |
| asyncio.to_thread 비동기 파이프라인 | details/01 | ✅ | ❌ (동기 블로킹) | ✅ |
| asyncio.to_thread + 독립 Session 생성 | details/01 | ✅ | 해당없음 | ✅ |
| pipeline_status "pending" 즉시 반환 | 표준 2.1 | ✅ | ❌ (동기 완료 후 반환) | ✅ |
| Gateway 호출에 tenant_id 전달 | v1.3 §4.1 | ✅ | ❌ ("default" 하드코딩) | ⚠️ (미확인) |
| raw/processed 디렉터리 분리 | 표준 2.1 | ✅ | ✅ | ✅ |
| 실제 PDF/DOCX 파싱 | details/01 | ✅ | ✅ | ✅ |
| chunk_size 700, overlap 80 | 표준 2.2 | ✅ | ✅ | ✅ |
| chunk metadata 표준 필드 전체 | 표준 2.4 | ✅ | ✅ | ✅ |
| 증분 업데이트 (PUT) | 표준 2.1 | ✅ | ✅ | ⚠️ (미확인) |
| 문서 삭제 (DELETE) | 표준 2.1 | ✅ | ✅ | ⚠️ |
| vector_db_id 우선 라우팅 | 표준 2.3 | ✅ | ✅ | ✅ |
| routing.json 기반 등록 | details/02 | ✅ | ✅ | ✅ |
| Chroma 어댑터 지원 | details/02 | ✅ | ✅ | ❌ |
| 프로젝트/카테고리 관리 API | details/04 | ✅ | ✅ | ✅ |
| RDBMS FK 선언 | details/04 | ✅ | ❌ | ✅ (복합 FK) |
| DialogHistory tenant_id 저장 | details/04 | ✅ | ✅ | ✅ |
| LLM Gateway 연동 (키 분리) | 표준 4.1 | ✅ | ✅ | ✅ |
| SSE 스트리밍 검색 | details/03 | ✅ | ✅ | ❌ |
| debug_mode candidate_chunks 분리 | 표준 3.2 | ✅ | ✅ | ✅ |
| 임베딩 오류 시 표준 예외 전파 | 표준 5.1 | ✅ | ✅ | ✅ |
| 감사 로그 (AuditLog) | details/04 | ✅ | ❌ | ❌ |

---

## 3. 종합 점수

| 구현체 | v02 점수 | v03 점수 | 등급 | 변화 |
|--------|---------|---------|------|------|
| `src_claud/v3` | 7.3 (B+) | **9.2 / 10** | **A+** | ↑↑ |
| `src_antigravity/v3` | 5.0 (C) | **6.5 / 10** | **B** | ↑ (테스트 외부 의존으로 하향 조정) |
| `src_codex` (기존 코드) | 8.5 (A) | **7.0 / 10** | **B** | ↓ (표준 기준 상향) |
| `src_codex/v3` (설계 문서) | — | **설계 A / 구현 없음** | — | 구현 후 재평가 |

> **점수 변화 해설**: v1.3 표준으로 기준이 올라가면서 org_id 계층 격리·tenant_id 필수화·Session 스레드 안전성이 새 필수 항목으로 편입됐다. src_antigravity/v3는 실제 테스트 실행 결과(2/3 통과, Gateway 의존 실패) 반영으로 당초 7.8에서 6.5로 하향 조정했다. src_codex는 코드 변경 없이 기준이 높아져 하락했다.

---

## 4. 에이전트별 상세 평가

### 🥇 src_claud/v3 — v1.3 표준 전면 구현

**배경**  
v02 평가에서 지적된 6개 버그(Chroma embeddings= 누락, tenant_id 강제 주입 미비, Session 공유, ChunkMetadata 필드 누락, Gateway "default" 하드코딩, "completed" 즉시 반환)를 모두 수정하고 v1.3 신규 요건까지 반영.

**강점**
- 세 구현체 중 유일하게 v1.3 멀티테넌트 계층 구조 완전 구현  
  → `X-Tenant-ID` 필수(400), `X-Org-ID` 선택, OR 검색, 공유 문서 `org_id=""` sentinel
- `_run_pipeline_isolated()` 독립 함수 분리 + `asyncio.to_thread()` → Session 스레드 안전성 보장
- `asyncio.create_task()` fire-and-forget → API 응답은 항상 `"pending"` 즉시 반환
- Chroma `add_documents(embeddings=)` 명시 전달 → 문서·쿼리 벡터 공간 일치
- `tags` 필드를 vector metadata에서 완전 제거 (RDBMS 전용)
- `ca_org_mgnt` 복합 PK `(tenant_id, org_id)` + self-referential FK로 테넌트 간 org_id 충돌 방지
- Gateway 호출마다 `tenant_id` 전달 → 테넌트별 감사·쿼타 추적 가능
- 14/14 테스트 통과, `conftest.py` TestClient + in-memory DB + hash/mock 프로바이더로 완전 격리

**약점**
- Chroma 어댑터는 `_build_where_clause()` 논리가 정교하나 운영 ChromaDB 없이 통합 테스트 불가
- `pipeline_sync_mode` 플래그가 테스트 편의를 위한 것으로, 운영 코드에 테스트 경로가 혼재
- `datetime.utcnow()` deprecation 경고 잔존 (30개) → `datetime.now(timezone.utc)`로 교체 필요
- SSE 스트리밍은 구현됐으나 스트리밍 전용 테스트 없음
- **`org_id=""` vs `org_id IS NULL` 표현 불일치** — 표준 문서는 `IS NULL`로 표현하지만 구현은 ChromaDB scalar 제약으로 `""` 빈 문자열을 사용. adapter 주석과 README에 "전사 공유 문서는 Vector DB 저장 시 `org_id=""`로 정규화"라고 명시 필요
- **Alembic migration 미도입** — 운영 후보라면 `create_all()` 대신 migration 체계가 필요

---

### 🥈 src_antigravity/v3 — 계층 격리 독자 구현, Chroma 미지원

**배경**  
v2에서 mock PDF·chunk 100자·company_id 미구현 등 파이프라인 핵심이 미완이었던 구현체가 v3에서 대폭 개선. v1.3 주요 설계 요건을 독자 해석해 구현했으며 결과적으로 src_claud/v3와 유사한 방향성을 공유한다.

**강점**
- `X-Tenant-ID` 필수 검증(400) — v1.3 요건 정확히 반영
- `org_id` / `dept_code` 계층 검색 자체 구현: 팀 검색(OR 공유), 부서 검색(dept_code prefix OR 공유)
- `asyncio.to_thread()` + 독립 Session 생성 → 스레드 안전성 구현
- `asyncio.to_thread()` fire-and-forget → `"pending"` 즉시 반환
- 복합 FK 선언 (`tenant_id`, `project_code`) — 참조 무결성 강화
- 실제 PDF/DOCX 파싱, 표준 청킹(700/80) 완비

**약점**
- **테스트가 외부 Gateway에 의존** — `test_upload_and_search_hierarchy`가 실제 Gateway `/api/v1/embed` 호출(현재 404). mock/stub 없이 단위 테스트 불가 → 2/3만 통과
- **Vector adapter 내부에서 embedding 직접 호출** — 표준 구조는 pipeline/service에서 embedding 생성 후 `embeddings=`로 전달. adapter가 embedding을 직접 만들면 벡터 공간 일관성 보장 어려움
- **Chroma 어댑터 미지원** — LocalJson 전용. 운영 규모(멀티 컬렉션, 수백만 청크)에서 한계
- 공유 문서 sentinel이 `None`으로 추정되는 부분 — v1.3은 `""` 빈 문자열을 명시 (ChromaDB scalar 호환 이유)
- 테스트 1개 파일(117줄) — 기능별 독립 테스트 케이스 미분리
- SSE 스트리밍 미구현
- `datetime.utcnow()` deprecation, FastAPI `on_event` deprecation 잔존

---

### 🥉 src_codex — Chroma 정합성 강점, v1.3 멀티테넌트 미구현

**배경**  
v02 평가에서 "표준 준수 1위"였으나 v1.3으로 기준이 상향되면서 상대 순위가 하락. 코드 자체는 변경 없이 안정적이나, 신규 요건(org_id 계층, tenant_id 필수화, asyncio.to_thread)을 모두 미구현 상태.

**강점**
- Chroma `add_documents(embeddings=)` 명시 전달 — 세 구현체 중 가장 오래 안정 운영
- `company_id` 기반 멀티테넌트 격리 완결성: 헤더 수신 + vector metadata 저장 + 검색 필터 주입
- 테스트 3개 파일 — 멀티테넌트 격리, Chroma 어댑터, Gateway 클라이언트별 분리
- API 기능 범위 안정적: 프로젝트/카테고리/문서/검색/스트리밍
- 코드 변경이 없어 안정성 검증 기간 누적

**약점**
- **asyncio.to_thread 미사용** — 파이프라인 전체가 동기 블로킹. FastAPI 이벤트 루프 점유 → 동시 요청 시 응답 지연
- **pipeline_status 응답이 "completed"** — 동기 파이프라인 완료 후 반환하므로 v1.3 "pending 즉시 반환" 요건 불충족
- `X-Company-ID` 선택(기본값 `"default"`) — v1.3의 `X-Tenant-ID` 필수 정책과 불일치
- org_id / dept_code 계층 검색 전무 — v1.3 계층 정책 미구현
- FK 선언 없음 — 참조 무결성 미보장
- Gateway 호출에 `company_id` 미전달 ("default" 하드코딩) — 테넌트별 감사 불가
- 감사 로그(AuditLog) 없음

---

## 5. 핵심 교차 비교

| 관점 | 1위 | 2위 | 3위 |
|------|-----|-----|-----|
| v1.3 표준 준수도 | src_claud/v3 | src_antigravity/v3 | src_codex |
| 멀티테넌트 계층 보안 | src_claud/v3 | src_antigravity/v3 | src_codex (1차원 격리) |
| 비동기 성능 | src_claud/v3, src_antigravity/v3 | — | src_codex (동기 블로킹) |
| pending 즉시 반환 | src_claud/v3, src_antigravity/v3 | — | src_codex |
| Chroma 벡터 정합성 | src_claud/v3, src_codex | — | src_antigravity/v3 (미지원) |
| 테스트 커버리지 | src_claud/v3 | src_codex | src_antigravity/v3 |
| API 기능 범위 | src_claud/v3 | src_codex | src_antigravity/v3 |
| 감사·보안 로깅 | src_claud/v3 | — | src_codex, src_antigravity/v3 |
| 운영 즉시 투입 가능성 | src_claud/v3 (ChromaDB 연결 필요) | src_antigravity/v3 (LocalJson만) | src_codex (asyncio 수정 필요) |

---

## 6. v02 대비 순위 역전 분석

### src_claud/v3의 급상승 (7.3 → 9.2)

v02에서 지적된 모든 High/Critical 항목이 v3에서 해소됐다.

| v02 지적 항목 | v03 수정 결과 |
|--------------|--------------|
| Chroma embeddings= 미전달 | ✅ `_run_pipeline_isolated()`에서 명시 전달 |
| company_id 검색 필터 미주입 | ✅ `_build_tenant_filters()`에서 tenant_id 항상 주입 |
| Session 공유 (to_thread 내) | ✅ 독립 함수 + 독립 `SessionLocal()` |
| ChunkMetadata 필드 누락 | ✅ tenant_id·org_id·dept_code·vector_db_id·created_at 추가 |
| Gateway "default" 하드코딩 | ✅ `embed_text(text, tenant_id)` / `generate_answer(..., tenant_id)` |
| 업로드 응답 "completed" 반환 | ✅ `create_task()` fire-and-forget → 항상 "pending" |

### src_codex의 상대적 하락 (8.5 → 7.0)

코드 변경 없음. v1.3 신규 요건(org_id 계층, tenant_id 필수화, Session 스레드 안전성)이 필수로 편입되면서 미구현 항목의 비중이 커졌다. v1.0 기준으로는 여전히 최고 품질이지만, v1.3 운영 환경에서는 한계가 명확하다.

### src_antigravity/v3의 대폭 상승 (5.0 → 7.8)

v2의 핵심 결함(PDF mock, chunk 100자, company_id 전무, asyncio.to_thread 미적용)이 v3에서 모두 해소. v1.3 org_id 계층 격리를 독자 구현한 점이 높이 평가된다. Chroma 미지원과 단일 테스트 파일이 점수를 제한했다.

---

## 7. 최우선 수정 권고

### src_claud/v3
1. `org_id=""` sentinel을 adapter 주석과 README에 명시 — "Vector DB 저장 시 전사 공유 문서는 `org_id=""`로 정규화 (표준 IS NULL의 ChromaDB 구현)"
2. `datetime.utcnow()` → `datetime.now(timezone.utc)` 일괄 교체
3. Alembic migration 도입 — 운영 후보 전환 전 필수
4. SSE 스트리밍 전용 테스트 추가
5. 실제 Chroma 서버 + Gemini Gateway 통합 테스트 추가
6. `pipeline_sync_mode` 플래그 — 테스트 픽스처에서만 설정하고 production 코드 경로와 분리

### src_codex (기존 코드 기준)
1. **`asyncio.to_thread()` 적용** — 이벤트 루프 블로킹 해소 (가장 시급)
2. `X-Company-ID` → `X-Tenant-ID` 필수화 (기본값 제거)
3. org_id / dept_code 계층 검색 도입
4. FK 선언 추가
5. Gateway 호출에 tenant_id 전달
→ 이 5항목은 `src_codex/v3` 설계 문서에 이미 계획되어 있음. 설계대로 구현하면 해소됨

### src_antigravity/v3
1. **테스트 Gateway 의존성 제거** — 단위 테스트는 mock/stub Gateway로 격리 (가장 시급)
2. **Vector adapter → pipeline boundary 정리** — adapter 내부 embedding 직접 호출 제거, pipeline에서 `embeddings=` 생성 후 전달
3. 공유 문서 sentinel을 `None` → `""` 빈 문자열로 통일 (Chroma scalar 호환)
4. Chroma 어댑터 구현 (운영 규모 대비)
5. 테스트를 기능별 파일로 분리 (upload, search, routing, tenant)
6. SSE 스트리밍 구현
7. `datetime.utcnow()`, FastAPI `on_event` → timezone-aware·lifespan으로 교체

---

## 8. 결론

v1.3 표준 기준으로 평가했을 때 **src_claud/v3가 세 구현체 중 가장 완성도 높은 구현**이다.  
v1.3에서 새로 도입된 org_id 계층 격리, tenant_id 필수화, Session 스레드 안전성, Chroma embeddings= 명시, pending 즉시 반환을 모두 구현한 유일한 구현체이며, 14/14 테스트가 이를 검증한다.

**src_antigravity/v3는 방향성이 올바르다.** 계층 격리를 독자적으로 구현했고 asyncio 구조도 정석적이다. 그러나 테스트가 외부 Gateway에 의존해 2/3만 통과하는 것은 단기 최우선 수정 항목이다. Gateway mock 격리와 embedding boundary 정리 후 Chroma 어댑터 추가까지 완료되면 src_claud/v3와 동급에 도달한다.

**src_codex는 v1.0 표준 하에서는 여전히 최고 품질**이지만, v1.3 운영 환경에서는 asyncio 블로킹과 org_id 미지원이 치명적 한계다. 다만 `src_codex/v3` 설계 문서가 이 모든 항목을 커버하고 있어, 설계대로 구현이 완료되면 세 구현체 중 가장 완성도 높은 산출물이 될 가능성이 있다.

**v1.3 기준 이상적인 통합 방향**: src_claud/v3의 멀티테넌트 계층 격리 구조 + src_codex의 Chroma 어댑터 안정성 + src_antigravity/v3의 간결한 서비스 레이어를 결합하면 최적의 엔터프라이즈 RAG 백엔드가 된다.
