# ont_platform v3 — 프로젝트 상태

> 모든 상태 정보의 **Single Source of Truth**  
> 🔄 매 주기마다 이 파일을 업데이트합니다.

---

## 📊 현재 상태 (2026-05-19)

### 컴포넌트 상태

| 항목 | 상태 | 진행도 | 비고 |
|------|------|--------|------|
| **백엔드 (FastAPI)** | ✅ 실행 가능 | 100% | 포트 8001, conda `claud_be` |
| **프론트엔드 (Next.js)** | ✅ 실행 가능 | 100% | 포트 3001, conda `claud_fe` |
| **단위 테스트** | ✅ 통과 | 100% | 29/29 통과 |
| **통합 테스트** | ⚠️ 진행중 | 4% | 1/25 통과 → **목표 20/25 (80%)** |
| **비즈니스 액션** | ❌ 미구현 | 0% | Phase 3 핵심 |
| **Write-back** | ❌ 미구현 | 0% | Phase 3 핵심 |
| **RBAC & 거버넌스** | ⚠️ 설계 중 | 30% | Phase 3 진행 |

### 전체 진행도
```
▓▓▓▓▓▓▓░░░░░░░░░░░░ 42%
```
**완성도**: ~42% (조회 기능 완성, 실행·액션 미완성)

---

## 🎯 현재 Phase (Phase 2: 진행 중 → Phase 3 준비)

### Phase 2 (현재)
**마감**: 2026-05-18 (연장: 2026-05-24)  
**목표**: 통합 테스트 1/25 (4%) → **20/25 (80%)**

**작업 항목**:
- [ ] 온톨로지 데이터 매칭 최적화
- [ ] 벡터 검색 성능 개선
- [ ] 엣지 케이스 처리
- [ ] 실패 케이스 분석 및 고속 수정

### Phase 3 (준비 중)
**시작**: 2026-05-20 (문서 작성 중)  
**본격 개발**: 2026-05-27 (Week 1 시작)  
**마감**: 2026-07-31

**준비 상황**:
- ✅ 액션 정의서 완성 ([PHASE3_ACTION_DEFINITION.md](./PHASE3_ACTION_DEFINITION.md))
  - 6개 액션 상세 정의 (ApproveProject, RejectProject, ChangeDeadline, RequestMoreInfo, StartPayment, CompleteProject)
  - 권한 모델 RBAC 상세화
  - 구현 로드맵 (4주)

- ✅ 상태 기계 & Write-back 설계서 완성 ([PHASE3_STATE_MACHINE.md](./PHASE3_STATE_MACHINE.md))
  - PROJECT 엔티티 상태 기계 (6개 상태, 10개 전이)
  - Write-back 메커니즘 상세 (Changelog, Queue, Worker)
  - 저장소 구조 & 모니터링

**다음 단계 (이번주 중)**:
- [ ] workflow.json 확장 (ai-voucher-2025 도메인)
- [ ] ActionDefinition 모델 구현
- [ ] 전제 조건 & 조건부 권한 로직

---

## 🟡 다음 Phase (Phase 3: 2026-05-20 ~ 2026-05-31)

### 비즈니스 액션 구현

**1. ActionType 추가**
- [ ] `ApproveProject`
- [ ] `RejectProject`
- [ ] `ChangeStatus`
- 관련 파일: `v3/src/backend/models/`

**2. 상태 전이 규칙 (10개 이상)**
- [ ] PROJECT: Submitted → Approved → InProgress → Completed
- [ ] Approved ↔ Rejected (재심)
- [ ] 기타 전이 규칙

**3. RBAC 권한 모델**
- [ ] admin / manager / team_lead / member
- [ ] 엔드포인트별 권한 체크

---

## 🟢 향후 Phase (6~7월: Phase 3 완료)

- [ ] Write-back 동기화 (외부 시스템 반영)
- [ ] 프론트엔드 Action UI
- [ ] Decision Record System

---

## 📈 주간 진행 현황

| 주차 | 기간 | 목표 | 상태 |
|------|------|------|------|
| **1주** | 05-12 ~ 05-18 | 기반 구축 | ✅ 완료 |
| **2주** | 05-19 | 통합 테스트 80% | ⏳ 진행중 |
| **3주** | 05-20 ~ 05-26 | Phase 3 착수 | ⬜ 예정 |
| **4주** | 05-27 ~ 05-31 | Phase 3 마무리 | ⬜ 예정 |

---

## 🔧 최근 변경사항

### 2026-05-19
- ✅ 문서화 정리 완료
  - CLAUDE.md 업데이트 (폴더 구조)
  - task_logs 정책화 (LOGGING_POLICY.md)
  - 폴더별 README 작성 (requirements, cross-source-comparison)
  - 프로젝트 전체 개요 작성 (README.md)
  - **STATUS.md 신설** (상태 정보 중앙화)

### 2026-05-16 ~ 2026-05-18
- ✅ 플랫폼 비교 평가 완료
  - Antigravity, Claude, Codex 종합 평가
  - cross-source-comparison/ 폴더 구성

### 2026-05-15
- ✅ 요건 추적도 대량 업데이트

---

## 📍 주요 파일 위치

```
상태 정보:      E:\ontology_edu\X_ont_std\STATUS.md (이 파일)
프로젝트 컨텍스트: E:\ontology_edu\X_ont_std\CLAUDE.md
전체 개요:      E:\ontology_edu\X_ont_std\README.md
백엔드:         E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend\
프론트엔드:     E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend\
통합 테스트:    E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend\tests\integration\
아키텍처:       E:\ontology_edu\X_ont_std\ont_platform\v3\ARCHITECTURE.md
로드맵:         E:\ontology_edu\X_ont_std\ont_platform\v3\ROADMAP.md
```

---

## 🔗 참고 문서

- [CLAUDE.md](./CLAUDE.md) — 프로젝트 컨텍스트 & 개발 규칙
- [README.md](./README.md) — 프로젝트 전체 개요
- [LOGGING_POLICY.md](./task_logs/LOGGING_POLICY.md) — 작업 기록 정책

---

**마지막 업데이트**: 2026-05-19  
**다음 업데이트**: 2026-05-26 (주간 리뷰)

