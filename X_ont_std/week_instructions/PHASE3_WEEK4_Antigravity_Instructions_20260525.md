# Phase 3 Week 4 Antigravity (Performance) 작업 지시서

**기간**: 2026-06-17 ~ 2026-06-21 (5일)  
**담당**: Antigravity (Performance Agent)  
**목표**: Phase 3 최종 성능 테스트 + 부하 테스트 + 성능 리포트  
**예상시간**: 10~12시간

---

## 🎯 Week 4 Antigravity 임무

Phase 3 전체 시스템의 성능을 측정하고 최적화:
1. **API 성능 벤치마크** (응답시간, 처리량)
2. **부하 테스트** (액션 실행 + 동기화)
3. **최종 성능 리포트** (성능 지표 + 최적화 권고)

---

## 📋 Task 분해

### Task 1: API 성능 벤치마크 (3~4시간)
**도구**: Apache JMeter 또는 Locust (Python)

#### 테스트 시나리오

**Scenario 1: 기본 액션 실행 (5분)**
```
API: POST /api/workflow/execute
매개변수:
  - action: approve_project
  - entity_id: proj_001
  - approver: pm@example.com

목표:
  - 응답시간: < 500ms (p95)
  - 처리량: > 100 RPS (Requests Per Second)
  - 에러율: < 1%
  - Throughput: > 10 actions/sec
```

**Scenario 2: Changelog 조회 (5분)**
```
API: GET /api/changelog/history
매개변수:
  - page: 1
  - page_size: 50

목표:
  - 응답시간: < 200ms (p95)
  - 처리량: > 500 RPS
  - 에러율: < 1%
```

**Scenario 3: WriteBack 통계 조회 (5분)**
```
API: GET /api/writeback/statistics

목표:
  - 응답시간: < 100ms (p95)
  - 처리량: > 1000 RPS
  - 에러율: < 1%
```

#### 벤치마크 스크립트 (Locust 예시)
```python
from locust import HttpUser, task, between

class Phase3PerformanceTest(HttpUser):
    wait_time = between(0.5, 2)
    
    @task(1)
    def execute_action(self):
        self.client.post(
            "/api/workflow/execute",
            json={
                "entity_id": "proj_001",
                "action": "approve_project",
                "approver": "pm@example.com"
            }
        )
    
    @task(2)
    def query_changelog(self):
        self.client.get(
            "/api/changelog/history?page=1&page_size=50"
        )
    
    @task(1)
    def get_statistics(self):
        self.client.get("/api/writeback/statistics")
```

#### 측정 항목
- ✅ 응답시간 (평균, 중위수, p95, p99)
- ✅ 처리량 (RPS, actions/sec)
- ✅ 에러율 (%)
- ✅ CPU 사용률 (%)
- ✅ 메모리 사용률 (%)
- ✅ 데이터베이스 쿼리 시간

#### 결과 리포트
```
API 성능 벤치마크
─────────────────────────────────────────
POST /api/workflow/execute
  응답시간: 150ms (avg), 120ms (p50), 280ms (p95)
  처리량: 200 RPS
  에러율: 0.2%
  
GET /api/changelog/history
  응답시간: 80ms (avg), 60ms (p50), 150ms (p95)
  처리량: 800 RPS
  에러율: 0%
  
GET /api/writeback/statistics
  응답시간: 30ms (avg), 25ms (p50), 50ms (p95)
  처리량: 2000 RPS
  에러율: 0%
─────────────────────────────────────────
```

---

### Task 2: 부하 테스트 (액션 + 동기화) (4~5시간)
**도구**: Locust 또는 Apache JMeter

#### 테스트 목표
실제 사용 패턴 시뮬레이션:
1. 동시에 여러 액션 실행
2. WriteBackWorker가 동기화 처리
3. SAP API 응답 시간 포함

#### 부하 테스트 시나리오

**Scenario A: 점진적 부하 증가 (10분)**
```
사용자 수: 1 → 10 → 50 → 100 (매 2분마다 증가)
각 사용자:
  - 1분마다 액션 실행
  - 3초마다 통계 조회
  
목표:
  - 100 사용자에서 에러율 < 5%
  - 응답시간 저하 선형적 (p95 < 2초)
```

**Scenario B: 지속적 부하 (10분)**
```
사용자 수: 50 (상수)
액션 타입 분배:
  - ApproveProject: 30%
  - RejectProject: 20%
  - StartPayment: 20%
  - ChangeDeadline: 15%
  - RequestMoreInfo: 10%
  - CompleteProject: 5%
  
목표:
  - 지속적으로 안정적인 성능 유지
  - 메모리 누수 없음
  - 데이터 무결성 보장
```

**Scenario C: 피크 부하 (5분)**
```
사용자 수: 200 (최대)
모든 사용자가 동시에 액션 실행
  
목표:
  - 최대 1분 동안 견딜 수 있어야 함
  - 에러율 < 10% (허용 가능)
  - 이후 복구 시간 < 2분
```

#### 부하 테스트 스크립트
```python
from locust import HttpUser, task, between, events
import time

class Phase3LoadTest(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.project_counter = 0
    
    @task(3)
    def execute_random_action(self):
        actions = [
            ("approve_project", {"approver": "pm@example.com"}),
            ("reject_project", {"reason": "Budget issue", "rejected_by": "reviewer@example.com"}),
            ("start_payment", {"amount": 5000000, "approved_by": "cfo@example.com"}),
        ]
        
        action, params = random.choice(actions)
        self.client.post(
            "/api/workflow/execute",
            json={
                "entity_id": f"proj_{self.project_counter:03d}",
                "action": action,
                **params
            }
        )
        self.project_counter += 1
    
    @task(1)
    def check_statistics(self):
        self.client.get("/api/writeback/statistics")
```

#### 측정 항목
- ✅ 부하 곡선 (사용자 수 vs 응답시간)
- ✅ 에러율 추이
- ✅ CPU/메모리 사용률 추이
- ✅ 데이터베이스 연결 풀 상태
- ✅ Worker 큐 크기
- ✅ 복구 시간 (피크 후)

#### 결과 리포트
```
부하 테스트 결과
─────────────────────────────────────────
시나리오 A: 점진적 부하
  1-10 사용자: 에러율 0%, p95=150ms
  10-50 사용자: 에러율 0.1%, p95=320ms
  50-100 사용자: 에러율 2%, p95=890ms
  
시나리오 B: 지속적 부하 (50 사용자, 10분)
  평균 응답시간: 200ms (안정적)
  에러율: 0.2%
  메모리: 450MB → 460MB (안정적)
  
시나리오 C: 피크 부하 (200 사용자, 5분)
  에러율: 8% (허용 범위)
  최대 응답시간: 3.2초
  복구 시간: 90초
─────────────────────────────────────────
```

---

### Task 3: 최종 성능 리포트 (2~3시간)
**파일**: `PHASE3_PERFORMANCE_REPORT.md`

#### 리포트 구성

```markdown
# Phase 3 최종 성능 리포트

## Executive Summary
- 전체 시스템 성능: 우수 (95% 기준 충족)
- 주요 성능 지표: [표]
- 최적화 권고: [3가지]

## 1. API 성능 벤치마크
### 응답시간
- POST /api/workflow/execute: 150ms (p95)
- GET /api/changelog/history: 80ms (p95)
- GET /api/writeback/statistics: 30ms (p95)

### 처리량
- 최대 RPS: 200 (액션 실행)
- 동시 사용자: 100

### 기준 충족도
✅ 응답시간 목표 달성
✅ 처리량 목표 달성
⚠️ 데이터베이스 쿼리 최적화 필요

## 2. 부하 테스트
### 안정성
- 100 사용자 지속 처리: 안정적
- 메모리 누수: 없음
- 데이터 무결성: 100% 보장

### 복원력
- 피크 부하 복구: 90초
- 에러율: < 10% (피크)

## 3. 성능 병목

### 1순위: 데이터베이스 쿼리
- 현상: Changelog 조회 시 JOIN 연산 多
- 영향: 응답시간 80ms (개선 가능성 50ms)
- 해결: Index 추가, 쿼리 최적화

### 2순위: Worker 처리 속도
- 현상: SAP 동기화 평균 500ms (Mock API 포함)
- 영향: WriteBackQueue 대기 시간 증가
- 해결: 병렬 처리, 배치 동기화

### 3순위: 메모리 관리
- 현상: 100 사용자 시 450MB → 안정적
- 영향: 없음 (현재 문제 없음)
- 해결: 모니터링 계속

## 4. 최적화 권고

### 즉시 적용 가능
1. Changelog 쿼리 Index 추가
   - 예상 개선: 30ms → 15ms
   - 복잡도: Low
   - 영향: 높음

2. WriteBackWorker 배치 처리
   - 예상 개선: 1개씩 처리 → 10개씩 배치
   - 복잡도: Medium
   - 영향: 높음

### 중기 계획
3. 데이터베이스 연결 풀 최적화
4. Redis 캐싱 (자주 조회되는 데이터)

## 5. 결론
- ✅ Phase 3 성능 목표 달성
- ✅ 프로덕션 배포 준비 완료
- ⚠️ 최적화 권고 반영 시 추가 개선 가능
```

#### 핵심 지표
```
성능 지표 요약
─────────────────────────────────────────
응답시간 (p95):
  - 액션 실행: 280ms (목표: < 500ms) ✅
  - 조회: 150ms (목표: < 200ms) ✅
  
처리량:
  - 최대 RPS: 200 (목표: > 100) ✅
  - 동시 사용자: 100 (목표: > 50) ✅
  
안정성:
  - 에러율: < 1% (목표: < 2%) ✅
  - 메모리 누수: 없음 ✅
  - 데이터 무결성: 100% ✅
─────────────────────────────────────────
```

---

## 🛠️ 성능 테스트 환경

### 하드웨어
```
CPU: 4 cores
RAM: 8GB
스토리지: SSD 50GB
```

### 소프트웨어
```
Database: SQLite (메모리 모드 테스트 후 파일 기반)
Backend: FastAPI (uvicorn 4 workers)
Frontend: Next.js (개발 서버)
```

### 테스트 도구
```
Locust 또는 Apache JMeter
Grafana (모니터링, 선택사항)
Python profiler (cProfile)
```

---

## 📊 완료 기준

```
✅ Task 1: API 성능 벤치마크
  - 3개 API 모두 측정
  - 응답시간, RPS 목표 달성
  - 상세 리포트 작성

✅ Task 2: 부하 테스트
  - 3개 시나리오 모두 실행
  - 100+ 사용자 처리 확인
  - 메모리 누수 검증

✅ Task 3: 최종 성능 리포트
  - 성능 벤치마크 요약
  - 병목 분석
  - 최적화 권고 3개 이상
  - 프로덕션 준비도 평가

✅ 전체 성능 기준 충족
  - 응답시간 < 500ms (p95)
  - 처리량 > 100 RPS
  - 에러율 < 1% (정상 부하)
```

---

## 📁 결과 저장 위치

```
ont_platform/v3/
├── PHASE3_PERFORMANCE_REPORT.md      ← 최종 리포트
├── performance_tests/
│   ├── locustfile.py                 ← 부하 테스트 스크립트
│   ├── benchmark_results.json         ← 벤치마크 결과
│   ├── load_test_results.json         ← 부하 테스트 결과
│   └── performance_charts/            ← 그래프 (선택)
└── docs/
    └── PERFORMANCE_OPTIMIZATION.md    ← 최적화 상세 가이드 (선택)
```

---

## 🚀 실행 순서

1. **Task 1 실행** (API 벤치마크) → 결과 수집 (30분)
2. **Task 2 실행** (부하 테스트) → 결과 분석 (1시간)
3. **Task 3 작성** (최종 리포트) → 완료

---

## 📈 성공 지표

| 지표 | 목표 | 예상 결과 |
|------|------|---------|
| 응답시간 (p95) | < 500ms | 150~300ms ✅ |
| 처리량 (RPS) | > 100 | 200 RPS ✅ |
| 동시 사용자 | > 50 | 100 ✅ |
| 에러율 | < 1% | 0.2~0.5% ✅ |
| 메모리 누수 | 없음 | 안정적 ✅ |

---

**예상 완료**: 2026-06-21  
**최종 검증**: 모든 성능 기준 충족 + 리포트 제출  
**다음**: Claude/Codex와 통합

