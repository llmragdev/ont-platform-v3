# AI 에이전트 표준 DB 상세 설계서 (v1.0)

## 1. 개요
본 문서는 `가이드 자료 배포 - 20240401`의 `WC_DB설계서_v1.0`을 기반으로, AI 에이전트의 비정형 데이터(문서)와 정형 데이터(메타데이터/벡터) 간의 효율적인 관리 및 추적을 위한 상세 스키마를 정의합니다.

## 2. 테이블 상세 명세

### 2.1 TB_DOC_MASTER (문서 마스터)
원천 문서의 업로드 상태 및 기본 메타데이터를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `DOC_ID` | VARCHAR(36) | PK | 문서 고유 식별자 (UUID) |
| `FILE_NAME` | VARCHAR(255) | NOT NULL | 파일 원본 명칭 |
| `FILE_PATH` | VARCHAR(512) | NOT NULL | 스토리지 내 저장 경로 |
| `FILE_SIZE` | BIGINT | - | 파일 크기 (Bytes) |
| `TENANT_ID` | VARCHAR(50) | NOT NULL | 테넌트/그룹 식별자 |
| `STATUS` | VARCHAR(20) | - | 처리 상태 (PENDING, COMPLETED, FAILED) |
| `REG_DT` | DATETIME | DEFAULT NOW() | 등록 일시 |

### 2.2 TB_DOC_CHUNK (문서 청크)
문서를 임베딩 단위로 분할한 텍스트 조각과 벡터 매핑 정보를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `CHUNK_ID` | VARCHAR(36) | PK | 청크 고유 식별자 |
| `DOC_ID` | VARCHAR(36) | FK | TB_DOC_MASTER 외래키 |
| `CONTENT` | TEXT | NOT NULL | 청크된 실제 텍스트 내용 |
| `PAGE_NO` | INT | - | 원본 문서 내 위치 (페이지 번호 등) |
| `CHUNK_SEQ` | INT | - | 문서 내 청크 순서 |
| `VECTOR_ID` | VARCHAR(128) | INDEX | 벡터 DB 내 식별자 |
| `TOKEN_COUNT` | INT | - | 해당 청크의 토큰 수 |

### 2.3 TB_VECTOR_MAPPING (벡터 DB 매핑)
서로 다른 벡터 DB 엔진 및 모델과의 연동 정보를 관리합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `VECTOR_ID` | VARCHAR(128) | PK | 벡터 DB 내 고유 ID |
| `ENGINE_TYPE` | VARCHAR(20) | - | 엔진 종류 (CHROMA, FAISS, ELASTIC) |
| `COLLECTION_NAME`| VARCHAR(100) | - | 벡터 DB 내 컬렉션/인덱스 명 |
| `MODEL_ID` | VARCHAR(50) | - | 사용된 임베딩 모델 식별자 |

## 3. 인덱스 및 검색 전략
*   **Join 최적화**: `TB_DOC_CHUNK`와 `TB_DOC_MASTER`는 `DOC_ID`를 기준으로 Join하여 검색 결과의 메타데이터를 즉시 추출합니다.
*   **벡터 검색 연동**: 벡터 DB에서 검색된 `ID`는 `TB_DOC_CHUNK.VECTOR_ID`와 1:1 매칭되어 원문 컨텍스트를 복원하는 데 사용됩니다.

## 4. 데이터 격리 정책
*   `TENANT_ID`를 모든 쿼리의 기본 필터 조건으로 사용하여 멀티테넌트 환경에서의 데이터 유출을 방지합니다.
