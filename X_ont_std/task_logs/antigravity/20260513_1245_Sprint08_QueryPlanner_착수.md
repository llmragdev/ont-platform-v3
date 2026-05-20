# 20260513_1245_Sprint08_QueryPlanner_착수

## 1. 제안 및 착수 맥락
- **현황**: Sprint 07(물리 격리 및 서비스 레이어) 완료 (38/38 테스트 통과).
- **작업 방향**: 수석 아키텍트 Codex의 권고를 반영하여 데이터 액세스 레이어(Repository)를 먼저 보완한 후, 이를 기반으로 Query Planner(Intent 기반 하이브리드 검색)를 구현함.
- **자율 착수**: 가이드 원칙 5번에 의거, 계획 수립 후 즉시 실행 단계로 진입함.

## 2. 작업 범위 (Scope)
- **Repository Layer 구현**:
  - `src/backend/app/repositories/base.py`: 파일 기반 공통 저장 로직.
  - `src/backend/app/repositories/ontology.py`: 엔티티/관계 CRUD 및 TenantContext 필터링.
- **Service Layer 고도화**:
  - `src/backend/app/services/ontology.py`: Repository를 사용하도록 리팩토링 및 `filter_by_property` 추가.
  - `src/backend/app/services/query_planner.py` (신규):
    - LLM 기반 Intent 분류 (descriptive | filter | compare | calculate | hybrid).
    - 의도에 따른 실행 계획(Execution Plan) 생성 및 라우팅.
- **API 개발**:
  - `src/backend/app/api/hybrid.py`: `/api/hybrid/ask` 엔드포인트 구현.
  - `src/backend/app/main.py`: 신규 서비스 및 라우터 등록.

## 3. 완료 기준 (DoD)
- [ ] Repository 패턴 적용으로 서비스 코드의 데이터 관심사 분리 완료.
- [ ] 질문 유형에 따른 정확한 Intent 분류 (v1.0 로직 개선 이식).
- [ ] Filter Intent 처리 시 온톨로지 속성 기반 정확한 매칭 결과 반환.
- [ ] Descriptive Intent 처리 시 Vector Search 연동 및 Score 기반 정렬.
- [ ] `src/backend/tests/test_sprint08_dod.py` 자동 테스트 통과.

## 4. 참고 산출물
- 아키텍트 권고: `AI_TASK_CONTROL/codex/20260513_1100_다음단계_권고.md`
- v1.0 레거시: `archive/v1.0/backend/app/query_classifier.py`, `ontology_query_engine.py`
