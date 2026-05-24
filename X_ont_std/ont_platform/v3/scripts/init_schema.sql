-- PostgreSQL 온톨로지 스키마 초기화
-- 사용: psql -d ont_db -f init_schema.sql

-- 1. Timestamp 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. entities 테이블
CREATE TABLE IF NOT EXISTS entities (
    -- 기본 키
    id VARCHAR(255) PRIMARY KEY,

    -- 분류
    entity_type VARCHAR(100) NOT NULL,

    -- 테넌트 + 문서
    domain_id VARCHAR(100) NOT NULL,
    doc_id VARCHAR(255),

    -- 속성 (반정형 데이터)
    properties JSONB DEFAULT '{}',

    -- 버전 관리 (낙관적 잠금)
    version INT DEFAULT 1 CHECK (version > 0),

    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 제약사항
    CONSTRAINT entities_id_not_empty CHECK (id != ''),
    CONSTRAINT entities_type_not_empty CHECK (entity_type != ''),
    CONSTRAINT entities_domain_not_empty CHECK (domain_id != '')
);

-- entities 인덱스
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_domain ON entities(domain_id);
CREATE INDEX IF NOT EXISTS idx_entities_doc ON entities(doc_id);
CREATE INDEX IF NOT EXISTS idx_entities_properties ON entities USING GIN(properties);
CREATE INDEX IF NOT EXISTS idx_entities_created ON entities(created_at DESC);

-- entities 트리거
DROP TRIGGER IF EXISTS entities_update_timestamp ON entities;
CREATE TRIGGER entities_update_timestamp
BEFORE UPDATE ON entities
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- 3. relationships 테이블
CREATE TABLE IF NOT EXISTS relationships (
    -- 기본 키
    id VARCHAR(255) PRIMARY KEY,

    -- 관계 정의
    from_entity_id VARCHAR(255) NOT NULL
        REFERENCES entities(id) ON DELETE CASCADE,
    to_entity_id VARCHAR(255) NOT NULL
        REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,

    -- 테넌트 + 문서
    domain_id VARCHAR(100) NOT NULL,
    doc_id VARCHAR(255),

    -- 관계 가중치 (선택)
    weight DECIMAL(10,2),

    -- 속성
    properties JSONB DEFAULT '{}',

    -- 버전 관리
    version INT DEFAULT 1 CHECK (version > 0),

    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 제약사항
    CONSTRAINT relationships_id_not_empty CHECK (id != ''),
    CONSTRAINT relationships_type_not_empty CHECK (relation_type != ''),
    CONSTRAINT relationships_from_to CHECK (from_entity_id != to_entity_id)
);

-- relationships 인덱스
CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relation_type);
CREATE INDEX IF NOT EXISTS idx_relationships_domain ON relationships(domain_id);
CREATE INDEX IF NOT EXISTS idx_relationships_created ON relationships(created_at DESC);

-- 복합 인덱스 (JOIN 성능)
CREATE INDEX IF NOT EXISTS idx_relationships_from_type ON relationships(from_entity_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_relationships_to_type ON relationships(to_entity_id, relation_type);

-- relationships 트리거
DROP TRIGGER IF EXISTS relationships_update_timestamp ON relationships;
CREATE TRIGGER relationships_update_timestamp
BEFORE UPDATE ON relationships
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- 4. audit_log 테이블
CREATE TABLE IF NOT EXISTS audit_log (
    -- 기본 키
    id SERIAL PRIMARY KEY,

    -- 감사 대상
    domain_id VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255),

    -- 작업 종류
    operation VARCHAR(50) NOT NULL
        CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'QUERY')),

    -- 상태 변경
    old_state JSONB,
    new_state JSONB,

    -- 사용자/컨텍스트
    actor VARCHAR(100),
    actor_ip VARCHAR(45),

    -- 타임스탬프 (자동)
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 추가 메타데이터
    metadata JSONB DEFAULT '{}'
);

-- audit_log 인덱스
CREATE INDEX IF NOT EXISTS idx_audit_domain ON audit_log(domain_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_operation ON audit_log(operation);

-- 5. ontology_metadata 테이블
CREATE TABLE IF NOT EXISTS ontology_metadata (
    -- 기본 키
    domain_id VARCHAR(100) PRIMARY KEY,

    -- 버전 관리
    ontology_version VARCHAR(50),
    schema_version INT DEFAULT 1,

    -- 통계
    entity_count INT DEFAULT 0,
    relationship_count INT DEFAULT 0,

    -- 상태
    status VARCHAR(50) DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'deprecated')),

    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 메타데이터
    description TEXT,
    owner VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- ontology_metadata 트리거
DROP TRIGGER IF EXISTS ontology_metadata_update_timestamp ON ontology_metadata;
CREATE TRIGGER ontology_metadata_update_timestamp
BEFORE UPDATE ON ontology_metadata
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- 6. ontology_triples VIEW (논리적 트리플)
DROP VIEW IF EXISTS ontology_triples;
CREATE VIEW ontology_triples AS
-- 엔티티 속성을 트리플로 변환
SELECT
    CONCAT('entity:', e.id) AS subject,
    CONCAT('property:', key) AS predicate,
    value::TEXT AS object,
    'entity_property' AS triple_type,
    e.domain_id
FROM entities e,
     jsonb_each_text(e.properties) AS props(key, value)

UNION ALL

-- 관계를 트리플로 변환
SELECT
    CONCAT('entity:', r.from_entity_id) AS subject,
    CONCAT('relation:', r.relation_type) AS predicate,
    CONCAT('entity:', r.to_entity_id) AS object,
    'relationship' AS triple_type,
    r.domain_id
FROM relationships r;

-- 7. 초기 메타데이터 삽입
INSERT INTO ontology_metadata (domain_id, ontology_version, schema_version, status, owner)
VALUES ('ontology_v1', '1.0.0', 1, 'active', 'system')
ON CONFLICT (domain_id) DO NOTHING;

-- 스키마 초기화 완료
SELECT 'Schema initialization complete' as status;
SELECT
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public') as table_count,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public') as index_count;
