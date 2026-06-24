# v5.3 UI 수동 Smoke 및 Word 증거 검증 보고

- 작성자: Codex
- 기준 시각: 2026-06-24 10:05 KST
- 검증 자료: 사용자 생성 Word 저장 결과 8건
- 판정: UI 수동 smoke GO

## 1. 검증 개요

사용자가 UI에서 직접 질의 후 `Word 저장` 기능으로 결과를 저장했다. Codex는 저장된 `.doc` 파일의 내부 HTML 메타데이터를 확인하여 v5.3 판정, confidence, 이미지 포함 여부를 검증했다.

검증 위치:

- `C:\Users\nkchoi2\Downloads\통과필요`
- `C:\Users\nkchoi2\Downloads\차단 필요`
- `C:\Users\nkchoi2\Downloads`

## 2. 차단 필요 테스트 결과

| 질문 | 기대 | 실제 판정 | 신뢰도 | 이미지 |
|---|---|---|---:|---|
| Snowflake External/Internal Stage 운영 | 차단 | `NO_ANSWER / blocked` | `0%` | 포함 |
| Kubernetes 벡터 DB + LLM 배포 아키텍처 | 차단 | `NO_ANSWER / blocked` | `0%` | 포함 |
| Azure AI Search + OpenAI PDF QA 인덱스 설계 | 차단 | `NO_ANSWER / blocked` | `0%` | 포함 |
| Snowflake RAG 정형 테이블 + PDF 통합 전략 | 차단 | `NO_ANSWER / blocked` | `0%` | 포함 |

판정: PASS

## 3. 통과 필요 테스트 결과

| 질문 | 기대 | 실제 판정 | 신뢰도 | 이미지 |
|---|---|---|---:|---|
| DB 스키마를 온톨로지로 변환하는 절차 | 부분 답변 | `PARTIAL / partial` | `75%` | 포함 |
| 온톨로지 기반 QA에서 상위 온톨로지 역할 | 부분 답변 | `PARTIAL / partial` | `75%` | 포함 |
| 지휘통제(C2) 온톨로지 관계 그래프 활용 | 부분 답변 | `PARTIAL / partial` | `75%` | 포함 |
| 문서 근거와 온톨로지 근거 충돌 시 제한 | 일반/제한 답변 | `GENERAL_ONLY / partial` | `55%` | 포함 |

판정: PASS

## 4. Word 저장 기능 확인

8개 파일 모두 내부 HTML에서 `data:image/png;base64` 이미지가 포함되어 있음을 확인했다.

확인 항목:

- 질문 텍스트 저장: PASS
- v5.3 판정 저장: PASS
- confidence 저장: PASS
- 화면 캡처 이미지 포함: PASS

## 5. 종합 판정

| 항목 | 판정 |
|---|---|
| Snowflake/Kubernetes/Azure 외부 도메인 차단 | GO |
| 내부 온톨로지 관련 질문 부분 답변 | GO |
| `NO_ANSWER / 0%` UI 표시 | GO |
| `PARTIAL / 75%` UI 표시 | GO |
| `GENERAL_ONLY / 55%` UI 표시 | GO |
| Word evidence 저장 | GO |

최종 판정:

```text
V5.3 Phase 1 UI Manual Smoke: GO
```

단, Cypress 자동화 실행은 환경 이슈로 별도 WAIT/SKIP 상태이며, 본 판정은 사용자 수동 UI smoke와 Word evidence 기반이다.

