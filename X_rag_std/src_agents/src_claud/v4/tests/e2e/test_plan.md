# E2E 테스트 계획 (v4)

**버전**: v4  
**작성일**: 2026-05-25  
**담당**: Codex Agent (통합 & QA)  
**목표**: 전체 워크플로우 및 신규 기능 검증

---

## 테스트 시나리오 (10개 이상)

### 시나리오 1: 단일 테넌트 기본 검색

**사전조건**:
- 테넌트: `company_abc`
- 문서 2개 업로드 (온톨로지 관련)

**작업 흐름**:
1. PDF 파일 업로드 → 벡터 변환 및 저장
2. "온톨로지" 키워드로 검색
3. 결과 확인

**검증 항목**:
- ✅ 문서가 정상 업로드됨 (doc_id 반환)
- ✅ 관련 문서가 검색 결과에 포함됨
- ✅ 응답시간 < 200ms
- ✅ 응답 형식 정상 (chunks, metadata 포함)

**예상 결과**:
```json
{
  "chunks": [
    {
      "chunk_id": "...",
      "text": "온톨로지는...",
      "metadata": {
        "doc_id": "...",
        "tenant_id": "company_abc",
        "category_large": "기술"
      }
    }
  ],
  "total_chunks": 2
}
```

---

### 시나리오 2: 멀티테넌트 격리

**사전조건**:
- 테넌트 A (`company_abc`): 5개 문서 업로드
- 테넌트 B (`company_xyz`): 5개 문서 업로드
- 모두 같은 "정책" 키워드 포함

**작업 흐름**:
1. 테넌트 A로 "정책" 검색
2. 결과의 모든 doc_id가 A 소유 확인
3. 테넌트 B로 동일 검색
4. 결과의 모든 doc_id가 B 소유 확인

**검증 항목**:
- ✅ 테넌트 A 검색 시 A 문서만 반환 (B 문서 제외)
- ✅ 테넌트 B 검색 시 B 문서만 반환 (A 문서 제외)
- ✅ 데이터 누수 없음 (cross-tenant 검색 차단)

**예상 결과**:
```
테넌트 A 검색:
- chunks[0].metadata.tenant_id == "company_abc"
- chunks[1].metadata.tenant_id == "company_abc"
- ...
- 모든 doc_id ∈ A의 문서 목록

테넌트 B 검색:
- chunks[0].metadata.tenant_id == "company_xyz"
- chunks[1].metadata.tenant_id == "company_xyz"
- ...
- 모든 doc_id ∈ B의 문서 목록
```

---

### 시나리오 3: org_id 계층 접근 (팀원 권한)

**사전조건**:
- 테넌트: `company_abc`
- org_id별 문서:
  - `"0100"` (부서): 3개 문서
  - `"0101"` (팀1): 3개 문서
  - `"0102"` (팀2): 3개 문서
  - `""` (전사 공유): 2개 문서

**작업 흐름**:
1. X-Org-ID: `"0102"` (팀2 멤버) 로 "정책" 검색
2. 반환된 doc의 org_id 확인

**검증 항목**:
- ✅ 0102 팀 문서 포함 (자신의 조직)
- ✅ 0100 부서 문서 포함 (상위 조직)
- ✅ 전사 공유("") 문서 포함
- ✅ 0101 팀 문서는 제외 (권한 없음)

**예상 결과**:
```json
{
  "chunks": [
    {
      "text": "...",
      "metadata": {"org_id": "0102"}  // ✅
    },
    {
      "text": "...",
      "metadata": {"org_id": "0100"}  // ✅
    },
    {
      "text": "...",
      "metadata": {"org_id": ""}  // ✅ (전사 공유)
    }
  ],
  "total_chunks": 8  // 0102(3) + 0100(3) + 전사(2)
}
```

---

### 시나리오 4: org_id 계층 접근 (부서장 권한)

**사전조건**:
- 테넌트: `company_abc`
- org_id별 문서: 시나리오 3 동일

**작업 흐름**:
1. X-Org-ID: `"0100"` (부서장) 로 "정책" 검색
2. 반환된 doc의 org_id 확인

**검증 항목**:
- ✅ 0100 부서 문서 포함
- ✅ 0101, 0102 팀 문서 포함 (하위 조직)
- ✅ 전사 공유("") 문서 포함
- ✅ 모든 계층의 문서 조회 가능

**예상 결과**:
```
총 11개 반환 (0100(3) + 0101(3) + 0102(3) + 전사(2))
```

---

### 시나리오 5: 다중 필터 조합

**사전조건**:
- 테넌트: `company_abc`
- 다양한 카테고리/날짜 문서 20개:
  - category_large: "인사", "기술", "규정" (각 7개)
  - 날짜: 2026-01-01 ~ 2026-05-25

**작업 흐름**:
1. "채용" 검색 + category_large="인사" AND date_from=2026-03-01 필터
2. 결과 확인

**검증 항목**:
- ✅ category_large="인사" 문서만 반환
- ✅ date >= 2026-03-01 문서만 반환
- ✅ 검색어 "채용"과 관련된 문서 상위 반환
- ✅ 필터 조건 모두 만족하는 문서만 반환

**예상 결과**:
```
인사 카테고리 + 2026-03-01 이후 문서만 반환
category_large="인사" AND date >= 2026-03-01 검증
```

---

### 시나리오 6: 재순위화 (Reranking)

**사전조건**:
- 기본 검색으로 10개 결과 획득

**작업 흐름**:
1. POST /api/v1/rag/search → chunks 획득
2. POST /api/v1/rag/rerank → 재순위화
3. 순서 변경 확인

**검증 항목**:
- ✅ 재순위화 전후 순서가 변경됨
- ✅ 관련성 점수 재계산 (relevance_score 변경)
- ✅ 동일한 chunks 반환 (순서만 변경)
- ✅ 응답시간 < 100ms

**예상 결과**:
```json
{
  "chunks": [
    {
      "chunk_id": "...",
      "relevance_score": 0.95,  // 재계산됨
      "rerank_position": 1
    },
    {
      "chunk_id": "...",
      "relevance_score": 0.87,
      "rerank_position": 2
    }
  ]
}
```

---

### 시나리오 7: 쿼리 확장 (Query Expansion)

**사전조건**:
- 쿼리: "정책"

**작업 흐름**:
1. POST /api/v1/rag/expand-query → 확장된 쿼리 획득
2. 동의어/유사어 확인

**검증 항목**:
- ✅ 원본 쿼리 포함
- ✅ 동의어 포함 (예: "규정", "규칙")
- ✅ 확장 쿼리 최소 3개 이상
- ✅ 가중치 (weight) 설정 (원본 > 동의어)

**예상 결과**:
```json
{
  "original_query": "정책",
  "expanded_queries": [
    {"query": "정책", "weight": 1.0},
    {"query": "규정", "weight": 0.8},
    {"query": "규칙", "weight": 0.7},
    {"query": "지침", "weight": 0.6}
  ]
}
```

---

### 시나리오 8: 배치 검색 (Batch Search)

**사전조건**:
- 5개 검색 쿼리

**작업 흐름**:
1. POST /api/v1/rag/batch-search (5개 쿼리 한 번에)
2. 응답시간 측정
3. 각 쿼리 결과 확인

**검증 항목**:
- ✅ 모든 5개 쿼리 처리 완료
- ✅ 순차 검색 대비 응답시간 50% 이상 개선
- ✅ 각 쿼리 결과 독립적 (간섭 없음)
- ✅ 응답 형식: results[0], results[1], ... results[4]

**예상 결과**:
```json
{
  "results": [
    {
      "query": "온톨로지",
      "chunks": [...],
      "total_chunks": 5
    },
    {
      "query": "채용",
      "chunks": [...],
      "total_chunks": 3
    },
    ...
  ],
  "processing_time_ms": 150
}
```

**성능 목표**:
- 단일 검색 × 5 = ~600ms
- 배치 검색 = ~300ms (50% 개선)

---

### 시나리오 9: 문서 전체 라이프사이클

**사전조건**:
- 테넌트: `company_abc`
- 테스트 PDF 파일 1개

**작업 흐름**:
1. 문서 업로드 (POST /documents/upload)
2. 벡터 변환 및 저장 (자동)
3. 검색으로 조회 가능 확인
4. 메타데이터 업데이트
5. 문서 삭제 (DELETE)

**검증 항목**:
1. **업로드**: 
   - ✅ 200 응답, doc_id 반환
   - ✅ 저장소에 파일 존재

2. **벡터 저장**:
   - ✅ 청크 생성됨
   - ✅ 임베딩 변환 완료
   - ✅ 벡터DB 저장됨

3. **검색 가능**:
   - ✅ 업로드된 문서의 키워드로 검색 가능
   - ✅ 정확한 doc_id 반환

4. **메타데이터 업데이트**:
   - ✅ PUT /documents/{doc_id} 성공
   - ✅ category_large, category_mid 변경
   - ✅ 검색 결과 업데이트 확인

5. **삭제**:
   - ✅ DELETE /documents/{doc_id} 200 응답
   - ✅ 검색 불가능 확인
   - ✅ 저장소에서 제거

**예상 결과**:
```
1. POST /documents/upload → {"doc_id": "abc123"}
2. (자동 벡터 변환)
3. POST /search → chunks 포함 확인
4. PUT /documents/abc123 → 200 성공
5. DELETE /documents/abc123 → 204 성공
6. POST /search → 삭제된 doc_id 제외
```

---

### 시나리오 10: 에러 처리

**작업 흐름**:

#### 10-A: X-Tenant-ID 누락

```bash
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "온톨로지"}'
```

**검증**: 
- ✅ 400 Bad Request 반환
- ✅ 에러 메시지: "X-Tenant-ID is required"

#### 10-B: 잘못된 필터 사용

```bash
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "X-Tenant-ID: company_abc" \
  -d '{"query": "온톨로지", "filters": {"invalid_field": "value"}}'
```

**검증**:
- ✅ 400 Bad Request 반환
- ✅ 에러 메시지: "Invalid filter field"

#### 10-C: 존재하지 않는 문서 업데이트

```bash
curl -X PUT http://localhost:8000/api/v1/documents/nonexistent_id \
  -H "X-Tenant-ID: company_abc" \
  -d '{"category_large": "인사"}'
```

**검증**:
- ✅ 404 Not Found 반환
- ✅ 에러 메시지: "Document not found"

#### 10-D: 서버 에러 (예: 벡터DB 연결 실패)

**검증**:
- ✅ 500 Internal Server Error 반환
- ✅ 에러 메시지: "Vector DB connection failed"

---

## 테스트 환경

| 항목 | 값 | 설명 |
|------|-----|------|
| **벡터 DB 엔진** | `local_json` (기본) | 테스트 시 파일 기반 저장 |
| **LLM 프로바이더** | `gemini_http` | 쿼리 확장, 재순위화용 LLM |
| **테스트 데이터** | 50개 실제 PDF | AI Lab 제공 + 합성 데이터 |
| **동시 사용자** | 최대 100명 (시뮬레이션) | 부하 테스트 단계 |
| **응답시간 SLA** | p99 < 200ms | 성능 목표 |
| **테스트 데이터 보관** | `tests/e2e/data/` | 공유 테스트 파일 |

---

## 성공 기준

### 기능 검증
- ✅ 시나리오 1-10 모두 통과
- ✅ 응답 형식 정상 (JSON 스키마 준수)
- ✅ 데이터 무결성 보장 (조직별 격리)

### 성능 목표
- ✅ 평균 응답시간 < 150ms
- ✅ p99 응답시간 < 200ms
- ✅ 배치 검색 순차 대비 50% 이상 개선

### 안정성
- ✅ 에러 처리 정상 (400, 404, 500)
- ✅ 데이터 누수 없음 (멀티테넌트 격리)
- ✅ 응답 일관성 (재실행 시 동일 결과)

---

## 테스트 실행 계획

### Week 2 (2026-06-08 ~ 2026-06-14)

1. **Task 1 (이 문서)**: 테스트 계획 수립 ✅
2. **Task 2**: test_multitenant_e2e.py 작성 (시나리오 2, 멀티테넌트)
3. **Task 3**: test_org_hierarchy_e2e.py 작성 (시나리오 3, 4)

### Week 3 (2026-06-15 ~ 2026-06-21)

4. **Task 4**: test_search_quality.py 작성 (벤치마크 50개 쿼리)
5. **Task 5**: MIGRATION_GUIDE.md 작성 (v3→v4)
6. **Task 6**: CI/CD 파이프라인 (.github/workflows/ci.yml)

---

## 참고 자료

| 문서 | 용도 |
|------|------|
| RAG_표준_설계_v1.6.md | 설계 기준 |
| README.md (v4) | API 엔드포인트 명세 |
| test_multitenant_org_hierarchy.py | 기존 단위 테스트 참고 |

---

**작성**: Codex Agent (2026-05-25)  
**다음 단계**: Task 2 - 멀티테넌트 E2E 테스트 (test_multitenant_e2e.py)
