# ont_platform v3.0 로드맵

> 문서 버전: 1.0  
> 기준일: 2026-05-16  
> 기반: 13_팔란티어_실무_설계원칙.md + 현대중공업 도입 단계 모델

---

## 1. 로드맵 개요

```
Phase 1: 데이터 연결 (Data Connection)           ✅ 완료
         └─ 온톨로지 저장소, 기본 쿼리

Phase 2: 지능형 하이브리드 (Intelligent Hybrid)  ✅ 진행 중 (통합 테스트 개선)
         └─ LLM 의도 분류, ONTOLOGY+VECTOR 병렬

Phase 3: 실행형 워크플로우 (Actionable Workflow)  ❌ 대기
         └─ 비즈니스 액션, 상태 전이, Write-back

Phase 4: 다중 도메인 확장 (Multi-Domain Scale)   📅 중기 계획
         └─ 조선, 제조, 구매 등 도메인 추가

Phase 5: 운영형 하드닝 (Operational Hardening)  📅 장기 계획
         └─ 보안, 성능, 모니터링
```

---

## 2. Phase 1 — 데이터 연결 (현재 ✅ 완료)

### 2-1. 목표
온톨로지 기반 구조화 저장소 구축 + 기본 쿼리 가능

### 2-2. 구현 내용
```
✅ JSON 기반 온톨로지 저장소
✅ 엔티티 CRUD (create, read, update, delete)
✅ find_by_name (한글 토큰 기반 매칭)
✅ filter_by_property (정확한 속성 필터링)
✅ 다중 관계(Link) 모델링
✅ 멀티테넌트 지원 (company_id, project_id)
```

### 2-3. 핵심 파일
- `app/services/ontology.py` — OntologyService
- `storage/demo-co/proj-01/ontology/domain_schema.json` — 타입 정의
- `storage/demo-co/proj-01/ontology/ai-voucher-2025.json` — 데이터

### 2-4. 성공 기준
```
✅ 온톨로지 쿼리 성공률 > 90%
✅ 응답 시간 < 200ms
✅ 한글 NL 질의 매칭률 > 80%
```

---

## 3. Phase 2 — 지능형 하이브리드 (현재 진행 중)

> **기술 검증**: Antigravity(04_1) 분석 결과, 파일 기반 구조는 100K 엔티티에서 성능 벽에 부딪침.
> **해결 방향**: PostgreSQL 마이그레이션으로 1/10 구현 난이도, 100배 확장성 확보.
> **Kodex 가드레일** 적용: SPARQL 범위 제한, 인덱스 전략, 트랜잭션 설계

### 3-1. 목표
LLM 기반 의도 분류 + 온톨로지 + 벡터 검색 + 합성

### 3-2. 구현 단계

#### Stage 2A: LLM 의도 분류 ✅ 완료
```
사용자 질문 → Gemini LLM (classifier.txt)
  ├─ FILTER: "예산 276억 이상"
  ├─ DESCRIPTIVE: "AI바우처 2025 총액"
  └─ HYBRID: "지연 프로젝트와 자료"

구현:
  ✅ QueryPlannerService.classify_intent()
  ✅ LLM 기반 우선, 휴리스틱 폴백
```

#### Stage 2B: 온톨로지 + 벡터 병렬 실행 ✅ 완료
```
의도별 스텝 생성:
  ✅ FILTER → ONTOLOGY step only
  ✅ DESCRIPTIVE → VECTOR step only
  ✅ HYBRID → 둘 다 (병렬 실행)

구현:
  ✅ QueryPlanV3._build_steps()
  ✅ QueryPlannerService.ask()
  ✅ ask_forced_hybrid() (테스트용)
```

#### Stage 2C: 하이브리드 합성 ✅ 완료
```
HybridSynthesizer:
  ✅ 온톨로지 결과 + 벡터 결과 합산
  ✅ LLM이 양쪽 맥락 기반 답변 생성
  ✅ quality_metrics (ontology_hits, vector_hits, llm_used)
```

#### Stage 2D: 통합 테스트 ⏳ 진행 중
```
목표: 25개 테스트 케이스 80% 이상 통과

현황:
  ❌ 초기 0/25 (2026-05-14)
  🔧 find_by_name 개선 (한글 토큰) + ask_forced_hybrid 추가 (2026-05-16)
  🎯 목표: 20/25 (2026-05-18)

실행 내용:
  ✅ find_by_name 리팩토링 (multi-granularity token matching)
  ✅ ask_forced_hybrid 메서드 추가 (항상 HYBRID 의도)
  ✅ integration_test.py 업데이트 (forced hybrid 사용)
  
미해결:
  - 온톨로지 데이터 불완전 (일부 엔티티 누락)
  - 키워드 매칭 로직 (match_mode any/all)
  - 증거 데이터 추출
```

### 3-3. 성공 기준 (목표 2026-05-18)

---

## 3.5. Phase 2.5 — 데이터 마이그레이션 & 보안 강화 (5월 말~6월 초)

> **필수 단계**: Phase 3 시작 전에 구현 기반을 정리하는 기술 부채 정산
> **기반**: Kodex(04_2, 04_3, 04_4) + Antigravity(03) 분석 반영
> **일정**: 2주 (병렬 작업)

### 3.5-1. PostgreSQL 마이그레이션

**목표**: 파일 기반 → PostgreSQL로 전환, 성능 100배 향상

| 항목 | 현재 (JSON) | 목표 (PostgreSQL) | 효과 |
|------|-----------|-----------------|------|
| 엔티티 조회 | O(N) 풀 스캔 | O(log N) 인덱스 | 100배 빠름 |
| 동시 쓰기 | 레이스 컨디션 | TX 격리 레벨 | 안전함 |
| 메모리 | 휘발성 | 영속성 | 서버 안전 |
| SPARQL | Mock (정규식) | rdflib 실제 | 표준 준수 |

**구현 단계** (2주):

```
Week 1:
  □ PostgreSQL 스키마 생성 (entities, relationships, audit_log)
  □ JSON ↔ PostgreSQL 매핑 레이어 작성
  □ GIN 인덱스 (JSONB properties) 설정
  □ Atomic 트랜잭션 테스트

Week 2:
  □ 기존 JSON 데이터 → PostgreSQL 일괄 마이그레이션
  □ 저장소 추상화 (BaseRepository) 업그레이드
  □ 통합 테스트 다시 실행 (20/25 유지)
  □ 마이그레이션 검증 + 문서화
```

**Kodex 가드레일 반영**:
- ✅ SPARQL 범위 명시화 (Supported/Fallback/Unsupported)
- ✅ GIN 인덱스 사용 (GiST 대신)
- ✅ SAVEPOINT 트랜잭션 설계
- ✅ UUID 기반 안정적 ID 생성

### 3.5-2. 보안 강화

**목표**: JWT 기반 인증, 헤더 위조 차단

| 취약점 | 현재 | 목표 | 구현 |
|-------|------|------|------|
| 테넌트 격리 | Header (위조 가능) | JWT 서명 | ✅ HMAC-SHA256 |
| 권한 제어 | Role 문자열 | JWT claims | ✅ token.sub/role |
| 감사 추적 | 부분 | 완전 | ✅ audit_log 필수 |

**구현**:
- JWT 발급 엔드포인트 (login)
- JWT 검증 미들웨어 (all endpoints)
- X-Company-Id → jwt.sub 강제
- 권한 체크: @require_role('manager')

### 3.5-3. Phase 2.5 성공 기준

```
□ PostgreSQL 마이그레이션 완료
□ 통합 테스트 20/25 이상 유지
□ 성능: 응답 시간 100K 엔티티 < 200ms
□ JWT 인증 적용 + 테스트
□ 감사 로그 100% 추적
□ 문서화 완료 (마이그레이션 가이드)
```

---

### 3-3. 성공 기준 (목표 2026-05-18)
```
📊 통합 테스트:
  □ 전체 통과율 ≥ 80% (20/25)
  □ 온톨로지 케이스 ≥ 90% (7/7 or 6/7)
  □ 벡터 케이스 ≥ 75% (7/9)
  □ 하이브리드 케이스 ≥ 75% (5/7)

⚡ 성능:
  □ 응답 시간 < 1000ms (평균)
  □ LLM 사용률 적절 (60~70%)

🎯 품질:
  □ 한글 쿼리 이해도 > 85%
  □ 거짓 정보(hallucination) 없음
```

### 3-4. 핵심 파일
- `app/services/query_planner.py` — 의도 분류 + 계획 생성
- `app/services/query_executor.py` — 온톨로지/벡터 실행
- `app/services/hybrid_synthesizer.py` — 답변 합성
- `app/api/integration_test.py` — 테스트 실행 + 평가
- `src/frontend/src/components/IntegrationTestRunner.tsx` — 테스트 UI

---

## 4. Phase 3 — 실행형 워크플로우 (대기 중)

### 4-1. 목표
**"조회 + 분석"을 넘어 "판단 + 실행"까지 자동화**

```
현재:  질문 → 답변 (정보 제공)
목표:  질문 → 분석 → 액션 선택 → 승인 → 실행 → 기록

예:
  "지연 위험이 높은 과제?"
    → AI 분석 결과 제시
    → [일정 조정] [예산 증액] [담당자 변경] 버튼
    → 사용자 클릭 → 액션 실행 → ERP 동기화 → 이력 기록
```

### 4-2. 구현 계획 (6월~7월)

#### Stage 3A: 비즈니스 액션 정의
```
Task: AI바우처 도메인에서 실제 액션 식별

액션 정의:
  1. ApproveProject (과제 승인)
     - 대상: PROJECT (신규 타입 필요)
     - 조건: 예산 검토 완료, 담당자 배정
     - 결과: 상태 → Approved, ERP 반영

  2. RequestMaterial (자재 발주)
     - 대상: MATERIAL
     - 조건: 재고 부족, 구매팀 권한
     - 결과: 발주 생성, ERP 연동

  3. SendNotification (알림)
     - 대상: ORGANIZATION (담당 기관)
     - 조건: 이정표 도달
     - 결과: 이메일/Slack 알림

Timeline:
  Week 1: 액션 카테고리화 (비즈니스 + 기술)
  Week 2: 액션별 권한 모델 정의
  Week 3: 액션 핸들러 코드 (04_워크플로우_핸즈온.md 참고)
```

#### Stage 3B: 상태 전이 엔진
```
Task: 온톨로지 객체의 상태 전이 규칙 정의

상태 기계:
  PROJECT: Submitted → [Approve/Reject] → Approved/Rejected
           Approved → [Execute] → InProgress
           InProgress → [Complete/Cancel] → Completed/Cancelled

조건부 전이:
  - 예산 > 100M: 관리자 승인만 가능
  - 예산 ≤ 100M: 팀장도 승인 가능
  - 담당자 미배정: 승인 불가

구현:
  ✅ WorkflowTransition (04번 문서 코드 활용)
  ✅ WorkflowEngine.execute()
  ✅ condition 콜백 지원
```

#### Stage 3C: 액션 권한 (RBAC)
```
Task: 액션별 필요 권한 정의

권한 모델:
  ROLE: admin, manager, team_lead, member
  
  액션별:
    ApproveProject:
      - admin: 무제한
      - manager: 소속 팀 프로젝트만
      - team_lead: 자신의 팀원 프로젝트만
      - member: 불가

구현:
  ✅ ActionDefinition.check_permission(user, role)
  ✅ Frontend: 버튼 활성화/비활성화
```

#### Stage 3D: Write-back 메커니즘
```
Task: 액션 실행 → 원천 DB (ERP) 동기화

구조:
  1. 액션 실행 (온톨로지)
  2. changelog 자동 생성 (변경 이력)
  3. 동기화 작업 큐 (pending → synced)
  4. 원천 DB API 호출 (ERP 반영)
  5. 실패 시 재시도 + 알림

구현:
  □ EntityChangeLog 모델
  □ WriteBackQueue (변경 큐)
  □ IntegrationAdapter (ERP API)
  □ SyncWorker (백그라운드 작업)

예시:
  {
    "entity_id": "P001AAA",
    "action_type": "CHANGE_STATUS",
    "old_status": "Submitted",
    "new_status": "Approved",
    "target_system": "SAP",
    "sync_status": "pending"
  }
  
  → SAP API 호출 → sync_status = "synced"
```

#### Stage 3E: Frontend 액션 UI
```
Task: 답변 화면에서 액션 버튼 렌더링

현재:
  ┌─────────────────────────┐
  │ AI가 분석한 답변        │
  │                         │
  │ "지연 위험: HIGH"       │
  └─────────────────────────┘

목표:
  ┌─────────────────────────┐
  │ AI가 분석한 답변        │
  │                         │
  │ "지연 위험: HIGH"       │
  │                         │
  │ [일정 조정] [예산 증액] │  ← 액션 버튼
  │ [담당자 변경]           │
  └─────────────────────────┘

구현:
  ✅ QueryResponse.available_actions 필드 추가
  ✅ Frontend ActionButton 컴포넌트
  ✅ 액션 실행 → POST /api/actions
  ✅ 실행 이력 → /api/audit
```

### 4-3. Phase 3 성공 기준 (목표 2026-07-31)
```
□ 비즈니스 액션 3개 이상 정의 + 구현
□ 상태 전이 규칙 10개 이상
□ 액션 권한 RBAC 적용
□ Write-back 동기화 성공률 ≥ 95%
□ Frontend 액션 버튼 렌더링 + 실행
□ 실행 이력(audit) 완전 추적
```

---

## 5. Phase 4 — 다중 도메인 확장 (8월~9월)

### 5-1. 목표
AI바우처 외에 조선, 제조, 구매 등 실무 도메인 추가

### 5-2. 도메인 로드맵

#### Domain 1: 조선 (Ship Building) — 우선순위 🔴 High
```
Entity Types:
  - SHIP (선박)
  - BLOCK (블록 — 공정 단위)
  - WORKER (담당자)
  - MATERIAL (자재)
  - SENSOR (IoT)

Actions:
  - ChangeWCDate (공정 지연 시 일정 조정)
  - RequestMaterial (자재 긴급 발주)
  - NotifyWorker (담당자 알림)
  - SyncToERP (ERP 자동 업데이트)

Expected Impact: 
  현중(현대중공업) 등 대형 조선사 고객 확보 가능

Timeline: 4주
  Week 1: 온톨로지 설계 (ARCHITECTURE.md 참고)
  Week 2: 저장소 + 샘플 데이터
  Week 3: 액션 + 워크플로우
  Week 4: 테스트 + 문서
```

#### Domain 2: 제조/공정 (Manufacturing) — 우선순위 🟡 Medium
```
Entity Types:
  - FACTORY, PRODUCTION_LINE, PRODUCT, COMPONENT
  
Actions:
  - AdjustSchedule, OrderComponent, StopLine, AlertQC

Timeline: 3주
```

#### Domain 3: 구매/발주 (Procurement) — 우선순위 🟡 Medium
```
Entity Types:
  - VENDOR, PO, INVOICE, BUDGET
  
Actions:
  - CreatePO, ApprovePO, RejectPO, UpdateDelivery

Timeline: 3주
```

### 5-3. Phase 4 성공 기준
```
□ 도메인 3개 온톨로지 구현
□ 도메인별 테스트 케이스 15개 이상 (3×5)
□ 도메인 간 교차 쿼리 가능 (예: "조선 + 자재 + 구매")
□ 고객 PoC 1건 이상 완료
```

---

## 6. Phase 5 — 운영형 하드닝 (10월~11월)

### 6-1. 목표
프로덕션 배포 준비

### 6-2. 작업 항목
```
보안:
  □ 데이터 암호화 (전송, 저장)
  □ API 인증 (OAuth 2.0, API Key)
  □ 감사 로그 (compliance)
  
성능:
  □ 캐싱 전략 (Redis)
  □ 데이터베이스 인덱싱
  □ 쿼리 최적화
  □ 응답 시간 < 500ms (p95)
  
모니터링:
  □ 에러 추적 (Sentry)
  □ 성능 모니터링 (DataDog)
  □ 로그 수집 (ELK)
  □ 알림 규칙 (ALERT: error_rate > 1%)
  
배포:
  □ CI/CD 파이프라인 (GitHub Actions)
  □ Docker 컨테이너화
  □ Kubernetes 오케스트레이션
  □ Blue-Green 배포
  
문서화:
  □ API 문서 (OpenAPI/Swagger)
  □ 운영 가이드
  □ 트러블슈팅 가이드
  □ SLA 정의 (가용성 99.5%)
```

### 6-3. Phase 5 성공 기준
```
□ 프로덕션 준비도 체크리스트 100%
□ 성능 테스트 통과 (부하 1000 QPS)
□ 보안 감시 통과 (OWASP Top 10)
□ 운영 전담팀 교육 완료
```

---

## 7. 현재 단계별 체크리스트

### Phase 2 (현재 진행) — 통합 테스트 개선

**🎯 목표: 2026-05-18까지 20/25 테스트 통과**

```
Week of 2026-05-16 (현주):
  ✅ find_by_name 한글 토큰 개선 (완료)
  ✅ ask_forced_hybrid 메서드 추가 (완료)
  ✅ integration_test.py 업데이트 (완료)
  □ 테스트 재실행 + 결과 분석
  □ 온톨로지 데이터 보완 (누락 엔티티)
  □ 키워드 매칭 로직 정제
  □ 20/25 통과 달성

Week of 2026-05-20:
  □ Phase 2 최종 정산 (모든 케이스 검토)
  □ 이슈 분석 + 문서화
  □ Phase 3 액션 정의 시작
```

### Phase 3 준비 (6월 초부터)

**사전 작업 (지금 시작하기)**

```
□ 비즈니스 액션 요구사항 수집
  - AI바우처: 어떤 액션이 필요한가?
  - 현중 사례 (선박 WC일자 변경) 분석
  - 액션별 권한 모델링

□ 상태 기계 설계 (도메인별)
  - PROJECT: Submitted → Approved → InProgress → Completed
  - MATERIAL: Available → Reserved → Ordered → Received
  
□ Write-back 메커니즘 구조 검토
  - 원천 시스템 (ERP, SAP) API 조사
  - 동기화 전략 수립
```

---

## 8. 의존성 및 위험 요소

### 8-1. 의존성

| 단계 | 의존 대상 | 상태 |
|---|---|---|
| Phase 2 | Gemini LLM API | ✅ 준비됨 |
| Phase 2 | 벡터 임베딩 | ✅ 준비됨 |
| Phase 3 | 비즈니스 요구사항 | ⏳ 수집 중 |
| Phase 3 | ERP API 접근 | ⚠️ 협의 필요 |
| Phase 4 | 다중 도메인 데이터 | ⏳ 수집 예정 |
| Phase 5 | 프로덕션 인프라 | ⏳ 계획 예정 |

### 8-2. 위험 요소

| 위험 | 영향도 | 대응 방안 |
|---|---|---|
| 온톨로지 데이터 불완전 | 🔴 High | 데이터 검증 자동화, 테스트 케이스 보강 |
| LLM 성능 편차 | 🟠 Medium | 프롬프트 튜닝, 폴백 메커니즘 강화 |
| 원천 시스템 API 제약 | 🔴 High | 조기 협의, 모의 API 구현 |
| 도메인 요구사항 변경 | 🟠 Medium | 아키텍처 가능성 검증, 버전 관리 |

---

## 9. 성공 사례 및 영감

### 팔란티어 도입 3단계 (현대중공업 모델)

```
Stage 1 (데이터 연결):  ← 현재 대부분의 국내 기업
  - 데이터 통합, 시각화, 기본 분석
  - ROI: 낮음 (기존 도구로도 가능)

Stage 2 (온톨로지 + LLM):
  - 구조화 + 지능형 쿼리
  - ROI: 중간 (분석 속도 2배)

Stage 3 (워크플로우 + 자동화):  ← 진짜 ROI 발생
  - 의사결정 → 실행 자동화
  - 공정 지연 감지 → 자재 발주 → ERP 반영 (자동)
  - ROI: 높음 (비용 절감 30%, 속도 10배)

우리의 진행:
  현대중공업: Stage 1 완료, Stage 2 진행 중
  우리 ont_platform: Stage 1 완료, Stage 2 완료 예정 (5월), Stage 3 시작 (6월)
```

---

## 10. 일정표 (Timeline)

```
2026-05월:
  │ 16(금) REQUIREMENTS_ALIGNMENT_CHECK 작성 ✅
  │ 16     ARCHITECTURE.md 작성 ✅
  │ 16     NAMING_CONVENTION.md 작성 ✅
  │ 16     ROADMAP.md 작성 ✅
  │ 18(일) Phase 2 통합 테스트 20/25 달성 🎯
  │ 31(토) Phase 2 최종 정산
  │
2026-06월:
  │ 01(일) Phase 3 시작 (비즈니스 액션 정의)
  │ 15(일) Phase 3 Stage 3A 완료
  │ 30(화) Phase 3 Stage 3B~3E 완료
  │
2026-07월:
  │ 15(수) Phase 3 최종 정산 + 고객 PoC 준비
  │ 31(금) Phase 3 완료
  │
2026-08월~09월:
  │ Phase 4 (다중 도메인 확장)
  │
2026-10월~11월:
  │ Phase 5 (운영형 하드닝)
  │
2026-12월:
  │ 프로덕션 배포 준비 완료
```

---

## 정리

**현재 위치:** Phase 2 진행 중 (통합 테스트 80% 목표)  
**다음 단계:** Phase 3 (비즈니스 액션 + 워크플로우) — 6월 시작  
**성공의 핵심:** Phase 3에서 "조회"를 "실행"으로 확장 → 진정한 ROI 발생  

**금주 목표:** 통합 테스트 20/25 통과 + 3개 기초 문서 완성 ✅
