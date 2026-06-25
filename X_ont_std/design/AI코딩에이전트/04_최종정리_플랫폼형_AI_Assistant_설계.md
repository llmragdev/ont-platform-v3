# 플랫폼형 AI Assistant 최종 설계 정리

**문서 번호**: 04  
**작성자**: Codex  
**작성일**: 2026-06-14  
**대상 시스템**: ont_platform v5  
**상태**: 기존 AI 코딩 에이전트 설계를 보완하는 최종 방향 정리  

---

## 1. 결론

기존 `AI코딩에이전트` 설계는 “자연어 -> 코드 생성 -> 실행 -> 설명”을 중심으로 작성되어 있다.  
이 방향은 유효하지만, 현재 ont_platform v5의 제품 방향에는 조금 좁다.

최종 방향은 다음처럼 정리한다.

```text
AI 코딩 에이전트
  -> 전역 AI Assistant
  -> 온톨로지 Query Builder
  -> 테이블/DB Query Builder
  -> Streamlit 스타일 업무 앱 빌더
  -> 워크플로우/스킬/외부 실행 연결
```

즉, 우리는 단순한 DB 쿼리 도구나 개발자용 코딩 보조 도구를 만드는 것이 아니다.

**우리는 온톨로지 기반으로 업무 객체와 관계를 이해하고, 필요한 쿼리/분석/앱/워크플로우를 AI가 생성해주는 업무 실행형 AI Assistant를 만든다.**

---

## 2. 기존 문서와 새 방향의 차이

| 구분 | 기존 설계 | 최종 보완 방향 |
|---|---|---|
| 진입 방식 | 좌측 메뉴의 AI 코딩 에이전트 화면 | 우측 하단 전역 AI Assistant |
| 중심 기능 | 자연어 -> SQL/Python/SPARQL 생성 | 현재 화면 맥락 기반 질의/앱/워크플로우 생성 |
| 데이터 관점 | DB/쿼리 중심 | 온톨로지 객체/관계 + 테이블/DB + RAG |
| UI 결과 | 코드, 결과 테이블, 설명 | 코드/쿼리 + 차트 + 앱 화면 + 공유 URL |
| Streamlit 관계 | Python 코드 생성 대상 | 플랫폼 내부 앱 빌더 + Streamlit Export |
| 워크플로우 연결 | 후속 확장 기능 | 핵심 차별점 |
| 외부 실행 | API 호출 생성 | MCP/스킬/writeback과 연결 |
| 제품 포지션 | AI 코딩 도구 | 온톨로지 기반 AI 업무 앱/자동화 Assistant |

---

## 3. 제품 포지션

외부 설명 시 다음 표현을 사용한다.

```text
일반 AI 코딩 에이전트는 SQL이나 코드를 생성하는 데 머무릅니다.
이 플랫폼의 AI Assistant는 온톨로지, 워크플로우, RAG, 외부 시스템 실행 기반을 활용해
업무 질문을 질의, 분석 앱, 워크플로우 실행으로 연결합니다.
```

짧은 표현:

```text
Ontology Query + Streamlit 스타일 업무 앱 빌더 + Workflow 실행 Assistant
```

한국어 제품 설명:

```text
온톨로지 기반 업무 질의/앱 생성 Assistant
```

---

## 4. 왜 기존 플랫폼이 중요한가

AI 코딩 에이전트만 단독으로 만들면 다음 수준에 머문다.

```text
자연어 입력
  -> SQL 생성
  -> 코드 실행
  -> 결과 출력
```

이것은 비교적 흔한 코딩 보조 도구다.

하지만 ont_platform v5 위에 붙이면 다음이 가능하다.

```text
자연어 업무 요청
  -> 현재 화면/선택 객체/워크플로우 컨텍스트 인식
  -> 온톨로지 객체/관계 해석
  -> DB/SPARQL/RAG 질의 생성
  -> 결과 테이블/차트/관계 그래프 생성
  -> Streamlit 스타일 업무 앱으로 저장
  -> 필요 시 워크플로우 노드 또는 스킬로 연결
  -> 외부 MCP writeback 실행
  -> 실행 이력과 온톨로지 관계 저장
```

플랫폼이 있기 때문에 쉬워지는 부분:

| 기반 | AI Assistant가 얻는 장점 |
|---|---|
| 온톨로지 스키마 | AI가 테이블/컬럼을 추측하지 않고 업무 객체/관계를 기준으로 질의 생성 |
| 객체/관계 탐색 | 답변 결과를 그래프와 업무 맥락으로 연결 |
| 워크플로우 빌더 | 생성된 분석이나 조치를 업무 절차로 저장 가능 |
| 스킬 시스템 | 댓글 등록, 정비지시 생성, 온톨로지 저장 같은 실행 기능 재사용 |
| MCP 연동 | 외부 시스템에 실제 결과 등록 가능 |
| 감사 로그 | 누가 어떤 질의/앱/실행을 만들었는지 추적 가능 |
| RAG | 문서 근거와 온톨로지 관계를 함께 활용 |
| company_id/project_id | 고객사/프로젝트별 분리 가능 |

---

## 5. UX 최종 방향

### 5.1 좌측 메뉴가 아니라 우측 하단 전역 Assistant

AI Assistant는 별도 좌측 메뉴가 아니라, 모든 화면에서 접근 가능한 우측 하단 아이콘으로 제공한다.

```text
전체 화면 공통
  -> 우측 하단 AI 아이콘
  -> 클릭 시 AI Assistant 패널 열림
```

이유:

- 좌측 메뉴가 복잡해지지 않는다.
- 현재 화면의 맥락을 AI가 활용할 수 있다.
- Streamlit/Cortex 스타일의 즉시 질의/코드/앱 생성 경험을 제공한다.
- Palantir AIP처럼 업무 화면 옆에서 AI가 액션을 제안하는 구조가 된다.

### 5.2 패널 구조

```text
┌────────────────────────────┐
│ AI Assistant                │
│ 현재 화면: 빌더와 실행       │
│ 선택 항목: 공장 정비 워크플로우 │
├────────────────────────────┤
│ 추천 작업                   │
│ - 이 워크플로우 설명하기      │
│ - 온톨로지 쿼리 생성          │
│ - 데이터 앱 만들기            │
│ - 실패 원인 분석             │
├────────────────────────────┤
│ 대화 영역                   │
├────────────────────────────┤
│ 생성 쿼리/앱 Preview         │
│ [검증] [실행] [앱 저장]       │
└────────────────────────────┘
```

### 5.3 현재 화면별 동작 예

| 현재 화면 | Assistant 동작 |
|---|---|
| 빌더와 실행 | 워크플로우 설명, 노드 추가 제안, 실패 원인 분석 |
| 관계 탐색 | 선택 객체 관련 SPARQL/그래프 질의 생성 |
| 스키마 관리 | 스키마 기반 질의 템플릿 생성 |
| 인스턴스 편집 | 데이터 품질 점검, 누락 속성 추천 |
| 문서 RAG 질의 | 답변 근거를 앱/워크플로우로 저장 |
| 통합 질의 | 질의 결과를 대시보드/앱으로 전환 |
| 데이터 흐름 | 실패 가능 지점 분석, 영향 경로 설명 |

---

## 6. 카테고리 구조

AI Assistant가 생성하고 관리하는 대상은 크게 두 카테고리로 나눈다.

### 6.1 테이블/DB 카테고리

목적:

- DB 연결
- 테이블 목록 조회
- 컬럼/스키마 확인
- 샘플 데이터 조회
- SQL 생성/실행
- 결과 테이블 저장
- 온톨로지 객체와 매핑

권장 메뉴 또는 하위 영역:

```text
데이터
  - 테이블/DB
  - 쿼리 콘솔
  - 쿼리 결과
  - 온톨로지 매핑
```

주의:

테이블/DB는 중심이 아니라 데이터 소스 중 하나다.  
제품의 중심은 온톨로지와 업무 앱 생성이다.

### 6.2 Streamlit 스타일 앱 카테고리

목적:

- 쿼리 결과를 앱 화면으로 구성
- 지표 카드/테이블/차트/관계 그래프 배치
- 앱 저장
- 앱 실행
- 공유 URL 생성
- Streamlit 코드 Export

권장 메뉴 또는 하위 영역:

```text
앱 빌더
  - 앱 목록
  - 새 앱 만들기
  - 앱 편집
  - 앱 실행
  - 공유 앱
  - Streamlit Export
```

---

## 7. Streamlit과의 관계

우리는 Streamlit을 그대로 복제하지 않는다.  
Streamlit의 장점인 **간결한 세션, 빠른 쿼리, 빠른 앱 화면 생성, 공유 가능한 URL**을 온톨로지 플랫폼에 맞게 흡수한다.

| Streamlit | 우리 플랫폼 |
|---|---|
| Python 코드로 데이터 앱 생성 | AI가 온톨로지/DB/RAG 기반 앱 스펙 생성 |
| DataFrame 중심 | 업무 객체/관계 중심 |
| 개발자가 코드 작성 | AI Assistant가 질의/차트/앱 초안 생성 |
| 앱 실행 URL 제공 | `/apps/{appId}` 또는 공유 URL 제공 |
| 세션 상태 관리 | company_id/project_id/current_view/selected_object 중심 간결 세션 |
| 단일 앱 중심 | 앱 + 워크플로우 + 온톨로지 + 감사 로그 연결 |

---

## 8. 세션 모델

세션은 복잡하게 만들지 않는다.  
Streamlit처럼 간결하게 현재 컨텍스트만 유지한다.

```json
{
  "session_id": "sess_abc123",
  "company_id": "demo-co",
  "project_id": "proj-01",
  "current_view": "workflow-graph",
  "selected_object_id": "equipment-001",
  "selected_workflow_id": "wfg-001",
  "selected_app_id": "factory-repeated-fault",
  "last_query_id": "q-001"
}
```

세션에 담을 것:

- 현재 사용자
- company_id/project_id
- 현재 화면
- 선택한 객체
- 선택한 워크플로우
- 선택한 앱
- 최근 질의 결과

세션에 담지 않을 것:

- 전체 원본 데이터
- 민감한 payload
- 전체 LLM prompt
- 외부 MCP endpoint

---

## 9. 앱 저장과 외부 URL

AI Assistant가 만든 결과는 앱으로 저장할 수 있어야 한다.

### 9.1 내부 앱 URL

```text
/apps/{appId}
/apps/demo-co/proj-01/{appId}
```

예:

```text
/apps/factory-repeated-fault
/apps/customer-reply-monitor
```

### 9.2 외부 공유 URL

외부 공유는 별도 토큰과 read-only 정책이 필요하다.

```text
/share/{shareId}
/share/{shareId}?token=xxxxx
```

외부 공유 화면에서 노출하지 말아야 할 것:

- 내부 API 경로
- storage 경로
- MCP endpoint
- workflow node id
- raw prompt
- raw LLM response
- 민감 payload
- 전체 온톨로지 스키마

외부 공유 화면에 보여줄 것:

- 앱 제목
- 설명
- 지표 카드
- 차트
- 테이블
- 관계 그래프
- 데이터 기준 시각
- 데모 데이터 여부

---

## 10. App Spec 모델

Streamlit 스타일 앱은 코드 자체보다 먼저 App Spec으로 저장한다.

```json
{
  "app_id": "factory-repeated-fault",
  "title": "공장 반복 고장 분석",
  "company_id": "demo-co",
  "project_id": "proj-01",
  "description": "최근 7일 반복 고장 설비와 정비지시 상태를 보여주는 앱",
  "layout": [
    {
      "type": "metric",
      "title": "반복 고장 설비 수",
      "query_id": "q1"
    },
    {
      "type": "table",
      "title": "최근 7일 반복 고장 목록",
      "query_id": "q2"
    },
    {
      "type": "chart",
      "title": "설비별 고장 횟수",
      "query_id": "q3"
    },
    {
      "type": "graph",
      "title": "고장-설비-정비지시 관계",
      "query_id": "q4"
    }
  ]
}
```

---

## 11. Streamlit Export

플랫폼 내부 앱 렌더링이 1순위다.  
실제 Streamlit 런타임 연동은 2차 또는 3차 기능으로 둔다.

### 11.1 1차: Streamlit 코드 Export

```python
import streamlit as st

st.title("공장 반복 고장 분석")

df = run_query("recent_repeated_faults")

st.metric("반복 고장 설비 수", len(df))
st.dataframe(df)
st.bar_chart(df.set_index("equipment_name")["fault_count"])
```

### 11.2 2차: Streamlit 앱 실행

고려할 것:

- 프로세스 관리
- 포트 관리
- 사용자별 세션
- 보안 샌드박스
- 파일 시스템 접근 제한
- 외부 공유 정책

권장 순서:

```text
App Spec 저장
  -> 내부 /apps/{appId} 렌더링
  -> 공유 URL
  -> Streamlit 코드 Export
  -> 실제 Streamlit runtime 실행
```

### 11.3 Streamlit SDK 연동

`design/coding ai/01_streamlit_cortex_agent_design.md`의 핵심 아이디어는 유지한다.  
다만 최종 제품 방향에서는 Streamlit을 1차 UI 엔진으로 삼기보다, **플랫폼 내부 App Spec 렌더링 이후의 확장 수단**으로 둔다.

Streamlit 앱 개발자가 플랫폼 기능을 쉽게 호출할 수 있도록 Python SDK를 제공할 수 있다.

```python
import workflow_workbench as ww

df = ww.cortex.query_data("최근 7일 반복 고장 설비 보여줘")
summary = ww.cortex.complete("이 결과를 현장 담당자용으로 요약해줘")
run = ww.workflow.run("factory-maintenance", inputs={"status": "open", "limit": 1})
```

권장 SDK 모듈:

| 모듈 | 역할 |
|---|---|
| `ww.cortex` | LLM, RAG, 자연어 질의, 쿼리 생성 |
| `ww.ontology` | 스키마, 객체, 관계, SPARQL 조회 |
| `ww.workflow` | 워크플로우 실행과 상태 조회 |
| `ww.apps` | App Spec 저장, 앱 조회, 공유 링크 생성 |
| `ww.audit` | 실행 이력과 외부 호출 이력 조회 |

### 11.4 Streamlit Live Preview

고급 기능으로 콘솔 내부에 Streamlit 편집/미리보기 환경을 제공할 수 있다.

```text
좌측 또는 중앙: Monaco Editor
우측: Streamlit Live Preview iframe
상단: 저장 / 실행 / 공유 / Export
```

구현 시 고려 사항:

- Streamlit 앱은 Docker 또는 별도 sandbox에서 실행한다.
- 앱별 포트, 프로세스, 세션을 관리해야 한다.
- 외부 공유 시 내부 API key와 MCP endpoint를 노출하지 않는다.
- app.py 원문은 내부 저장소에 보관하고, 외부 공유 화면에는 앱 결과만 노출한다.
- 초기 MVP에서는 Live Preview보다 App Spec 기반 내부 렌더링이 우선이다.

### 11.5 Streamlit 기능 우선순위

| 단계 | 기능 | 우선순위 |
|---|---|---|
| 1 | App Spec 기반 내부 앱 렌더링 | 최우선 |
| 2 | 공유 URL | 높음 |
| 3 | Streamlit 코드 Export | 중간 |
| 4 | `workflow-workbench-sdk` 제공 | 중간 |
| 5 | Streamlit Live Preview iframe | 낮음 |
| 6 | Docker Sandbox 기반 앱 실행 | 낮음, 보안 검토 후 |

---

## 12. API 설계 초안

### 12.1 Assistant 대화

```http
POST /api/assistant/chat
```

요청:

```json
{
  "message": "최근 7일간 반복 고장이 많은 설비를 차트로 보여줘",
  "context": {
    "current_view": "ontology-graph",
    "company_id": "demo-co",
    "project_id": "proj-01",
    "selected_object_id": "factory-sejong"
  }
}
```

응답:

```json
{
  "intent": "create_app",
  "summary": "최근 7일 반복 고장 설비 분석 앱을 제안합니다.",
  "generated_queries": [],
  "app_spec_preview": {},
  "actions": ["validate", "execute", "save_app"]
}
```

### 12.2 쿼리 생성/검증/실행

```http
POST /api/assistant/query/generate
POST /api/assistant/query/validate
POST /api/assistant/query/execute
```

### 12.3 앱 저장/조회

```http
POST /api/apps
GET /api/apps
GET /api/apps/{app_id}
PUT /api/apps/{app_id}
DELETE /api/apps/{app_id}
```

### 12.4 공유 링크

```http
POST /api/apps/{app_id}/share
GET /api/share/{share_id}
```

### 12.5 Streamlit Export

```http
POST /api/apps/{app_id}/export/streamlit
```

---

## 13. 프론트엔드 영향 프로그램

| 파일 | 변경/추가 내용 |
|---|---|
| `frontend/src/components/AIAssistantPanel.tsx` | 우측 하단 전역 Assistant 패널 |
| `frontend/src/components/AIAssistantButton.tsx` | 전역 플로팅 버튼 |
| `frontend/src/components/GeneratedQueryPreview.tsx` | 생성 쿼리 표시 |
| `frontend/src/components/AppSpecPreview.tsx` | 앱 스펙 미리보기 |
| `frontend/src/components/AppBuilder.tsx` | Streamlit 스타일 앱 빌더 |
| `frontend/src/components/AppRenderer.tsx` | `/apps/{appId}` 렌더링 |
| `frontend/src/components/TableDbExplorer.tsx` | 테이블/DB 카테고리 화면 |
| `frontend/src/components/StreamlitExportPanel.tsx` | Streamlit 코드 Export |
| `frontend/src/components/StreamlitPreviewPanel.tsx` | Streamlit Live Preview iframe, 후순위 |
| `frontend/src/components/Sidebar.tsx` | 데이터/앱 빌더 카테고리 추가 검토 |
| `frontend/src/app/page.tsx` | view key 및 렌더러 추가 |
| `frontend/src/lib/api.ts` | assistant/apps API 클라이언트 추가 |
| `frontend/src/types/api.ts` | Assistant, Query, AppSpec 타입 추가 |

---

## 14. 백엔드 영향 프로그램

| 파일 | 변경/추가 내용 |
|---|---|
| `backend/app/models/assistant.py` | Assistant 요청/응답 모델 |
| `backend/app/models/app_spec.py` | App Spec 모델 |
| `backend/app/models/query_spec.py` | Query Spec 모델 |
| `backend/app/api/assistant.py` | Assistant API |
| `backend/app/api/apps.py` | App 저장/조회/공유 API |
| `backend/app/services/assistant_service.py` | 의도 분석/응답 orchestration |
| `backend/app/services/query_generation_service.py` | 온톨로지/SPARQL/SQL 생성 |
| `backend/app/services/query_validation_service.py` | 안전성/문법/권한 검증 |
| `backend/app/services/query_execution_service.py` | read-only 쿼리 실행 |
| `backend/app/services/app_spec_service.py` | 앱 스펙 저장/렌더 데이터 구성 |
| `backend/app/services/streamlit_export_service.py` | Streamlit 코드 생성 |
| `backend/app/services/streamlit_runtime_service.py` | Streamlit sandbox 실행/중지/상태 확인, 후순위 |
| `sdk/workflow_workbench/` | 외부 Streamlit 앱용 Python SDK, 후순위 |
| `backend/app/main.py` | assistant/apps router 등록 |

---

## 15. 구현 우선순위

### Phase 1: 전역 Assistant MVP

목표: 우측 하단 Assistant에서 현재 화면 맥락을 받아 설명/쿼리 초안을 생성한다.

범위:

- 플로팅 AI 버튼
- Assistant 패널
- 현재 화면 context 전달
- 자연어 질문 입력
- 온톨로지 질의/SPARQL 초안 생성
- 생성 결과 preview
- 복사 버튼

예상 기간:

```text
1~2주
```

### Phase 2: Query 실행과 앱 저장

목표: 생성된 쿼리를 검증/실행하고 앱 스펙으로 저장한다.

범위:

- 쿼리 검증
- read-only 실행
- 결과 테이블 표시
- 차트 추천
- App Spec 저장
- `/apps/{appId}` 렌더링

예상 기간:

```text
2~4주
```

### Phase 3: Streamlit Export와 공유 URL

목표: 내부 앱을 외부 공유하거나 Streamlit 코드로 내보낸다.

범위:

- 공유 링크 생성
- read-only 공유 화면
- Streamlit 코드 Export
- 민감정보 제거

예상 기간:

```text
2~3주
```

### Phase 4: 워크플로우/스킬 연동

목표: Assistant가 만든 질의/앱/분석을 워크플로우 노드와 스킬로 연결한다.

범위:

- “워크플로우 노드로 추가”
- “스킬로 저장”
- 실행 이력 연결
- 감사 로그 연결

예상 기간:

```text
3~5주
```

---

## 16. 보안 원칙

### 16.1 쿼리 실행

- 1차는 read-only만 허용한다.
- destructive SQL은 금지한다.
- Python 실행은 초기 범위에서 제외하거나 별도 샌드박스 이후 허용한다.
- 실행 전 권한과 company_id/project_id 범위를 검증한다.

### 16.2 외부 공유

- share token 기반으로 접근한다.
- 공유 앱은 read-only다.
- 내부 API, storage 경로, MCP endpoint를 노출하지 않는다.
- 원본 prompt와 raw LLM response를 노출하지 않는다.
- 공유 범위와 만료일을 설정할 수 있어야 한다.

### 16.3 LLM 사용

- 온톨로지 스키마/요약 컨텍스트만 제공한다.
- 민감 payload는 prompt에 넣지 않는다.
- 생성 쿼리는 실행 전 검증한다.
- 실행 로그와 감사 로그를 남긴다.

---

## 17. 기존 문서 보완 방향

현재 문서들은 다음처럼 해석한다.

| 문서 | 유지/보완 방향 |
|---|---|
| `00_아키텍처_개요.md` | 기존 코딩 에이전트 개념의 기본 자료로 유지. 단, 최종 제품 방향은 본 문서가 우선한다. |
| `01_컴포넌트_상세설계.md` | 6개 컴포넌트는 유효. 다만 Code Generator 중심에서 Query/App/Workflow Generator로 확장한다. |
| `02_시스템통합설계.md` | 좌측 메뉴 통합보다 전역 Assistant 패널 중심으로 수정 필요. App Spec/API 추가 필요. |
| `03_구현계획.md` | Phase 1 범위를 SPARQL/온톨로지 질의 + Assistant MVP로 축소해 재정렬 필요. |
| `README.md` | 본 문서를 최종 방향 문서로 링크하고, 기존 문서와의 관계를 명시한다. |
| `../coding ai/01_streamlit_cortex_agent_design.md` | Streamlit SDK, Live Preview, Docker Sandbox 아이디어는 유효. 단, 본 문서에서는 후순위 확장 기능으로 재배치한다. |

---

## 18. 최종 메시지

최종적으로 이 기능은 “AI 코딩 에이전트”라는 이름보다 아래 표현이 더 적합하다.

```text
온톨로지 기반 AI 업무 앱 Assistant
```

또는:

```text
Ontology Query & App Builder
```

기술적으로는 SQL/Python/SPARQL 생성이 가능하지만, 제품적으로는 다음 메시지가 핵심이다.

```text
사용자는 현재 업무 화면에서 AI에게 요청하고,
AI는 온톨로지와 데이터 소스를 이해해 쿼리, 차트, 앱, 워크플로우 초안을 만들며,
그 결과를 플랫폼 내부 앱 또는 공유 URL로 제공할 수 있습니다.
```
