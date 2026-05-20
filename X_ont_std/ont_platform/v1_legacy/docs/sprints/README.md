# 스프린트 보고서 인덱스

> 에자일 방식으로 진행되는 `claud_통합` 프로젝트의 스프린트 단위 이력과 상태를 추적합니다.
> 각 스프린트 보고서는 **목표 → 완료 → 문제 → 개선** 구조로 작성됩니다.

---

## 스프린트 현황 요약

| Sprint | 기간 | 주제 | 상태 | 테스트 |
|--------|------|------|------|--------|
| [Sprint 01](sprint_01.md) | 2026-05-11 | 통합 기반 구축 (백엔드 + 프론트 초기) | ✅ 완료 | pytest 17/17 |
| [Sprint 02](sprint_02.md) | 2026-05-11 | 인프라 강화 (JWT·DB·OTel·Docker·E2E) | ✅ 완료 | pytest 59/59 · E2E 6/6 |
| [Sprint 03](sprint_03.md) | 2026-05-12 | 온톨로지 재설계 Phase 1~5 + Vector RAG | ✅ 완료 | pytest 67/67 · evaluate 10/10 |
| [Sprint 04](sprint_04.md) | 2026-05-12 ~ 13 | 하이브리드 질의 시스템 (온톨로지 + RAG) | ✅ 완료 | pytest 64/64 |
| [Sprint 05](sprint_05.md) | 2026-05-13 | 통합 테스트 자동화 + 문서화 체계 | 🔄 진행 중 | - |

---

## 누적 지표

| 지표 | Sprint 01 | Sprint 02 | Sprint 03 | Sprint 04 | Sprint 05 |
|------|-----------|-----------|-----------|-----------|-----------|
| pytest 통과 수 | 17 | 59 | 67 | 64 (신규) | - |
| API 엔드포인트 수 | ~12 | ~20 | ~28 | ~35 | - |
| 프론트 화면 수 | 5 | 6 | 9 | 12 | - |
| 발견된 버그 | 2 | 3 | 1 | 4 | - |
| 회귀 건수 | 0 | 0 | 0 | 0 | - |

---

## 스프린트 신규 작성 방법

```bash
# 새 스프린트 시작 시 템플릿 복사
cp docs/sprints/TEMPLATE.md docs/sprints/sprint_06.md
# → 내용 채운 뒤 이 README의 표에 행 추가
```

템플릿: [TEMPLATE.md](TEMPLATE.md)

---

## 전체 기술 결정 이력 (ADR 요약)

| 날짜 | 결정 | 이유 | Sprint |
|------|------|------|--------|
| 2026-05-11 | 폴더명 `claud_통합` (한글) 유지 | 기존 프로젝트와 일관성 | Sprint 01 |
| 2026-05-11 | LLM: `google-genai` SDK (langchain 미사용) | langchain-google-genai가 v1beta 임베딩 모델 강제 → 404 | Sprint 01 |
| 2026-05-11 | JWT 외부 라이브러리 없이 표준 라이브러리로 구현 | 교육 환경 최소 의존성 | Sprint 02 |
| 2026-05-11 | `eval/exec` 금지 → condition 화이트리스트 파서 | 보안 | Sprint 02 |
| 2026-05-12 | 온톨로지 스키마 JSON 외부화 | 코드 수정 없이 타입 추가 가능 | Sprint 03 |
| 2026-05-12 | 임베딩: `models/gemini-embedding-001` 직접 호출 | langchain 우회 | Sprint 03 |
| 2026-05-12 | 하이브리드 쿼리: `generate_text()` 신규 메서드 | `generate()`는 RAG 전용 (search_results 필수) | Sprint 04 |
| 2026-05-12 | 온톨로지 관리 라우트 `/api/ontology/mgmt/...` 네임스페이스 | `/api/ontology/schema` 중복 라우트 충돌 해소 | Sprint 04 |
