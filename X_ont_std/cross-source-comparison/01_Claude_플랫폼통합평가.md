# 3개 플랫폼 아키텍처 통합 평가

> 평가일: 2026-05-16  
> 평가자: Claude Haiku  
> 대상: ont_platform v3 vs antigravity_platform vs Codex-통합 v3

---

## 1. 3개 플랫폼 개요

| 항목 | **ont_platform/v3** | **antigravity_platform** | **Codex-통합/v3** |
|------|------------------|------------|---------|
| **상태** | ✅ 개발 완료 | 🔄 설계 단계 | 📋 설계 완료 |
| **핵심** | 하이브리드 온톨로지 | 범용 엔진 아키텍처 | Palantir 실무 원칙 |
| **기술 스택** | FastAPI + JSON + Gemini | FastAPI + Mermaid 다이어그램 | FastAPI + Materialize/Write-back |
| **구현 수준** | 통합 테스트 단계 | 도면 단계 | 설계 원칙 정의 |
| **배포 준비** | Phase 2 (80% 목표) | Phase 0 (미시작) | Phase 3 예정 |

---

## 2. 아키텍처 비교

### 2.1 ont_platform/v3 — 하이브리드 온톨로지 플랫폼

**계층 구조:**
```
사용자 요청
    ↓
[QueryPlanner] — LLM 의도 분류
    ↓
┌─────────────────────────────────┐
│ ONTOLOGY 검색 ↔ VECTOR 검색 (병렬) │
└─────────────────────────────────┘
    ↓
[HybridSynthesizer] — LLM 답변 합성
    ↓
응답 (sources + evidence + trace)
```

**특징:**
- LLM 기반 의도 분류 (FILTER/DESCRIPTIVE/HYBRID)
- 온톨로지와 벡터의 병렬 실행
- 결과 합성 및 감시 추적(trace)
- Tenant 격리 (company_id, project_id)
- Repository 패턴으로 데이터 접근 추상화

**구현 현황:**
- ✅ 의도 분류 (완료)
- ✅ ONTOLOGY/VECTOR 검색 (완료)
- ✅ 합성 및 합성 (완료)
- 🔄 통합 테스트 (1/25 진행 중)

**파일 구조:**
```
src/backend/
  ├── app/
  │   ├── models/      # 데이터 모델 (query_intent, ontology, tenant_context)
  │   ├── services/    # 핵심 로직 (ontology, query_planner, hybrid_synthesizer)
  │   ├── repositories/# 데이터 접근 (ontology repository)
  │   └── api/         # REST API (integration_test, hybrid)
  └── storage/         # 파일 기반 저장소
```

**장점:**
✓ 명확한 계층화 및 관심사 분리  
✓ 실제 작동하는 구현  
✓ 감시 추적 및 감사 로그 내장  
✓ 의도 분류로 비용 최적화  

**단점:**
✗ Materialize/Write-back 미구현  
✗ 온톨로지 데이터 품질 의존  
✗ LLM API 할당량 제한  

---

### 2.2 antigravity_platform — 범용 엔진 아키텍처

**3단계 레이어 구조:**
```
┌──────────────────────────────────────┐
│ Presentation Layer (UI)              │
│ - Next.js App Router                 │
│ - React Flow Graph View              │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Intelligence Layer (Query Processing)│
│ - Hybrid Query Planner               │
│ - Response Synthesizer               │
│ - Reliability Guardrail              │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Core Engine Layer                    │
│ - Vector Search Engine               │
│ - Generic Ontology Engine            │
│ - Workflow Graph Engine              │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Infrastructure & Security            │
│ - Tenant-Aware Auth Middleware       │
│ - Audit & Observability Service      │
│ - Project/Tenant Isolated Filesystem │
└──────────────────────────────────────┘
```

**특징:**
- Tenant-Aware Middleware (Context 강제)
- Repository Pattern (테넌트 필터 자동 주입)
- Generic Schema Engine (JSON-Driven UI)
- Hybrid Query (BM25 + 벡터 + RRF)
- 감시 추적 자동화
- 민감 정보 자동 암호화

**설계 원칙:**
1. **데이터 격리** — Tenant 단위 강제 분리
2. **범용 엔진** — 어떤 온톨로지도 수용 가능
3. **지능형 질의** — 실행 계획 기반
4. **Server-Driven UI** — 백엔드 스키마 정의가 UI 결정

**파일 구조 (설계):**
```
app/
  ├── api/
  │   ├── dependencies.py      # Tenant context resolver
  │   ├── documents.py
  │   └── rag.py
  ├── core/
  │   ├── errors.py
  │   ├── auth_context.py
  │   └── time.py
  ├── db/
  │   ├── session.py
  │   └── migrations/
  ├── models/
  │   ├── db_models.py
  │   └── schemas.py
  ├── repositories/
  │   ├── company_repository.py
  │   ├── document_repository.py
  │   └── dialog_repository.py
  └── services/
      ├── document_pipeline.py
      ├── rag_service.py
      ├── tenant_scope.py
      └── vector_adapters.py
```

**장점:**
✓ Tenant 격리 철저 (context 강제)  
✓ 범용성 높음 (어떤 도메인도 수용)  
✓ 웹 프론트엔드 내장 (Next.js)  
✓ Guardrail로 신뢰성 보장  
✓ 감시 추적 자동화  

**단점:**
✗ 아직 설계 단계 (구현 미시작)  
✗ 복잡도 높음 (많은 모듈)  
✗ Next.js 의존 → 배포 복잡성 증가  

---

### 2.3 Codex-통합/v3 — Palantir 실무 설계 원칙

**Action-Driven Modeling:**
```
비즈니스 액션 정의 (사용자 승인 필요)
    ↓
역방향으로 필요한 엔티티/속성 도출
    ↓
온톨로지 설계 (이미 존재하는 데이터 X)
    ↓
Materialize — 논리 → 물리 데이터셋
    ↓
Write-back — 액션 결과 → 원천 DB 동기화
```

**핵심 개념:**

1. **Materialize** (논리 → 물리)
   ```
   온톨로지 정의 (논리 레이어)
      ↓ (변환 규칙)
   물리 데이터셋 (JSON/CSV)
      ↓ (스냅샷 관리)
   시계열 버전 관리
   ```

2. **Write-back** (액션 결과 동기화)
   ```
   사용자 액션 (예: "바우처 할당")
      ↓ (검증 + 승인)
   원천 DB 업데이트 (Oracle/SAP)
      ↓ (감시 로그)
   감사 추적 기록
   ```

3. **Ontology Provenance**
   ```json
   {
     "entity": "AI바우처 2025",
     "source": "정책문서 p.5",
     "confidence": 0.95,
     "status": "Approved",
     "cost_allocated": {"llm_calls": 3, "tokens": 450}
   }
   ```

4. **Governance**
   - 도메인별 폴더 표준화
   - 네이밍 컨벤션: `[부서]_[주제]_[버전]`
   - 비용 추적 (LLM 호출, Token 단위)
   - 권한 관리 (승인/반려)

**주요 특징:**
- 비즈니스로부터 역방향 시작 (기술 주도 X)
- 데이터 신선도 보장 (Materialize)
- 액션 추적 및 검증 (Write-back)
- 비용 거버넌스 (Token 계산)
- 감사 추적 (Provenance)

**적용 대상:**
- 조선 도메인: 선박 건조 → Materialize + Write-back
- 제조 도메인: 품질 관리 → 역방향 설계
- 구매 도메인: 발주 → LLM-Tool 통합
- 에이버 도메인: 바우처 할당 → 액션 기반

**장점:**
✓ 실무 경험 기반  
✓ 액션 주도 설계 (비용 통제)  
✓ 데이터 신선도 관리  
✓ 비용 추적 및 거버넌스  
✓ 감시 추적 자동화  

**단점:**
✗ 구현 복잡도 높음 (Materialize/Write-back)  
✗ 온톨로지 설계 재학습 필요  
✗ 초기 모델링 오버헤드  

---

## 3. 기술 비교

### 3.1 질의 처리 흐름

| 단계 | **ont_platform/v3** | **antigravity** | **Codex-통합** |
|------|------------------|-----------|----------|
| 입력 분석 | LLM 의도 분류 | LLM Strategy 결정 | 액션 정의 (사용자) |
| 검색 전략 | 의도별 최적화 | Hybrid (BM25+벡터) | Materialize 참조 |
| 컨텍스트 | Trace + Audit | Guardrail 검증 | Provenance + 비용 |
| 결과 처리 | HybridSynthesizer | Response Synthesizer | Write-back 검증 |

### 3.2 데이터 모델

**ont_platform/v3:**
```python
entity = {
    "id": "E001",
    "type": "PROGRAM",
    "name": "AI바우처 2025",
    "properties": {"budget": "276억원", "year": 2025},
    "created_at": "...", "version": 1, "status": "active"
}
```

**antigravity_platform:**
```python
# JSON-Driven UI (스키마가 UI 결정)
ontology_schema = {
    "entity_types": [
        {
            "name": "PROGRAM",
            "properties": [
                {"name": "budget", "type": "string", "ui_type": "text"},
                {"name": "year", "type": "integer", "ui_type": "number"}
            ]
        }
    ]
}
```

**Codex-통합:**
```python
entity_with_provenance = {
    "id": "E001",
    "name": "AI바우처 2025",
    "source_document": "정책_2025_v1.0",
    "page": 5,
    "confidence": 0.95,
    "status": "Approved",  # Candidate/Approved
    "materialized_from": "POLICY_2025_v1",
    "actions_enabled": {"create": true, "update": true, "delete": false},
    "cost_allocated": {"llm_calls": 3, "tokens": 450}
}
```

### 3.3 저장소 및 배포

| 항목 | **ont_platform** | **antigravity** | **Codex-통합** |
|------|-----------------|-----------|----------|
| DB | JSON 파일 | JSON (설계) | JSON + Oracle/SAP |
| 저장 위치 | `storage/{company}/{project}/` | 파일 시스템 (테넌트 격리) | Materialize: JSON, 원천: RDBMS |
| 버전 관리 | version 필드 | 미정 | Provenance + 스냅샷 |
| 배포 방식 | FastAPI 독립 | FastAPI + Next.js | FastAPI + Workflow Engine |

---

## 4. 통합 전략

### 4.1 현재 상태

```
ont_platform/v3 (Phase 2)
└─ 통합 테스트 중 (1/25)
   └─ find_by_name 토큰 매칭 ✓
   └─ ask_forced_hybrid 메서드 추가 ✓
   └─ 온톨로지 데이터 검증 필요

antigravity_platform (Phase 0)
└─ 설계 단계
   └─ 범용성 추구
   └─ 웹 UI 내장

Codex-통합/v3 (설계 원칙)
└─ Phase 3 적용 예정
   └─ Materialize/Write-back
   └─ Action-Driven Modeling
```

### 4.2 권장 통합 로드맵

**Phase 2 (현재 — 6월 완료)**
- ont_platform/v3: 통합 테스트 20/25 달성
- 온톨로지 데이터 품질 검증
- find_by_name 알고리즘 최적화

**Phase 3 (6월 ~ 8월)**
- Codex-통합 원칙 도입
- Materialize 규칙 정의 (AI바우처 도메인)
- Write-back 워크플로우 프로토타입
- 비즈니스 액션 정의

**Phase 4 (8월 ~ 10월)**
- 다중 도메인 온톨로지 확장
- antigravity 범용 엔진 적용
- Server-Driven UI 도입

**Phase 5 (10월 이후)**
- 운영형 하드닝
- 성능 최적화
- 다중 채널 지원 (LLM Gateway 확장)

### 4.3 아키텍처 통합도

```
Final Architecture (Phase 5)
────────────────────────────
┌─ Presentation Layer (antigravity 설계)
│  └─ Next.js UI (Server-Driven)
│
├─ Intelligence Layer
│  ├─ Query Planner (ont_platform)
│  ├─ Action Router (Codex-통합)
│  └─ Response Synthesizer
│
├─ Core Engine Layer
│  ├─ Ontology Engine (ont_platform + Codex Provenance)
│  ├─ Vector Engine (RAG 표준)
│  └─ Workflow Engine (Write-back)
│
└─ Infrastructure (antigravity 설계)
   ├─ Tenant-Aware Middleware
   ├─ Audit & Observability
   └─ Materialize Pipeline (Codex-통합)
```

---

## 5. 각 플랫폼의 역할

### ont_platform/v3 — 핵심 쿼리 엔진
- LLM 기반 의도 분류
- ONTOLOGY/VECTOR 병렬 검색
- 하이브리드 결과 합성
- 감시 추적

### antigravity_platform — 범용 아키텍처 틀
- Tenant 격리 철저
- Context 강제 관리
- Server-Driven UI
- Guardrail (신뢰성)

### Codex-통합 — 거버넌스 및 액션
- Action-Driven 설계
- Materialize (논리 → 물리)
- Write-back (원천 DB 동기화)
- Provenance (출처 추적)
- 비용 거버넌스

---

## 6. 주요 의사결정 포인트

### Q1: 어느 플랫폼을 주축으로 삼을까?

**A: Codex-통합/v3를 기준 골격으로 삼고, ont_platform/v3를 질의/운영 계층으로 결합**
- ✓ Codex-통합/v3는 Palantir 실무 원칙(Materialize/Write-back/Governance)을 가장 직접적으로 반영
- ✓ ont_platform/v3는 하이브리드 질의, LLM 분류, metric API의 완성도가 높음
- ✓ antigravity_platform은 모듈형 API와 UI/UX 참고 소스로 선별 흡수 가능
- ✓ 최종 통합은 기준 골격과 기능 계층을 분리하는 방식이 안정적

### Q2: Materialize/Write-back을 언제 추가할까?

**A: Phase 3 (비즈니스 액션 정의 후)**
- AI바우처 도메인에서 구체적 액션 정의
- 데이터 신선도 보장 필요 시점
- Codex-통합/v3의 Workflow/Write-back 계층에 ont_platform 질의 결과를 연결

### Q3: Next.js UI를 도입할까?

**A: Phase 4 (전사 확대 시)**
- 현재: FastAPI 백엔드만으로 충분
- Phase 3까지: 내부 테스트 (단순 웹)
- Phase 4: Server-Driven UI 도입 (다중 도메인)

---

## 7. 결론

| 플랫폼 | 평가 | 역할 |
|-------|------|------|
| **Codex-통합/v3** | ⭐⭐⭐⭐⭐ | **기준 골격** — Palantir 실무 원칙 |
| **ont_platform/v3** | ⭐⭐⭐⭐⭐ | **질의/운영** — 하이브리드/LLM/메트릭 |
| **antigravity_platform** | ⭐⭐⭐⭐☆ | **UI/UX** — 모듈형 API/화면 경험 |

**핵심 성공 요소:**
1. **기준 골격 확정**: Codex-통합/v3를 Palantir 실무 원칙 기준으로 유지
2. **질의/운영 결합**: ont_platform/v3의 하이브리드/LLM/메트릭 계층 연결
3. **UI/UX 흡수**: antigravity_platform의 모듈형 API/화면 경험 선별 반영
4. **거버넌스 강화**: Provenance + Write-back + 비용 추적

---

**작성일:** 2026-05-16  
**다음 리뷰:** Phase 2 완료 (2026-06-01)
