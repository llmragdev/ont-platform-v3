# 검색 응답 명세 업데이트

**파일**: `E:\ontology_edu\X_rag_std\zz-표준 설계\RAG 개발 가이드_v1.1.docx`  
**업데이트 완료**: 2026-05-18  
**섹션**: "검색 응답 주요 필드" 표

---

## 📋 업데이트 개요

### 배경
문서의 "검색 응답 주요 필드" 표가 실제 JSON 응답 예시와 맞지 않아 일관성 문제 발생.  
표에는 8개 필드만 정의되어 있었으나, JSON 예시에는 18개의 필드가 포함됨.

### 목표
JSON 응답 예시를 **명확한 표준 사양(Authoritative Specification)**으로 정의하고,  
문서의 표를 이에 맞게 완전히 업데이트.

---

## 🔄 변경 사항

### 이전 표 (8개 필드)
```
| 필드명 | 타입 | 설명 |
|--------|------|------|
| data.answer | String | ... |
| data.used_chunks[].chunk_id | String | ... |
| data.used_chunks[].content | String | ... |
| data.used_chunks[].similarity_score | Float | ... |
| data.used_chunks[].metadata.source_url | String | ... |
| data.used_chunks[].metadata.page_no | Integer | ... |
| data.debug_info | Object | ... |
```

### 새로운 표 (18개 필드)
```
| 필드명 | 타입 | 설명 |
|--------|------|------|
| status | String | 응답 상태: "success" 또는 "error" |
| error | Object\|null | 오류 발생 시: {code, message} 또는 null |
| data.query | String | 사용자가 입력한 검색 쿼리 |
| data.answer | String | LLM이 생성한 답변 텍스트 |
| data.used_chunks[].chunk_id | String | 청크 고유 ID (doc_id#chunkN 형식) |
| data.used_chunks[].content | String | LLM이 채택한 청크 원문 |
| data.used_chunks[].similarity_score | Float | 벡터 유사도 점수 (0.0~1.0) |
| data.used_chunks[].metadata.source_name | String | 원본 파일명 |
| data.used_chunks[].metadata.source_url | String | 문서 저장소 URL |
| data.used_chunks[].metadata.page_no | Integer | 원본 파일 내 페이지 번호 |
| data.used_chunks[].metadata.category_large | String | 대분류 (예: 인사, 규정, 기술) |
| data.used_chunks[].metadata.category_mid | String | 중분류 (벡터DB 라우팅 기준) |
| data.used_chunks[].metadata.vector_db_id | String | 벡터DB 식별자 |
| data.used_chunks[].metadata.tenant_id | String | 다중테넌트 격리용 테넌트 ID |
| data.used_chunks[].metadata.org_id | String | 조직 계층 코드 |
| data.used_chunks[].metadata.dept_code | String | 부서 코드 |
| data.debug_info.execution_time_ms | Integer | API 응답 시간 (밀리초) |
| data.debug_info.candidate_chunks | Array | 미채택 청크 목록 |
```

---

## ✅ 추가된 필드 (10개)

| # | 필드명 | 카테고리 | 설명 |
|----|--------|---------|------|
| 1 | status | 루트 | HTTP 응답 상태 명시 |
| 2 | error | 루트 | 오류 처리 (null 또는 {code, message}) |
| 3 | data.query | 응답 데이터 | 사용자 입력 쿼리 반향 |
| 4 | data.used_chunks[].metadata.source_name | 메타데이터 | 원본 파일명 (URL과 중복 제거용) |
| 5 | data.used_chunks[].metadata.category_large | 메타데이터 | 대분류 카테고리 |
| 6 | data.used_chunks[].metadata.category_mid | 메타데이터 | 중분류 카테고리 (라우팅 기준) |
| 7 | data.used_chunks[].metadata.vector_db_id | 메타데이터 | 청크를 저장한 벡터DB 식별 |
| 8 | data.used_chunks[].metadata.tenant_id | 메타데이터 | 테넌트 격리 (SaaS 시스템) |
| 9 | data.used_chunks[].metadata.org_id | 메타데이터 | 조직 계층 코드 |
| 10 | data.used_chunks[].metadata.dept_code | 메타데이터 | 부서 코드 |

> **참고**: `data.debug_info.execution_time_ms`와 `data.debug_info.candidate_chunks`의 상세 필드도 별도 행으로 추가

---

## 📊 필드 구성 분석

### 계층별 분포

```
응답 구조 (Response Structure)
├── 루트 레벨 (Root Level) - 2개
│   ├── status ......................... 응답 상태
│   └── error .......................... 오류 정보
│
├── data 레벨 (Main Response Data) - 3개
│   ├── query .......................... 입력 쿼리
│   ├── answer ......................... 생성 답변
│   └── used_chunks[] .................. 인용 청크 배열
│
├── used_chunks[] 레벨 - 4개
│   ├── chunk_id ....................... 청크 ID
│   ├── content ........................ 청크 원문
│   ├── similarity_score ............... 유사도
│   └── metadata ....................... 메타데이터
│
├── metadata 레벨 - 10개
│   ├── source_name .................... 파일명
│   ├── source_url ..................... 저장소 URL
│   ├── page_no ........................ 페이지 번호
│   ├── category_large ................. 대분류
│   ├── category_mid ................... 중분류
│   ├── vector_db_id ................... 벡터DB ID
│   ├── tenant_id ...................... 테넌트 ID
│   ├── org_id ......................... 조직 코드
│   └── dept_code ...................... 부서 코드
│
└── debug_info 레벨 - 2개 (debug_mode: true 시에만)
    ├── execution_time_ms .............. 응답 시간
    └── candidate_chunks ............... 후보 청크
```

### 용도별 분류

**1. 시스템 응답 (2개)**: status, error
**2. 비즈니스 응답 (3개)**: query, answer, used_chunks
**3. 벡터 검색 데이터 (1개)**: similarity_score
**4. 문서 추적 (2개)**: source_name, source_url, page_no
**5. 분류 정보 (2개)**: category_large, category_mid
**6. 라우팅 (1개)**: vector_db_id
**7. 테넌트/조직 격리 (3개)**: tenant_id, org_id, dept_code
**8. 디버깅 (2개)**: execution_time_ms, candidate_chunks

---

## 🎯 권장 사항

### 1. API 응답 구현
표에 정의된 모든 필드를 JSON 응답에 포함하여 클라이언트와 통합 문서 간 일관성 유지.

### 2. 선택적 필드 처리
- **필수 필드** (항상 포함):
  - status, error
  - data.query, data.answer
  - data.used_chunks[].chunk_id, content, similarity_score, metadata

- **조건부 필드**:
  - debug_info.* → debug_mode: true 시에만 포함

### 3. 클라이언트 문서
API 클라이언트 가이드에도 이 표를 참조하여 응답 파싱 로직 구현.

---

## ✨ 개선 효과

| 항목 | 이전 | 이후 | 효과 |
|------|------|------|------|
| **명세 완전성** | 8개 필드 | 18개 필드 | 100% 커버리지 |
| **일관성** | JSON과 표 불일치 | 완전 일치 | 혼란 제거 |
| **가독성** | 필드 목록만 존재 | 필드 + 설명 | 이해도 향상 |
| **추적 가능성** | 제한적 메타데이터 | 풍부한 메타데이터 | 감시/분석 용이 |
| **테넌트 격리** | 정의 없음 | 명시적 정의 | SaaS 호환 |

---

## 📁 관련 파일

- **수정 대상**: `E:\ontology_edu\X_rag_std\zz-표준 설계\RAG 개발 가이드_v1.1.docx`
- **검증 스크립트**: 
  - `update_search_response_table.py` (표 내용 업데이트)
  - `verify_search_response_table.py` (포맷팅 확인)

---

## 🔗 연관 문서

- JSON 응답 예시: `E:\ontology_edu\X_rag_std\check_search_response.py` (라인 78-109)
- 이전 수정 이력: `MODIFICATIONS_SUMMARY.md`

---

**결론**: 제공된 JSON 응답 예시는 **완전하고 정확한 명세**이며, 이를 기준으로 문서의 표를 완전히 동기화했습니다. 이제 API 구현과 문서가 일치합니다.
