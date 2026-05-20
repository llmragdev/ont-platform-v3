# 상세설계 04: RDBMS 메타데이터 및 도메인 스키마 (Legacy 호환) (v1.3)

## 1. 개요
본 문서는 기존 2025년도/2024년도 시스템(`WC_DB설계서_v1.0_20240321.xlsx`)의 테이블 구조를 바탕으로, 새로운 RAG 표준 아키텍처에 맞게 RDBMS 스키마를 설계합니다. 기존 프론트엔드 화면과 인터페이스 호환성을 유지합니다.

---

## 2. 주요 테이블 설계 (Snake Case 변환 및 RAG 통합)

### 2.1. 도메인 및 권한 테이블

#### ca_company (업체/테넌트 정보)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `tenant_id` | VARCHAR(64) | PK | 테넌트 고유 ID (ex: "company_abc") |
| `company_name` | VARCHAR(255) | NOT NULL | 업체명 |
| `created_at` | DATETIME | NOT NULL | 등록 시각 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | 활성 여부 |

#### ca_org_mgnt (조직 관리)
조직 계층 코드 체계(`{DD}{TT}`)를 기준으로 설계합니다. 멀티테넌트 환경에서 `org_id`는 테넌트별로 중복될 수 있으므로 `(tenant_id, org_id)` 복합 PK를 사용합니다.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `tenant_id` | VARCHAR(64) | PK(1/2), FK → ca_company.tenant_id | 소속 업체 |
| `org_id` | VARCHAR(8) | PK(2/2) | 조직 계층 코드 — `{DD}{TT}` 형식. ex: "0102" (01부서 02팀) |
| `org_name` | VARCHAR(255) | NOT NULL | 조직명 (조직 개편 시 이 필드만 변경) |
| `dept_code` | CHAR(2) | NOT NULL | 부서 코드 (org_id 앞 2자리 파생값) |
| `org_level` | SMALLINT | NOT NULL | 계층 깊이 (1=부서, 2=팀, 3=파트) |
| `parent_org_id` | VARCHAR(8) | NULL, FK → ca_org_mgnt(tenant_id, parent_org_id) | 상위 조직 (동일 테넌트 내 자기 참조) |
| `created_at` | DATETIME | NOT NULL | 등록 시각 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | 활성 여부 |

> **org_id 설계 원칙**
> * PK는 `(tenant_id, org_id)` 복합키 — `company_abc`의 "0102"와 `company_xyz`의 "0102"는 별개의 행입니다.
> * org_id는 식별자 역할만 합니다. 조직 이름이 바뀌어도 org_id는 변경하지 않습니다.
> * 부서 이동(ex: 0102 → 0202)이 필요한 경우 인덱스 교체(기본설계 2.8항) 패턴을 사용합니다.
> * zero-padding 필수: "01" (O), "1" (X)

#### ca_user (사용자 정보)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `user_id` | VARCHAR(64) | PK | 사용자 고유 ID |
| `tenant_id` | VARCHAR(64) | FK → ca_company.tenant_id | 소속 업체 (테넌트 키) |
| `org_id` | VARCHAR(8) | FK → ca_org_mgnt(tenant_id, org_id), NULL | 소속 조직 |
| `user_name` | VARCHAR(255) | NOT NULL | 사용자명 |
| `email` | VARCHAR(255) | NULL | 이메일 |
| `created_at` | DATETIME | NOT NULL | 등록 시각 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | 활성 여부 |

---

### 2.2. 프로젝트 및 카테고리 테이블 (RAG 라우팅 핵심)

#### wc_project (프로젝트 메타 정보)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `project_code` | CHAR(6) | PK | 6자리 프로젝트 코드 (기존 스펙) |
| `project_name` | VARCHAR(255) | NOT NULL | 프로젝트명 |
| `tenant_id` | VARCHAR(64) | FK → ca_company.tenant_id | 소속 업체 |
| `vector_db_id` | VARCHAR(128) | NOT NULL | 프로젝트 전용 Vector DB 식별자 |
| `created_at` | DATETIME | NOT NULL | 생성 시각 |
| `updated_at` | DATETIME | NULL | 최근 수정 시각 |

#### wc_category (카테고리 정보)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `category_id` | INTEGER | PK, AUTOINCREMENT | 카테고리 고유 ID |
| `project_code` | CHAR(6) | FK → wc_project.project_code | 소속 프로젝트 |
| `category_mid` | VARCHAR(128) | NOT NULL | 중분류 (라우팅 기준) |
| `category_low` | VARCHAR(128) | NULL | 소분류 |
| `vector_db_id` | VARCHAR(128) | NOT NULL | 이 카테고리에 매핑된 Vector DB 식별자 |
| `created_at` | DATETIME | NOT NULL | 생성 시각 |

#### wc_intent (인텐트 분류기용)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `intent_id` | INTEGER | PK, AUTOINCREMENT | 인텐트 고유 ID |
| `project_code` | CHAR(6) | FK → wc_project.project_code | 소속 프로젝트 |
| `intent_name` | VARCHAR(255) | NOT NULL | 인텐트명 |
| `category_mid` | VARCHAR(128) | NULL | 연결 카테고리 |
| `created_at` | DATETIME | NOT NULL | 생성 시각 |

---

### 2.3. RAG 문서 파이프라인 관리 테이블

#### wc_project_rag_doc (문서 원본 및 메타데이터)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `doc_id` | VARCHAR(64) | PK | 문서 고유 ID (UUID) |
| `project_code` | CHAR(6) | FK → wc_project.project_code | 소속 프로젝트 |
| `tenant_id` | VARCHAR(64) | FK → ca_company.tenant_id | 소속 업체 (테넌트 키) |
| `org_id` | VARCHAR(8) | FK → ca_org_mgnt(tenant_id, org_id), NULL | 문서 소유 조직. NULL이면 전사 공유 문서 |
| `file_name` | VARCHAR(512) | NOT NULL | 원본 파일명 |
| `source_url` | TEXT | NULL | 원본 파일 경로/URL |
| `category_mid` | VARCHAR(128) | NULL | 중분류 카테고리 |
| `category_low` | VARCHAR(128) | NULL | 소분류 카테고리 |
| `pipeline_status` | VARCHAR(16) | NOT NULL, DEFAULT 'pending' | `pending`\|`processing`\|`completed`\|`error` |
| `assigned_vector_db` | VARCHAR(128) | NULL | 최종 적재된 Vector DB 식별자 |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | 문서 버전 (증분 업데이트 시 증가) |
| `error_message` | TEXT | NULL | 파이프라인 오류 상세 메시지 |
| `created_at` | DATETIME | NOT NULL | 등록 시각 |
| `updated_at` | DATETIME | NULL | 최근 수정 시각 |

---

### 2.4. 채팅 및 요약 이력 테이블

#### wc_dialog_history (대화 이력)
| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `dialog_id` | INTEGER | PK, AUTOINCREMENT | 대화 고유 ID |
| `tenant_id` | VARCHAR(64) | FK → ca_company.tenant_id | 소속 업체 (테넌트 키) |
| `org_id` | VARCHAR(8) | FK → ca_org_mgnt(tenant_id, org_id), NULL | 질의한 조직 |
| `project_code` | CHAR(6) | FK → wc_project.project_code, NULL | 연결 프로젝트 |
| `user_id` | VARCHAR(64) | NULL | 질의한 사용자 |
| `query` | TEXT | NOT NULL | 사용자 질의 |
| `answer` | TEXT | NOT NULL | 생성된 답변 |
| `used_chunks_meta` | JSON | NULL | 채택된 청크 메타데이터 목록 |
| `execution_time_ms` | INTEGER | NULL | 응답 생성 소요 시간(ms) |
| `created_at` | DATETIME | NOT NULL | 대화 시각 |

---

## 3. FK 의존 관계 요약

```
ca_company (tenant_id)
  ├── ca_org_mgnt.tenant_id
  ├── ca_user.tenant_id
  ├── wc_project.tenant_id
  ├── wc_project_rag_doc.tenant_id
  └── wc_dialog_history.tenant_id

ca_org_mgnt (tenant_id, org_id) ← 복합 PK
  ├── ca_user.(tenant_id, org_id) (nullable)
  ├── ca_org_mgnt.(tenant_id, parent_org_id) (self-ref, nullable)
  ├── wc_project_rag_doc.(tenant_id, org_id) (nullable)
  └── wc_dialog_history.(tenant_id, org_id) (nullable)

wc_project (project_code)
  ├── wc_category.project_code
  ├── wc_intent.project_code
  ├── wc_project_rag_doc.project_code
  └── wc_dialog_history.project_code (nullable)
```

---

## 4. org_id 계층 코드 운영 가이드

### 4.1. 코드 체계 예시
```
0100  →  01부서 공통 소유 문서 (팀 미배정, 부서 단위 공유 문서의 소유 코드)
0101  →  01부서 01팀 소유 문서
0102  →  01부서 02팀 소유 문서
0200  →  02부서 공통 소유 문서
0201  →  02부서 01팀 소유 문서
```

> **소유 코드 vs 검색 범위 구분**
> * `0100`은 문서 소유 코드이지 검색 범위 코드가 아닙니다.
> * 01부서 전체 검색 = `dept_code == "01"` 조건 사용 (기본설계 2.5항 격리 레벨 참조)
> * 팀 검색 시 `org_id IS NULL`(전사 공유 문서)도 포함됩니다.

### 4.2. 조직 개편 대응 (Index Swap 패턴)
조직 개편 시 org_id가 변경되는 경우 RDBMS 레코드는 UPDATE로 수정하되, 벡터 DB chunk metadata는 건별 수정 대신 **Index Swap 패턴**을 사용합니다. (기본설계 2.8항)

```
1. 신규 컬렉션에 새 org_id 기준으로 야간 배치 재색인
2. routing.json collection_name 교체 (원자적 전환)
3. 구 컬렉션 삭제 (D+3 이후 안전 삭제)
```

---

## 5. 필드 명명 규칙

| 규칙 | 예시 |
|------|------|
| PK: 도메인 + `_id` 또는 `_code` | `tenant_id`, `org_id`, `project_code` |
| FK: 참조 테이블의 PK 이름과 동일 | `tenant_id` → `ca_company.tenant_id` |
| 시각: `_at` 접미사, timezone-aware ISO 8601 권장 | `created_at`, `updated_at` |
| 상태: `_status` 접미사 | `pipeline_status` |
| 버전: `version` (INTEGER, 1부터 시작) | `version` |
