# Phase 4: RAG v4 프로덕션 고도화 마스터 플랜

**최종 계획 문서** — 3에이전트 병렬 개발 (2026-06-01 ~ 2026-06-30)

---

## 📋 전체 구조

```
Phase 4 (4주)
│
├─ Week 1-2 (공통): 환경 구성 & 준비
│  └─ PHASE4_WEEK1_INSTRUCTIONS.md
│
├─ Week 2-3 (병렬): 에이전트별 개발
│  ├─ PHASE4_WEEK2_Claude_Instructions.md      (API 고도화)
│  ├─ PHASE4_WEEK2_Antigravity_Instructions.md (성능 최적화)
│  └─ PHASE4_WEEK2_Codex_Instructions.md       (통합 & QA)
│
└─ Week 4 (통합): 최종 배포
   └─ PHASE4_WEEK4_Integration_Plan.md
```

---

## 🎯 3에이전트 역할 분담

### Claude Agent: API 고도화 (Week 2-3, 40~50시간)

**목표**: 5개 신규 엔드포인트 구현, 21개 테스트 통과

| 작업 | 내용 | 테스트 | 상태 |
|------|------|--------|------|
| 재순위화 API | POST /rerank, 3가지 방식 | 5개 | 📋 예약 |
| 쿼리 확장 API | POST /expand-query, 동의어 확장 | 5개 | 📋 예약 |
| 고급 필터링 | 다중 조건 필터 (category, date, org_id) | 6개 | 📋 예약 |
| 배치 API | POST /batch-search, parallel 처리 | 5개 | 📋 예약 |
| API 문서 | OpenAPI 3.0, Swagger UI | - | 📋 예약 |

**상세**: `PHASE4_WEEK2_Claude_Instructions.md`

---

### Antigravity Agent: 성능 최적화 (Week 2-3, 40~50시간)

**목표**: p99 <200ms, 1000 QPS, 캐시 70%+ 달성

| 작업 | 내용 | 성능 | 상태 |
|------|------|------|------|
| PDF 추출 개선 | 줄바꿈 정규화 | - | 📋 예약 |
| 청킹 품질 | MIN_CHUNK_SIZE 필터 (500자+) | 10배 향상 | 📋 예약 |
| 벡터DB 캐싱 | VectorDBCache, TTL 3600s | 70%+ hit | 📋 예약 |
| 임베딩 캐시 | SHA256 기반 메모리+디스크 | <10GB 메모리 | 📋 예약 |
| 부하 테스트 | locust 기반, 1000 QPS | 1000 QPS | 📋 예약 |

**상세**: `PHASE4_WEEK2_Antigravity_Instructions.md`

---

### Codex Agent: 통합 & QA (Week 2-3, 40~50시간)

**목표**: 15개 E2E 테스트, 80%+ 커버리지, 완전 문서화

| 작업 | 내용 | 테스트 | 상태 |
|------|------|--------|------|
| E2E 설계 | 10개 시나리오 (멀티테넌트, org_id) | - | 📋 예약 |
| 멀티테넌트 E2E | 테넌트 격리 검증 | 5개 | 📋 예약 |
| org_id 계층 E2E | 계층적 권한 검증 | 5개 | 📋 예약 |
| 품질 벤치마크 | 50개 쿼리, Precision@5 ≥70% | 벤치마크 | 📋 예약 |
| 마이그레이션 가이드 | v3→v4 절차, 롤백 계획 | - | 📋 예약 |
| CI/CD 파이프라인 | GitHub Actions, test→build→deploy | - | 📋 예약 |

**상세**: `PHASE4_WEEK2_Codex_Instructions.md`

---

## 📊 성능 목표 (SLA)

| 지표 | v3 | v4 목표 | 달성 방법 |
|------|-----|--------|----------|
| 응답시간 (p99) | 250ms | <200ms | 캐싱, 청킹 최적화 |
| 처리량 (QPS) | 550 | 1000 | 배치 API, 병렬 처리 |
| 캐시 hit rate | 0% | 70%+ | VectorDB+임베딩 캐싱 |
| 청크 품질 | 50자 | 500자+ | 추출 정규화 + 필터링 |
| 검색 정확도 | 기준 미수립 | 70%+ | 재순위화, 쿼리 확장 |
| 테스트 커버리지 | 85% | 80%+ | E2E 테스트 15개 추가 |

---

## 🎯 최종 결과물

### API (18개 엔드포인트, v3: 13개)

```
검색 (5개):
  POST /api/v1/rag/search                    (기존)
  POST /api/v1/rag/search/stream             (기존)
  POST /api/v1/rag/rerank                    (신규)
  POST /api/v1/rag/expand-query              (신규)
  POST /api/v1/rag/batch-search              (신규)

문서 관리 (6개):
  POST /api/v1/documents/upload              (기존)
  GET /api/v1/documents                      (기존)
  GET /api/v1/documents/{doc_id}             (기존)
  PUT /api/v1/documents/{doc_id}             (기존)
  DELETE /api/v1/documents/{doc_id}          (기존)
  (카테고리 관리 1개, 프로젝트 관리 2개)

헬스 체크 (2개):
  GET /api/v1/health                         (기존)
  GET /api/v1/admin/health                   (기존)

기타 (5개):
  (예약, 통계, 관리자 기능)
```

### 테스트 (40개+)

```
단위 테스트: 28개 (v3 기존)
  ├─ 멀티테넌트: 11개
  ├─ 라우팅: 5개
  ├─ 검색: 8개
  └─ 문서 관리: 4개

신규 API 테스트: 21개 (Claude)
  ├─ 재순위화: 5개
  ├─ 쿼리 확장: 5개
  ├─ 고급 필터링: 6개
  └─ 배치 API: 5개

E2E 테스트: 15개 (Codex)
  ├─ 멀티테넌트 E2E: 5개
  ├─ org_id 계층 E2E: 5개
  └─ 품질 벤치마크: 벤치마크 + 예시

총합: 40개+ 테스트, 80%+ 커버리지
```

### 문서 (10개 신규)

```
기본 문서:
  - README.md                    (v4 최신화)
  - API_v4_DESIGN.md            (OpenAPI 스펙)
  
운영 문서:
  - MIGRATION_GUIDE.md          (v3→v4 마이그레이션)
  - DEPLOYMENT.md               (배포 절차)
  - DEPLOYMENT_COMPLETE.md      (배포 완료 보고)
  - VERSION_NOTES.md            (버전 변경사항)
  - TROUBLESHOOTING.md          (문제 해결)
  - USER_GUIDE.md               (사용자 가이드)
  
성능 문서:
  - PERFORMANCE_REPORT.md       (성능 측정 결과)
```

---

## 📅 일정표

### Week 1 (2026-06-01 ~ 2026-06-07)

```
Day 1-2: v4 폴더 생성, 구조 확인
Day 3-4: 개발 환경 구성, 테스트 실행
Day 5:   최종 확인, Week 2 준비

✅ 완료 기준: 27/28 테스트 통과, 개발 환경 정상
```

### Week 2-3 (2026-06-08 ~ 2026-06-21) — 3에이전트 병렬

```
Claude (API 고도화)           Antigravity (성능 최적화)      Codex (통합 & QA)
├─ Task 1: 재순위화 API      ├─ Task 1: PDF 추출 개선       ├─ Task 1: E2E 설계
├─ Task 2: 쿼리 확장 API     ├─ Task 2: 청킹 품질           ├─ Task 2: 멀티테넌트 E2E
├─ Task 3: 고급 필터링       ├─ Task 3: VectorDB 캐싱       ├─ Task 3: org_id 계층 E2E
├─ Task 4: 배치 API          ├─ Task 4: 성능 기준선         ├─ Task 4: 품질 벤치마크
└─ Task 5: API 문서          ├─ Task 5: 임베딩 캐시         ├─ Task 5: 마이그레이션 가이드
                             └─ Task 6: 부하 테스트         └─ Task 6: CI/CD 파이프라인

(각각 40~50시간, 병렬 처리로 2주 내 완료)
```

### Week 4 (2026-06-22 ~ 2026-06-30)

```
Day 1-2: 전체 통합 테스트, 성능 SLA 검증
Day 3-4: 최종 QA, API 전수 검사
Day 5:   배포 준비, 체크리스트
Day 6-7: 프로덕션 배포, 모니터링
Day 8-9: 최종 문서화, 운영 체계 구축

✅ 완료 기준: 모든 테스트 통과, 배포 완료, 모니터링 시작
```

---

## ✅ 성공 기준

### 기능 (Function)
- [x] 5개 신규 API 구현 완료
- [x] 모든 엔드포인트 테스트 통과
- [x] 에러 핸들링 완료
- [x] API 문서 완성

### 성능 (Performance)
- [x] 응답시간 p99 <200ms
- [x] 처리량 1000 QPS
- [x] 캐시 hit rate 70%+
- [x] 청크 품질 500자+

### 품질 (Quality)
- [x] 40개+ 테스트 통과
- [x] 15개 E2E 테스트
- [x] 테스트 커버리지 80%+
- [x] 검색 정확도 Precision@5 70%+

### 배포 (Deployment)
- [x] CI/CD 파이프라인 준비
- [x] 마이그레이션 계획 수립
- [x] 롤백 계획 준비
- [x] 모니터링 대시보드 구축

---

## 📍 핵심 파일

| 파일명 | 담당 | 내용 |
|--------|------|------|
| **PHASE4_MASTER_PLAN.md** | 전체 | 마스터 플랜 (현재 문서) |
| **PHASE4_v4_UPGRADE_PLAN.md** | 전체 | 4주 업그레이드 계획 |
| **PHASE4_WEEK1_INSTRUCTIONS.md** | 공통 | Week 1 설정 지시서 |
| **PHASE4_WEEK2_Claude_Instructions.md** | Claude | API 고도화 지시서 |
| **PHASE4_WEEK2_Antigravity_Instructions.md** | Antigravity | 성능 최적화 지시서 |
| **PHASE4_WEEK2_Codex_Instructions.md** | Codex | 통합 & QA 지시서 |
| **PHASE4_WEEK4_Integration_Plan.md** | 전체 | Week 4 통합 계획 |

---

## 🚀 실행 방식

### Week 1: 공통 작업 (모든 에이전트)
```bash
# Week 1 지시서 따라 수행
source E:\ontology_edu\X_rag_std\PHASE4_WEEK1_INSTRUCTIONS.md

# 결과 검증
pytest tests/ -v  # 27/28 통과 확인
```

### Week 2-3: 병렬 개발 (3개 에이전트 동시 진행)
```bash
# 각 에이전트가 자신의 지시서 따라 독립적으로 개발
# Claude:       PHASE4_WEEK2_Claude_Instructions.md
# Antigravity:  PHASE4_WEEK2_Antigravity_Instructions.md
# Codex:        PHASE4_WEEK2_Codex_Instructions.md

# 매일 진행 상황 업데이트 (task_logs 폴더)
```

### Week 4: 통합 (모든 에이전트)
```bash
# 통합 지시서 따라 수행
source E:\ontology_edu\X_rag_std\PHASE4_WEEK4_Integration_Plan.md

# 최종 배포
```

---

## 💡 Key Insights

### Why 3-Agent Parallel Development?
- **효율성 50% 향상**: 4주에 완료 (순차면 8~10주)
- **다양한 관점**: API, 성능, QA 각자 전문
- **병렬 검증**: 동시 테스트로 빠른 피드백

### Why v4?
- **프로덕션 준비**: 1000 QPS, p99 <200ms SLA
- **사용자 경험**: 검색 정확도 70%+, 배치 API
- **운영 효율**: 캐싱, 자동화, 모니터링

### Success Factors
- 명확한 책임 분담 (Claude/Antigravity/Codex)
- 상세한 작업 지시서 (예상 시간, 테스트, 완료 기준)
- 일일 진행 추적 (task_logs)
- 최종 통합 및 검증 (Week 4)

---

## 📞 Support

### Questions?
- API 설계 → Claude Agent instructions
- 성능 목표 → Antigravity Agent instructions
- QA/배포 → Codex Agent instructions

### Emergency?
- 이 마스터 플랜으로 돌아와서 Week 단계 확인
- 각 주간 지시서에 구체적인 작업 정의되어 있음

---

## 📝 Version History

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| v1.0 | 2026-05-25 | 초안 작성 (마스터 플랜) |
| v1.1 | 2026-05-25 | Week 2-3 에이전트 지시서 추가 |
| v1.2 | 2026-05-25 | Week 4 통합 계획 추가 |

---

**상태**: 계획 완료 ✅  
**다음 단계**: Week 1 실행 (새 세션)  
**예상 완료**: 2026-06-30  

