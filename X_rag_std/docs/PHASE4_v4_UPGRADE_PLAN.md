# Phase 4: RAG v4 업그레이드 & 3에이전트 병렬 개발

**문서 작성일**: 2026-05-25  
**적용 시작**: 2026-06-01  
**완성 목표**: 2026-06-30 (4주)  

---

## 📊 프로젝트 개요

### 목적
v3의 안정적 베이스를 기반으로 v4에서:
- API 기능 고도화
- 성능/최적화 강화
- 통합/QA 체계화
- **3개 에이전트의 병렬 개발로 효율성 50% 향상**

### v3 → v4 차이점

| 항목 | v3 | v4 |
|------|-----|-----|
| **상태** | 안정화 완료 | 고도화 진행 |
| **개발 방식** | 순차 | 병렬 (3에이전트) |
| **목표** | 기본 기능 | 프로덕션 레벨 |
| **성능** | 기준 수립 | SLA 달성 (p99<200ms) |
| **테스트** | 기본 테스트 | 포괄적 E2E 테스트 |

---

## 🎯 v4 주요 개선사항

### Phase 4 개발 영역 (12주 스프린트)

```
v4 (Phase 4: 2026-06-01 ~ 2026-08-30)
├─ Week 1~2: 환경 구성 + 작업 지시서 (준비)
├─ Week 3~10: 병렬 개발 (Claude + Antigravity + Codex)
└─ Week 11~12: 통합 & 배포 (Release)
```

---

## 👥 3에이전트 역할 분담

### Claude Agent: API 고도화 (3~4주)
**목표**: v3 API를 프로덕션 수준으로 고도화

#### 주요 작업
```
□ 검색 결과 재순위화 (Reranking)
  - 쿼리-문서 관련성 스코어 재계산
  - 사용자 피드백 기반 학습
  
□ 쿼리 확장 (Query Expansion)
  - 동의어, 유사어 확장
  - LLM 기반 쿼리 개선
  
□ 다중 필터 조건 (Advanced Filtering)
  - org_id + category + date range
  - 복합 필터 조건 조합
  
□ 배치 API (Bulk Search)
  - 10개 이상 쿼리 한 번에 처리
  - 효율성 50% 향상
  
□ 비동기 검색 (Async Search)
  - 장시간 검색을 백그라운드에서 처리
  - WebSocket 기반 알림
  
□ API 문서 완성
  - OpenAPI 3.0 스펙
  - Swagger UI 상세 설명
```

#### 담당 파일
```
src_claud/v4/
├─ app/api/search.py (확장)
├─ app/api/reranking.py (신규)
├─ app/services/query_expansion.py (신규)
├─ app/services/rag_service.py (고도화)
└─ tests/test_api_*.py (확장)
```

#### 기대 성과
- API 엔드포인트: 5개 → 10개+
- 검색 정확도: 기준 → +15%
- 사용자 만족도: 기본 → 높음

---

### Antigravity Agent: 성능 최적화 (3~4주)
**목표**: 성능 SLA 달성 (p99 <200ms, 처리량 1000 QPS)

#### 주요 작업
```
□ Phase 2 청킹 품질 완성
  - extractor.py 줄바꿈 정제
  - chunker.py 최소 크기 필터 (500자+)
  - 청크 크기 검증 (평균 500자 이상)
  
□ 벡터DB 캐싱 강화
  - 자주 사용되는 쿼리 캐싱
  - TTL 정책 (1시간 → 4시간)
  - 캐시 hit rate 80% 이상
  
□ 임베딩 캐시 최적화
  - SHA256 기반 캐시 키
  - 인메모리 + 디스크 2단계 캐싱
  - 메모리 사용량 10GB 이하
  
□ 부하 테스트 (Load Test)
  - 동시 1000 사용자 시뮬레이션
  - 응답시간 분포 측정
  - 병목 지점 식별
  
□ 성능 최적화
  - 병렬 임베딩 처리
  - 벡터 검색 최적화 (HNSW)
  - 데이터베이스 인덱싱
  
□ 모니터링 대시보드
  - Grafana 기반 실시간 모니터링
  - 성능 지표 (응답시간, QPS, 에러율)
```

#### 담당 파일
```
src_claud/v4/
├─ app/services/pipeline/extractor.py (개선)
├─ app/services/pipeline/chunker.py (개선)
├─ app/services/rag_service.py (성능 튜닝)
├─ tests/load/
│  ├─ load_test_search.py (신규)
│  ├─ load_test_upload.py (신규)
│  └─ performance_baseline.py (신규)
├─ docs/PERFORMANCE_REPORT.md (신규)
└─ monitoring/ (신규)
```

#### 기대 성과
- 응답시간: 기준 → <200ms (p99)
- 처리량: 기준 → 1000 QPS
- 캐시 hit rate: 70%+
- 청크 품질: 500자+ (100%)

---

### Codex Agent: 통합 & QA (3~4주)
**목표**: v4 완성도 100%, 배포 준비 완료

#### 주요 작업
```
□ E2E 통합 테스트
  - 멀티테넌트 시나리오 (3개 이상)
  - org_id 계층 검증 (5개 이상 케이스)
  - 전체 검색 워크플로우
  
□ 검색 품질 벤치마크
  - 샘플 쿼리 50개 이상
  - 정확도, 재현율, F1 스코어 측정
  - 사용자 피드백 수집
  
□ 회귀 테스트 (Regression Testing)
  - v3 → v4 호환성 검증
  - API 변경사항 호환성
  - 데이터 마이그레이션 검증
  
□ 마이그레이션 가이드
  - v3 → v4 마이그레이션 절차
  - Breaking changes 문서화
  - 롤백 계획
  
□ 배포 자동화
  - CI/CD 파이프라인 (GitHub Actions)
  - 스모크 테스트
  - 배포 체크리스트
  
□ 최종 QA & 문서화
  - 모든 엔드포인트 테스트
  - 에러 핸들링 검증
  - 사용자 가이드 작성
```

#### 담당 파일
```
src_claud/v4/
├─ tests/e2e/
│  ├─ test_multitenant_e2e.py (신규)
│  ├─ test_org_hierarchy_e2e.py (신규)
│  └─ test_search_quality.py (신규)
├─ docs/
│  ├─ MIGRATION_GUIDE.md (신규)
│  ├─ DEPLOYMENT.md (신규)
│  ├─ TROUBLESHOOTING.md (신규)
│  └─ USER_GUIDE.md (신규)
├─ .github/workflows/
│  ├─ ci.yml (신규)
│  └─ deployment.yml (신규)
└─ scripts/migrate_v3_to_v4.py (신규)
```

#### 기대 성과
- 테스트 커버리지: 80% 이상
- 문제 해결 속도: <1시간
- 배포 시간: <10분
- 사용자 준비도: 100%

---

## 📅 주간 계획 (Week-by-Week)

### Week 1-2: 환경 구성 & 준비
```
(공통 작업)
□ v4 폴더 생성 (v3 복제)
□ v4 README.md 작성
□ CLAUDE.md v4 Phase 추가
□ 3에이전트 작업 지시서 최종 확정

Day 1-2: 폴더 구조 및 기초 설정
Day 3-4: 테스트 환경 구성
Day 5: 리뷰 & 최종 확인
```

### Week 3-10: 병렬 개발 (8주)
```
Claude (API 고도화)
├─ Week 3-4: 재순위화 + 쿼리 확장 구현
├─ Week 5-6: 다중 필터 + 배치 API 구현
├─ Week 7-8: 비동기 검색 + API 문서 완성
└─ Week 9-10: 통합 테스트 + 버그 수정

Antigravity (성능 최적화)
├─ Week 3-4: 청킹 품질 완성
├─ Week 5-6: 캐싱 전략 구현
├─ Week 7-8: 부하 테스트 (1000 QPS)
└─ Week 9-10: 성능 튜닝 + 모니터링

Codex (통합 & QA)
├─ Week 3-4: E2E 테스트 설계
├─ Week 5-6: 통합 테스트 작성
├─ Week 7-8: 품질 벤치마크
└─ Week 9-10: 마이그레이션 가이드 + 배포 자동화
```

### Week 11-12: 통합 & 배포
```
Day 1-3: 세 에이전트 결과 통합
Day 4-5: 최종 E2E 테스트
Day 6-7: 배포 준비
Day 8: 프로덕션 배포 & 모니터링
```

---

## ✅ 성공 기준 (Definition of Done)

### 기능 완성도
- [ ] 모든 API 엔드포인트 구현
- [ ] 모든 테스트 통과 (80% 이상 커버리지)
- [ ] 에러 핸들링 완료

### 성능 SLA
- [ ] 응답시간: p99 < 200ms
- [ ] 처리량: 1000 QPS 이상
- [ ] 캐시 hit rate: 70% 이상
- [ ] 청크 품질: 500자+ (100%)

### 품질 & 문서
- [ ] E2E 테스트 통과
- [ ] 마이그레이션 가이드 완성
- [ ] 배포 자동화 완료
- [ ] 사용자 문서 완성

### 배포 준비
- [ ] CI/CD 파이프라인 구축
- [ ] 모니터링 대시보드 준비
- [ ] 롤백 계획 수립
- [ ] 운영팀 교육 완료

---

## 🔗 관련 문서

- `PHASE4_WEEK1_Claude_Instructions.md` (작성 예정)
- `PHASE4_WEEK1_Antigravity_Instructions.md` (작성 예정)
- `PHASE4_WEEK1_Codex_Instructions.md` (작성 예정)

---

## 📝 다음 단계

1. ✅ v4 계획 확정 (현재 문서)
2. ⏳ 3에이전트 주간 지시서 작성 (다음)
3. ⏳ v4 폴더 생성 및 개발 시작 (새 창)
