# ont_platform v4.0

**상태**: 🚀 Phase 4 Week 3 시작 (2026-08-05) | PostgreSQL + Redis 기반 아키텍처

---

## 📚 문서 네비게이션

모든 프로젝트 문서는 **`../v3/docs/` 디렉토리**에서 일괄 관리됩니다 (v4는 문서 공유).

**시작하기**:
- 📖 **프로젝트 개요**: [../v3/ROADMAP.md](../v3/ROADMAP.md)
- 🏗️ **시스템 아키텍처**: [../v3/docs/guides/ARCHITECTURE.md](../v3/docs/guides/ARCHITECTURE.md)
- 📋 **Phase 4 지시서**: [../v3/docs/phases/phase4/AGENT_INSTRUCTIONS.md](../v3/docs/phases/phase4/AGENT_INSTRUCTIONS.md)
- 📝 **v4 기술 준비**: [../v3/docs/phases/phase4/TECHNICAL_PREP.md](../v3/docs/phases/phase4/TECHNICAL_PREP.md)

---

## v3 대비 v4 주요 변경

| 항목 | v3 | v4 |
|------|----|----|
| 저장소 | JSON 파일 기반 | **PostgreSQL (Neon)** |
| 캐싱 | 없음 | **Redis (Schema/Entity LRU)** |
| SPARQL | 시뮬레이션/정규식 | **rdflib 실제 처리** |
| 메타데이터 | 없음 | **EntityMetadata, LineageInfo, Transformation** |
| 감사 로그 | 파일 기반 | **PostgreSQL audit_logs 테이블** |
| 백엔드 포트 | 8001 | **8002** |
| 프론트엔드 포트 | 3001 | **3002** |
| DB 마이그레이션 | - | **Alembic** |

---

## 실행 방법

### 환경 준비 (최초 1회)

```bash
# 백엔드 의존성
conda activate claud_be
pip install -r E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend\requirements.txt

# 프론트엔드 의존성
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\frontend
npm install
```

### 데이터베이스 초기화

```bash
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend

# Alembic 마이그레이션 실행
alembic upgrade head
```

### 프론트엔드 실행 (포트 3002)

```bash
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\frontend
npm run dev
# → http://localhost:3002
```

### 백엔드 실행 (포트 8002)

```bash
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend
uvicorn app.main:app --reload --port 8002
```

> 프론트엔드가 포트 3002에서 실행 중이어야 API 호출이 됩니다.

---

## 환경 변수 (필수)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | Neon PostgreSQL 연결 문자열 | postgresql://... (필수) |
| `REDIS_URL` | Redis 캐시 연결 | redis://localhost:6379 |
| `GEMINI_API_KEY` | Gemini API 키 (선택) | 미설정 |
| `HMAC_SECRET` | HMAC 인증 활성화 (선택) | 미설정 |
| `COMPANY_ID` | 테넌트 회사 ID | `demo_company` |
| `PROJECT_ID` | 테넌트 프로젝트 ID | `demo_project` |

**예시** (`.env` 파일):
```
DATABASE_URL=postgresql://user:password@neon-host/dbname
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=AIza...
```

---

## API 엔드포인트 요약

| 엔드포인트 | 설명 | 변경사항 |
|-----------|------|---------|
| `GET /api/health` | 헬스체크 | **`version: 4.0.0`** |
| `POST /api/ontology/entities` | 엔티티 생성 | PostgreSQL 저장 |
| `GET /api/ontology/entities/{id}` | 엔티티 조회 | Redis 캐시 적용 |
| `POST /api/ontology/sparql` | SPARQL 쿼리 | rdflib 기반 실행 |
| `GET /api/metadata/lineage/{entity_id}` | 혈통 조회 | **[신규]** |
| `GET /api/audit/logs` | 감시 로그 | **[신규]** DB 저장 |
| `POST /api/ontology/import` | 외부 온톨로지 import | **[신규]** DBpedia/Wikidata |

Swagger UI: `http://localhost:8002/docs`

---

## 테스트 실행

```bash
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v4\src\backend

# 모든 통합 테스트
pytest tests/integration/ -v

# 특정 테스트
pytest tests/integration/test_domain_schema.py -v
```

---

## 주요 파일 구조

```
v4/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/            hybrid.py, workflow.py, metrics.py, metadata_endpoints.py
│   │   │   ├── db/             database.py (PostgreSQL + Redis), models.py (ORM)
│   │   │   ├── models/         ontology_schema.py, entity_metadata.py, audit.py
│   │   │   ├── repositories/   schema_repository.py (PostgreSQL 기반)
│   │   │   ├── services/       cache_service.py, lineage_service.py, rdf_converter.py
│   │   │   ├── middleware/     auth.py (HMAC)
│   │   │   ├── migrations/     alembic (DB 마이그레이션)
│   │   │   └── main.py
│   │   ├── tests/integration/  test_domain_schema.py, test_schema_repository.py, ...
│   │   ├── alembic.ini
│   │   └── requirements.txt    (redis, alembic 포함)
│   └── frontend/
│       └── src/
│           ├── app/            layout.tsx, page.tsx
│           ├── components/     (포트 3002에서 실행)
│           └── lib/            api.ts (v4 포트 8002 지정)
└── README.md
```

---

## PostgreSQL + Redis 설정

### Neon PostgreSQL (클라우드)
[../v3/docs/setup/NEON.md](../v3/docs/setup/NEON.md) 참고:
```bash
# CONNECTION_STRING 얻기 → DATABASE_URL로 설정
DATABASE_URL=postgresql://user:password@host.neon.tech/database
```

### Redis (로컬 개발)
```bash
# Redis 설치 (Windows)
choco install redis

# Redis 시작
redis-server

# Python에서 테스트
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

---

## Phase 4 Week 3-4 작업

### Week 3 (08-05 ~ 08-18): Metadata + Audit System
- Task 3-1: EntityMetadata, LineageInfo, Transformation 모델 및 DB 테이블
- Task 3-2: EntityVersion, AuditLog 모델 및 DB 테이블
- Task 3-3: AuditRepository, LineageService 구현

### Week 4 (08-19 ~ 09-01): RDF + External Ontology
- Task 4-1: RDFConverter 구현 (양방향 변환)
- Task 4-2: OntologyImporter (DBpedia, Wikidata, RDF 파일)
- Task 4-3: SPARQL API 엔드포인트

상세 지시서: `week_instructions/PHASE4/Week_3_Metadata/`, `week_instructions/PHASE4/Week_4_RDF/`

---

## 마이그레이션 & 롤백

### v3 → v4 데이터 마이그레이션
현재 v4는 v3 API와 호환 (JSON→PostgreSQL 동적 변환).
완전한 마이그레이션은 Week 5 이후 계획.

### 긴급 롤백
```bash
# Alembic으로 이전 버전으로 롤백
alembic downgrade -1
```

---

## 성능 목표 (Phase 4)

| 메트릭 | Phase 3 | Phase 4 Target | 개선도 |
|--------|---------|---------------|--------|
| 스키마 쿼리 | ~200ms | <50ms | 4배 |
| 엔티티 조회 | ~300ms | <200ms | 1.5배 |
| SPARQL 쿼리 | ~5000ms | <500ms | 10배 |
| 캐시 히트율 | 0% | ≥80% | New |
| 동시 사용자 | 50 | 200+ | 4배 |

---

**v4 시작**: 2026-08-05  
**v3 유지**: 호환성 보장 (포트 8001)  
**다음 단계**: Week 3 Metadata 구현
