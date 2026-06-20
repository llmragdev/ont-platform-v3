# 🛠️ 온톨로지 기반 Cortex AI 스타일 Streamlit 에이전트 설계서

본 문서는 **Snowflake Cortex AI**와 **Streamlit in Snowflake(SiS)** 모델을 벤치마킹하여, 사용자가 Python 스크립트(Streamlit)만으로 온톨로지 플랫폼의 AI 기능과 워크플로우를 결합한 대화형 에이전트 애플리케이션을 빠르게 개발·배포할 수 있도록 하는 아키텍처 설계 및 구현 방안을 기술합니다.

---

## 🏗️ 1. 통합 아키텍처 개요

Snowflake가 Streamlit을 인수하여 데이터 앱 개발을 대중화했듯이, 온톨로지 플랫폼 v5도 **FastAPI 백엔드(SDK) + Streamlit UI**를 결합하여 사용자가 직접 코딩 에이전트 앱을 빌드할 수 있는 환경을 제공합니다.

```
┌───────────────────────────────────────────────────────────────────┐
│              Streamlit AI 에이전트 앱 (User Sandbox)                │
│  - 대화형 Chat 인터페이스, 실시간 시각화, 데이터 다운로드           │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ (Workflow Workbench Python SDK)
                                  ↓
┌───────────────────────────────────────────────────────────────────┐
│               Workflow Workbench SDK (ww-sdk)                     │
│  - ww.cortex (LLM, RAG, 코드생성 API)                             │
│  - ww.ontology (스키마, 인스턴스, SPARQL API)                     │
│  - ww.workflow (워크플로우 실행 및 모니터링 API)                  │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ (REST API / gRPC)
                                  ↓
┌───────────────────────────────────────────────────────────────────┐
│                FastAPI Backend (ont_platform)                     │
│  - LLM 통합 샌드박스, SPARQL DB, Vector DB, Workflow Engine       │
└───────────────────────────────────────────────────────────────────┘
```

---

## 📦 2. Python SDK 설계 (`workflow-workbench-sdk`)

Streamlit 앱 개발자가 아주 직관적으로 온톨로지와 AI 에이전트를 제어할 수 있도록 랩핑한 Python SDK 인터페이스입니다.

### 2.1 `ww.cortex` (AI 및 LLM 서비스)
* `ww.cortex.complete(prompt: str, model: str = "claude-3-5") -> str`
  - 일반 자연어 텍스트 생성 및 추론.
* `ww.cortex.query_data(query: str) -> pd.DataFrame`
  - 자연어로 질의하면 LLM이 온톨로지 스키마를 참고하여 SQL/SPARQL을 자동 생성한 뒤 실행하고, 결과를 Pandas DataFrame으로 반환.
* `ww.cortex.extract_answer(document_id: str, question: str) -> str`
  - 특정 문서 RAG 기반의 질문 답변 추출.

### 2.2 `ww.workflow` (워크플로우 제어)
* `ww.workflow.run(workflow_id: str, inputs: dict) -> dict`
  - 빌더에서 설계한 워크플로우를 백엔드에서 트리거하여 최종 실행 결과 및 DLQ 적재 상태 반환.

---

## 🚀 3. 단계별 로드맵 (Streamlit 개발 에이전트 실현 방안)

### 📍 Phase 1: SDK 래퍼 및 외부 연동 (2주)
- FastAPI 백엔드의 주요 컨트롤러를 Python 라이브러리(`workflow-workbench-sdk`)로 패키징합니다.
- 로컬의 Streamlit 환경에서 이 패키지를 `pip install`하여 즉시 온톨로지 데이터를 조회하고 워크플로우를 돌릴 수 있도록 인증/통신 모듈을 정립합니다.

### 📍 Phase 2: 콘솔 내 'Streamlit 앱 에디터' 임베딩 (3주)
- React 프론트엔드 내에 **Monaco Editor(VS Code 스타일 에디터)**와 **Streamlit Live Preview Iframe**을 배치합니다.
- 사용자가 온톨로지 콘솔 웹 화면에서 직접 Streamlit 파이썬 코드를 타이핑하고 [저장]하면, 백엔드 내부의 Docker Sandbox에서 Streamlit이 기동되어 즉시 우측 화면에 대시보드 UI가 렌더링되게 만듭니다.

### 📍 Phase 3: AI Streamlit Auto-Coder (4주)
- 사용자가 **"최근 감사 로그 에러 현황을 파이 차트로 보여주는 앱 만들어줘"**라고 콘솔 내 챗봇에게 요청하면, AI 코딩 에이전트가 Streamlit 파이썬 코드를 자동으로 빌드하여 `app.py`로 저장한 뒤, Iframe으로 즉시 띄워주는 완전 자동화 에이전트 루프를 구현합니다.
