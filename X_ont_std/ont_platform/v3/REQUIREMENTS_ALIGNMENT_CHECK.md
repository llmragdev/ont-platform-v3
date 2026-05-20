# ont_platform v3 → 13_팔란티어_실무_설계원칙.md 요건 적용 점검

> 점검일: 2026-05-16  
> 점검 대상: ont_platform v3.0 소스코드 (backend + frontend)  
> 기준 문서: req_doc_hub/분석/13_팔란티어_실무_설계원칙.md

---

## 요약

| 요건 | 현황 | 등급 | 개선 필요 |
|---|---|---|---|
| 1. Materialize + Write-back | ❌ 미구현 | 🔴 Critical | 높음 |
| 2. 역방향 설계 (Action 중심) | ⚠️ 부분 | 🟠 High | 중간 |
| 3. LLM-Tool 통합 (AIP 방식) | ✅ 기본 구현됨 | 🟢 Good | 낮음 |
| 4. 비용·거버넌스 문서화 | ❌ 없음 | 🔴 Critical | 높음 |
| 5. 도메인 시나리오 확장 | ⚠️ AI바우처만 | 🟠 High | 중간 |
| 6. 도입 단계 로드맵 | ❌ 없음 | 🔴 Critical | 높음 |

**종합 점수: 42/100** — 기본 구조 O, 실무 요구사항 X

---

## 1. Materialize + Write-back 메커니즘

### 요구사항
```
논리 레이어 (온톨로지) → 물리화 (Materialize)
액션 수정 → 별도 스토리지 저장 → 원천 DB Write-back (선택적)
```

### 현 상태
```
✅ 논리 레이어: JSON 기반 entities, properties, relationships
❌ 물리화: 없음 (JSON 파일이 그대로 저장소)
❌ Write-back: 구현되지 않음 (검색 결과: 0개)
```

### 코드 증거
**`app/services/ontology.py`**:
```python
def upsert_entity(self, doc_id: str, entity: Dict, ctx: TenantContext) -> Dict:
    data = self.repo.load_document(doc_id, ctx)  # JSON 로드
    existing = {e["id"]: i for i, e in enumerate(data["entities"])}
    entity.setdefault("created_at", now)
    # ... 수정 후 저장하지만, 원천 DB(ERP 등)에 반영 안 함
```

### 설계 오류의 영향
```
현재: 팔란티어 화면에서 "계획 수정" → JSON 파일만 변경
문제: ERP, SAP 등 원천 시스템 미동기
      → "팔란티어는 정확한데 ERP는 구 데이터" 혼선 발생
```

### 개선 필요사항
- [ ] Materialize 대상 명시 (어떤 entities를 물리화할 것인가)
- [ ] Write-back 메커니즘 설계 (액션 → 원천 DB 반영 구조)
- [ ] 변경 이력 저장소 별도 구성 (변경 타임라인 추적)

**등급: 🔴 Critical** — 실제 운영 환경에서 데이터 불일치 발생 위험

---

## 2. 역방향 설계 (Action 중심)

### 요구사항
```
순서: Action 식별 → 대상 객체 → 필요 속성 → 데이터 소스
현재: 데이터 → 테이블 → 속성 정의
```

### 현 상태

**`app/models/query_intent.py` ActionType enum**:
```python
class ActionType(str, Enum):
    FILTER = "FILTER"        # 쿼리 액션
    SEARCH = "SEARCH"        # 쿼리 액션
    COMPARE = "COMPARE"      # 쿼리 액션
    CALCULATE = "CALCULATE"  # 쿼리 액션
```

❌ **비즈니스 액션 전혀 없음:**
- 승인 (Approve)
- 반려 (Reject)
- 상태 변경 (ChangeStatus)
- 발주 요청 (RequestProcurement)
- 알림 (Notify)

❌ **온톨로지 설계가 데이터 중심:**
```json
{
  "type": "PROGRAM",
  "name": "AI바우처 2025",
  "properties": {"budget": "276억원", "year": 2025}
}
```
→ "budget을 조회"하는 설계
→ "budget 변경을 승인"하는 설계 아님

### 설계 오류의 영향
```
데이터를 조회만 할 뿐, 실행 불가
팔란티어의 차별점 (워크플로우 자동화)이 전혀 발현 안 됨
= 비싼 Snowflake처럼 쓰는 중
```

### 개선 필요사항
- [ ] 비즈니스 액션 정의 (AI바우처: 과제 승인, 예산 변경 등)
- [ ] 액션별 상태 전이 규칙 정의
- [ ] 액션 실행 권한 설계 (누가 뭘 할 수 있는가)
- [ ] 13_팔란티어_실무_설계원칙.md의 "역방향 설계" 섹션 참고 후 재설계

**등급: 🟠 High** — 아키텍처 전체에 영향

---

## 3. LLM–온톨로지 Tool 통합 (AIP 방식)

### 요구사항
```
사용자 질문
  → LLM 의도 분류
  → Tool 호출: 온톨로지 쿼리
  → 실시간 데이터 기반 답변 + Action 제시
```

### 현 상태
```
✅ LLM 의도 분류: query_planner._llm_classify() 있음
✅ 온톨로지 쿼리: find_by_name, filter_by_property 있음
✅ 하이브리드 합성: HybridSynthesizer.synthesize() 있음
⚠️ Action 제시: 결과는 출력하되, 액션 버튼/실행 없음
```

### 코드 증거
**`app/services/query_planner.py`**:
```python
def ask(self, query: str, ctx: TenantContext) -> QueryResponse:
    plan = self.classify_intent(query, ctx)  # ✅ 분류
    # ... ONTOLOGY/VECTOR 스텝 실행
    response = self.synthesizer.synthesize(...)  # ✅ 합성
    return response  # 답변만 반환, 액션 없음
```

**`app/api/integration_test.py`**:
```python
response = svc.ask_forced_hybrid(case["question"], ctx)
# 응답에 actual_answer만 있고, available_actions가 없음
```

### 현재 수준
- Phase 1: 데이터 조회 ✅
- Phase 2: 조회 + LLM 합성 ✅
- Phase 3: 합성 + Action 실행 ❌

### 개선 필요사항
- [ ] QueryResponse에 `available_actions` 필드 추가
- [ ] Frontend에서 액션 버튼 렌더링
- [ ] 액션 클릭 시 workflow engine 실행

**등급: 🟢 Good** — 기본은 됨, 확장만 필요

---

## 4. 비용 구조 + 관리 부채 (거버넌스)

### 요구사항
```
- Materialize 비용 명시
- 파이프라인 실행 비용 계획
- 네이밍 컨벤션 강제
- 의존 관계 문서화
```

### 현 상태
```
❌ 문서화 전혀 없음
❌ 네이밍 컨벤션 없음
❌ 의존 관계 추적 방법 없음
```

### 파일 구조 (현황)
```
storage/demo-co/proj-01/ontology/
  ├── domain_schema.json
  ├── ai-voucher-2025.json
  └── (향후 추가될 예시들 — 정렬 없음)

test_data/
  ├── ai-voucher-2025/
  │   └── qa_dataset.json
  └── (다른 도메인 없음)
```

### 설계 오류의 영향
```
6개월 후 현황:
- "이 entities가 어디서 쓰이는가?" 파악 불가
- 스키마 변경 시 영향 범위 파악 어려움
- 기술 부채 급증
```

### 개선 필요사항
- [ ] `ARCHITECTURE.md` 작성: 저장 구조, Materialize 계획
- [ ] `NAMING_CONVENTION.md`: [도메인]_[객체타입]_v[버전] 패턴
- [ ] `COST_PLANNING.md`: Materialize 대상, 동기화 주기, 예상 비용
- [ ] `DEPENDENCY_MAP.md`: entities → features → screens 연결 문서

**등급: 🔴 Critical** — 장기 운영 관점에서 필수

---

## 5. 도메인 시나리오 확장

### 요구사항
```
다중 도메인 지원 가능한 아키텍처
조선·제조 등 구체적 시나리오 예시
```

### 현 상태
```
✅ 멀티테넌트 아키텍처: company_id, project_id 있음
✅ 멀티 스키마: domain_schema.json (PROGRAM, ORGANIZATION 등)
❌ 도메인 예시: AI바우처 2025만 있음
```

### 현재 데이터
```
✅ entities: 22개 (PROGRAM 2, ORGANIZATION 9, CATEGORY 4, METRIC 4, EVENT 3)
❌ 다른 도메인 없음 (조선, 제조, 구매 등)
```

### 개선 필요사항
- [ ] 조선 도메인 온톨로지 추가 (Ship ↔ Block ↔ Material ↔ Worker)
- [ ] 제조/공정 도메인 예시
- [ ] 구매/발주 도메인 예시

**등급: 🟠 High** — 교육·데모 시 설득력 향상

---

## 6. 도입 단계 로드맵

### 요구사항
```
Phase 1: 데이터 연결
Phase 2: 온톨로지 모델링
Phase 3: 워크플로우 + AIP (ROI 구간)

각 단계의 명확한 정의와 체크포인트
```

### 현 상태
```
❌ 문서 없음
❌ 단계별 요구사항 명시 안 됨
```

### 현재 프로젝트 위치
```
Phase 1.5: 데이터 연결 + 기본 온톨로지 ✅
Phase 2.5: 온톨로지 쿼리 + RAG ✅
Phase 3.0: 워크플로우 + Action 실행 ❌ (Action 정의 없음)
```

### 개선 필요사항
- [ ] `ROADMAP.md` 작성
- [ ] Phase별 체크리스트 (자신감 있게 진행)
- [ ] 현중(현대중공업) 사례 반영: "1/3 → 3/3 로드맵"

**등급: 🔴 Critical** — 다음 단계 추진 방향 불명확

---

## 우선순위 개선 계획

### 즉시 (1주일)
1. `ARCHITECTURE.md` 작성 (Materialize 계획 포함)
2. `NAMING_CONVENTION.md` 작성
3. `ROADMAP.md` 작성

### 단기 (2~3주)
1. 비즈니스 액션 정의 (AI바우처 도메인 기준)
2. ActionType enum 확장 (Approve, Reject, ChangeStatus 등)
3. Workflow 엔진 통합 (기존 04_워크플로우_핸즈온.md 코드 활용)

### 중기 (1개월)
1. Write-back 메커니즘 설계 및 구현
2. 조선 도메인 온톨로지 추가 (다중 도메인 증명)
3. Frontend에 Action 버튼 렌더링

---

## 결론

**현 상태:**
- ✅ 온톨로지 기본 구조와 RAG 하이브리드 쿼리는 잘 구현됨
- ❌ 13번 문서의 핵심 요구사항 (Materialize, Write-back, Action, 거버넌스) 미흡

**개선 방향:**
- 13번 문서의 "역방향 설계" 방법론을 따라 Action 중심으로 재설계
- 문서화 3종 세트 (Architecture, Convention, Roadmap) 작성
- 비즈니스 액션 구현으로 "실행형 AI" 역할 확보

**기대 효과:**
- 현중 같은 기업에 제안할 때 "왜 팔란티어인가"를 명확하게 설명 가능
- 강의/PoC 진행 시 설득력 향상
