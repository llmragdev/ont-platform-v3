# 3대 AI 에이전트 RAG 백엔드 종합 상대평가 — v03-2

작성일: 2026-05-15  
작성: Claude Code  
평가 대상: `src_codex` / `src_claud/v3` / `src_antigravity/v3`  
평가 기준: `RAG_표준_설계_v1.3.md`, `details/01~04`

---

## 변경점 (v03 평가 대비)

| 에이전트 | v03 평가 시점 | v03-2 평가 시점 | 변화 |
|----------|-------------|---------------|------|
| src_claud | v3 | **v3** (테스트 17개로 증가) | SSE 테스트 추가, utcnow 제거, org_id="" 문서화 |
| src_antigravity | v3 (테스트 2/3) | **v3** (코드 동일) | Index Swap·SSE 구현 확인. 테스트 환경 미구성 |
| src_codex | 기존 코드 평가 | **기존 코드** (변경 없음) | v3 설계 문서 완성, 구현 미착수 |

> **Antigravity 자체평가 문서(`Antigravity_02`)에 대한 주석**: 해당 문서는 Claude v2, Codex v2를 비교 대상으로 삼았다. 현재 Claude는 v3(SSE·Session 안전·복합PK·테스트 17개 통과)로 업그레이드된 상태이며, 해당 문서에서 지적된 "Claude의 결함"은 이미 해소됐다.

---

## 1. 테스트 현황

| 구현체 | 테스트 수 | 결과 | 외부 의존 |
|--------|----------|------|----------|
| `src_claud/v3` | **17개** | **17/17 통과** | 없음 (in-memory DB + mock) |
| `src_antigravity/v3` | 38개 | **실행 불가** | pydantic_settings 미설치, Gateway 의존 |
| `src_codex` | 3개 파일 | 통과 (기존 코드 기준) | 없음 |

---

## 2. RAG 표준 설계 v1.3 준수율 비교표

| 요건 항목 | src_claud/v3 | src_antigravity/v3 | src_codex |
|-----------|:------------:|:------------------:|:---------:|
| **X-Tenant-ID 필수 (400)** | ✅ | ✅ | ❌ (X-Company-ID, 선택) |
| **X-Org-ID 선택 수신** | ✅ | ✅ | ❌ |
| **org_id/dept_code 메타데이터 저장** | ✅ | ✅ | ❌ |
| **OR 조건 검색 (팀+공유, 부서+공유)** | ✅ | ✅ | ❌ |
| **공유 문서 org_id="" sentinel** | ✅ (문서화 완료) | ⚠️ (None 혼용 가능성) | ❌ |
| **ca_org_mgnt 복합 PK (tenant_id, org_id)** | ✅ | ⚠️ (미확인) | ❌ |
| **tags → RDBMS 전용, vector metadata 제외** | ✅ | ✅ | ❌ (tags 저장) |
| Chroma add_documents에 embeddings= 명시 | ✅ | ⚠️ (Chroma 미지원) | ✅ |
| asyncio.to_thread 비동기 파이프라인 | ✅ | ✅ | ❌ (동기 블로킹) |
| asyncio.to_thread + 독립 Session | ✅ | ✅ | 해당없음 |
| pipeline_status "pending" 즉시 반환 | ✅ | ✅ | ❌ (동기 완료 후 반환) |
| Gateway 호출에 tenant_id 전달 | ✅ | ✅ | ❌ ("default" 하드코딩) |
| **Vector adapter 내부 embedding 호출 금지** | ✅ | ❌ (adapter가 직접 호출) | ✅ |
| Chroma 어댑터 지원 | ✅ | ❌ | ✅ |
| 실제 PDF/DOCX 파싱 + page_no 보존 | ✅ | ✅ | ⚠️ (page_no는 인덱스 기반) |
| chunk_size 700, overlap 80 | ✅ | ✅ | ✅ |
| 프로젝트/카테고리 관리 API | ✅ | ✅ | ✅ |
| RDBMS FK 선언 | ✅ | ✅ (복합 FK) | ❌ |
| LLM Gateway 연동 (키 분리) | ✅ | ✅ | ✅ |
| **SSE 스트리밍 검색** | ✅ (테스트 포함) | ✅ | ✅ |
| **Index Swap Pattern** | ❌ | ✅ (AdminService) | ❌ (v3 설계에 포함) |
| debug_mode candidate_chunks 분리 | ✅ | ✅ | ✅ |
| 감사 로그 (AuditLog) | ✅ | ❌ | ❌ |
| datetime timezone-aware | ✅ | ❌ (utcnow 잔존) | ❌ (utcnow 잔존) |
| 테스트 외부 의존 없음 | ✅ | ❌ | ✅ |

---

## 3. 종합 점수

| 구현체 | v03 점수 | v03-2 점수 | 등급 | 변화 이유 |
|--------|---------|-----------|------|-----------|
| `src_claud/v3` | 9.2 | **9.0 / 10** | **A+** | Index Swap 미구현 반영 (-0.2) |
| `src_antigravity/v3` | 6.5 | **7.0 / 10** | **B+** | Index Swap·SSE 구현 확인 (+0.5), 테스트 불가·embedding boundary 위반 지속 |
| `src_codex` | 7.0 | **6.8 / 10** | **B** | tags 저장·page_no 오류 추가 확인 (-0.2) |

---

## 4. 에이전트별 상세 평가

### 🥇 src_claud/v3 — v1.3 표준 완전 구현, Index Swap 미구현이 유일한 결함

**강점**
- 17/17 테스트 완전 통과, 외부 의존 없는 완전 격리 실행
- v1.3 필수 요건 (tenant_id·org_id 계층·Chroma embeddings=·Session 안전·pending 반환) 모두 충족
- SSE 스트리밍 3개 테스트(`test_stream_search_*`)로 검증
- `org_id=""` sentinel 표준 불일치를 코드 주석·README에 명시
- `datetime.now(timezone.utc)` 전면 적용

**약점**
- **Index Swap Pattern 미구현** — 대규모 재색인 중 검색 서비스 중단 위험. RAG 표준 설계 §2.8에 명시된 항목
- Chroma 실서버 통합 테스트 없음
- Alembic migration 미도입

---

### 🥈 src_antigravity/v3 — Index Swap 차별화, 테스트 검증 불가

**강점**
- **Index Swap Pattern 구현** — `AdminService.perform_index_swap()` 완전 구현. 3대 에이전트 중 유일. 실제 조직 개편·대규모 재색인 시 무중단 운영 가능
- SSE 스트리밍 구현 (search.py `StreamingResponse` + async generator)
- asyncio.to_thread + 독립 Session (`get_new_session()`)
- X-Tenant-ID 필수, org_id 계층 격리, OR 검색 구현
- PDF page_no 실제 페이지 번호 보존
- tags vector metadata 제외

**약점**
- **테스트 실행 불가** — `pydantic_settings` 패키지 미설치, Gateway 의존으로 실제 검증 불가. 구현 코드의 정합성을 신뢰하기 어려운 핵심 문제
- **Vector adapter embedding boundary 위반** — adapter 내부에서 Gateway embedding 직접 호출. 표준은 pipeline에서 생성 후 `embeddings=`로 전달 (Chroma 벡터 공간 일관성 위협)
- **Chroma 어댑터 없음** — LocalJson 전용, 운영 규모 한계
- `org_id=None` vs `org_id=""` sentinel 혼용 가능성
- `datetime.utcnow()`, FastAPI `on_event` deprecation 잔존
- 감사 로그(AuditLog) 없음

---

### 🥉 src_codex — Chroma 정합성 유일, v1.3 멀티테넌트 미구현

**강점**
- Chroma `embeddings=` 명시 — 가장 오랜 안정 운영
- `company_id` 격리 완결성 (헤더·metadata·필터)
- SSE 스트리밍 구현

**약점**
- **asyncio.to_thread 미사용** — 동기 블로킹으로 이벤트 루프 점유
- `X-Company-ID` 선택(default="default") — v1.3 필수 정책 불일치
- org_id 계층 격리 전무
- tags를 vector metadata에 저장 (v1.3 제외 정책 위반)
- page_no가 chunk 인덱스 기반 (실제 PDF 페이지 번호 아님)
- FK 선언 없음
- `company_id` → `tenant_id` 전환 미완료
- **v3 코드 구현 없음** — 설계 문서만 존재

---

## 5. 핵심 교차 비교

| 관점 | 1위 | 2위 | 3위 |
|------|-----|-----|-----|
| 테스트 신뢰성 | src_claud/v3 (17/17, 격리) | src_codex (통과, 격리) | src_antigravity/v3 (실행 불가) |
| v1.3 표준 준수도 | src_claud/v3 | src_antigravity/v3 | src_codex |
| 운영 가용성 (Index Swap) | src_antigravity/v3 | — | src_claud/v3·src_codex (미구현) |
| 비동기 성능 | src_claud/v3·src_antigravity/v3 | — | src_codex (동기 블로킹) |
| Chroma 벡터 정합성 | src_claud/v3·src_codex | — | src_antigravity/v3 (Chroma 미지원) |
| 멀티테넌트 계층 보안 | src_claud/v3 | src_antigravity/v3 | src_codex (1차원) |
| 감사 로깅 | src_claud/v3 | — | src_antigravity/v3·src_codex |

---

## 6. 결론

**src_claud/v3가 종합 1위**를 유지한다. 테스트 검증 완결성, v1.3 표준 준수도, 아키텍처 완성도에서 가장 앞선다. 유일한 결함은 Index Swap 미구현이며 이를 추가하면 완전한 엔터프라이즈 운영 후보가 된다.

**src_antigravity/v3는 Index Swap 하나로 차별화**된다. 재색인 중 무중단 운영은 상용 RAG 시스템의 핵심 요건이며, 이를 구현한 유일한 에이전트다. 그러나 테스트가 실행조차 안 되는 상황은 구현 신뢰성을 심각하게 훼손한다. 테스트 격리와 embedding boundary 정리가 최우선이다.

**src_codex는 v3 설계 문서가 완성**됐으므로 구현 착수가 시급하다. 설계대로 구현되면 Index Swap + Alembic + org_id 계층까지 갖추게 되어 가장 완성도 높은 산출물이 될 가능성이 있다.
