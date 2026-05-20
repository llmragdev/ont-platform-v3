# 3대 AI 에이전트 RAG 백엔드 종합 상대평가

작성일: 2026-05-14  
작성: Claude Code  
평가 대상: `src_codex` / `src_claud/v2` / `src_antigravity/v2`  
평가 기준: `RAG_표준_설계_v1.0.md`, `details/01~04`

---

## 1. 테스트 통과 현황

| 구현체 | 테스트 수 | 통과 | 비고 |
|--------|----------|------|------|
| `src_codex` | 14개 | 14/14 | pytest, 기능별 분리 |
| `src_claud/v2` | 14개 | 14/14 | pytest + conftest fixture |
| `src_antigravity/v2` | 1개 | 1/1 | 단일 통합 테스트 |

테스트 수와 범위에서 `src_codex`와 `src_claud/v2`가 동급, `src_antigravity/v2`는 크게 미달.

---

## 2. 표준 설계 준수율 비교표

| 요건 항목 | 출처 | src_codex | src_claud/v2 | src_antigravity/v2 |
|-----------|------|:---------:|:------------:|:------------------:|
| 문서 상태 전이 (pending→completed/error) | 표준 2.1 | ✅ | ✅ | ✅ |
| raw/processed 디렉터리 분리 | 표준 2.1 | ✅ | ✅ | ❌ |
| 실제 PDF/DOCX 파싱 | details/01 | ✅ pypdf | ✅ pypdf+docx | ❌ Mock fallback |
| chunk_size 500~800, overlap 50~100 | 표준 2.2 | ✅ 700/80 | ✅ 700/80 | ❌ 100자 하드코딩 |
| chunk metadata 표준 필드 전체 포함 | 표준 2.4 | ✅ | ⚠️ vector_db_id 누락 | ❌ doc_id 등 다수 누락 |
| 증분 업데이트 (PUT endpoint) | 표준 2.1 | ✅ | ✅ | ❌ |
| 문서 삭제 (DELETE endpoint) | 표준 2.1 | ✅ | ✅ | ❌ |
| vector_db_id 우선 라우팅 | 표준 2.3 | ✅ | ✅ | ⚠️ 하드코딩 |
| routing.json 기반 등록 | details/02 | ✅ | ✅ | ❌ |
| Chroma 어댑터 | details/02 | ✅ | ✅ | ❌ |
| Chroma add_documents에 embeddings= 명시 | details/02 | ✅ | ❌ | 해당없음 |
| X-Company-ID 헤더 수신 | 표준 3.1 | ✅ | ✅ | ❌ |
| vector metadata에 company_id 저장 | 표준 3.1 | ✅ | ❌ | ❌ |
| 검색 필터에 company_id 강제 주입 | 표준 3.1 | ✅ | ❌ | ❌ |
| debug_mode 시 candidate_chunks 분리 | 표준 3.2 | ✅ | ✅ | ✅ |
| asyncio.to_thread 비동기 파이프라인 | details/01 | ❌ (동기) | ✅ | ✅ |
| asyncio.to_thread + Session 스레드 안전 | details/01 | 해당없음 | ❌ | ❌ |
| 프로젝트/카테고리 관리 API | details/04 | ✅ | ✅ | ❌ |
| RDBMS FK 선언 | details/04 | ❌ | ✅ (v2에서 추가) | ❌ |
| wc_category.vector_db_id 컬럼 | details/04 | ✅ | ✅ | ❌ |
| DialogHistory.company_id | details/04 | ✅ | ✅ | ❌ |
| LLM Gateway 연동 (키 분리) | 표준 4.1 | ✅ | ✅ | ✅ |
| Gateway 호출에 실제 company_id 전달 | 표준 4.1 | ✅ | ❌ (default 하드코딩) | ❌ |
| 스트리밍 검색 (SSE) | details/03 | ✅ | ✅ | ❌ |
| 임베딩 오류 시 표준 예외 전파 | 표준 5.1 | ✅ | ✅ | ❌ ([0.1,0.2] fallback) |

---

## 3. 종합 점수

| 구현체 | 점수 | 등급 |
|--------|------|------|
| `src_codex` | **8.5 / 10** | A |
| `src_claud/v2` | **7.3 / 10** | B+ |
| `src_antigravity/v2` | **5.0 / 10** | C |

---

## 4. 에이전트별 상세 평가

### 🥇 src_codex — 표준 준수 1위

**강점**
- 세 구현체 중 유일하게 company_id 멀티테넌트 격리를 완전 구현(헤더 수신 + vector metadata 저장 + 검색 필터 강제 주입)
- Chroma add_documents 시 embeddings= 명시 전달 → 문서/쿼리 벡터 공간 일치 보장
- 표준 chunk metadata 필드 전체 포함(doc_id, source_url, created_at, vector_db_id, category_mid, company_id)
- Gateway 호출 시 실제 company_id 전달 → 테넌트별 감사·쿼타 관리 가능
- 증분 업데이트, 삭제, 스트리밍, 프로젝트/카테고리 API까지 표준 요건 대부분 구현

**약점**
- `asyncio.to_thread` 미적용 — FastAPI 이벤트 루프 블로킹 (가장 치명적인 미해결 이슈)
- FK 선언 없음 (참조 무결성 미보장)
- page_no가 실제 PDF 페이지 번호가 아닌 chunk 인덱스
- datetime.utcnow() deprecation 경고 다수

---

### 🥈 src_claud/v2 — 아키텍처 범위 최대

**강점**
- API 범위 최대: 프로젝트/카테고리 CRUD, 문서 삭제, SSE 스트리밍, 감사 로그, 헬스체크까지 구현
- ABC 인터페이스 + providers.py 팩토리 패턴으로 LLM/임베딩/벡터DB 교체 가능 구조
- FK 선언 추가(v2에서), FastAPI lifespan 패턴, conftest 기반 테스트 격리
- VECTOR_DB_ENGINE 환경변수로 local_json/chroma 선택 지원

**약점**
- Chroma add_documents에 embeddings= 미전달 → Chroma 기본 임베딩과 쿼리 임베딩 공간 불일치 위험
- vector chunk metadata에 company_id, vector_db_id, created_at 누락
- RAG 검색 필터에 company_id 미강제 주입 → 멀티테넌트 격리 불완전
- asyncio.to_thread 내에서 동일 SQLAlchemy Session 공유 → 운영 간헐적 DB 오류 가능
- Gateway LLM/임베딩 호출에 company_id "default" 하드코딩

---

### 🥉 src_antigravity/v2 — 비동기 구조 도입, 기능 미달

**강점**
- asyncio.to_thread 적용으로 이벤트 루프 블로킹 문제 구조적 해소
- LLM Gateway 연동 방향 올바름
- debug_mode 시 candidate_chunks vs used_chunks 분리 구조 준수

**약점**
- PDF 파싱이 Mock — 실제 PDF 업로드 시 "Mock" 텍스트가 임베딩됨 (운영 불가)
- chunk_size 100자 하드코딩, 최대 10개 제한 → 5페이지 이상 문서 내용 절단
- 임베딩 오류 시 [0.1, 0.2] fallback 반환 → 장애를 테스트 통과로 위장
- company_id 멀티테넌트 격리 전무 (헤더 수신 없음)
- routing registry 없음 → `vdb_{category_mid}_01` 하드코딩
- 증분 업데이트(PUT), 삭제(DELETE), 프로젝트/카테고리 API 없음
- asyncio.to_thread 도입했으나 동일 Session 공유 문제 동일 보유

---

## 5. 핵심 교차 비교

| 관점 | 1위 | 2위 | 3위 |
|------|-----|-----|-----|
| 표준 설계 준수도 | src_codex | src_claud/v2 | src_antigravity/v2 |
| API 기능 범위 | src_claud/v2 | src_codex | src_antigravity/v2 |
| 멀티테넌트 보안 | src_codex | - | - |
| 비동기 성능 | src_claud/v2, src_antigravity/v2 | - | src_codex (동기) |
| 테스트 커버리지 | src_codex | src_claud/v2 | src_antigravity/v2 |
| 운영 즉시 투입 가능 | src_codex (asyncio 수정 후) | src_claud/v2 (High 4건 수정 후) | 다수 수정 필요 |

---

## 6. 최우선 수정 권고

### src_codex
1. `asyncio.to_thread` 적용 (이벤트 루프 블로킹 해소)
2. FK 선언 추가
3. page_no를 실제 PDF 페이지 번호로 수정

### src_claud/v2
1. `ChromaAdapter.add_documents()`에 `embeddings=` 명시 전달
2. chunk metadata에 `company_id`, `vector_db_id`, `created_at` 추가
3. RAG 검색 필터에 `company_id` 강제 주입
4. `asyncio.to_thread` 내 새 Session 생성

### src_antigravity/v2
1. pypdf 통합 (PDF 파싱 Mock 제거)
2. chunk_size 700, overlap 80으로 표준화
3. 임베딩 오류 시 EmbeddingError 전파
4. company_id 격리 (헤더 + metadata + 필터)
5. routing.json 기반 라우팅 도입

---

## 7. 결론

세 구현체를 표준 설계 기준으로 평가했을 때 **src_codex가 가장 운영에 가까운 구현**입니다. 멀티테넌트 보안과 데이터 정합성을 가장 엄격하게 처리했으며, asyncio 적용 하나만 보완하면 즉시 운영 후보입니다.

**src_claud/v2는 기능 범위와 아키텍처 설계가 가장 앞서** 있으나, Chroma 임베딩 일관성과 company_id 격리라는 핵심 운영 리스크를 해결해야 합니다.

**src_antigravity/v2는** 비동기 구조를 도입한 점은 올바르나, PDF 파싱·metadata·라우팅·격리 등 핵심 파이프라인 구현이 부족해 현 상태로는 운영 불가입니다.

이상적인 방향은 src_codex의 멀티테넌트 격리 + 표준 metadata 구조와 src_claud/v2의 API 범위 + 아키텍처 패턴을 병합하는 것입니다.
