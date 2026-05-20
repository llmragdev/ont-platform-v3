# Antigravity RAG Backend Implementation

## 개요
본 저장소는 `AI_Agent_Mission_Directive.md` 지침에 따라 Antigravity가 작성한 RAG 백엔드 파이썬 코드입니다.

## 아키텍처 및 준수 사항 요약
1. **코딩 표준**: 모든 코드는 Python PEP 8 (snake_case 함수/변수, PascalCase 클래스)를 철저히 준수했습니다.
2. **프레임워크**: `FastAPI` 및 `Pydantic`을 활용하여 강력한 타입 힌팅과 스키마 검증을 구현했습니다 (`models.py`, `main.py`).
3. **물리적 분리 (Remote Retriever)**: 
   * `vector_db_adapter.py`에 `BaseVectorDbAdapter` 인터페이스와 `VectorDbRouter`를 구현하여 카테고리별로 물리적 VectorDB를 분리 접속하도록 설계했습니다.
   * `rag_service.py`에서 LangChain 종속성 없이 독립적으로 Vector DB를 조회하고 LLM 응답을 모의 생성하도록 Remote Retriever 패턴을 적용했습니다.
4. **디버그 모드 지원**: `RagSearchRequest`에 `debug_mode` 플래그를 추가하고, True일 경우에만 `candidate_chunks`와 실행 시간을 응답에 포함하도록 구현했습니다.

## 📂 버전 관리 구조 (v1 vs v2)
본 저장소는 코드 품질 피드백에 따라 두 가지 버전으로 관리됩니다.

1. **`v1/` (Mock 스캐폴딩)**
   * 초기 아키텍처 구상 및 API 응답 스키마(Pydantic) 증명을 위해 작성된 프로토타입.
   * 비즈니스 로직(VectorDB, RDBMS)이 더미(Mock) 데이터로 동작합니다.
2. **`v2/` (Improved Prototype)**
   * **Layered Architecture**: 계층 분리 적용 및 실제 파이프라인 관통.
   * **LLM Gateway 연동**: 실제 임베딩 및 응답 생성 수행.
3. **`v3/` (Enterprise-Grade / Current)**
   * **RAG 표준 v1.3 완벽 준수**: `tenant_id` 기반 격리 및 `org_id` 계층 검색 구현.
   * **운영급 파이프라인**: `pypdf` 실제 파싱 및 표준 청킹(700/80) 적용.
   * **보안 및 정합성**: `X-Tenant-ID` 필수 검증, DB 복합키 설계, 스레드 안전성 확보.

---

## 🚀 실행 가이드 (Conda 폴더 기반 가상환경)

본 프로젝트는 의존성 관리를 위해 **Conda의 폴더 기반 가상환경** 사용을 권장합니다. 모든 실행은 최신 표준이 적용된 **`v3`** 버전을 강력히 권장합니다.

### 1. 가상환경 생성 및 활성화
명령 프롬프트를 열고 아래 명령어를 통해 프로젝트 루트로 이동한 뒤 실행하세요.

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_antigravity
conda create --prefix ./env python=3.10 -y
conda activate ./env
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
pip install pypdf python-docx  # v3 필수 패키지
```

---

## 📂 버전별 상세 가이드
- **v3 (최신 표준)**: [src_antigravity/v3/README.md](./v3/README.md) - 테넌트 격리 및 실 운영 환경 가이드
- **v2 (기존)**: `v2/test_endpoints_v2.py` 참고

### 3. v3 테스트 스크립트 실행 (권장)
최신 표준 v1.3 준수 여부를 확인하기 위해 테스트를 실행합니다.

```bash
cd E:\ontology_edu\X_rag_std\src_agents\src_antigravity\v3
pytest test_v3_standard.py -v
```
*(실행 시 100% PASSED가 뜨면 파이프라인이 정상 작동하는 것입니다.)*

### 4. 실제 서버 구동 (v3)
브라우저에서 Swagger UI를 통해 직접 테스트하려면 FastAPI 서버를 구동합니다.

```bash
# v3 폴더로 이동
cd E:\ontology_edu\X_rag_std\src_agents\src_antigravity\v3

# 서버 기동
uvicorn main:app --reload --port 8000
```
* 브라우저에서 `http://localhost:8000/docs` 에 접속하여 API를 직접 호출해 볼 수 있습니다.
* 구동과 동시에 폴더 내부에 SQLite 데이터베이스(`rag_standard_v2.db`) 파일이 자동 생성됩니다.
