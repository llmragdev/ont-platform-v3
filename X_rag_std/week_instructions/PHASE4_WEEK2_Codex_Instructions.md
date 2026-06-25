# Phase 4 Week 2-3 Codex (통합 & QA) 작업 지시서

**기간**: 2026-06-08 ~ 2026-06-21 (2주)  
**담당**: Codex Agent (Integration & QA)  
**목표**: E2E 테스트 설계 + 통합 테스트 작성  
**예상시간**: 40~50시간

---

## 🎯 Week 2-3 Codex 임무

v4 완성도 100%, 배포 준비:
1. **E2E 테스트 설계** — 멀티테넌트 + org_id (Week 2)
2. **통합 테스트 작성** — 모든 엔드포인트 (Week 2-3)
3. **품질 벤치마크** — 검색 정확도 측정 (Week 3)
4. **마이그레이션 가이드** — v3→v4 절차 (Week 3)

---

## 📋 Task 분해

### Week 2 (Day 1-5): E2E 테스트 + 통합 테스트

#### Task 1: E2E 테스트 설계 (2~3시간)

**파일**: `tests/e2e/test_plan.md` (신규)

**목표**: 전체 워크플로우 테스트 계획 수립

**내용**:

```markdown
# E2E 테스트 계획 (v4)

## 테스트 시나리오 (10개 이상)

### 시나리오 1: 단일 테넌트 기본 검색
```
- 사전조건: company_abc 테넌트
- 작업: 문서 업로드 → 검색 → 결과 반환
- 검증: 관련 문서 포함, 응답시간 <200ms
```

### 시나리오 2: 멀티테넌트 격리
```
- 사전조건: company_abc, company_xyz 테넌트 각각 5개 문서
- 작업: company_abc로 검색
- 검증: company_abc 문서만 반환 (company_xyz 격리 확인)
```

### 시나리오 3: org_id 계층 접근
```
- 사전조건: org_id 0100(부서), 0101(팀), 0102(팀) 문서
- 작업: 0101 사용자가 검색
- 검증: 0101 + 0100 + 전사공유 문서 반환
```

### 시나리오 4: 다중 필터 조합
```
- 사전조건: 다양한 카테고리/날짜 문서 50개
- 작업: category=채용 AND date_from=2026-01-01 검색
- 검증: 필터 조건 만족하는 문서만 반환
```

### 시나리오 5: 재순위화 적용
```
- 사전조건: 10개 검색 결과
- 작업: rerank API로 재순위화
- 검증: 순서 변경, 관련성 점수 재계산
```

### 시나리오 6: 쿼리 확장
```
- 사전조건: "정책" 쿼리
- 작업: expand-query로 확장
- 검증: 동의어 포함 (규정, 규칙 등), 가중치 적용
```

### 시나리오 7: 배치 검색
```
- 사전조건: 5개 쿼리
- 작업: batch-search로 한 번에 처리
- 검증: 모두 처리, 응답시간 50% 개선
```

### 시나리오 8: 스트리밍 검색
```
- 사전조건: 장시간 검색
- 작업: SSE 스트리밍 검색 요청
- 검증: 실시간 결과 수신, 타임아웃 없음
```

### 시나리오 9: 문서 전체 라이프사이클
```
- 작업:
  1. 문서 업로드
  2. 벡터 변환 및 저장
  3. 검색으로 조회 가능 확인
  4. 문서 업데이트
  5. 삭제
- 검증: 각 단계 성공, 최종 삭제 확인
```

### 시나리오 10: 에러 처리
```
- 작업:
  1. X-Tenant-ID 없이 요청
  2. 잘못된 필터 사용
  3. 존재하지 않는 문서 업데이트
- 검증: 적절한 HTTP 에러 코드 반환
```

## 테스트 환경

| 항목 | 값 |
|------|-----|
| 벡터DB | local_json (테스트용) |
| 테스트 데이터 | 50개 실제 PDF |
| 동시 사용자 | 최대 100명 |
| 목표 응답시간 | p99 <200ms |

## 성공 기준

- ✅ 10개 시나리오 모두 통과
- ✅ 응답시간 SLA 충족
- ✅ 데이터 무결성 보장
```

---

#### Task 2: 멀티테넌트 E2E 테스트 (3~4시간)

**파일**: `tests/e2e/test_multitenant_e2e.py` (신규)

**목표**: 멀티테넌트 격리 검증

**테스트**:
```python
class TestMultitenantE2E:
    """멀티테넌트 E2E 테스트"""
    
    def test_tenant_isolation_full_lifecycle(self, client):
        """테넌트 격리 전체 라이프사이클"""
        # 1. company_abc 문서 10개 업로드
        for i in range(10):
            client.post(
                "/api/v1/documents/upload",
                headers={"X-Tenant-ID": "company_abc"},
                files={"file": pdf_files[i]}
            )
        
        # 2. company_xyz 문서 5개 업로드
        for i in range(5):
            client.post(
                "/api/v1/documents/upload",
                headers={"X-Tenant-ID": "company_xyz"},
                files={"file": pdf_files[i]}
            )
        
        # 3. company_abc로 검색
        resp = client.post(
            "/api/v1/rag/search",
            headers={"X-Tenant-ID": "company_abc"},
            json={"query": "온톨로지"}
        )
        
        # 4. company_abc 문서만 반환 확인
        chunks = resp.json()["chunks"]
        doc_ids = [c["metadata"]["doc_id"] for c in chunks]
        # 모든 doc_id가 company_abc 소유 문서여야 함
        assert all(doc_id in company_abc_doc_ids for doc_id in doc_ids)
    
    def test_tenant_list_documents_isolation(self, client):
        """테넌트별 문서 목록 격리"""
        # company_abc 문서 목록
        resp_abc = client.get(
            "/api/v1/documents",
            headers={"X-Tenant-ID": "company_abc"}
        )
        abc_docs = len(resp_abc.json()["documents"])
        
        # company_xyz 문서 목록
        resp_xyz = client.get(
            "/api/v1/documents",
            headers={"X-Tenant-ID": "company_xyz"}
        )
        xyz_docs = len(resp_xyz.json()["documents"])
        
        # 각 테넌트는 자신의 문서만 보임
        assert abc_docs == 10
        assert xyz_docs == 5
    
    def test_tenant_cross_tenant_search_blocked(self, client):
        """크로스 테넌트 검색 차단"""
        # company_abc로 검색 후 company_xyz X-Tenant-ID로 요청하면
        # 전혀 다른 결과 반환 (또는 빈 결과)
        pass
    
    # 5개 테스트
```

---

#### Task 3: org_id 계층 E2E 테스트 (3~4시간)

**파일**: `tests/e2e/test_org_hierarchy_e2e.py` (신규)

**목표**: org_id 계층 권한 검증

**테스트**:
```python
class TestOrgHierarchyE2E:
    """org_id 계층 E2E 테스트"""
    
    def test_org_hierarchy_full_search(self, client):
        """조직 계층별 검색 권한"""
        # 사전조건: 3개 org_id 문서 (0100, 0101, 0102)
        
        # 팀원(0102) 검색 시:
        # - 0102 팀 문서 ✅
        # - 0100 부서 문서 ✅ (같은 부서)
        # - 전사공유(org_id="") ✅
        # - 0101 팀 문서 ❌ (다른 팀)
        
        resp = client.post(
            "/api/v1/rag/search",
            headers={
                "X-Tenant-ID": "company_abc",
                "X-Org-ID": "0102"
            },
            json={"query": "정책"}
        )
        
        doc_org_ids = [c["metadata"]["org_id"] for c in resp.json()["chunks"]]
        assert "0102" in doc_org_ids
        assert "0100" in doc_org_ids
        assert "" in doc_org_ids  # 전사공유
        assert "0101" not in doc_org_ids  # 다른 팀
    
    def test_org_hierarchy_department_level(self, client):
        """부서장 검색"""
        # 부서장(0100) 검색 시:
        # - 0100, 0101, 0102 모두 ✅
        # - 전사공유 ✅
        
        resp = client.post(
            "/api/v1/rag/search",
            headers={
                "X-Tenant-ID": "company_abc",
                "X-Org-ID": "0100"
            },
            json={"query": "정책"}
        )
        
        doc_org_ids = [c["metadata"]["org_id"] for c in resp.json()["chunks"]]
        assert all(
            org_id in ["0100", "0101", "0102", ""] 
            for org_id in doc_org_ids
        )
    
    # 5개 테스트
```

---

### Week 3 (Day 1-5): 품질 벤치마크 + 마이그레이션

#### Task 4: 검색 품질 벤치마크 (3~4시간)

**파일**: `tests/e2e/test_search_quality.py` (신규)

**목표**: 검색 정확도 측정 (샘플 쿼리 50개)

**구현**:
```python
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

class SearchQualityBenchmark:
    """검색 품질 벤치마크"""
    
    SAMPLE_QUERIES = [
        # 온톨로지 관련 (5개)
        {"query": "온톨로지", "expected_category": "기술"},
        {"query": "knowledge graph", "expected_category": "기술"},
        {"query": "semantic web", "expected_category": "기술"},
        {"query": "RDF", "expected_category": "기술"},
        {"query": "semantic relationship", "expected_category": "기술"},
        
        # HR 관련 (5개)
        {"query": "신입사원", "expected_category": "인사"},
        {"query": "채용 공고", "expected_category": "인사"},
        {"query": "급여 규정", "expected_category": "인사"},
        {"query": "복리후생", "expected_category": "인사"},
        {"query": "퇴직금", "expected_category": "인사"},
        
        # 규정 관련 (5개)
        {"query": "취업규칙", "expected_category": "규정"},
        {"query": "휴가 정책", "expected_category": "규정"},
        {"query": "근무시간", "expected_category": "규정"},
        {"query": "보안 규정", "expected_category": "규정"},
        {"query": "인사 평가", "expected_category": "규정"},
        
        # ... 50개 총
    ]
    
    def run_benchmark(self, client) -> dict:
        """벤치마크 실행"""
        results = []
        
        for test_case in self.SAMPLE_QUERIES:
            query = test_case["query"]
            expected = test_case["expected_category"]
            
            # 검색 실행
            resp = client.post(
                "/api/v1/rag/search",
                headers={"X-Tenant-ID": "company_abc"},
                json={"query": query, "limit": 10}
            )
            
            chunks = resp.json()["chunks"]
            
            # 상위 5개 중 expected 카테고리 문서 개수
            top_5_categories = [
                c["metadata"]["category_large"] for c in chunks[:5]
            ]
            
            hits = sum(1 for cat in top_5_categories if cat == expected)
            precision = hits / 5  # 상위 5개 중 정확한 카테고리
            
            results.append({
                "query": query,
                "expected": expected,
                "precision@5": precision,
                "chunks_returned": len(chunks)
            })
        
        # 통계
        df = pd.DataFrame(results)
        return {
            "avg_precision": df["precision@5"].mean(),
            "median_precision": df["precision@5"].median(),
            "coverage": (df["chunks_returned"] > 0).sum() / len(df),
            "results_by_category": df.groupby("expected")["precision@5"].mean().to_dict()
        }

def test_search_quality_benchmark(client):
    """검색 품질 벤치마크"""
    benchmark = SearchQualityBenchmark()
    results = benchmark.run_benchmark(client)
    
    # 기대값
    assert results["avg_precision"] >= 0.70  # 70% 이상
    assert results["coverage"] >= 0.95  # 95% 이상 결과 반환
```

**성능 목표**:
- ✅ 평균 Precision@5: ≥ 70%
- ✅ 결과 커버리지: ≥ 95%
- ✅ 카테고리별 정확도 측정

---

#### Task 5: v3→v4 마이그레이션 가이드 (2~3시간)

**파일**: `docs/MIGRATION_GUIDE.md` (신규)

**목표**: v3 사용자를 v4로 마이그레이션

**내용**:

```markdown
# v3 → v4 마이그레이션 가이드

## 주요 변경사항

### 호환성 변경 (Breaking Changes)
- ❌ 기존 `/api/v1/rag/search` 응답 형식 변경 없음 (호환)
- ✅ 신규 엔드포인트: `/api/v1/rag/rerank`, `/api/v1/rag/expand-query`, `/api/v1/rag/batch-search`
- ✅ 신규 필터: `filters` 파라미터 추가 (선택)

### API 호환성

| API | v3 | v4 | 비고 |
|-----|----|----|------|
| POST /search | ✅ | ✅ | 호환 |
| POST /batch-search | ❌ | ✅ | 신규 |
| POST /rerank | ❌ | ✅ | 신규 |
| POST /expand-query | ❌ | ✅ | 신규 |
| GET /documents | ✅ | ✅ | 호환 |

### 성능 개선

| 지표 | v3 | v4 | 개선율 |
|------|----|----|--------|
| 응답시간 (p99) | 250ms | <200ms | 20% ↓ |
| 캐시 hit rate | 미지원 | 70%+ | 신규 |
| 배치 쿼리 효율 | 순차 처리 | 50% ↓ | 신규 |
| 청크 품질 | 50자 | 500자+ | 10배 ↑ |

## 마이그레이션 절차

### 1단계: v4 배포 (병렬 운영)
```bash
# v3과 v4 동시 운영
# v3: port 8000
# v4: port 9000

# 트래픽 점진적 이동:
# Day 1: 5% → v4
# Day 2: 10%
# Day 3: 25%
# Day 4: 50%
# Day 5: 100%
```

### 2단계: 데이터 마이그레이션
```bash
# v3 벡터DB → v4 벡터DB 복사
# metadata.db 마이그레이션
# 정합성 검증
```

### 3단계: 롤백 계획
```
만약 문제 발생 시:
1. 트래픽 즉시 v3로 회귀
2. v3 데이터 복구 (백업 사용)
3. 원인 분석 후 v4 수정
```

## 사용자 가이드

### v3 코드에서 v4로 업그레이드 (선택사항)

```python
# v3 (기존 - 계속 사용 가능)
response = requests.post(
    "http://localhost:9000/api/v1/rag/search",
    headers={"X-Tenant-ID": "company_abc"},
    json={"query": "온톨로지"}
)

# v4 (신규 기능 사용)
# 1. 쿼리 확장 사용
expand_resp = requests.post(
    "http://localhost:9000/api/v1/rag/expand-query",
    headers={"X-Tenant-ID": "company_abc"},
    json={"query": "온톨로지"}
)
expanded_queries = [q["query"] for q in expand_resp.json()["expanded_queries"]]

# 2. 배치 검색 (효율 50% 향상)
batch_resp = requests.post(
    "http://localhost:9000/api/v1/rag/batch-search",
    headers={"X-Tenant-ID": "company_abc"},
    json={
        "queries": [
            {"query": q} for q in expanded_queries
        ]
    }
)

# 3. 결과 재순위화
rerank_resp = requests.post(
    "http://localhost:9000/api/v1/rag/rerank",
    headers={"X-Tenant-ID": "company_abc"},
    json={
        "query": "온톨로지",
        "chunks": batch_resp.json()["results"][0]["chunks"]
    }
)
```

## FAQ

### Q1: v3 데이터는 v4에서 사용 가능?
**A**: 네, v4는 v3 벡터DB와 호환됩니다. 마이그레이션 가이드 2단계 참고.

### Q2: 응답 형식이 변경되나?
**A**: 기존 API는 100% 호환입니다. 신규 기능만 추가되었습니다.

### Q3: 롤백 가능한가?
**A**: 네, 3단계 롤백 계획을 참고하세요.
```

---

#### Task 6: CI/CD 파이프라인 초안 (2~3시간)

**파일**: `.github/workflows/ci.yml` (신규)

**목표**: 자동화된 테스트 및 배포

**GitHub Actions Workflow**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Run E2E tests
      run: |
        pytest tests/e2e/ -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t rag-v4:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        docker tag rag-v4:${{ github.sha }} rag-v4:latest
        # Push to ECR or DockerHub

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # 배포 스크립트 (선택사항)
        echo "Deploying v4..."
```

---

## 📊 완료 기준

```
✅ Task 1: E2E 테스트 설계
  - test_plan.md 완성 (10개 시나리오)
  - 테스트 환경 명시
  - 성공 기준 정의

✅ Task 2: 멀티테넌트 E2E 테스트
  - test_multitenant_e2e.py 완성
  - 5개 E2E 테스트 통과

✅ Task 3: org_id 계층 E2E 테스트
  - test_org_hierarchy_e2e.py 완성
  - 5개 E2E 테스트 통과

✅ Task 4: 검색 품질 벤치마크
  - 50개 샘플 쿼리로 측정
  - Precision@5 ≥ 70%
  - 커버리지 ≥ 95%

✅ Task 5: v3→v4 마이그레이션 가이드
  - MIGRATION_GUIDE.md 완성
  - Breaking Changes 명시
  - 롤백 계획 수립

✅ Task 6: CI/CD 파이프라인
  - ci.yml 초안 완성
  - Test → Build → Deploy 자동화

✅ 전체: 15개 E2E 테스트 통과
✅ 테스트 커버리지: ≥ 80%
✅ 문서 완성도: 100%
```

---

## 📁 디렉토리 구조

```
src_claud/v4/
├── tests/
│   ├── e2e/
│   │   ├── __init__.py
│   │   ├── test_plan.md           ← 신규 (계획 문서)
│   │   ├── test_multitenant_e2e.py     ← 신규 (5 테스트)
│   │   ├── test_org_hierarchy_e2e.py   ← 신규 (5 테스트)
│   │   └── test_search_quality.py      ← 신규 (벤치마크)
├── docs/
│   ├── API_v4_DESIGN.md
│   ├── MIGRATION_GUIDE.md         ← 신규
│   ├── DEPLOYMENT.md              ← 신규
│   └── USER_GUIDE.md              ← 신규
├── .github/
│   └── workflows/
│       └── ci.yml                 ← 신규 (CI/CD)
└── scripts/
    └── migrate_v3_to_v4.py        ← 신규 (마이그레이션 스크립트)
```

---

## 🚀 실행 순서

1. **Task 1: E2E 테스트 설계** (2~3시간)
2. **Task 2: 멀티테넌트 E2E** (3~4시간)
3. **Task 3: org_id 계층 E2E** (3~4시간)
4. **Task 4: 품질 벤치마크** (3~4시간)
5. **Task 5: 마이그레이션 가이드** (2~3시간)
6. **Task 6: CI/CD 파이프라인** (2~3시간)

---

**예상 완료**: 2026-06-21  
**최종 검증**: 15개 E2E 테스트 통과 + 문서 완성  
**다음**: Week 4 통합 및 최종 배포

