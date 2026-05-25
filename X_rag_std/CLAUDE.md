# RAG 표준 설계 프로젝트 컨텍스트

> Claude Code가 이 폴더를 열 때마다 자동으로 읽는 파일입니다.
> **항상 이 파일을 먼저 읽고 작업을 시작하세요.**

---

## 🎯 프로젝트 정체성

**RAG 표준 설계** — 엔터프라이즈 RAG 시스템의 설계 표준 및 가이드 문서

- 독립적인 표준 설계 프로젝트 (제품 개발 아님)
- Word + Markdown 문서 중심
- ont_platform v3의 RAG 검색 기능을 위한 기준 제공

**핵심 소스**:
- `src_agents/src_claud/v3/` — FastAPI 기반 RAG API (최종 버전)
- `src_agents/llm_gateway/` — LLM 마이크로서비스

**핵심 요건**:
- RAG 표준 설계 v1.6.md와 일관성 유지
- 멀티테넌트/org_id 기반 문서 격리
- 라우팅 규칙 기반 벡터DB 선택 (프로젝트별 분리)

---

## 🗂️ 폴더 구조

```
E:\ontology_edu\X_rag_std\
├── zz-표준 설계\
│   ├── RAG 개발 가이드_v1.1.docx          ⭐ 기본 개발 가이드 (공식)
│   ├── RAG_표준_설계_v1.6.md              ← 다음 단계 (상세 설계)
│   ├── RAG_표준_설계_v1.6_임베딩 대상 문서 관리.md
│   ├── RAG_표준_설계_v1.6_임베딩 대상 문서 관리.docx
│   ├── (향후) RAG_상세_설계_가이드.md     ← 완전 레퍼런스 (TBD)
│   └── old\                               ← 작업 파일 백업 (v1.5 + 27개 Python)
└── convert_to_word.py                     ← MD → Word 변환 유틸
```

---

## 📊 현재 상태

| 항목 | 상태 | 비고 |
|------|------|------|
| **RAG 개발 가이드 v1.1.docx** | ✅ 공식 기준 | 기본 개발 가이드 (다중 프로젝트, org_id 테스트용) |
| **RAG 표준 설계 v1.6.md** | ✅ 완성 | 다음 단계 (상세 설계, 참고용) · 9개 섹션 · 프로젝트/카테고리 관리 API 포함 |
| **임베딩 문서 관리 API 명세** | ✅ 완성 | 5개 API, 17개 메타데이터, 청킹/라우팅/상태 워크플로우 |
| **RAG 상세 설계 가이드** | 🔲 예약 | 향후 v1.6 기반 완전 레퍼런스 (필요시) |

---

## 🚦 지금 당장 해야 할 것

### Phase 4: v4 고도화 (우선순위: 높음) 🔨 진행 중 (2026-06-01~)

**목표**: 프로덕션 레벨 RAG v4 완성 (3에이전트 병렬 개발)

**개발 방식**:
- Claude: API 고도화 (재순위화, 쿼리 확장, 다중 필터, 배치 API, 비동기 검색)
- Antigravity: 성능 최적화 (청킹, 캐싱, 부하 테스트 → p99 <200ms, 1000 QPS)
- Codex: 통합 & QA (E2E 테스트, 마이그레이션 가이드, 배포 자동화)

**예상 시간**: 4주  
**담당**: 3에이전트 병렬

**상세**: `docs/PHASE4_v4_UPGRADE_PLAN.md`, `week_instructions/PHASE4_WEEK1_INSTRUCTIONS.md` 참고

---

### 개발 기준 확정 (우선순위: 높음) ✅ 완료 (2026-05-19)

**포지셔닝 변경**:
- **기본 개발 가이드**: `RAG 개발 가이드_v1.1.docx`
  - 다중 프로젝트 테스트 시 `project_code`, `org_id` 하드코딩으로 분리 가능
  - 프로젝트/카테고리 관리 API 불포함 (필요시 v1.6 참고)
- **상세 설계 참고**: `RAG_표준_설계_v1.6.md`
  - 완전한 설계 (프로젝트/카테고리 관리 API §6.3, RDBMS 설계 부록 포함)
  - 구현 중 세부사항 필요 시 참고
- **향후 계획**: `RAG_상세_설계_가이드.md` (필요시 신설)

### Phase 2: 청킹 품질 개선 (우선순위: 높음) 🔲 예약

**배경**: PDF 청크 크기가 50자 미만으로 너무 짧음 → RAG 검색 품질 저하
- **원인**: PDF 줄바꿈이 많아 각 문단이 짧아짐
- **목표**: 청크 최소 500자 이상 보장

**작업**:
1. **extractor.py** — PDF 추출 후 줄바꿈 정제
   - 단일 `\n` → 스페이스 변환 (의미 보존)
   - 문단 구조 `\n\n` 유지
   - 다중 공백 정규화

2. **chunker.py** — SemanticChunker에 최소 크기 필터링
   - `MIN_CHUNK_SIZE = 150` 미만 청크 제외
   - 너무 작은 청크로 인한 의미 단절 방지

3. **integration_test_ailab.py** — 청크 크기 검증
   - 평균/최소/최대 청크 크기 측정
   - 로깅 강화

**예상 시간**: 1-2시간  
**담당**: Claude Code

---

## 📝 최근 작업 이력

### 2026-05-20 (오전)

✅ **프로젝트 구조 명확화 및 실행 환경 구축**
- CLAUDE.md에 `핵심 소스` 및 `핵심 요건` 추가
  - src_agents/src_claud/v3 (최종 버전)
  - src_agents/llm_gateway (LLM 마이크로서비스)
- `app/core/key_pool.py` 신규 생성 (누락된 모듈)
  - API 키 풀 관리 (키 로테이션 지원)
  - GEMINI_API_KEY 또는 GEMINI_API_KEYS 환경변수 지원

✅ **Swagger UI 헤더 입력 기능 개선**
- search.py, documents.py, projects.py 수정
  - `Request.headers` → `Header()` 파라미터로 변경
  - X-Tenant-ID (필수), X-Org-ID (선택) Swagger UI에 표시
  - 설명(description) 필드 추가로 명확성 향상

✅ **청킹 품질 문제 식별 및 개선 계획 수립**
- 현황: PDF 청크 크기 50자 미만 → RAG 검색 품질 저하
- 원인 분석: PDF 줄바꿈이 많아 문단이 짧아짐
- Phase 2 계획 수립: extractor.py, chunker.py 개선

### 2026-05-19 (저녁 후속)

✅ **Phase 1 Task 1.3 완료: 라우팅 설정 수정**
- `app/core/config.py`의 `DEFAULT_ROUTING_CONFIG` 업데이트
  - HR001 (채용) → vdb_hr_recruit_01
  - HR002 (급여) → vdb_hr_payroll_01
  - POLICY001 (취업규칙) → vdb_policy_01
  - TECH001 (ontology) → vdb_ontology_01
- `test_multitenant_org_hierarchy.py` 라우팅 fixture 수정
  - JSON 구조를 `routing_rules` 배열로 변경
  - `target_category_mid` 배열 형식으로 통일
- **결과**: 28개 테스트 100% 통과 ✅ (이전 24/28)

✅ **Phase 1 Task 1.2 완료: integration_test_ailab.py 확장**
- 검색 쿼리 11개 추가
  - 온톨로지 5개: "온톨로지", "자연언어처리", "knowledge graph", "semantic relationship", "NLP embedding"
  - 국방 3개: "국방 지휘통제", "온톨로지 국방", "command control system"
  - 교차조직 3개: "AI language model", "현대 문인 데이터베이스", "감성 분석"
- 성능 지표 수집
  - 응답시간 측정 (start_time/response_time)
  - 청크 수 추적
  - 평균 응답시간 계산
- 결과 요약 강화
  - 업로드 통계, 검색 성능, 테스트 환경 표시

✅ **통합테스트 방식.md 업데이트**
- Phase 1 모든 작업 완료 표시
- 단위테스트 통과율 100% (28/28) 반영
- 라우팅 정확도 100% (4/4) 반영
- 통합테스트 11개 쿼리 명시

### 2026-05-19 (저녁)

✅ **통합테스트 방식 문서화**
- `통합테스트 방식.md` 완성 (7개 섹션)
  - 프로젝트 현황, 개발 상태, 테스트 방식
  - 앞으로 할 일 (Phase 1/2/3)
  - 파일 구조, 주요 지표
- `integration_test_ailab.py` 완성
  - 8개 실제 PDF 기반 통합테스트
  - 멀티테넌트/org_id 분류 로직
  - 검색 품질 검증

✅ **v3 README.md 확장**
- 테스트 데이터 정의 추가 (테넌트, org_id, 프로젝트)
- 테스트 시나리오 3가지 (팀 업로드, 조직별 권한, 전사 공유)
- API 엔드포인트 개요 추가
- 통합테스트 실행 방법 추가

✅ **테스트 케이스 추가** (11개)
- `test_multitenant_org_hierarchy.py` 신규 생성
- 멀티테넌트 격리 (1개) ✅
- org_id 계층 (2개) ✅
- 프로젝트별 라우팅 (4개) ❌ 3개 실패
- E2E 시나리오 (2개) ✅

### 2026-05-19 (오후)

✅ **전체 테스트 실행 및 분석**
- 28개 테스트 중 24개 통과 (85.7%)
- 멀티테넌트 격리: ✅ 완전 작동
- org_id 계층 검색: ✅ 완전 작동
- E2E 시나리오: ✅ 완전 작동
- 라우팅 설정: ❌ 4개 미세 조정 필요

✅ **v1.6 업그레이드 완료**
- `RAG_표준_설계_v1.5.md` → `RAG_표준_설계_v1.6.md` 파일명 변경
- v1.6 버전 이력 추가 (포지셔닝 변경 명시)
- v1.5 관련 파일들 `old/` 폴더로 이동
- **새로운 포지셔닝**:
  - v1.1.docx = 기본 개발 가이드 (공식)
  - v1.6.md = 다음 단계 (상세 설계, 참고용)
  - 향후: 상세 설계 가이드 별도 신설

### 2026-05-19 (오전)

✅ **임베딩 대상 문서 관리 API 명세 완성**
- `RAG_표준_설계_v1.5_임베딩 대상 문서 관리.md` 신규 생성
- Word 자동 생성: `RAG_표준_설계_v1.5_임베딩 대상 문서 관리.docx`
- 5개 API (업로드/목록/상태/재업로드/삭제) 상세 정의

---

## 🔧 유틸리티

**Markdown → Word 변환**:
```bash
python convert_to_word.py
```

- 입력: `zz-표준 설계\*.md`
- 출력: `zz-표준 설계\*.docx`
- 테이블, 제목 레벨, 코드 블록 자동 변환

---

## 📍 핵심 파일

| 파일명 | 용도 | 상태 |
|--------|------|------|
| **`RAG 개발 가이드_v1.1.docx`** | 🎯 **기본 개발 가이드** (공식) | ✅ 현 기준 |
| `RAG_표준_설계_v1.6.md` | 다음 단계 (상세 설계) | ✅ 완전 |
| `RAG_표준_설계_v1.6_임베딩 대상 문서 관리.md` | 문서 관리 API 상세 | ✅ 참고용 |
| (향후) `RAG_상세_설계_가이드.md` | 완전 레퍼런스 | 🔲 예약 |
| `old/RAG_표준_설계_v1.5_보고용.md` | v1.5 보고용 | 📦 백업 |
| `old/RAG_표준_설계_v1.5_매핑.md` | v1.5 섹션 매핑 | 📦 백업 |

---

## 📌 작업 규칙

- 작업 로그는 `E:\ontology_edu\X_ont_std\task_logs\claude\YYYYMMDD_HHMM_작업명.md` 에 기록
- 이 파일은 상태 변화가 있으면 업데이트
- **주의**: 이는 **표준 문서 프로젝트**입니다. 실제 제품 개발은 ont_platform_v3 워크스페이스를 사용하세요.

---

## 🔗 관련 프로젝트

**ont_platform_v3 워크스페이스**: 실제 제품 개발 (FastAPI + Next.js)
- X_ont_std/ 하위의 모든 자료 포함:
  - requirements/: 요건 문서
  - task_logs/: 작업 로그
  - references/: 참고 자료
  - ont_platform/: 제품 코드
- 이 RAG 표준이 구현 기준으로 사용됨
