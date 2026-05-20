# 06. 하이브리드 질의 실행 계획 명세 (Hybrid Query Plan Spec)

## 1. Pydantic 모델 기반 엄격한 정의

LLM의 출력을 다음의 Pydantic 스키마로 강제 파싱하여 런타임 오류를 방지합니다.

### 1.1 온톨로지 연산 모델 (OntologyAction)
```python
class FilterOperator(str, Enum):
    EQ = "=="
    GT = ">"
    LT = "<"
    CONTAINS = "contains"

class OntologyFilter(BaseModel):
    prop: str
    op: FilterOperator
    val: Any

class OntologyAggregateParams(BaseModel):
    type: str
    function: Literal["sum", "avg", "count"]
    field: str
    filters: list[OntologyFilter] = []
```

### 1.2 벡터 검색 모델 (VectorAction)
```python
class VectorSearchParams(BaseModel):
    query: str
    top_k: int = 5
    doc_ids: list[str] = []
```

---

## 2. 플랜 유효성 검증 (Plan Validator)

계획 실행 전, 시스템은 다음 항목을 자동으로 검토합니다.
1. **Schema Check**: 요청된 `type`과 `field`가 현재 온톨로지 스키마에 존재하는가?
2. **Scope Check**: `doc_ids`가 현재 사용자의 테넌트/프로젝트 소속인가?
3. **Logic Check**: `AGGREGATE` 시 대상 필드가 숫자 타입인가?

---

## 3. 실행 및 합성 결과 구조

최종 답변 생성 시 LLM에게 전달되는 컨텍스트는 다음과 같습니다.
```json
{
  "plan_executed": true,
  "ontology_results": [...],
  "vector_results": [...],
  "reasoning_trace": {
    "steps": ["EQUIPMENT 필터링 완료 (3건)", "관련 MANUAL 검색 완료"]
  }
}
```
