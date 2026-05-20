# Phase 2 Repository 구현 지시 기록

작성일: 2026-05-13 11:10  
작성자: Codex

## 맥락

Codex가 다음 단계로 `Phase 2: 범용 데이터 레이어 / 온톨로지 Repository 구현`을 권고했다.
사용자는 "그래 진행해"라고 승인했다.

## 작업 범위

- BaseRepository 구현
- OntologyObjectRepository 구현
- OntologyRelationshipRepository 구현
- TenantContext 기반 company/project 자동 필터
- `/api/v1/ontology/objects` CRUD 추가
- `/api/v1/ontology/relationships` CRUD 추가
- 권한/격리 자동 테스트 추가

## 완료 기준(DoD)

- viewer는 객체/관계 쓰기 API에서 403
- editor는 자기 project에 객체/관계 생성 가능
- 다른 company/project 객체 직접 조회는 403 또는 404
- 클라이언트 body의 company_id/project_id는 서버에서 신뢰하지 않음
- 삭제는 물리 삭제가 아니라 status tombstone 처리
- 기존 ontology 테스트와 Phase 1 tenant 테스트가 회귀 없이 통과

## 참고 산출물

- `E:\ontology_edu\Codex-통합\docs\FINAL_DESIGN.md`
- `E:\ontology_edu\Codex-통합\docs\04_FINAL_DATA_SCHEMA.md`
- `E:\ontology_edu\Codex-통합\docs\05_MVP_IMPLEMENTATION_PLAN.md`
- `E:\ontology_edu\Codex-통합\project\src\backend\app\tenant.py`
- `E:\ontology_edu\Codex-통합\project\src\backend\app\storage_config.py`

## 완료 결과

완료일: 2026-05-13

- `app/repositories.py`에 TenantContext 기반 BaseRepository, OntologyObjectRepository, OntologyRelationshipRepository 구현
- `/api/v1/ontology/objects` 객체 목록/생성/상세/수정/비활성화 API 추가
- `/api/v1/ontology/relationships` 관계 목록/생성/비활성화 API 추가
- 서버 TenantContext 기준으로 company_id/project_id를 강제 주입하여 클라이언트 입력을 신뢰하지 않도록 처리
- 삭제는 물리 삭제가 아니라 `status=disabled` tombstone으로 처리
- `tests/test_repository_phase2.py`에 권한, 테넌트 격리, 스코프 강제, tombstone 테스트 추가

## 검증

- 실행 위치: `E:\ontology_edu\Codex-통합\project\src\backend`
- 명령: `pytest`
- 결과: `24 passed`
