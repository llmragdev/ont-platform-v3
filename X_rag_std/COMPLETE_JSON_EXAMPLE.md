# RAG 검색 응답 완전 예제

## 검색 요청 (POST /api/rag/search)

```json
{
  "query": "2026년 인사 규정 알려줘",
  "top_k": 5,
  "debug_mode": true,
  "filters": {
    "category_large": "인사",
    "category_mid": "채용",
    "vector_db_id": "vdb_hr_recruit_01"
  }
}
```

---

## 검색 응답 - 성공 (status: "success")

### ✅ 성공 응답 예제 (debug_mode: true)

```json
{
  "status": "success",
  "data": {
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면 신입 채용 시 기본급은 연봉 3,000만 원 이상이며, 복리후생으로는 4대 보험과 퇴직금이 보장됩니다.",
    "used_chunks": [
      {
        "chunk_id": "doc_a1b2c3d4#chunk4",
        "content": "2026년 인사 규정 제3조 - 신입 채용 기본급\n신입 사원의 기본급은 학위 및 경력에 따라 다음과 같이 책정한다.\n- 학사 학위: 연 3,000만 원 이상\n- 석사 학위: 연 3,500만 원 이상\n- 박사 학위: 연 4,000만 원 이상",
        "similarity_score": 0.92,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 12,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      },
      {
        "chunk_id": "doc_a1b2c3d4#chunk5",
        "content": "2026년 인사 규정 제5조 - 복리후생\n모든 정규직 사원에게 다음의 복리후생을 제공한다.\n1) 4대 보험: 국민연금, 건강보험, 고용보험, 산재보험\n2) 퇴직금: 근속년수 1년 이상 시 월급의 30일분 이상\n3) 휴가: 연 15일의 유급휴가",
        "similarity_score": 0.88,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 15,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      },
      {
        "chunk_id": "doc_a1b2c3d4#chunk6",
        "content": "2026년 인사 규정 제8조 - 신입 연수 프로그램\n신입 사원은 입사 후 2주간의 필수 연수를 이수해야 한다.\n- 1주차: 회사 문화 및 기본 교육\n- 2주차: 부서별 OJT 및 실무 교육",
        "similarity_score": 0.76,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 18,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      }
    ],
    "debug_info": {
      "execution_time_ms": 145,
      "candidate_chunks": [
        {
          "chunk_id": "doc_a1b2c3d4#chunk2",
          "content": "2026년 인사 규정 제1조 - 목적\n본 규정은 회사의 인사 관리에 관한 기본 사항을 정함을 목적으로 한다.",
          "similarity_score": 0.62,
          "metadata": {
            "source_name": "2026_인사규정.pdf",
            "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
            "page_no": 1,
            "category_large": "인사",
            "category_mid": "일반",
            "vector_db_id": "vdb_hr_recruit_01",
            "tenant_id": "company_abc",
            "org_id": "0102",
            "dept_code": "01"
          }
        },
        {
          "chunk_id": "doc_a1b2c3d4#chunk7",
          "content": "2026년 인사 규정 제10조 - 성과 평가\n정규직 사원의 성과 평가는 연 2회 실시하며, 평가 결과에 따라 보상이 결정된다.",
          "similarity_score": 0.58,
          "metadata": {
            "source_name": "2026_인사규정.pdf",
            "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
            "page_no": 22,
            "category_large": "인사",
            "category_mid": "평가",
            "vector_db_id": "vdb_hr_recruit_01",
            "tenant_id": "company_abc",
            "org_id": "0102",
            "dept_code": "01"
          }
        },
        {
          "chunk_id": "doc_a1b2c3d4#chunk12",
          "content": "2026년 인사 규정 제12조 - 근로 시간\n근로 시간은 주 40시간을 기준으로 하며, 주 5일(월~금) 근무 체제를 따른다.",
          "similarity_score": 0.54,
          "metadata": {
            "source_name": "2026_인사규정.pdf",
            "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
            "page_no": 25,
            "category_large": "인사",
            "category_mid": "근로",
            "vector_db_id": "vdb_hr_recruit_01",
            "tenant_id": "company_abc",
            "org_id": "0102",
            "dept_code": "01"
          }
        }
      ]
    }
  },
  "error": null
}
```

---

### ✅ 성공 응답 예제 (debug_mode: false)

```json
{
  "status": "success",
  "data": {
    "query": "2026년 인사 규정 알려줘",
    "answer": "2026년 인사 규정에 따르면 신입 채용 시 기본급은 연봉 3,000만 원 이상이며, 복리후생으로는 4대 보험과 퇴직금이 보장됩니다.",
    "used_chunks": [
      {
        "chunk_id": "doc_a1b2c3d4#chunk4",
        "content": "2026년 인사 규정 제3조 - 신입 채용 기본급\n신입 사원의 기본급은 학위 및 경력에 따라 다음과 같이 책정한다.\n- 학사 학위: 연 3,000만 원 이상\n- 석사 학위: 연 3,500만 원 이상\n- 박사 학위: 연 4,000만 원 이상",
        "similarity_score": 0.92,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 12,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      },
      {
        "chunk_id": "doc_a1b2c3d4#chunk5",
        "content": "2026년 인사 규정 제5조 - 복리후생\n모든 정규직 사원에게 다음의 복리후생을 제공한다.\n1) 4대 보험: 국민연금, 건강보험, 고용보험, 산재보험\n2) 퇴직금: 근속년수 1년 이상 시 월급의 30일분 이상\n3) 휴가: 연 15일의 유급휴가",
        "similarity_score": 0.88,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 15,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      },
      {
        "chunk_id": "doc_a1b2c3d4#chunk6",
        "content": "2026년 인사 규정 제8조 - 신입 연수 프로그램\n신입 사원은 입사 후 2주간의 필수 연수를 이수해야 한다.\n- 1주차: 회사 문화 및 기본 교육\n- 2주차: 부서별 OJT 및 실무 교육",
        "similarity_score": 0.76,
        "metadata": {
          "source_name": "2026_인사규정.pdf",
          "source_url": "https://storage.example.com/docs/2026_인사규정.pdf",
          "page_no": 18,
          "category_large": "인사",
          "category_mid": "채용",
          "vector_db_id": "vdb_hr_recruit_01",
          "tenant_id": "company_abc",
          "org_id": "0102",
          "dept_code": "01"
        }
      }
    ],
    "debug_info": {
      "execution_time_ms": 145,
      "candidate_chunks": []
    }
  },
  "error": null
}
```

---

## 검색 응답 - 실패 (status: "error")

### ❌ 오류: 벡터 DB를 찾을 수 없음

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "VECTOR_DB_NOT_FOUND",
    "message": "지정한 벡터 DB(vdb_hr_recruit_01)를 찾을 수 없습니다."
  }
}
```

### ❌ 오류: 검색 쿼리 필드 누락

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "필수 필드 'query'가 누락되었습니다."
  }
}
```

### ❌ 오류: 카테고리 필터 오류

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_CATEGORY",
    "message": "필터 'filters.category_large'의 값이 유효하지 않습니다. 허용된 값: 인사, 규정, 기술, 재무"
  }
}
```

### ❌ 오류: 벡터화 실패

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "EMBEDDING_FAILED",
    "message": "쿼리 벡터화 중 오류 발생: 임베딩 서버가 응답하지 않습니다."
  }
}
```

### ❌ 오류: 검색 결과 없음

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "NO_RESULTS",
    "message": "검색 쿼리와 일치하는 문서를 찾을 수 없습니다."
  }
}
```

---

## 📊 응답 필드 매핑

### 성공 응답 필드 분포

| 섹션 | 필드 | 데이터 타입 | 예시 | 설명 |
|------|------|-----------|------|------|
| **루트** | status | String | "success" | 응답 상태 |
| **루트** | error | null | null | 성공 시 null |
| **data** | query | String | "2026년 인사 규정 알려줘" | 사용자 입력 쿼리 |
| **data** | answer | String | "2026년 인사 규정에 따르면..." | LLM 생성 답변 |
| **used_chunks[]** | chunk_id | String | "doc_a1b2c3d4#chunk4" | 청크 고유 ID |
| **used_chunks[]** | content | String | "2026년 인사 규정 제3조..." | 청크 원문 |
| **used_chunks[]** | similarity_score | Float | 0.92 | 유사도 점수 |
| **metadata** | source_name | String | "2026_인사규정.pdf" | 원본 파일명 |
| **metadata** | source_url | String | "https://storage.example.com/..." | 저장소 URL |
| **metadata** | page_no | Integer | 12 | 페이지 번호 |
| **metadata** | category_large | String | "인사" | 대분류 |
| **metadata** | category_mid | String | "채용" | 중분류 |
| **metadata** | vector_db_id | String | "vdb_hr_recruit_01" | 벡터DB ID |
| **metadata** | tenant_id | String | "company_abc" | 테넌트 ID |
| **metadata** | org_id | String | "0102" | 조직 코드 |
| **metadata** | dept_code | String | "01" | 부서 코드 |
| **debug_info** | execution_time_ms | Integer | 145 | API 응답 시간 |
| **debug_info** | candidate_chunks[] | Array | [...] | 미채택 청크 (debug_mode=true 시만) |

### 실패 응답 필드 분포

| 필드 | 데이터 타입 | 예시 | 설명 |
|------|-----------|------|------|
| status | String | "error" | 응답 상태 |
| data | null | null | 에러 시 null |
| error.code | String | "VECTOR_DB_NOT_FOUND" | 에러 코드 |
| error.message | String | "지정한 벡터 DB를 찾을 수 없습니다." | 에러 메시지 |

---

## 🔑 주요 특징

### 1. used_chunks 배열
- **복수 청크**: 3개 청크 포함하여 배열 특성 표현
- **내림차순 정렬**: similarity_score 기준으로 정렬 (0.92 → 0.88 → 0.76)
- **모든 필드**: 각 청크마다 모든 metadata 필드 포함

### 2. candidate_chunks 배열
- **조건부**: debug_mode=true 시에만 포함
- **실제 청크**: 주석 대신 실제 청크 객체들의 배열
- **유사도 기준**: used_chunks보다 낮은 유사도 점수

### 3. 다양한 에러 케이스
- 벡터 DB 미존재
- 필수 필드 누락
- 잘못된 카테고리
- 임베딩 실패
- 검색 결과 없음

---

## ✅ 검증 체크리스트

- [x] 모든 18개 필드가 응답에 포함됨
- [x] used_chunks가 배열로 여러 청크 포함
- [x] candidate_chunks가 실제 청크 객체 배열
- [x] debug_mode에 따른 조건부 필드 처리
- [x] 에러 응답 케이스별 예시 제공
- [x] 모든 metadata 필드 각 청크에 포함
- [x] 유사도 점수가 내림차순 정렬
