# Sprint 03 — 온톨로지 재설계 Phase 1~5 + Vector RAG

> **기간**: 2026-05-12
> **상태**: ✅ 완료
> **이전 스프린트**: [Sprint 02](sprint_02.md)

---

## 1. 스프린트 목표

- [x] 온톨로지 스키마를 Python 하드코딩 → JSON 외부화 (Phase 1)
- [x] 범용 그래프 탐색 + object_context 일반화 (Phase 2)
- [x] 관계 CRUD API + 액션 스키마 통합 (Phase 3)
- [x] 온톨로지 그래프 캔버스 React Flow UI (Phase 4)
- [x] sensitive 필드 자동 마스킹 정책 파일화 (Phase 5)
- [x] PDF 업로드 + Chroma 벡터 DB 임베딩 + 하이브리드 BM25+Vector 검색

---

## 2. 백로그 → 완료 항목

| ID | 항목 | 구분 | 결과 |
|----|------|------|------|
| S-01 | 온톨로지 스키마 JSON 외부화 (Phase 1) | feature | ✅ |
| S-02 | 범용 graph traversal + object_context (Phase 2) | feature | ✅ |
| S-03 | 관계 CRUD API + action_types 스키마 연결 (Phase 3) | feature | ✅ |
| S-04 | 온톨로지 그래프 React Flow 캔버스 (Phase 4) | feature | ✅ |
| S-05 | sensitive 자동 마스킹 (Phase 5) | feature | ✅ |
| S-06 | PDF 업로드 + Chroma 벡터 DB | feature | ✅ |
| S-07 | 하이브리드 BM25 + Vector 검색 | feature | ✅ |

---

## 3. 기술 변경 사항

### 신규 파일

| 파일 경로 | 역할 |
|-----------|------|
| `backend/app/config/ontology.default.json` | 온톨로지 스키마 (객체 타입/관계 타입/액션 타입) |
| `backend/app/config/policy.default.json` | 마스킹 정책 (role × object_type × fields) |
| `backend/app/vector_search.py` | VectorSearchService (Chroma + 임베딩) |
| `frontend/src/components/OntologyExplorerCanvas.tsx` | React Flow 온톨로지 그래프 |
| `backend/tests/test_ontology_schema.py` | 스키마 8 케이스 |

### 변경 파일

| 파일 경로 | 변경 내용 요약 |
|-----------|---------------|
| `backend/app/ontology.py` | JSON 로딩, 범용 탐색, 관계 CRUD, React Flow 형식 반환 |
| `backend/app/policy.py` | `mask_object()` if-else 완전 제거 → 정책 파일 기반 |
| `backend/app/rag.py` | `extract_object_ids(schema?)` — id_prefix 동적 정규식 |
| `backend/app/app_context.py` | VectorSearchService 주입, schema 기반 PolicyEngine |
| `backend/app/main.py` | 온톨로지 그래프/관계 CRUD 라우트 추가 |

---

## 4. 발견된 문제

### 🐛 버그

| # | 현상 | 원인 | 해결 방법 |
|---|------|------|-----------|
| B-01 | `langchain-google-genai`가 v1beta 임베딩 모델 강제 사용 → 404 | 라이브러리가 `models/embedding-001` (deprecated) 호출 | `google-genai` SDK 직접 호출로 전환, `models/gemini-embedding-001` 명시 |

### 🚧 블로커

없음

---

## 5. 개선된 점

- **확장성**: 새 객체 타입 추가 = JSON 한 항목 → Python 코드 수정 0
- **마스킹**: role × type × field 조합을 정책 파일로 선언 → 코드 수정 없이 규칙 변경
- **RAG**: BM25 단독 → BM25 + Vector 하이브리드 (의미 기반 검색 추가)
- **온톨로지 UI**: 텍스트 목록 → React Flow 캔버스 시각화
- **일반화**: Order 전용 context → 모든 객체 타입 범용 context

---

## 6. 테스트 결과

| 테스트 종류 | Sprint 02 | Sprint 03 | 비고 |
|------------|-----------|-----------|------|
| pytest | 59/59 | 67/67 | +8건 (ontology_schema) |
| 시나리오 자동 검증 | 5/5 | 5/5 | 회귀 없음 |
| evaluate.py | 10/10 | 10/10 | 회귀 없음 |
| E2E (Playwright) | 6/6 | 6/6 | 회귀 없음 |
| 회귀 건수 | 0 | 0 | Phase 1~5 전 구간 0 |

---

## 7. 다음 스프린트 제안 백로그

- [ ] 하이브리드 질의 엔드포인트 (`/api/hybrid/ask`) (High)
- [ ] 온톨로지 쿼리 엔진 (filter/compare/calculate/relations) (High)
- [ ] 질문 유형 분류기 (LLM + 폴백) (High)
- [ ] 온톨로지 스키마/인스턴스 관리 UI 화면 (Medium)
- [ ] React Flow 기반 온톨로지 그래프 편집 화면 (Medium)

---

## 8. 회고

### 잘 된 것 👍
- 5개 Phase 연속으로 회귀 0건 유지 — `_step()` 패턴이 파이프라인 관리에 효과적
- langchain 의존성 제거 → SDK 직접 호출로 버전 충돌 문제 근본 해결
- 정책 파일화로 마스킹 규칙이 코드가 아닌 데이터가 됨

### 아쉬운 것 👎
- Vector RAG는 API 키 없으면 임베딩 실패 → 테스트 격리가 어려움
- 온톨로지 그래프 편집 기능 없음 (조회만)

### 다음에 시도할 것 🔁
- 온톨로지 데이터를 직접 질의하는 구조형 쿼리 엔진 구현
