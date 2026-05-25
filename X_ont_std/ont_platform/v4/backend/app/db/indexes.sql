-- rdf_graphs 테이블 인덱싱
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rdf_graphs_entity_id 
ON rdf_graphs(entity_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rdf_graphs_created_at 
ON rdf_graphs(created_at DESC);

-- imported_entities 테이블 인덱싱
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_imported_entities_external_uri 
ON imported_entities(external_uri);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_imported_entities_source 
ON imported_entities(source);

-- entity_mappings 테이블 인덱싱
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_mappings_internal 
ON entity_mappings(internal_entity_id, confidence DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entity_mappings_external 
ON entity_mappings(external_entity_id, external_source);

-- sparql_queries 테이블 인덱싱
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sparql_queries_hash 
ON sparql_queries(MD5(query_text));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sparql_queries_executed_at 
ON sparql_queries(executed_at DESC);
