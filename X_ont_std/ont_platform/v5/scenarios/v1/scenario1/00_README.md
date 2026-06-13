# Scenario v1 / Scenario 1

## 목적

이 폴더는 v5 P0 시나리오 1의 요구사항, API 계약, 트리거 설계, 고객사 mock 인프라 설계, 연동 테스트 결과를 보관한다.

Scenario 1의 목표:

```text
고객 문의 등록
  -> ont_platform v5가 문의 이벤트를 인식
  -> LLM 경로로 댓글 메시지 생성
  -> ont_platform v5가 customer_mcp 호출
  -> customer_mcp가 customer_board API 호출
  -> ont_platform v5가 결과와 audit 저장
```

## 서버 구성

| Server | Port | Owner | Role |
| --- | ---: | --- | --- |
| solution backend | 8001 | ont_platform v5 | workflow, LLM draft, customer MCP client adapter |
| solution frontend | 3002 | ont_platform v5 | 운영/시연 UI |
| customer_mcp | 8080 | 고객사 영역 | MCP 중계 및 고객사 API adapter |
| customer_board | 8090 | 고객사 영역 | SQLite 기반 고객사 게시판 mock |

## 책임 경계

- v5는 `customer_mcp`만 호출한다.
- v5는 `customer_board`를 직접 호출하지 않는다.
- `customer_mcp`와 `customer_board`는 고객사 영역이다.
- v5의 책임은 댓글 메시지 생성, customer_mcp 호출, 처리 상태/audit 저장이다.

## 문서 읽는 순서

1. `00_README.md`: 폴더 진입점
2. `10_REQUIREMENTS_OVERALL.md`: 전체 요구사항
3. `11_REQUIREMENTS_ONT_PLATFORM.md`: ont_platform v5 요구사항
4. `12_REQUIREMENTS_CUSTOMER_MCP.md`: 고객사 MCP 요구사항
5. `20_CUSTOMER_MCP_CALL_SPEC.md`: v5 -> customer_mcp 호출 계약
6. `21_CUSTOMER_MCP_RUNTIME_GUIDE.md`: `s1_customer_mcp` 구동/검증 요약
7. `30_TRIGGER_DESIGN.md`: Scenario 1-1/1-2 트리거 설계
8. `40_CUSTOMER_MOCK_INFRA_DESIGN.md`: 고객사 mock 인프라 설계
9. `50_DESIGN_AND_DEVELOPMENT_REPORT.md`: 고객사 모의 인프라 설계 및 개발 보고서
10. `60_SCENARIO_EXECUTION_ONE_PAGER.md`: webhook/batch 시나리오 실행 한 장 요약
11. `70_WORKFLOW_SCREEN_TEST_GUIDE.md`: Workflow Builder 화면 테스트 방법
12. `80_WORKFLOW_BUILDER_SCENARIO_GRAPH_DESIGN.md`: Workflow Builder 시나리오 그래프 설계
13. `85_WORKFLOW_ONTOLOGY_TRACE_DESIGN.md`: 워크플로우 실행 결과를 온톨로지에 저장/시각화하는 설계
14. `90_INTEGRATION_SMOKE_TEST_RESULT.md`: 연동 smoke test 결과
15. `95_FACTORY_REPEATED_FAULT_SCENARIO_PROPOSAL.md`: 공장 반복 장애 확장 예시
16. `96_FACTORY_AUTOMATION_SERVER_DEV_GUIDE.md`: 공장 자동화 mock 서버 개발 가이드
17. `../../../../../design/workflow/온톨로지_워크플로우_솔루션_설명서.md`: 솔루션 사용자 설명서

