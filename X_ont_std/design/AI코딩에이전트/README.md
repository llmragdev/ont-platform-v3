# AI 코딩 에이전트 설계 문서

**대상 시스템**: ont_platform v5  
**정리 기준일**: 2026-06-14  
**최종 방향**: 우측 하단 전역 AI Assistant + 온톨로지 Query Builder + 테이블/DB Query Builder + Streamlit 스타일 앱 빌더

---

## 1. 현재 폴더 구조

루트에는 지금 의사결정과 구현 방향에 직접 필요한 문서만 둔다.

| 문서 | 역할 | 우선순위 |
|---|---|---|
| [04_최종정리_플랫폼형_AI_Assistant_설계.md](./04_최종정리_플랫폼형_AI_Assistant_설계.md) | 최종 제품 방향과 구현 기준 | 최우선 |
| [05_CORTEX_vs_ONTOLOGY_COMPARISON.md](./05_CORTEX_vs_ONTOLOGY_COMPARISON.md) | Snowflake Cortex AI와 온톨로지 플랫폼 비교 | 전략/외부 설명 |
| [06_Codex_AI_Assistant_MVP_구현완료보고.md](./06_Codex_AI_Assistant_MVP_구현완료보고.md) | Codex 1차 MVP 구현 범위, 변경 프로그램, 검증 결과 | 구현 완료 보고 |
| [07_ClaudeCode_작업인수인계_및_잔여과제.md](./07_ClaudeCode_작업인수인계_및_잔여과제.md) | Claude Code 후속 작업 지시, Streamlit 실행 API 잔여 과제 | 작업 인수인계 |
| [08_ClaudeCode_구현_완료_보고.md](./08_ClaudeCode_구현_완료_보고.md) | Streamlit 앱 실행 기능 및 백엔드 API 구현 완료 보고 | 구현 완료 보고 |

초기 설계와 아이디어 문서는 `archive` 하위로 이동했다.

```text
archive/
  legacy_design/
    00_아키텍처_개요.md
    01_컴포넌트_상세설계.md
    02_시스템통합설계.md
    03_구현계획.md

  reference_ideas/
    04_idea_seq1_antigravity.md
    06_streamlit_cortex_agent_design.md
```

---

## 2. 최종 제품 방향

기존 설계는 “자연어 -> 코드 생성 -> 실행 -> 설명” 중심이었다.  
현재 최종 방향은 더 넓다.

```text
전역 AI Assistant
  -> 온톨로지 Query Builder
  -> 테이블/DB Query Builder
  -> Streamlit 스타일 업무 앱 빌더
  -> 워크플로우/스킬/외부 실행 연결
```

핵심은 단순 코딩 보조가 아니다.

```text
사용자는 현재 업무 화면에서 AI에게 요청하고,
AI는 온톨로지와 데이터 소스를 이해해 쿼리, 차트, 앱, 워크플로우 초안을 만들며,
그 결과를 플랫폼 내부 앱 또는 공유 URL로 제공한다.
```

---

## 3. 읽는 순서

### 빠른 의사결정

1. [04_최종정리_플랫폼형_AI_Assistant_설계.md](./04_최종정리_플랫폼형_AI_Assistant_설계.md)
2. [05_CORTEX_vs_ONTOLOGY_COMPARISON.md](./05_CORTEX_vs_ONTOLOGY_COMPARISON.md)

### 구현자가 참고할 때

1. 04번 최종정리 문서
2. 08번 Claude Code 구현 완료 보고 (최신 실행 계층 정보)
3. 06번 Codex MVP 구현 완료 보고
4. 07번 Claude Code 작업 인수인계
5. `archive/legacy_design/01_컴포넌트_상세설계.md`
6. `archive/legacy_design/02_시스템통합설계.md`
7. `archive/reference_ideas/06_streamlit_cortex_agent_design.md`

단, archive 문서는 참고용이다. 구현 우선순위와 제품 방향은 04번 문서를 따른다.

---

## 4. 문서별 판단

| 문서 | 현재 판단 |
|---|---|
| 04 최종정리 | 최종 기준 문서. 유지 |
| 05 Cortex 비교 | 외부 설명과 전략 비교에 유용. 유지 |
| 06 Codex MVP 구현 완료 보고 | 실제 구현 범위와 다음 개발 순서를 추적하기 위해 유지 |
| 07 Claude Code 작업 인수인계 | Streamlit 실행 API와 URL 연결 실패 해결을 위한 후속 작업 문서 |
| 08 Claude Code 구현 완료 보고 | 백엔드 API `/run` 및 fallback preview 연동 검증용 문서. 유지 |
| 00~03 초기 설계 | 개념과 세부 컴포넌트 참고용. archive 이동 |
| 04 Antigravity idea | 일부 아이디어 참고용. archive 이동 |
| 06 Streamlit 설계 | SDK/Live Preview/Docker Sandbox 참고용. archive 이동 |

---

## 5. 구현 우선순위

1. 우측 하단 전역 AI Assistant 버튼/패널
2. 현재 화면 context 전달
3. 온톨로지 질의/SPARQL 초안 생성
4. 생성 쿼리 preview와 복사
5. read-only 쿼리 검증/실행
6. 결과 테이블/차트 표시
7. App Spec 저장
8. `/apps/{appId}` 내부 렌더링
9. 공유 URL
10. Streamlit 코드 Export
11. Streamlit Live Preview/Docker Sandbox

---

## 6. 외부 설명용 문장

```text
일반 AI 코딩 에이전트는 SQL이나 코드를 생성하는 데 머무릅니다.
이 플랫폼의 AI Assistant는 온톨로지, 워크플로우, RAG, 외부 시스템 실행 기반을 활용해
업무 질문을 질의, 분석 앱, 워크플로우 실행으로 연결합니다.
```

짧게는 다음처럼 표현한다.

```text
Ontology Query + Streamlit 스타일 업무 앱 빌더 + Workflow 실행 Assistant
```
