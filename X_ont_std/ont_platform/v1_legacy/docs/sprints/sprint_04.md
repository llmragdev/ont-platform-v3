# Sprint 04 — 하이브리드 질의 시스템 구축

> **기간**: 2026-05-12 ~ 2026-05-13
> **상태**: ✅ 완료
> **이전 스프린트**: [Sprint 03](sprint_03.md)

---

## 1. 스프린트 목표

- [x] 질문 유형 분류기 구현 (LLM + 폴백)
- [x] 온톨로지 쿼리 엔진 5종 연산 구현
- [x] `/api/hybrid/ask` 통합 엔드포인트
- [x] HybridQuery UI 화면 (통합 질의)
- [x] 온톨로지 스키마·인스턴스·그래프 편집 관리 화면 3종
- [x] 통합 테스트 45건 작성 및 통과
- [x] `.env` 파일 USB → 로컬 복사 (배포 안정화)

---

## 2. 백로그 → 완료 항목

| ID | 항목 | 구분 | 결과 |
|----|------|------|------|
| S-01 | `query_classifier.py` — LLM 분류 + 폴백 | feature | ✅ |
| S-02 | `ontology_query_engine.py` — filter/compare/calculate/relations/find | feature | ✅ |
| S-03 | `LLMGateway.generate_text()` 신규 메서드 | feature | ✅ |
| S-04 | `AppContext.ask_hybrid()` 메서드 | feature | ✅ |
| S-05 | `POST /api/hybrid/ask` 엔드포인트 | feature | ✅ |
| S-06 | `HybridQuery.tsx` 프론트 화면 | feature | ✅ |
| S-07 | `OntologySchemaManager.tsx` 스키마 관리 | feature | ✅ |
| S-08 | `OntologyInstanceEditor.tsx` 인스턴스 편집 | feature | ✅ |
| S-09 | `OntologyGraphEditor.tsx` 관계 그래프 편집 | feature | ✅ |
| S-10 | Sidebar 재구성 (4그룹, 3 ViewKey 추가) | feature | ✅ |
| S-11 | `test_hybrid_query.py` 45건 통합 테스트 | test | ✅ |
| S-12 | `/api/ontology/mgmt/...` 라우트 네임스페이스 정리 | fix | ✅ |
| S-13 | `.env` 로컬 복사 (USB 의존성 제거) | infra | ✅ |

---

## 3. 기술 변경 사항

### 신규 파일

| 파일 경로 | 역할 |
|-----------|------|
| `backend/app/query_classifier.py` | 질문 → 5종 유형 분류 (LLM + JSON 폴백) |
| `backend/app/ontology_query_engine.py` | 구조형 질의 (filter/compare/calculate/relations/find) |
| `frontend/src/components/HybridQuery.tsx` | 통합 질의 UI (온톨로지 + RAG + AI 답변) |
| `frontend/src/components/OntologySchemaManager.tsx` | 8 빌트인 타입 + 도메인 타입/관계 관리 |
| `frontend/src/components/OntologyInstanceEditor.tsx` | 엔티티 인스턴스 CRUD + PDF 재추출 |
| `frontend/src/components/OntologyGraphEditor.tsx` | React Flow 관계 그래프 편집 |
| `backend/tests/test_hybrid_query.py` | 45건 통합 테스트 |

### 변경 파일

| 파일 경로 | 변경 내용 요약 |
|-----------|---------------|
| `backend/app/llm_gateway.py` | `generate_text(prompt)` 신규 (search_results 불필요) |
| `backend/app/app_context.py` | `ask_hybrid()` 추가 |
| `backend/app/main.py` | hybrid 엔드포인트, mgmt 라우트 네임스페이스, .env auto-copy 제거 |
| `frontend/src/components/Sidebar.tsx` | ViewKey 3개 추가, 4그룹 재구성 |
| `frontend/src/app/page.tsx` | 4개 컴포넌트 라우팅 추가 |
| `frontend/src/types/api.ts` | Hybrid/Ontology 관련 타입 추가 |
| `frontend/src/lib/api.ts` | `api.hybridAsk()` + `api.ontologyMgmt.*` 13개 메서드 |
| `backend/.env` | USB(F:)에서 로컬로 복사 (USB 없이 동작 가능) |

---

## 4. 발견된 문제

### 🐛 버그

| # | 현상 | 원인 | 해결 방법 |
|---|------|------|-----------|
| B-01 | `POST /api/hybrid/ask` 404 반환 | `llm_gateway.generate()`가 `search_results=[]`이면 `AppError(404)` | `generate_text()` 메서드 신규 추가, `ask_hybrid()`에서 사용 |
| B-02 | `/api/ontology/schema` 중복 라우트 500 | 기존 그래프용 + 신규 mgmt 라우트가 같은 path 충돌 | 관리용 라우트를 `/api/ontology/mgmt/schema/...`로 네임스페이스 분리 |
| B-03 | PDF 업로드 실패 "GEMINI_API_KEY not available for embeddings" | `.env` 파일이 USB(F:)에만 있고 드라이브 미연결 | `backend/.env`로 물리 복사, `main.py`의 auto-copy shutil 코드 제거 |
| B-04 | TypeScript 빌드 오류 — `useRef`, `OntologyRelationship` 미사용 임포트 | 컴포넌트 작성 중 불필요 import 잔존 | 미사용 import 제거 |

### 🚧 블로커

| # | 내용 | 해결 방법 |
|---|------|----------|
| BL-01 | 온톨로지 DB가 비어 있어 구조형 질의 테스트 불가 | test fixture에서 `monkeypatch`로 `ontology_store` 모듈 속성 격리 + `tmp_path` 사용 |
| BL-02 | `conda run` UnicodeEncodeError (cp949 인코딩) | conda run 우회, `/c/Users/.../anaconda3/envs/claud_be/python` 직접 호출 |

---

## 5. 개선된 점

- **질의 범위 확장**: BM25+Vector 단순 검색 → 유형 분류 후 온톨로지/RAG 혼합 처리
- **LLM Gateway 역할 분리**: RAG 전용 `generate()` + 범용 `generate_text()` 명확히 구분
- **UI 완성도**: 5 분석 화면 + 4 온톨로지 관리 화면으로 콘솔 기능 완성
- **배포 안정성**: `.env` 로컬 복사로 USB 의존성 제거
- **테스트 격리**: monkeypatch + tmp_path로 파일 시스템 의존 온톨로지 테스트 완전 격리

---

## 6. 테스트 결과

| 테스트 종류 | Sprint 03 | Sprint 04 | 비고 |
|------------|-----------|-----------|------|
| pytest (기존) | 67/67 | 67/67 | 회귀 없음 |
| pytest (신규 hybrid) | - | 45/45 | 신규 |
| 시나리오 자동 검증 | 5/5 | 5/5 | 회귀 없음 |
| evaluate.py | 10/10 | 10/10 | 회귀 없음 |
| E2E (Playwright) | 6/6 | 6/6 | 회귀 없음 |
| 회귀 건수 | 0 | 0 | |

---

## 7. 다음 스프린트 제안 백로그

- [ ] 통합 테스트 자동화 프로그램 (시나리오 하드코딩 + 실제 API 호출 + HTML 리포트) (High)
- [ ] 온톨로지 시드 데이터 주입 → hybrid 질의 E2E 검증 (High)
- [ ] 질문 유형 분류 정확도 측정 지표 추가 (Medium)
- [ ] 스프린트 문서화 체계 구축 (Medium)

---

## 8. 회고

### 잘 된 것 👍
- 4개 버그 모두 근본 원인 분석 후 해결 (우회책 없음)
- `generate_text()` 분리로 LLM Gateway 책임이 명확해짐
- monkeypatch 격리 패턴으로 파일 시스템 의존 테스트 해결

### 아쉬운 것 👎
- 온톨로지 DB가 비어 있어 구조형 질의(filter/compare/calculate)의 실제 동작을 UI에서 테스트하기 어려움
- hybrid 질의 품질 (분류 정확도, 온톨로지+RAG 혼합 품질) 측정 체계 없음

### 다음에 시도할 것 🔁
- 시나리오 하드코딩 방식의 통합 테스트로 "어떤 질문 → 어떤 경로" 검증 자동화
