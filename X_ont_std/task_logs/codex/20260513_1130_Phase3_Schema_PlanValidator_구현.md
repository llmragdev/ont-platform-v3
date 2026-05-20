# Phase 3 Schema / Plan Validator 구현 지시 기록

작성일: 2026-05-13 11:30  
작성자: Codex

## 맥락

Phase 1에서 TenantContext와 설정 로딩을 구현했고, Phase 2에서 멀티테넌트 Repository와 v1 CRUD API를 구현했다.
Codex가 다음 단계로 `Phase 3: 스키마 검증 + Plan Validator`를 권고했고, 사용자는 "phase 3 해야 되는거 아냐?"라고 확인했다.

## 작업 범위

- 온톨로지 객체 생성/수정 시 스키마 기반 타입, 필수값, enum, 미정의 속성 검증
- 관계 생성 시 관계 타입, source/target 타입, 관계 속성 검증
- 하이브리드 질의 plan 실행 전 Plan Validator 계층 추가
- invalid plan은 실행하지 않고 명확한 오류로 반환
- Phase 2 API와 기존 ontology 테스트 회귀 방지

## 완료 기준(DoD)

- 존재하지 않는 object type은 400
- 필수 속성 누락은 400
- enum 허용값 위반은 400
- 미정의 속성 입력은 400
- 관계 source/target 타입 불일치는 400
- 존재하지 않는 filter property 또는 metric을 가진 plan은 실행 전 차단
- `pytest` 전체 통과

## 완료 결과

완료일: 2026-05-13

- `app/validators.py`에 `SchemaValidator` 추가
- 객체 생성/수정 시 object type, 필수 속성, enum, 타입, 미정의 속성 검증 적용
- 관계 생성 시 relationship type, source/target type, 관계 속성 검증 적용
- `hybrid_ask`에서 plan 생성 직후 `validate_query_plan`을 수행하도록 Plan Validator 연결
- `tests/test_schema_validator_phase3.py`에 invalid object, invalid relationship, invalid plan 테스트 추가

## 검증

- 실행 위치: `E:\ontology_edu\Codex-통합\project\src\backend`
- 명령: `pytest`
- 결과: `31 passed`
