# Antigravity v2 개발 플랜 및 수정 설계도

## 1. 개요 및 v2 목표
v1(Mock 스캐폴딩) 단계에서 지적받은 **"실제 파이프라인 부재, 하드코딩된 DB, 검증되지 않은 테스트"** 등의 한계를 완벽히 해결합니다. v2에서는 Codex의 검증된 Layered Architecture(계층형 아키텍처)를 벤치마킹하여, 데이터가 실제로 RDBMS와 Vector DB에 적재되고 조회되는 **Production-Ready 백엔드**를 구축합니다.

---

## 2. v2 수정 아키텍처 (Layered Architecture 도입)

단일 폴더에 뭉쳐있던 v1 스크립트 구조를 버리고, 확장성과 유지보수성이 뛰어난 폴더 기반 계층 구조를 도입합니다.

```text
v2/
├── api/             # 엔드포인트(라우팅) 계층: HTTP 요청/응답 처리
│   ├── documents.py # POST /api/v1/documents/upload
│   └── search.py    # POST /api/v1/rag/search
├── core/            # 설정 및 환경변수 (Pydantic BaseSettings)
├── db/              # SQLAlchemy 엔진, 세션 팩토리, SQLite 초기화
├── models/          # 스키마 및 DB 모델
│   ├── schemas.py   # API 입출력용 Pydantic 모델
│   └── db_models.py # SQLAlchemy 2.0 (Mapped) 모델
├── repositories/    # 데이터 접근 계층 (RDBMS 통신)
│   ├── doc_repo.py  # wc_project_rag_doc 관리
│   └── chat_repo.py # wc_dialog_history 관리
└── services/        # 비즈니스 로직 계층
    ├── pipeline.py  # 파싱 -> 청킹 -> 임베딩 -> VectorDB 저장 파이프라인
    ├── rag_service.py # 검색 -> LLM 모의응답 (Remote Retriever)
    └── vector_db.py # VectorDB 라우팅 및 어댑터 (실제 Local JSON DB 사용)
```

---

## 3. v2 핵심 개선 플랜 (Action Items)

### 🎯 [Plan 1] 진짜 파이프라인 구현 (Upload to Vector DB)
* **문제**: v1은 업로드 시 상태값만 리턴.
* **해결**: `pipeline.py`를 신설하여 파일을 임시 스토리지에 저장 -> 텍스트 추출 -> Chunk 단위 분할(Character Text Splitter 등 활용) -> 더미 해싱/임베딩 -> Local Vector DB(JSON 기반)에 적재.
* **DB 연동**: 처리가 끝나면 `repositories/doc_repo.py`를 통해 RDBMS에 `pipeline_status='completed'`로 Update.

### 🎯 [Plan 2] RDBMS(SQLAlchemy)와 Repository 패턴
* **문제**: 선언만 된 RDBMS 테이블 모델들이 방치됨.
* **해결**: 모든 API 호출에 DB 세션을 물리고, `chat_repo.py`를 통해 RAG 검색 후 사용된 청크(`used_chunks`)와 사용자 질의를 `wc_dialog_history`에 즉시 `insert`.

### 🎯 [Plan 3] 라우팅 필터링 로직 수정
* **문제**: `vector_db_id`가 무시됨.
* **해결**: `vector_db.py`의 라우터에서 1순위로 `vector_db_id` 일치 여부를 검사하고, 없을 경우에만 2순위로 `category_mid` 기반 동적 라우팅을 수행.

### 🎯 [Plan 4] 견고한 자동 테스트 (Pytest Assert)
* **문제**: v1의 테스트는 단순 `print`에 의존.
* **해결**: `pytest`를 활용하여 업로드 API의 `status_code == 200` 검증, 검색 API 호출 후 `used_chunks`의 실제 반환 길이 `assert len(chunks) > 0` 검증 로직 작성.

---

## 4. 개발 마일스톤
* **Phase 1**: 폴더/아키텍처 스캐폴딩 및 SQLAlchemy 2.0 모델 재구성.
* **Phase 2**: `repositories`와 `services` (파이프라인, 라우팅) 코어 로직 작성.
* **Phase 3**: `api` 계층 통합 및 Pytest 기반 검증.
