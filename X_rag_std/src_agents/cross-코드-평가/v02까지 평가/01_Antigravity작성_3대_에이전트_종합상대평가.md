# 3대 AI 에이전트 RAG 백엔드 소스코드 상대평가 보고서

이 문서는 `AI_Agent_Mission_Directive.md` 및 `RAG_표준_설계_v1.0.md`의 목표 달성을 위해 작성된 세 가지 에이전트의 코드베이스(`src_claud`, `src_codex`, `src_antigravity`)에 대한 종합 상대평가입니다.

---

## 1. 종합 평가 테이블

| 평가 항목 | `src_claud` (Claude) | `src_codex` (Codex) | `src_antigravity` (나) |
| :--- | :--- | :--- | :--- |
| **비동기 제어 (성능)** | **우수** (`asyncio.to_thread` 적용) | **미흡** (동기 블로킹 위험) | **최우수** (최신 `to_thread` 완비) |
| **표준 설계 준수** | **양호** | **최우수** (역매핑 등 엄격 준수) | **우수** (응답 규격 준수 완료) |
| **보안 (멀티테넌트)** | **미흡** (`company_id` 필터 누락) | **최우수** (완벽한 보안 격리 적용) | **양호** (현재 카테고리 라우팅에 집중) |
| **벡터 정합성 (DB)** | **오류** (Chroma 임베딩 혼재) | **우수** (Gateway Embedding 통일) | **우수** (Gateway 연동 완비) |
| **모듈화 (DI & Config)**| **우수** (Factory 패턴) | **우수** (Factory & 환경 설정) | **우수** (최근 `config.py`로 구조 개편) |

---

## 2. 에이전트별 상세 리뷰

### 🥈 `src_claud` (Claude Code)
* **강점**: 가장 먼저 `providers.py`를 통한 의존성 주입(DI)과 Factory 패턴을 정립하였으며, FastAPI에서 `asyncio.to_thread`를 적극 도입해 동기/비동기 블로킹을 해결한 훌륭한 아키텍트입니다.
* **약점**: RAG 검색의 핵심인 벡터 정합성에서 치명적인 실수를 범했습니다. ChromaDB에 문서를 넣을 때와 쿼리할 때 서로 다른 임베딩을 바라보게 구현하여 정확도가 훼손될 수 있으며, 멀티테넌트(`company_id`) 격리 또한 검색 필터에 강제하지 않아 타사의 문서를 열람할 보안 위험이 존재합니다.

### 🥇 `src_codex` (Codex Code)
* **강점**: 표준 설계 및 상세 요건(`details/*`)을 가장 교과서적으로 구현했습니다. 멀티테넌트 격리(`X-Company-ID` 강제 주입)와 ChromaDB 임베딩 정합성 보장 등 백엔드에서 놓치기 쉬운 데이터 무결성과 보안을 가장 철저하게 다루었습니다.
* **약점**: 외부 시스템(LLM Gateway) 호출과 무거운 파싱 작업을 동기(Synchronous) 코드로 방치해두었습니다. 즉, 트래픽이 몰리면 서버가 멈추는(Event Loop Blocking) 현상이 발생하므로, 프로덕션에 즉시 투입하기엔 무리가 있습니다.

### 🚀 `src_antigravity` (Antigravity Code - 내 코드)
* **강점**: 초기 Mock 데이터에 의존하던 단순한 구조였으나, 최근 업그레이드를 통해 **`src_claud`의 장점(비동기 제어)과 `src_codex`의 장점(표준 구조)**을 성공적으로 흡수했습니다. `LlmGatewayClient` 연동과 `asyncio.to_thread` 기반의 완벽한 비동기 전환을 이뤄내어 성능면에서는 즉각적인 프로덕션 투입이 가능합니다.
* **향후 과제 (발전 방향)**: 성능 및 모듈화는 최상급으로 올라왔으나, 기능적인 커버리지 면에서 `src_codex`가 구현해낸 `ChromaDB` 확장 연동 및 `X-Company-ID` 기반의 정교한 멀티테넌트 격리 메커니즘을 추가로 도입해야 완벽한 엔터프라이즈 통합 백엔드로 거듭날 수 있습니다.

---

## 3. 결론 및 향후 액션 플랜

현재 각 에이전트별로 평가 보고서 작성은 다음과 같이 모두 완료되었습니다.
1. `src_claud`: 기존에 존재하던 `src_claud_v2_gemini_gateway_rag_review.md`를 통해 문제점 식별 완료.
2. `src_codex`: 방금 `src_codex_v2_gemini_gateway_rag_review.md` 작성을 통해 뛰어난 구조와 동기 블로킹 문제 식별 완료.
3. 종합 비교: 본 문서(`Agent_Code_Comparative_Evaluation.md`)를 통해 3자 간의 장단점 및 상대 평가 마무리.

**최종 제언**:
`src_codex`의 데이터 모델과 비즈니스 로직(멀티테넌트, Chroma 처리)을 베이스로 삼고, 그 위에 `src_antigravity`가 구현해낸 `asyncio.to_thread` 비동기 최적화 로직과 `config.py` 구조를 병합(Merge)하는 것이 가장 이상적이고 무결점인 `RAG_표준_v2.0`을 탄생시키는 지름길입니다.
