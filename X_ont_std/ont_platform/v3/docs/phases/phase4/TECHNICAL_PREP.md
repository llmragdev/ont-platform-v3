# Phase 4 기술 준비 가이드
## 온톨로지 확장성 개발 시작 전 체크리스트

**대상 기간**: 2026-05-25 ~ 2026-07-20 (준비 기간)  
**실행 시작**: 2026-07-21 (Week 1 시작)  
**담당**: 개발팀 리드 + 아키텍처 팀

---

## 1️⃣ 개발 환경 설정

### 1.1 Python 라이브러리 설치

```bash
# Python 3.9+ (현재 사용 중)

# RDF 처리
pip install rdflib==6.3.2
pip install SPARQLWrapper==2.0.0
pip install rdf2neo  # 선택: Neo4j 통합 시

# 데이터 처리
pip install pandas numpy

# 캐싱
pip install redis==5.0.1

# 검색 (선택: Week 7 이후)
pip install elasticsearch==8.11.0

# 비동기 작업
pip install celery[redis]==5.3.4

# 테스트
pip install pytest-benchmark
pip install hypothesis  # Property-based testing

# 문서
pip install sphinx rdflib-sphinx-extension
```

**설치 시간**: 10-15분  
**버전 확인**:
```bash
python -c "import rdflib; print(rdflib.__version__)"  # 6.3.2 이상
```

---

### 1.2 Frontend 라이브러리

```bash
cd src/frontend

# 그래프 시각화
npm install cytoscape cytoscape-cose-bilkent --save
npm install d3 @types/d3 --save
npm install force-graph react-force-graph-3d --save

# 상태 관리 (이미 설치됨 - 확인만)
npm list zustand react-query

# 성능 최적화
npm install react-window virtualized-list --save

# 데이터 비교
npm install deep-diff --save

# 테스트
npm install @testing-library/react @testing-library/jest-dom --save-dev
npm install jest-canvas-mock --save-dev  # Canvas 테스트용
```

**설치 시간**: 5-10분

---

### 1.3 외부 서비스 준비

#### SPARQL 엔드포인트 (선택)
```
Free options:
- DBpedia SPARQL: https://dbpedia.org/sparql
- Wikidata SPARQL: https://query.wikidata.org/sparql
- Semantic Web Company GraphDB (30-day trial)

Credentials needed: 없음 (public API)
```

#### Redis 인스턴스
```bash
# 로컬 테스트용
# Windows: Redis 설치 또는 Docker
docker run -d -p 6379:6379 redis:7-alpine

# 프로덕션: Neon Cloud Redis (기존과 동일한 인프라)
```

#### Elasticsearch (선택, Week 7 이후)
```bash
# 로컬 테스트용
docker run -d -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# 프로덕션: Elastic Cloud 또는 self-hosted
```

---

## 2️⃣ 코드 아키텍처 준비

### 2.1 기존 코드 구조 분석

```bash
# 현재 백엔드 구조
ont_platform/v3/src/backend/
├── app/
│   ├── main.py                  # FastAPI app
│   ├── models/
│   │   ├── __init__.py
│   │   ├── action.py            # ✅ ActionDefinition
│   │   ├── workflow.py          # ✅ Workflow, ActionExecution
│   │   ├── changelog.py         # ✅ ChangeLog, WriteBackQueue
│   │   ├── ontology_schema.py   # ➕ NEW (OntologyStyle, etc)
│   │   ├── domain_schema.py     # ➕ NEW (DomainSchema, EntityType)
│   │   ├── entity_metadata.py   # ➕ NEW (EntityMetadata, LineageInfo)
│   │   └── audit.py             # ➕ NEW (EntityVersion, AuditLog)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── workflow_repository.py   # ✅ 기존
│   │   ├── schema_repository.py     # ➕ NEW
│   │   ├── audit_repository.py      # ➕ NEW
│   │   └── metadata_repository.py   # ➕ NEW
│   ├── services/
│   │   ├── __init__.py
│   │   ├── workflow_service.py      # ✅ 기존
│   │   ├── rdf_converter.py         # ➕ NEW
│   │   ├── ontology_importer.py     # ➕ NEW
│   │   ├── lineage_service.py       # ➕ NEW
│   │   ├── ontology_cache.py        # ➕ NEW
│   │   └── ontology_indexing.py     # ➕ NEW
│   ├── api/
│   │   ├── __init__.py
│   │   ├── workflow_endpoints.py    # ✅ 기존
│   │   ├── ontology_endpoints.py    # ➕ NEW (SPARQL, export, import)
│   │   └── metadata_endpoints.py    # ➕ NEW (audit, lineage)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py              # ✅ 기존
│   │   ├── models.py                # ✅ 기존 (SQLAlchemy ORM)
│   │   └── migrations/              # ➕ 새 migration 파일들
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py              # ✅ 기존 (fixtures)
│       ├── integration/
│       │   ├── test_workflow_*.py    # ✅ 기존
│       │   ├── test_schema_*.py      # ➕ NEW
│       │   ├── test_metadata_*.py    # ➕ NEW
│       │   ├── test_rdf_*.py         # ➕ NEW
│       │   └── test_performance_*.py # ➕ NEW
│       └── unit/
│           └── ...
```

**확인 사항**:
- [ ] `/app/models/` 구조 확인
- [ ] `/app/repositories/` 확인 (ORM 패턴)
- [ ] `/app/services/` 확인 (비즈니스 로직)
- [ ] SQLAlchemy 버전 확인 (`pip show sqlalchemy`)

---

### 2.2 데이터베이스 마이그레이션 전략

#### Phase 3 현재 테이블
```sql
-- 기존
CREATE TABLE entities (...)
CREATE TABLE relationships (...)
CREATE TABLE changelogs (...)
CREATE TABLE action_executions (...)
CREATE TABLE writeback_queue (...)
```

#### Phase 4 추가 테이블
```sql
-- Week 1-2: Schema
CREATE TABLE domains (...)
CREATE TABLE entity_types (...)
CREATE TABLE relation_types (...)
CREATE TABLE property_definitions (...)

-- Week 3: Metadata
CREATE TABLE entity_metadata (...)
CREATE TABLE lineage_chains (...)
CREATE TABLE transformations (...)
CREATE TABLE entity_versions (...)
CREATE TABLE audit_logs (...)

-- Week 5+: Indexing
CREATE TABLE property_indices (...)
CREATE TABLE relationship_indices (...)
```

**마이그레이션 도구**:
```bash
# Alembic (현재 사용 중)
alembic revision --autogenerate -m "Add Phase 4 schema tables"
alembic upgrade head
```

---

### 2.3 API 엔드포인트 설계 (Week 1 준비)

#### Schema API (Week 1-2)
```
POST   /api/domains                    # 도메인 생성
GET    /api/domains/{domain_id}        # 도메인 조회
PUT    /api/domains/{domain_id}        # 도메인 수정
DELETE /api/domains/{domain_id}        # 도메인 삭제

POST   /api/domains/{domain_id}/entity-types
GET    /api/domains/{domain_id}/entity-types/{type_id}

POST   /api/domains/{domain_id}/relation-types
GET    /api/domains/{domain_id}/relation-types/{rel_id}

POST   /api/validate/entity
  Request:  {"entity": {...}, "domain_id": "..."}
  Response: {"valid": true, "errors": []}
```

#### Metadata API (Week 3)
```
GET    /api/entities/{entity_id}/metadata
GET    /api/entities/{entity_id}/lineage
GET    /api/entities/{entity_id}/versions
GET    /api/audit-logs?entity_id=...&action=...

POST   /api/entities/{entity_id}/versions/{version_id}/restore
```

#### RDF API (Week 4)
```
POST   /api/ontology/sparql
  Request:  {"query": "SELECT ..."}
  Response: {"results": {"bindings": [...]}}

GET    /api/ontology/export?domain_id=...&format=turtle
GET    /api/ontology/export?domain_id=...&format=rdfxml
GET    /api/ontology/export?domain_id=...&format=n3

POST   /api/ontology/import
  Form-data: file (RDF file)
  
POST   /api/ontology/import/dbpedia
  Request:  {"query": "...", "domain_id": "..."}

POST   /api/ontology/import/wikidata
  Request:  {"entity_id": "Q...", "domain_id": "..."}
```

---

## 3️⃣ 테스트 전략 준비

### 3.1 테스트 파일 구조

```bash
# Unit Tests (모델, 유틸리티)
tests/unit/
├── test_ontology_style_enum.py
├── test_property_definition.py
├── test_rdf_triple.py
└── test_lineage_info.py

# Integration Tests (저장소, 서비스)
tests/integration/
├── test_schema_repository.py
├── test_audit_repository.py
├── test_rdf_converter_integration.py
├── test_ontology_importer.py
├── test_lineage_service.py
└── test_sparql_endpoint.py

# E2E Tests (API 엔드포인트)
tests/e2e/
├── test_domain_schema_workflow.py
├── test_metadata_and_versioning.py
├── test_rdf_import_export.py
└── test_full_ontology_lifecycle.py

# Performance Tests (Benchmark)
tests/performance/
├── test_schema_performance.py
├── test_query_performance.py
├── test_cache_performance.py
└── test_import_performance.py
```

### 3.2 테스트 커버리지 목표

| 주간 | 대상 모듈 | 목표 커버리지 | 목표 테스트 수 |
|------|----------|-------------|-------------|
| 1-2 | schema_*.py | ≥ 90% | 20+ |
| 3 | metadata_*.py, audit_*.py | ≥ 90% | 20+ |
| 4 | rdf_*, importer*.py | ≥ 85% | 20+ |
| 5-8 | cache, index, UI | ≥ 80% | 20+ |
| **합계** | **모든 모듈** | **≥ 85%** | **120+** |

---

### 3.3 테스트 실행 명령어 (Template)

```bash
# Unit + Integration
cd ont_platform/v3/src/backend
pytest tests/unit tests/integration -v --cov=app --cov-report=html

# Performance
pytest tests/performance --benchmark-only --benchmark-json=results.json

# 특정 주간
pytest tests/ -k "week1" -v
pytest tests/ -k "week2" -v
```

---

## 4️⃣ 문서화 준비

### 4.1 개발 중 작성할 문서

| 문서명 | 작성 시점 | 담당 |
|--------|----------|------|
| PHASE4_ONTOLOGY_DEVELOPER_GUIDE.md | Week 4 완료 후 | Claude |
| PHASE4_SCHEMA_DESIGN_PATTERNS.md | Week 2 완료 후 | Claude |
| PHASE4_RDF_MAPPING_GUIDE.md | Week 4 완료 후 | Claude |
| PHASE4_LINEAGE_TRACKING_GUIDE.md | Week 3 완료 후 | Claude |
| PHASE4_API_REFERENCE.md | 주간별 | Claude |
| PHASE4_FRONTEND_COMPONENTS.md | Week 5 완료 후 | Codex |
| PHASE4_MIGRATION_GUIDE.md | 최종 | Claude + Codex |

### 4.2 예제 코드 준비

```python
# Week 1-2 후
# examples/01_define_domain_schema.py
# examples/02_validate_entity.py
# examples/03_query_by_style.py

# Week 3 후
# examples/04_track_entity_lineage.py
# examples/05_audit_entity_changes.py

# Week 4 후
# examples/06_convert_to_rdf.py
# examples/07_import_from_dbpedia.py
# examples/08_sparql_query.py
```

---

## 5️⃣ 팀 역할 분담

### Claude (Backend)
**담당**: Schema, Metadata, RDF 변환, API, 테스트  
**시간**: 60% (주당 24-30시간)

```
Week 1-2: OntologyStyle, DomainSchema (20h)
Week 3: EntityMetadata, AuditLog (20h)
Week 4: RDFConverter, OntologyImporter (20h)
Week 5-8: 성능 최적화, 문서화 (16h)
```

### Codex (Frontend)
**담당**: OntologyExplorer UI, 시각화, E2E 테스트  
**시간**: 40% (주당 16-20시간)

```
Week 1-4: 백엔드 API 대기 (8h, 리서치/설계)
Week 5-8: OntologyExplorer 구현 (32h)
```

### Antigravity (Performance)
**담당**: 성능 벤치마크, 캐싱 최적화, 부하 테스트  
**시간**: 25% (주당 10-12시간)

```
Week 1-4: 성능 기준선 수집 (8h)
Week 5-8: 캐싱, 인덱싱, 벤치마크 (20h)
```

---

## 6️⃣ 위험 관리

### 위험 1: RDF 라이브러리 복잡도
| 항목 | 설명 |
|------|------|
| **위험도** | 높음 |
| **영향** | Week 4 지연 (2-3주) |
| **완화책** | Week 1에 rdflib 프로토타입 작성, 벤치마크 |
| **모니터링** | 주간 스탠드업 |

### 위험 2: 대규모 그래프 성능
| 항목 | 설명 |
|------|------|
| **위험도** | 중간 |
| **영향** | 캐싱/인덱싱 필수 (Week 5-8 지연) |
| **완화책** | Week 3부터 성능 테스트 조기 시작 |
| **모니터링** | 주간 성능 리포트 |

### 위험 3: DBpedia/Wikidata API 변경
| 항목 | 설명 |
|------|------|
| **위험도** | 낮음 |
| **영향** | 임포터 로직 수정 필요 |
| **완화책** | API 래퍼 계층, 폴백 메커니즘 |
| **모니터링** | 월간 API 호환성 검사 |

---

## 7️⃣ 체크리스트 (2026-07-20 완료)

### 개발 환경
- [ ] Python 3.9+ 확인
- [ ] rdflib 6.3.2+ 설치
- [ ] redis 실행 중
- [ ] PostgreSQL/Neon 연결 확인
- [ ] Node.js 16+ 확인
- [ ] npm 라이브러리 설치

### 코드 준비
- [ ] Phase 3 코드 최종 확인 (commit된 상태)
- [ ] 기존 models/ 구조 분석
- [ ] 기존 repositories/ 패턴 이해
- [ ] 기존 services/ 패턴 이해

### 데이터베이스
- [ ] Alembic 마이그레이션 템플릿 준비
- [ ] Phase 4 테이블 ERD 생성
- [ ] 마이그레이션 순서 계획

### 테스트
- [ ] pytest 설정 확인
- [ ] conftest.py fixtures 검토
- [ ] 성능 테스트 기준선 수집

### 문서
- [ ] API 설계 문서 작성 시작
- [ ] 아키텍처 다이어그램 준비
- [ ] 스키마 ERD 생성

### 팀
- [ ] 일일 스탠드업 시간 정하기 (예: 09:00 KST)
- [ ] 주간 리뷰 시간 정하기 (예: 금요일 16:00)
- [ ] Slack 채널 설정

---

## 📚 참고 자료

### RDF/Semantic Web 학습
- [rdflib 공식 문서](https://rdflib.readthedocs.io/)
- [RDF 소개 (W3C)](https://www.w3.org/RDF/)
- [SPARQL 쿼리 언어](https://www.w3.org/TR/sparql11-query/)

### 그래프 시각화
- [Cytoscape.js](https://js.cytoscape.org/)
- [D3.js](https://d3js.org/)
- [Force-Graph](https://github.com/vasturiano/force-graph)

### 데이터 모델링
- [온톨로지 설계 패턴](https://patterns.dataincubator.org/)
- [Property Graph 모델](https://en.wikipedia.org/wiki/Property_graph)
- [Semantic Web 기초](https://www.w3.org/standards/semanticweb/)

---

## 최종 상태

```
✅ 개발 환경 설정 완료
✅ 코드 아키텍처 이해
✅ 데이터베이스 계획 수립
✅ 테스트 전략 준비
✅ 팀 역할 분담 정의

🚀 2026-07-21 Phase 4 Week 1 시작 준비 완료
```

---

**작성**: 2026-05-25  
**상태**: PREPARATION PHASE (2026-05-25 ~ 2026-07-20)  
**실행**: 2026-07-21 ~ 2026-09-30
