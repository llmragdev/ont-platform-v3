"""Phase 4 Week 3: RDF 및 외부 온톨로지 모델"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RDFFormat(str, Enum):
    """RDF 직렬화 형식"""
    RDF_XML = "rdf-xml"
    TURTLE = "turtle"
    N_TRIPLES = "n-triples"
    JSON_LD = "json-ld"
    N_QUADS = "n-quads"


class RDFDataType(str, Enum):
    """RDF 데이터 타입"""
    STRING = "http://www.w3.org/2001/XMLSchema#string"
    INTEGER = "http://www.w3.org/2001/XMLSchema#integer"
    FLOAT = "http://www.w3.org/2001/XMLSchema#float"
    BOOLEAN = "http://www.w3.org/2001/XMLSchema#boolean"
    DATETIME = "http://www.w3.org/2001/XMLSchema#dateTime"
    URI = "http://www.w3.org/2001/XMLSchema#anyURI"


class RDFTriple(BaseModel):
    """RDF 삼중쌍"""
    subject: str                    # URI
    predicate: str                  # 속성/관계 URI
    object: str                     # 값(리터럴) 또는 URI
    object_type: str = "uri"        # "uri" 또는 "literal"
    language_tag: Optional[str] = None  # 언어 (예: "ko", "en")
    datatype: Optional[str] = None  # 데이터 타입 URI
    graph_uri: Optional[str] = None # Named Graph (선택사항)


class RDFNamespace(BaseModel):
    """RDF 네임스페이스 정의"""
    prefix: str                     # 접두어 (예: "ex", "foaf")
    uri: str                        # 네임스페이스 URI (예: "http://example.com/")
    description: str = ""


class RDFResource(BaseModel):
    """RDF 리소스 (URI)"""
    uri: str
    labels: List[str] = []          # rdfs:label (다국어)
    descriptions: List[str] = []    # rdfs:comment (설명)
    types: List[str] = []           # rdf:type
    properties: Dict[str, List[str]] = Field(default_factory=dict)  # 속성 → 값들


class RDFGraph(BaseModel):
    """RDF 그래프"""
    graph_uri: Optional[str] = None
    triples: List[RDFTriple]
    namespaces: List[RDFNamespace] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""
    format: RDFFormat = RDFFormat.TURTLE


class ExternalOntologySource(str, Enum):
    """외부 온톨로지 소스"""
    DBPEDIA = "dbpedia"
    WIKIDATA = "wikidata"
    YAGO = "yago"
    SCHEMA_ORG = "schema.org"
    CUSTOM = "custom"


class ImportResult(BaseModel):
    """임포트 결과"""
    import_id: str
    source_type: ExternalOntologySource
    total_triples: int
    imported_entities: int
    imported_triples: int
    failed_count: int
    errors: List[Dict[str, Any]] = []
    warnings: List[str] = []
    import_timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0


class SPARQLQuery(BaseModel):
    """SPARQL 쿼리"""
    query_string: str
    query_type: str  # "SELECT", "CONSTRUCT", "DESCRIBE", "ASK"
    limit: Optional[int] = None
    offset: Optional[int] = None
    timeout_seconds: int = 30


class SPARQLResult(BaseModel):
    """SPARQL 쿼리 결과"""
    query_id: str
    variables: List[str]  # SELECT 결과의 변수들
    results: List[Dict[str, Any]]  # 각 행의 바인딩
    result_count: int
    execution_time_ms: float
    query_timestamp: datetime = Field(default_factory=datetime.utcnow)


class OntologyAlignment(BaseModel):
    """온톨로지 정렬 (매핑)"""
    alignment_id: str
    source_ontology: str
    target_ontology: str
    mappings: List[Dict[str, Any]]  # {source_uri, target_uri, similarity_score}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class ConceptMapping(BaseModel):
    """개념 매핑"""
    source_concept: str             # 원본 개념 URI
    target_concept: str             # 대상 개념 URI
    mapping_type: str               # "exact", "close", "broader", "narrower"
    confidence_score: float         # 0.0 ~ 1.0
    manual_mapping: bool = False    # 수동 매핑 여부
    notes: Optional[str] = None
