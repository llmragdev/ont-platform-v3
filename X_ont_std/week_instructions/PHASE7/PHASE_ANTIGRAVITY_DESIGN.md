# PHASE_ANTIGRAVITY: ont_platform v5 옵션 기반 멀티라우팅 RAG 설계서

**작성일**: 2026-06-07  
**작성자**: Antigravity (RAG 아키텍처 담당 에이전트)  
**상태**: 설계 승인 대기 (일단 설계만 진행)  
**대상 시스템**: `ont_platform v5` (업그레이드 버전)

---

## 📌 1. 설계 배경 및 목표

기존 `ont_platform v4`까지는 사용자의 질문이 인입되면 내부 의도 분류기(Heuristic/LLM Classifier)가 결정하는 의도(intent)에만 의존하여 강제로 단일 실행 경로를 거쳤습니다. 

`v5`에서는 사용자가 직접 검색 방식(온톨로지 전용, 벡터 유사도 전용, 하이브리드 자동 등)을 선택할 수 있는 **옵션 기반 멀티라우팅 검색 파이프라인**을 제공하고, 서빙 시스템을 `ont_platform/v5/`로 업그레이드합니다.

### 🎯 주요 아키텍처 목표
1. **서빙 옵션 추가 (`search_mode`)**: API 요청 시 검색 기법을 명시할 수 있도록 파라미터화.
2. **v5 독립 구조화**: `ont_platform/v5` 독립 디렉토리 하에서 다중 라우팅 모듈화 진행.
3. **EvidenceGate v5 통합**: 각 검색 모드별로 적합한 `EvidenceGate` 제약 조건 결합.

---

## 🏗️ 2. v5 디렉토리 구조 설계

v5 코드는 기존 v4의 안정적인 지식 그래프 파싱 및 벡터 빌더 인프라를 계승하고, `services` 및 `api` 레이어에 옵션 기반 라우터 기능을 이식합니다.

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  │  ├─ hybrid.py            ← [MODIFY] v5 검색 옵션 필드 반영 및 라우팅
│  │  │  └─ ...
│  │  ├─ models/
│  │  │  ├─ query_intent.py      ← [MODIFY] SearchMode Enum 및 v5 Request 스키마 추가
│  │  │  └─ ...
│  │  └─ services/
│  │     ├─ query_planner.py     ← [MODIFY] 지정 옵션에 따른 QueryPlan 강제 바이패스
│  │     ├─ evidence_gate.py     ← [MODIFY] 검색 모드별 제약 조건 차별화
│  │     └─ ...
```

---

## ⚙️ 3. API 요청 및 모델 정의 (v5 Schema)

### 3.1 SearchMode Enum 추가
```python
from enum import Enum

class SearchMode(str, Enum):
    AUTO = "auto"                     # 기존 의도 분류기 기반 자동 라우팅
    ONTOLOGY_ONLY = "ontology_only"   # 온톨로지 지식 그래프 및 SPARQL만 조회
    VECTOR_ONLY = "vector_only"       # Chroma DB 벡터 검색만 조회
    HYBRID = "hybrid"                 # 온톨로지 + 벡터 두 경로 모두 실행 후 LLM 합성
```

### 3.2 v5 AskRequest 모델 확장
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AskRequestV5(BaseModel):
    question: str = Field(..., description="사용자 질문")
    search_mode: SearchMode = Field(default=SearchMode.AUTO, description="검색 라우팅 모드")
    doc_ids: Optional[List[str]] = Field(default=None, description="특정 문서 필터링 목록")
    override: Optional[Dict[str, Any]] = None
```

---

## 🔄 4. 옵션 기반 멀티라우팅 파이프라인 (Routing Core)

쿼리 플래너(`QueryPlannerService`)의 의도 분류 및 실행 스텝 빌드 부분에 `search_mode` 필터를 적용합니다.

```
                  [API Request: AskRequestV5]
                              │
                              ▼
                [QueryPlannerService.ask_v5()]
                              │
          ┌───────────────────┼───────────────────┐
          ▼ (ontology_only)   ▼ (vector_only)     ▼ (hybrid / auto)
    [SPARQL Engine]     [Vector Engine]    [Classify Intent]
     · Graph Query       · Vector Search    · Heuristic / LLM
          │                   │                   │
          │                   │                   ▼
          │                   │            [Execute Both]
          └───────────────────┼───────────────────┘
                              │
                              ▼
                [EvidenceGate.check_evidence()]
                              │
                              ▼
                 [Grounded Synthesizer]
```

### 4.1 `QueryPlannerService` 멀티라우팅 구현 설계
```python
class QueryPlannerServiceV5(QueryPlannerService):
    def ask_v5(self, request: AskRequestV5, ctx: TenantContext) -> QueryResponse:
        query = request.question
        mode = request.search_mode
        
        # 1. 검색 모드에 따른 쿼리 계획(QueryPlan) 강제 재빌드
        if mode == SearchMode.ONTOLOGY_ONLY:
            plan = self._build_ontology_only_plan(query, ctx)
        elif mode == SearchMode.VECTOR_ONLY:
            plan = self._build_vector_only_plan(query, ctx)
        elif mode == SearchMode.HYBRID:
            plan = self._build_forced_hybrid_plan(query, ctx)
        else: # AUTO
            plan = self.classify_intent(query, ctx)
            
        # 2. 쿼리 계획 단계 실행
        ontology_results = []
        vector_results = []
        trace = [f"v5_router: search_mode={mode.value}"]
        
        for step in plan.steps:
            if step.engine == EngineType.ONTOLOGY:
                res = self.ontology_engine.execute(step, ctx, query)
                ontology_results.append(res)
            elif step.engine == EngineType.VECTOR:
                # Top_k는 옵션에 따라 조율 가능
                res = self.vector_svc.search(query, ctx, k=5)
                vector_results.extend(res)
                
        # 3. EvidenceGate v5 평가
        gate_res = self.evidence_gate.check_evidence(query, ontology_results, vector_results)
        
        # 4. 차단 검증 및 합성 분기
        if not gate_res["answer_allowed"]:
            return self._build_gate_response(query, plan, ontology_results, vector_results, gate_res, trace)
            
        return self.synthesizer.synthesize(query, plan, ontology_results, vector_results, trace)
```

---

## 🛡️ 5. EvidenceGate v5 제약 설계

검색 모드에 따라 제약 조건의 규칙이 유연하게 달라집니다.

* **ONTOLOGY_ONLY 모드**:
  - 벡터 검색 스코어를 검증하지 않습니다.
  - 온톨로지 결과 노드가 0개인 경우에만 `no_evidence` 제약 조건을 트리거하여 차단합니다.
* **VECTOR_ONLY 모드**:
  - 온톨로지 결과를 검증하지 않습니다.
  - 벡터 유사도 거리의 최솟값이 threshold(1.2)를 초과하거나 비어 있는 경우 `low_relevance` / `no_evidence`를 트리거합니다.
* **HYBRID / AUTO 모드**:
  - 두 경로 중 하나라도 확실한(Confidence가 높은) 근거가 있으면 통과시킵니다.
  - 질문 카테고리가 `Snowflake`일 경우, 어느 모드든 `category_mismatch`로 **즉시 강제 거절** 처리합니다.

---

## 📈 6. 수용 검증 기준 (Acceptance Criteria)

1. **라우팅 무결성**:
   - `search_mode = ontology_only` 시, 벡터 검색 API 또는 임베딩 질의 시간이 0ms이어야 함 (로그 상 `VECTOR` 스텝 생략 검증).
   - `search_mode = vector_only` 시, SPARQL 질의 및 지식 그래프 매핑 절차가 생략되어야 함 (로그 상 `ONTOLOGY` 스텝 생략 검증).
2. **안전장치 일관성**:
   - 모든 모드에서 Snowflake 질문 인입 시 `"해당 카테고리 문서와 관련이 없습니다"`가 정상 출력되는지 검증.
3. **성능 요건**:
   - `vector_only` 및 `ontology_only` 선택 시, 하이브리드 탐색 오버헤드가 제거되어 질의 응답 시간이 v4 대비 **최대 40% 단축**되어야 함.
