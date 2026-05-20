# 08. 인수 테스트 계획서 (Acceptance Test Plan)

## 1. 개요
본 문서는 `Antigravity-통합` 프로젝트의 각 Phase 및 Sprint 완료 시 통과해야 할 최종 인수 테스트 시나리오를 정의합니다. 모든 테스트는 자동화된 스크립트(`tests/automated_dod_check.py`)를 통해 검증되어야 합니다.

---

## 2. 테스트 시나리오 정의

### 2.1 보안 및 테넌트 격리 (Security & Isolation)
| ID | 테스트 항목 | 검증 시나리오 | 기대 결과 |
| :--- | :--- | :--- | :--- |
| **TC-SEC-01** | 인증 누락 | 헤더에 JWT 없이 API 호출 | 401 Unauthorized |
| **TC-SEC-02** | 토큰 만료 | 만료된 JWT로 API 호출 | 401 Unauthorized |
| **TC-SEC-03** | 테넌트 침범 | Company A의 토큰으로 Company B의 프로젝트 데이터 요청 | 403 Forbidden |
| **TC-SEC-04** | 권한 부족 (Read) | `viewer` 권한으로 `POST /api/v1/ontology/entities` 호출 | 403 Forbidden |
| **TC-SEC-05** | 권한 승인 (Write) | `editor` 권한으로 `POST /api/v1/ontology/entities` 호출 | 201 Created |

### 2.2 범용 온톨로지 엔진 (Generic Ontology)
| ID | 테스트 항목 | 검증 시나리오 | 기대 결과 |
| :--- | :--- | :--- | :--- |
| **TC-ONT-01** | 스키마 준수 | 정의되지 않은 타입의 엔티티 생성 시도 | 422 Unprocessable Entity |
| **TC-ONT-02** | 데이터 무결성 | 관계 생성 시 존재하지 않는 Source/Target ID 지정 | 422 Unprocessable Entity |
| **TC-ONT-03** | 삭제 정책 | 엔티티 삭제 시 연결된 관계의 상태 변화 확인 | 관계의 status가 'deleted'로 변경 |

### 2.3 지식 추출 및 RAG (Ingestion & Search)
| ID | 테스트 항목 | 검증 시나리오 | 기대 결과 |
| :--- | :--- | :--- | :--- |
| **TC-DOC-01** | 업로드 격리 | 문서 업로드 후 `documents_registry.json`의 `company_id` 확인 | 요청자의 테넌트 ID가 자동 기록됨 |
| **TC-DOC-02** | 검색 격리 | `GET /api/v1/documents` 호출 시 타 테넌트 문서 포함 여부 | 요청자의 테넌트 문서만 반환 |

### 2.4 하이브리드 질의 (Hybrid Query)
| ID | 테스트 항목 | 검증 시나리오 | 기대 결과 |
| :--- | :--- | :--- | :--- |
| **TC-QRY-01** | 실행 계획 생성 | "X 장비의 수리 이력 요약" 질문 | `ONTOLOGY` + `VECTOR`가 결합된 Plan 생성 |
| **TC-QRY-02** | 팩트 기반 응답 | 온톨로지 연산(Sum, Count) 결과와 자연어 합성 | LLM 답변 내 수치가 쿼리 결과와 100% 일치 |
| **TC-QRY-03** | 출처 명시 | 질의 응답 하단에 출처 데이터 포함 | 문서 파일명 및 온톨로지 노드 링크 포함 |

---

## 3. 테스트 환경 및 도구
- **Backend**: `pytest`, `httpx` (API Integration)
- **Frontend**: `Playwright` (E2E Scenario)
- **Evaluation**: `evaluate.py` (LLM Response Quality)
