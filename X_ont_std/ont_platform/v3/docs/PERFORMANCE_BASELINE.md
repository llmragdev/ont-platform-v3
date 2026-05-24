# 성능 기준선 및 목표 SLA 정의서

이 문서는 온톨로지 조회 시스템 `ont_platform`에서 유지하고 보장해야 하는 성능 목표 및 서비스 수준 계약(SLA)을 정의합니다.

## 성능 SLA (Service Level Agreements)

안정적이고 빠른 실행형 온톨로지 저장소를 운영하기 위해, 가장 자주 사용되는 SPARQL 쿼리 패턴에 대해 다음과 같은 엄격한 응답 속도 목표치를 적용합니다.

| 쿼리 유형 / 패턴 | 복잡도 | Warm 캐시 목표치 (p95) | Cold 캐시 목표치 (p95) |
|---|---|---|---|
| **단순 조회 (Simple Lookup)** | 패턴 #18, #21 | **< 3 ms** | **< 50 ms** |
| **1-Hop 관계 조회** | 패턴 #19, #20, #24 | **< 5 ms** | **< 300 ms** |
| **2-Hop 관계 조회** | 패턴 #25, #26 | **< 10 ms** | **< 1000 ms** |

---

## 벤치마크 테스트 시나리오

성능 측정은 다음의 4가지 주요 쿼리 카테고리를 대상으로 수행됩니다.

### 1. 단순 ID 조회 (패턴 #18)
특정 엔티티가 가진 단일 속성 값을 직접 조회합니다. (예: `ex:ship1 ex:name ?name`) 데이터베이스의 기본 키(Primary Key)를 사용하므로 가장 빠른 속도를 요구합니다.
- **Warm 캐시 목표**: 3ms 미만
- **Cold 캐시 목표**: 50ms 미만

### 2. 속성 및 타입 필터링 (패턴 #19, #20, #21)
특정 타입을 가지거나 JSONB 속성 조건을 만족하는 엔티티들을 검색합니다. (예: `?part ex:cost ?cost FILTER (?cost > 500)`) PostgreSQL의 GIN 인덱스 효율성을 검증합니다.
- **Warm 캐시 목표**: 5ms 미만
- **Cold 캐시 목표**: 300ms 미만

### 3. 1-Hop 관계 조회 (패턴 #24)
특정 엔티티에서 시작하여 1단계 관계를 맺고 있는 대상과 속성을 조회합니다. (예: `ex:supplier1 ex:supplies ?part . ?part ex:cost ?cost`) `relationships.from_entity_id` 인덱스의 성능을 검증합니다.
- **Warm 캐시 목표**: 5ms 미만
- **Cold 캐시 목표**: 300ms 미만

### 4. 2-Hop 관계 조회 (패턴 #25, #26)
관계를 두 번 거쳐 연결된 대상을 조인하여 조회합니다. (예: `ex:ship1 ex:has_block ?block . ?block ex:has_part ?part`) 여러 단계의 조인이 발생할 때의 데이터베이스 병목을 파악합니다.
- **Warm 캐시 목표**: 10ms 미만
- **Cold 캐시 목표**: 1000ms 미만

---

## 성능 측정 방법
정의된 응답 속도 목표치를 달성하고 있는지 검증하려면 다음 단계를 통해 로컬 자동 측정 스크립트를 실행합니다.

```powershell
# 1. 백엔드 FastAPI 서버 구동
cd ont_platform/v3/src/backend
conda activate claud_be
uvicorn app.main:app --reload --port 8001

# 2. 성능 측정 스크립트 실행 (새 터미널 창)
cd ont_platform/v3
python tests/load/baseline.py
```

이 스크립트는 로컬 백엔드 서버에 정의된 7가지 벤치마크 쿼리를 순차적으로 요청하여 Cold 캐시 및 Warm 캐시 상태의 응답 지연 시간을 각각 분리 수집한 뒤, 그 결과를 `tests/load/baseline_data.json` 파일에 저장합니다.
