# 엔터프라이즈 RAG 표준 기본설계서 (v1.3)

> **버전 이력**
>
> | 버전 | 일자 | 주요 변경 |
> |------|------|---------|
> | v1.0 | 2026-05-14 | 초안 작성 |
> | v1.1 | 2026-05-14 | `company_id` 메타데이터 필수화 · X-Company-ID 헤더 표준 신설 · 용어 통일 |
> | v1.2 | 2026-05-14 | `tenant_id` / `org_id` 계층 구조 도입 · Index Swap 패턴 추가 |
> | v1.3 | 2026-05-15 | **보안 및 정합성 강화**: X-Tenant-ID 필수화(Fallback 금지) · **OR 조건 검색 정책**(전사 공유 문서 포함) · RDBMS **복합키(Composite PK)** 설계 도입 · `dept_code` 기반 부서 필터링 명확화 · `tags` 메타데이터 Scalar 제한 |

---

## 1. 개요 및 설계 원칙

### 1.1 핵심 아키텍처 원칙 (Core Principles)
* **물리적 분리 (MSA 기반)**: LLM 추론 서버와 Vector DB 영역은 물리적으로 분리 가능해야 하며, `Remote Retriever` 패턴을 지향합니다.
* **멀티테넌트 격리 (Strict Isolation)**: 모든 데이터 저장·검색 시 `tenant_id`를 기반으로 물리적/논리적 격리를 강제합니다. 헤더 누락 시 "default" 처리를 금지하고 명시적 오류(400 Bad Request)를 반환합니다.
* **계층적 지식 공유 (Hierarchical Knowledge)**: 테넌트(회사) 단위 격리를 유지하되, 조직 코드(`org_id`)를 통해 부서/팀 단위의 미세 권한 제어 및 전사 공유 지식 조회를 지원합니다.

---

## 2. RAG 핵심 컴포넌트 설계 표준

### 2.1. 임베딩 대상 문서 관리
* **원본/가공 데이터 분리**: Raw Document와 Processed Data의 보관소를 분리합니다.
* **증분 업데이트(Incremental Update)**: 문서 갱신 시 `doc_id` 기준 기존 청크 삭제 후 새 청크를 삽입하며 버전을 관리합니다.

### 2.2. 벡터 DB 관리 및 라우팅
* **Routing Registry**: `routing.json` 또는 RDBMS 기반의 라우팅 테이블을 통해 `vector_db_id`별 엔진(Chroma/Qdrant/LocalJson) 및 컬렉션을 동적으로 매칭합니다.
* **임베딩 일관성**: 저장/검색 시 동일 모델을 사용하며, Vector DB 어댑터에서 임베딩을 직접 생성하여 전달(`embeddings=` 파라미터 명시)하는 것을 원칙으로 합니다.

### 2.3. 표준 메타데이터 매트릭스 (Metadata Matrix)

| 속성명 | 타입 | 필수 | 설명 |
| :--- | :--- | :--- | :--- |
| `doc_id` | String | 필수 | 원본 문서 고유 ID |
| `tenant_id` | String | 필수 | 테넌트 식별자 (Strict Filter) |
| `org_id` | String | 선택 | 조직 코드 (예: 0102). NULL 시 전사 공유 문서 |
| `dept_code` | String | 조건부 | `org_id` 앞 2자리 파생값. 부서 단위 필터링용 |
| `vector_db_id`| String | 필수 | 물리적 저장소 식별자 |
| `page_no` | Integer| 필수 | 실제 PDF/문서의 페이지 번호 |
| `created_at` | DateTime| 필수 | ISO 8601 형식 |

> **Note on Tags**: `tags`는 RDBMS/JSON 스토리지에는 배열로 저장할 수 있으나, Vector DB 메타데이터에는 필터 성능과 엔진 호환성을 위해 **콤마 분리 문자열(Scalar)** 형태로 변환하여 저장하거나 필터링에서 제외할 것을 권장합니다.

---

## 3. 멀티테넌트 및 계층 검색 정책

### 3.1. 헤더 표준 및 검증
* **`X-Tenant-ID`**: 필수. 누락 시 에러 처리.
* **`X-Org-ID`**: 선택. 누락 시 전사 범위로 간주(관리자/시스템용).

### 3.2. 계층별 검색 필터 로직 (OR 정책)
사용자가 특정 조직(`org_id`)에 소속되어 검색할 때, 해당 조직 문서와 전사 공유 문서를 동시에 조회하는 정책을 따릅니다.

| 검색 수준 | 필터 조건 (Filter Logic) | 검색 범위 |
| :--- | :--- | :--- |
| **팀 검색 (0102)** | `tenant_id == "A" AND (org_id == "0102" OR org_id IS NULL)` | 02팀 문서 + 전사 공유 |
| **부서 검색 (0100)**| `tenant_id == "A" AND (dept_code == "01" OR org_id IS NULL)` | 01부서 전체 + 전사 공유 |
| **전사 검색** | `tenant_id == "A"` | 회사 전체 문서 |

### 3.3. 조직 코드(`org_id`) 체계
* **형식**: `{DD}{TT}` (DD: 부서 2자리, TT: 팀 2자리)
* **0100의 의미**: 01부서 공통 소유 문서. (부서 전체 검색은 `dept_code == "01"`로 수행)

---

## 4. RDBMS 상세 설계 지침 (Composite Key)

데이터 정합성과 멀티테넌트 충돌 방지를 위해 주요 테이블은 복합키를 사용합니다.

* **`ca_org_mgnt`**:
  * PK: `(tenant_id, org_id)`
* **`wc_project`**:
  * PK: `(tenant_id, project_code)`
* **`wc_project_rag_doc`**:
  * PK: `doc_id` (UUID)
  * FK: `(tenant_id, project_code)`

---

## 5. 오류 및 예외 표준
* **임베딩 Fallback 금지**: Gateway 호출 실패 시 더미 벡터 반환을 금지하며, 반드시 `embedding_api_timeout` 예외를 발생시켜 문서 상태를 `error`로 기록해야 합니다.
* **Index Swap 패턴**: 조직 개편이나 대규모 데이터 갱신 시 신규 컬렉션 생성 후 라우팅 정보(Alias)를 교체하는 방식을 채택하여 서비스 중단과 데이터 불일치를 방지합니다.
