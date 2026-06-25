# Phase 4 Week 3: Metadata + Audit System
## Claude (Backend) 수행 지시서

**기간**: 2026-08-05 ~ 2026-08-18 (2주)  
**할당**: 80% (주당 24-30시간)  
**목표**: 메타데이터 및 감사 로그 시스템 완성 (PostgreSQL 기반)

---

## Task 3-1: EntityMetadata + LineageInfo + Transformation 모델

**기간**: 08-05 ~ 08-08 (3일)  
**목표**: 엔티티 메타데이터와 데이터 혈통 추적 모델 완성

### 구현 사항

```python
# app/models/entity_metadata.py

class PropertyChange(BaseModel):
    """속성 변경 기록"""
    property_name: str
    old_value: Optional[Any] = None
    new_value: Any
    changed_at: datetime
    changed_by: str

class EntityMetadata(BaseModel):
    """엔티티 메타데이터"""
    entity_id: str
    domain_id: str
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    version: int = 1
    tags: List[str] = []
    description: str = ""
    data_quality_score: Optional[float] = None  # 0-100
    last_validated_at: Optional[datetime] = None

class Transformation(BaseModel):
    """데이터 변환 기록"""
    transformation_id: str
    operation_type: str  # merge, split, enrich, filter, etc.
    input_entity_ids: List[str]
    output_entity_id: str
    transformation_rule: Dict[str, Any]
    performed_by: str
    performed_at: datetime
    status: str = "completed"  # completed, failed, pending
    error_message: Optional[str] = None

class LineageInfo(BaseModel):
    """데이터 혈통 정보"""
    entity_id: str
    source_entities: List[str]  # 직접 출처
    transformations: List[Transformation]  # 변환 체인
    data_quality_chain: List[float]  # 각 단계별 품질 점수
    created_from_import: Optional[Dict[str, Any]] = None  # DBpedia/Wikidata import 정보
```

### DB 테이블 설계 (Alembic 마이그레이션)

```sql
-- entity_metadata
CREATE TABLE entity_metadata (
    entity_id UUID PRIMARY KEY,
    domain_id VARCHAR NOT NULL,
    created_by VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by VARCHAR,
    updated_at TIMESTAMP,
    version INT DEFAULT 1,
    tags JSON,
    description TEXT,
    data_quality_score FLOAT,
    last_validated_at TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

-- transformations
CREATE TABLE transformations (
    transformation_id UUID PRIMARY KEY,
    operation_type VARCHAR NOT NULL,
    input_entity_ids JSON NOT NULL,
    output_entity_id UUID NOT NULL,
    transformation_rule JSON NOT NULL,
    performed_by VARCHAR NOT NULL,
    performed_at TIMESTAMP NOT NULL,
    status VARCHAR DEFAULT 'completed',
    error_message TEXT,
    FOREIGN KEY (output_entity_id) REFERENCES entities(id)
);

-- lineage_chains (혈통 저장)
CREATE TABLE lineage_chains (
    lineage_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    source_entities JSON,
    transformation_chain JSON,
    data_quality_chain JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

CREATE INDEX idx_lineage_entity_id ON lineage_chains(entity_id);
CREATE INDEX idx_transformation_output ON transformations(output_entity_id);
```

### 테스트 계획 (8개)

```python
def test_entity_metadata_creation():
    """엔티티 메타데이터 생성"""
    
def test_property_change_tracking():
    """속성 변경 기록"""
    
def test_transformation_merge_operation():
    """merge 변환 기록"""
    
def test_transformation_split_operation():
    """split 변환 기록"""
    
def test_lineage_single_source():
    """단일 소스 혈통"""
    
def test_lineage_multi_hop_chain():
    """다단계 변환 체인"""
    
def test_lineage_circular_dependency_detection():
    """순환 참조 감지"""
    
def test_data_quality_score_propagation():
    """품질 점수 전파"""
```

### 체크리스트

- [ ] EntityMetadata, Transformation, LineageInfo 모델 구현
- [ ] Alembic 마이그레이션 파일 작성 (entity_metadata, transformations, lineage_chains)
- [ ] 8개 테스트 작성 및 통과
- [ ] 기본 CRUD 메서드 구현

---

## Task 3-2: EntityVersion + AuditLog 모델

**기간**: 08-08 ~ 08-13 (4일)  
**목표**: 엔티티 버전 관리 및 감사 로그 시스템

### 구현 사항

```python
# app/models/audit.py

class EntityVersion(BaseModel):
    """엔티티 버전"""
    entity_id: str
    version_number: int  # 1, 2, 3, ...
    data: Dict[str, Any]  # 스냅샷
    changed_fields: List[str]  # 변경된 필드 목록
    changed_by: str
    changed_at: datetime
    change_reason: Optional[str] = None
    rollback_enabled: bool = True  # 롤백 가능 여부

class AuditLog(BaseModel):
    """감시 로그"""
    audit_id: str
    entity_id: str
    action: str  # create, update, delete, import, merge
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    performed_by: str
    performed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"  # success, failed
    error_details: Optional[str] = None
    retention_days: int = 365

class AuditQuery(BaseModel):
    """감시 로그 쿼리"""
    entity_id: Optional[str] = None
    action_filter: Optional[str] = None  # create, update, delete, *
    performed_by: Optional[str] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    limit: int = 100
    offset: int = 0
```

### DB 테이블 설계

```sql
-- entity_versions
CREATE TABLE entity_versions (
    version_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    version_number INT NOT NULL,
    data JSON NOT NULL,
    changed_fields JSON,
    changed_by VARCHAR NOT NULL,
    changed_at TIMESTAMP NOT NULL,
    change_reason TEXT,
    rollback_enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (entity_id) REFERENCES entities(id),
    UNIQUE(entity_id, version_number)
);

-- audit_logs
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY,
    entity_id UUID,
    action VARCHAR NOT NULL,
    old_value JSON,
    new_value JSON,
    performed_by VARCHAR NOT NULL,
    performed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR,
    user_agent TEXT,
    status VARCHAR DEFAULT 'success',
    error_details TEXT,
    retention_days INT DEFAULT 365,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

CREATE INDEX idx_audit_entity_id ON audit_logs(entity_id);
CREATE INDEX idx_audit_performed_by ON audit_logs(performed_by);
CREATE INDEX idx_audit_performed_at ON audit_logs(performed_at);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

### 테스트 계획 (10개)

```python
def test_version_creation():
    """버전 생성"""
    
def test_version_increment():
    """버전 증가"""
    
def test_version_rollback():
    """버전 롤백"""
    
def test_version_branch_creation():
    """버전 분기 생성"""
    
def test_audit_log_create_action():
    """create 감시 로그"""
    
def test_audit_log_update_action():
    """update 감시 로그"""
    
def test_audit_log_delete_action():
    """delete 감시 로그"""
    
def test_audit_log_query_by_entity():
    """엔티티별 로그 조회"""
    
def test_audit_log_query_by_actor():
    """액터별 로그 조회 (performed_by)"""
    
def test_retention_policy_cleanup():
    """보관 정책 자동 정리"""
```

### 체크리스트

- [ ] EntityVersion, AuditLog 모델 구현
- [ ] Alembic 마이그레이션 (entity_versions, audit_logs)
- [ ] 10개 테스트 작성 및 통과
- [ ] 성능 인덱스 생성 (performed_by, performed_at, entity_id, action)

---

## Task 3-3: AuditRepository + LineageService

**기간**: 08-13 ~ 08-18 (4일)  
**목표**: 감시 로그 저장소 및 혈통 서비스 구현

### 구현 사항

```python
# app/repositories/audit_repository.py

class AuditRepository:
    """감시 로그 저장소"""
    
    def create_audit_log(self, audit_log: AuditLog) -> AuditLog:
        """감시 로그 생성"""
        
    def query_logs(self, query: AuditQuery) -> List[AuditLog]:
        """감시 로그 쿼리"""
        # WHERE entity_id = ? AND action LIKE ? AND performed_by = ?
        
    def export_logs(self, query: AuditQuery, format: str = "json") -> bytes:
        """감시 로그 내보내기 (JSON/CSV)"""
        
    def cleanup_expired_logs(self) -> int:
        """보관 정책에 따른 로그 정리 (retention_days 기준)"""

# app/services/lineage_service.py

class LineageService:
    """데이터 혈통 서비스"""
    
    def resolve_full_chain(self, entity_id: str) -> LineageInfo:
        """전체 혈통 체인 해석"""
        # 출처부터 현재까지 모든 변환 추적
        
    def analyze_impact(self, entity_id: str) -> Dict[str, Any]:
        """영향 분석: 이 엔티티를 소스로 하는 모든 파생 엔티티"""
        # 정방향 그래프 탐색
        
    def detect_circular_dependencies(self, entity_id: str) -> bool:
        """순환 참조 감지"""
        # DFS로 사이클 검사
        
    def compute_data_quality_score(self, entity_id: str) -> float:
        """데이터 품질 점수 계산 (0-100)"""
        # 혈통 경로에서 품질 전파
```

### 테스트 계획 (7개)

```python
def test_audit_repository_crud():
    """감시 저장소 CRUD"""
    
def test_audit_log_query_multi_filter():
    """복합 필터 쿼리"""
    
def test_lineage_resolve_single_source():
    """단일 소스 혈통 해석"""
    
def test_lineage_resolve_multi_hop():
    """다단계 혈통 해석"""
    
def test_lineage_impact_analysis():
    """영향도 분석"""
    
def test_circular_dependency_detection():
    """순환 참조 감지"""
    
def test_data_quality_score_accuracy():
    """데이터 품질 점수 정확도 (≥95%)"""
```

### 성능 목표
- 감시 로그 쿼리: **< 200ms** (100K 로그)
- 혈통 해석: **< 500ms** (다단계 체인)
- 영향 분석: **< 1s** (100 파생 엔티티)

### 체크리스트

- [ ] AuditRepository 구현 (CRUD + Query)
- [ ] LineageService 구현 (Chain + Impact Analysis)
- [ ] 7개 테스트 작성 및 통과
- [ ] 성능 벤치마크 확인 (< 200ms, < 500ms)

---

## 📋 일일 진행 계획

### 08-05 (월) ~ 08-08 (목)
- [ ] EntityMetadata, Transformation 모델 구현
- [ ] Alembic 마이그레이션 작성 (entity_metadata, transformations)
- [ ] 8개 테스트 구현

### 08-09 (금) ~ 08-12 (월)
- [ ] EntityVersion, AuditLog 모델 구현
- [ ] Alembic 마이그레이션 (entity_versions, audit_logs)
- [ ] 10개 테스트 구현 및 통과

### 08-13 (화) ~ 08-16 (금)
- [ ] AuditRepository 구현
- [ ] LineageService 구현
- [ ] 7개 테스트 구현 및 통과

### 08-17 (토) ~ 08-18 (일)
- [ ] 성능 벤치마크
- [ ] 문서 작성
- [ ] 코드 리뷰

---

## 🎯 성공 기준

✅ EntityMetadata + Transformation + LineageInfo 모델 완성  
✅ EntityVersion + AuditLog 모델 완성  
✅ AuditRepository + LineageService 구현  
✅ 25개 통합 테스트 모두 통과  
✅ 성능 목표 달성 (쿼리 < 200ms, 혈통 < 500ms)  
✅ 코드 커버리지 ≥ 90%

---

## 📞 상호작용

**Codex와의 연계**:
- MetadataPanel.tsx UI 설계 (Task 3-1 완료 후)
- LineageViewer.tsx 프로토타입 (Task 3-3 완료 후)

**Antigravity와의 연계**:
- PostgreSQL 성능 기준선 (DB 테이블 생성 후)
- 감시 로그 쿼리 성능 테스트

---

**상태**: Task 3-1~3-3 준비 완료  
**예상 완료**: 2026-08-18  
**다음 단계**: Week 4 RDF 구현
