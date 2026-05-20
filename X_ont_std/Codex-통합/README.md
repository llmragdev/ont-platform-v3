# Codex Ontology Platform (Integrated)

`Codex-통합`은 교육용 프로토타입(`v1`)부터 운영형 MVP(`v2`), 그리고 팔란티어 실무 설계 원칙이 반영된 고도화 버전(`v3`)까지를 체계적으로 관리하는 통합 저장소입니다.

## 저장소 구조

```text
Codex-통합/
├── v1/                # [Legacy] Original Prototype (src_codex 기반)
│   └── (Vanilla Python/HTML/JS 기반 심플 데모)
├── v2/                # [Current] Integrated MVP (FastAPI + Next.js)
│   ├── src/           # 백엔드/프론트엔드 소스
│   └── storage/       # 테넌트/프로젝트별 JSON 저장소
├── v3/                # [Active] Palantir Practical Edition (고도화 중)
│   ├── src/           # Materialize, Write-back, Action-driven 반영 소스
│   └── storage/       # 운영형 스키마 및 가버넌스 적용
├── docs/              # 공통 설계 및 요건 문서
└── backup_old/        # 과거 백업 자료
```

## 로드맵 (Roadmap)

### v1: 개념 증명 (Proof of Concept)
- 팔란티어 온톨로지 1~10단계 흐름 구현
- 단일 프로세스 기반의 심플한 RAG 및 워크플로우 시연

### v2: 운영형 골격 (Operational Foundation)
- **FastAPI + Next.js** 기반의 현대적 아키텍처 전환
- 멀티테넌트(Company) 및 멀티프로젝트 권한 격리 구현
- JSON 기반의 확장 가능한 온톨로지 스토리지

### v3: 팔란티어 실무 고도화 (Palantir Practical Edition) - **진행 중**
팔란티어의 실제 현장 설계 원칙을 반영하여 프로토타입을 제품 수준으로 끌어올립니다.
- **Materialize & Write-back**: 논리 모델과 물리 데이터셋 분리, 외부 원천 DB 동기화 구현.
- **Action-Driven Modeling**: Action에서 시작하는 역방향 온톨로지 설계 방법론 적용.
- **Ontology Provenance**: 데이터의 출처(Doc ID, Page), 신뢰도, 승인 상태(Candidate/Approved) 관리.
- **Governance & Naming**: 도메인별 폴더 표준화 및 네이밍 컨벤션 적용.
- **Quality Evaluation**: `evaluate.py`를 통한 RAG 및 온톨로지 검색 품질 지표화.

---

## 주요 문서

- [FINAL_REQUIREMENTS.md](docs/FINAL_REQUIREMENTS.md)
- [FINAL_DESIGN.md](docs/FINAL_DESIGN.md)
- [03_FINAL_API_SPEC.md](docs/03_FINAL_API_SPEC.md)
- [04_FINAL_DATA_SCHEMA.md](docs/04_FINAL_DATA_SCHEMA.md)
- [05_MVP_IMPLEMENTATION_PLAN.md](docs/05_MVP_IMPLEMENTATION_PLAN.md)
- [06_ACCEPTANCE_TEST_PLAN.md](docs/06_ACCEPTANCE_TEST_PLAN.md)
- [07_UX_AND_OPERATIONS.md](docs/07_UX_AND_OPERATIONS.md)

## 실행 가이드 (v2/v3 기준)

각 버전 폴더의 `src/backend` 및 `src/frontend`에서 전용 환경을 사용하여 실행합니다.

### Backend (v2)
```powershell
cd E:\ontology_edu\X_ont_std\Codex-통합\v2\src\backend
conda activate codex_be
python -m uvicorn app.main:app --reload --port 8001
```

### Frontend (v2)
```powershell
cd E:\ontology_edu\X_ont_std\Codex-통합\v2\src\frontend
conda activate codex_fe
npm install
npm run dev
```

### 검증 (v2)
```powershell
conda activate codex_be
cd E:\ontology_edu\X_ont_std\Codex-통합\v2\src\backend
python -m pytest   # 31 passed
```

## Phase 1 구현 상태

완료:

- `app/storage_config.py`: 안전한 company/project ID 검증, storage 경로 팩토리, tenant/project settings 로더
- `app/tenant.py`: 단일 사용자 기반 `TenantContext`, 권한 resolve, `/api/v1/tenant/me` 응답 조립
- `data/{companies,projects,users,role_defaults}.json`: 개발용 identity seed
- `project/storage/*/tenant_settings.json`, `project_settings.json`: Secret Manager 없는 계층형 테넌트 설정
- `/api/v1/tenant/me`, `/api/v1/tenant/projects`
- Phase 1/2/3 API 테스트 21개 포함 전체 31개 통과

예시:

```powershell
conda activate codex_be
cd E:\ontology_edu\X_ont_std\Codex-통합\v2\src\backend
python -m uvicorn app.main:app --reload --port 8001
```

```text
GET http://localhost:8001/api/v1/tenant/me?user_id=alice
GET http://localhost:8001/api/v1/tenant/me?user_id=alice&include_paths=true
```
