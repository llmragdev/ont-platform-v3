# ont_platform v3 프로젝트 컨텍스트

> Claude Code가 이 폴더를 열 때마다 자동으로 읽는 파일입니다.
> **항상 이 파일을 먼저 읽고 작업을 시작하세요.**

---

## 🎯 프로젝트 정체성

**ont_platform v3** — 온톨로지 기반 통합 의사결정 시템

- 팔란티어(Foundry)의 경량화 특화 버전
- 조선/제조/건설 산업 타겟
- 핵심 기능: 데이터 → 의미(Ontology) → 영향도 분석 → **의사결정 → 액션 → 감사 추적**

---

## 🗂️ 폴더 구조

```
E:\ontology_edu\X_ont_std\
├── CLAUDE.md              ← 이 파일
├── requirements\          ← 요건 문서 (팔란티어 분석/추적도)
│   ├── 분석/
│   ├── 추적도/
│   ├── 교육자료/
│   └── 평가/
├── task_logs\             ← 작업 로그 (모든 세션의 기록)
│   └── claude/
│       ├── YYYYMMDD_HHMM_작업명.md
│       └── ...
├── cross-source-comparison\  ← 🔄 플랫폼 비교 분석 (향후 비교 시 활용)
│   ├── 01_Antigravity_통합 평가.md
│   ├── 01_Claude_플랫폼통합평가.md
│   ├── 01_Codex_통합 평가.md
│   └── (새로운 비교 분석 추가)
├── references\            ← 참고 자료 및 프로토타입
│   ├── old/               ← 이전 비교 검증 파일 (아카이브)
│   │   ├── claud에 대한 총평/     ← 2026-05-12~14 Claude 통합 검증
│   │   ├── src_codex/             ← 온톨로지 초기 프로토타입
│   │   ├── src_nextjs/            ← Next.js 초기 버전
│   │   └── src_sql/               ← DB 스키마 참고
│   ├── app.js, index.html, style.css  ← 웹 인터페이스 예제
│   └── README.md
└── ont_platform\
    ├── v1_legacy\         ← v1 원본 (policy, telemetry, workflow_graph_engine 참조용)
    ├── v2\                ← 구조화 버전
    └── v3\                ← 현재 개발 버전 (FastAPI + Next.js)
        ├── src/
        │   ├── backend/   ← FastAPI 백엔드 (포트 8001)
        │   ├── frontend/  ← Next.js 프론트엔드 (포트 3001)
        │   └── tests/integration/
        ├── ARCHITECTURE.md
        └── ROADMAP.md
```

---

## 🚦 현재 상태

**[→ STATUS.md 에서 최신 상태 확인](./STATUS.md)**

**요약**: 전체 완성도 ~42% (조회 기능 완성, 실행/액션 미완성)  
**현재 집중**: Phase 2 마무리 — 통합 테스트 목표 80% 달성

---

## 🔴 지금 당장 해야 할 것

### Phase 2 마무리 (마감: 2026-05-19)

**목표**: 통합 테스트 1/25 → **20/25** 달성

```bash
# 테스트 실행
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
pytest tests/integration/ -v --tb=short
```

**실패 원인 추정**:
- 온톨로지 데이터 매칭 최적화 미완
- 벡터 검색 성능 이슈

**작업 순서**:
1. 실패 케이스 목록 확인
2. 빠르게 고칠 수 있는 것 우선 처리
3. 20/25 달성 후 Phase 2 완료 선언

---

## ⚙️ 실행 명령

```bash
# 백엔드
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
uvicorn main:app --reload --port 8001

# 프론트엔드
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend
npm run dev
```

---

## 📍 핵심 파일 위치

```
v3 백엔드:      E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend\
v3 프론트:      E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend\
통합 테스트:    E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend\tests\integration\
아키텍처:       E:\ontology_edu\X_ont_std\ont_platform\v3\ARCHITECTURE.md
로드맵:         E:\ontology_edu\X_ont_std\ont_platform\v3\ROADMAP.md
상세 현황:      E:\ontology_edu\X_ont_std\task_logs\claude\20260519_종합현황_단계별계획.md
요건 문서:      E:\ontology_edu\X_ont_std\requirements\분석\, \추적도\
플랫폼 비교:    E:\ontology_edu\X_ont_std\cross-source-comparison\
```

---

## 🟡 Phase 3 (비즈니스 액션)

**기간**: 2026-05-27 ~ 2026-07-31 (10주)  
**상태**: 📋 계획 완료, 🔴 구현 시작 예정 (5월 27일)

### 📅 4주 단계별 계획

**[→ PHASE3_IMPLEMENTATION_PLAN.md 에서 상세 확인](./ont_platform/v3/PHASE3_IMPLEMENTATION_PLAN.md)**

#### Week 1 (05-27 ~ 05-31): ActionDefinition 모델 + 6개 액션
- [ ] ActionDefinition 모델 구현
- [ ] 6개 액션 코드 작성 (ApproveProject, RejectProject, ChangeDeadline, RequestMoreInfo, StartPayment, CompleteProject)
- [ ] 단위 테스트 30개 이상
- **목표**: 테스트 통과율 ≥ 90%

#### Week 2 (06-03 ~ 06-07): 권한 검증 + API 통합
- [ ] 조건부 권한 검증 완벽화 (금액별)
- [ ] API 엔드포인트 통합 테스트
- [ ] Swagger/OpenAPI 문서 작성
- **목표**: API 통합 테스트 ≥ 15개

#### Week 3 (06-10 ~ 06-14): Changelog + Write-back + Worker
- [ ] Changelog 저장소 구현 (JSONL)
- [ ] WriteBackQueue 모델 구현
- [ ] WriteBackWorker 백그라운드 구현 (재시도 로직 포함)
- [ ] SAP API Mock 구현
- **목표**: Write-back 성공률 ≥ 95%

#### Week 4 (06-17 ~ 06-21): Frontend + 최종 통합 테스트
- [ ] ActionButton 컴포넌트 구현 (React)
- [ ] QueryResult + 액션 버튼 통합
- [ ] Audit 대시보드 (액션 이력 조회)
- [ ] e2e 통합 테스트 15개 이상
- **목표**: 최종 통과율 ≥ 85%

#### Week 5-8 (06-24 ~ 07-21): 버그 수정 + PoC 준비
- [ ] 성능 최적화
- [ ] 버그 수정
- [ ] 고객 PoC 준비

### 📋 설계 문서

- **[PHASE3_ACTION_DEFINITION.md](./ont_platform/v3/PHASE3_ACTION_DEFINITION.md)** — 6개 액션 상세 정의
- **[PHASE3_STATE_MACHINE.md](./ont_platform/v3/PHASE3_STATE_MACHINE.md)** — 상태 기계 + Write-back
- **[PHASE3_IMPLEMENTATION_PLAN.md](./ont_platform/v3/PHASE3_IMPLEMENTATION_PLAN.md)** — ⭐ **Week별 상세 계획 + 산출물**

### 🎯 Success Criteria

```
Code:     6개 액션 모두 구현 + 테스트 통과
Testing:  단위(30+) + 통합(40+) + e2e(15+) 테스트
Quality:  코드 커버리지 ≥ 80%
Funcional: Write-back 성공률 ≥ 95%
Frontend: ActionButton + Audit 대시보드
```

---

## 🟢 6~7월 (Phase 3 완료)

- Write-back 동기화 (외부 시스템 반영)
- 프론트엔드 Action UI
- Decision Record System

---

## 🔗 참고 문서

- **팔란티어 분석**: 확장 제안, 회의록 정리 (E 드라이브)
- **RAG 표준**: 별도 워크스페이스 (rag_standards)에서 관리

---

## 📌 작업 규칙

- 작업 로그는 `E:\ontology_edu\AI_TASK_CONTROL\claude\YYYYMMDD_HHMM_작업명.md` 에 기록
- 이 파일은 세션 시작 시 상태 변화가 있으면 업데이트
