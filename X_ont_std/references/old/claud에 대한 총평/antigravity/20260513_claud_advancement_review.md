# 2026-05-13 claud_통합 고도화 및 재검증 지시서 (Antigravity)

## 1. 개요
`claud_통합` 프로젝트의 Sprint 06 완료 보고를 바탕으로, 시스템의 엔터프라이즈급 안정성과 확장성을 확보하기 위한 **Antigravity의 최종 고도화 지침**을 정리합니다. 이 지침은 단순히 기능을 추가하는 것이 아니라, 아키텍처 수준에서의 '결함'을 차단하고 '범용성'을 확보하는 데 목적이 있습니다.

---

## 2. 핵심 재검증 및 패치 (Sprint 06 안정화)

Claude는 아래 4가지 항목에 대해 **수정 전/후 코드 및 자동 테스트 결과**를 바탕으로 재보고해야 합니다.

1.  **사용자 체계 통합**: `alice/bob` 등 테넌트 사용자와 `analyst/admin` 등 기존 AppContext 사용자가 API에서 충돌하지 않는지 확인하고, 일원화된 Identity 모델로 통합.
2.  **권한 누락 전수 조사**: `DELETE /api/ontology/{doc_id}/relationships/{rel_id}` 등 삭제/수정 API에 `ontology:edit` 권한이 누락 없이 강제되는지 확인.
3.  **프론트-백엔드 동기화**: `TenantUserSwitcher`에서 선택한 사용자가 모든 하이브리드 질의 및 온톨로지 관리 API 호출 시 실제 Header/Param으로 전달되는지 검증.
4.  **DoD 자동화**: `sprint_06.md`에 명시된 D01~D14 검증 시나리오를 `tests/` 폴더 내의 자동화 스크립트로 구현하고 실행 결과 첨부.

---

## 3. Sprint 07 고도화 지시 (The Next Level)

성공적인 Sprint 06 마무리 후, 다음 4가지 핵심 과제를 Sprint 07의 목표로 할당합니다.

### A. 데이터 범용화 (Generic Ontology Persistence)
- **지시**: `ontology.py` 내의 `customers`, `orders` 등 특정 도메인 로직을 완전히 제거하고, `entities`와 `relationships`라는 공통 데이터 모델로 저장 구조를 리팩터링할 것.
- **점검 포인트**: 코드 수정 없이 JSON 설정만으로 새로운 엔티티 타입을 CRUD 할 수 있는가?

### B. 물리적 데이터 격리 (Physical Directory Isolation)
- **지시**: 모든 데이터를 `storage/{company_id}/{project_id}/` 디렉토리 구조로 물리적으로 분리하여 저장할 것.
- **점검 포인트**: `company_a`의 파일 시스템 오류가 `company_b`에 영향을 주지 않는 구조인가?

### C. 실행 계획 기반 질의 (Query Planner Prototype)
- **지시**: 질문을 받으면 바로 답을 생성하지 않고, 어떤 엔진을 어떤 순서로 쓸지 'Plan JSON'을 먼저 생성하는 `Query Planner` 모듈의 기초를 설계할 것.
- **점검 포인트**: LLM이 생성한 실행 계획을 시스템이 파싱하여 결정론적(Deterministic)으로 실행할 수 있는가?

### D. 상세 감사 로그 (Audit Trail with Diff)
- **지시**: 데이터 수정 시 단순히 '수정됨'이 아니라, 변경 전(Before)과 변경 후(After)의 데이터 차이(Diff)를 로그에 남기도록 `audit.py`를 고도화할 것.
- **점검 포인트**: 사고 발생 시 누가 어떤 필드를 어떻게 바꿨는지 정확히 역추적 가능한가?

---

## 4. 향후 계획
위 지시 사항의 이행 여부를 바탕으로 `Antigravity-통합`으로의 최종 아키텍처 이식 여부를 결정함.
