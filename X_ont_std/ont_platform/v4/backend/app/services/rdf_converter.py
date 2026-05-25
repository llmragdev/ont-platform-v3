"""Phase 4 Week 3: RDF 변환 서비스"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.rdf_model import (
    RDFTriple, RDFFormat, RDFNamespace, RDFGraph, RDFResource,
    RDFDataType, ExternalOntologySource
)
from app.models.ontology_schema import DomainSchema, EntityType, RelationType, PropertyType


class RDFConverter:
    """RDF 변환기 (엔티티 ↔ RDF Triple)"""

    def __init__(self, domain_schema: Optional[DomainSchema] = None, cache_service: Optional[Any] = None):
        self.domain_schema = domain_schema
        self.cache_service = cache_service
        self.namespaces: Dict[str, str] = {}
        self.base_uri = ""

    def set_domain_schema(self, schema: DomainSchema) -> None:
        """도메인 스키마 설정"""
        self.domain_schema = schema
        self.base_uri = f"http://ontology.example.com/{schema.domain_id}/"

        # RDF 네임스페이스 설정
        if schema.rdf_namespaces:
            for ns in schema.rdf_namespaces:
                self.namespaces[ns.prefix] = ns.uri

    def entity_to_rdf_triples(
        self, entity_id: str, entity_type: str, properties: Dict[str, Any]
    ) -> List[RDFTriple]:
        """엔티티를 RDF Triple로 변환"""
        if not self.domain_schema or not self.base_uri:
            raise ValueError("Domain schema must be set first")

        triples = []
        subject_uri = f"{self.base_uri}{entity_type.lower()}/{entity_id}"

        # 1. rdf:type 트리플
        entity_type_uri = f"{self.base_uri}class/{entity_type}"
        triples.append(RDFTriple(
            subject=subject_uri,
            predicate="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            object=entity_type_uri,
            object_type="uri"
        ))

        # 2. 속성 트리플
        if entity_type in self.domain_schema.entity_types:
            entity_def = self.domain_schema.entity_types[entity_type]

            for prop_name, prop_value in properties.items():
                if prop_name not in entity_def.properties:
                    continue

                prop_def = entity_def.properties[prop_name]
                prop_uri = f"{self.base_uri}property/{prop_name}"

                # 데이터 타입 결정
                datatype = self._get_rdf_datatype(prop_def.property_type)

                if isinstance(prop_value, list):
                    # 다중값 속성
                    for value in prop_value:
                        triples.append(RDFTriple(
                            subject=subject_uri,
                            predicate=prop_uri,
                            object=str(value),
                            object_type="literal",
                            datatype=datatype
                        ))
                else:
                    triples.append(RDFTriple(
                        subject=subject_uri,
                        predicate=prop_uri,
                        object=str(prop_value),
                        object_type="literal",
                        datatype=datatype
                    ))

        return triples

    def relation_to_rdf_triples(
        self, from_entity_id: str, from_type: str,
        to_entity_id: str, to_type: str,
        relation_type: str, relation_props: Optional[Dict[str, Any]] = None
    ) -> List[RDFTriple]:
        """관계를 RDF Triple로 변환"""
        if not self.domain_schema or not self.base_uri:
            raise ValueError("Domain schema must be set first")

        triples = []
        from_uri = f"{self.base_uri}{from_type.lower()}/{from_entity_id}"
        to_uri = f"{self.base_uri}{to_type.lower()}/{to_entity_id}"
        rel_uri = f"{self.base_uri}relation/{relation_type}"

        # 관계 트리플
        triples.append(RDFTriple(
            subject=from_uri,
            predicate=rel_uri,
            object=to_uri,
            object_type="uri"
        ))

        # 관계 속성 (있으면)
        if relation_props and relation_type in self.domain_schema.relation_types:
            rel_def = self.domain_schema.relation_types[relation_type]

            for prop_name, prop_value in relation_props.items():
                if prop_name not in rel_def.properties:
                    continue

                prop_def = rel_def.properties[prop_name]
                prop_uri = f"{self.base_uri}property/{prop_name}"
                datatype = self._get_rdf_datatype(prop_def.property_type)

                triples.append(RDFTriple(
                    subject=from_uri,
                    predicate=prop_uri,
                    object=str(prop_value),
                    object_type="literal",
                    datatype=datatype
                ))

        return triples

    def rdf_triples_to_entity(
        self, triples: List[RDFTriple], entity_type: str
    ) -> Dict[str, Any]:
        """RDF Triple을 엔티티로 변환"""
        if not self.domain_schema or not self.base_uri:
            raise ValueError("Domain schema must be set first")

        entity_data: Dict[str, Any] = {}

        if entity_type not in self.domain_schema.entity_types:
            raise ValueError(f"Unknown entity type: {entity_type}")

        entity_def = self.domain_schema.entity_types[entity_type]

        for triple in triples:
            # rdf:type은 스킵
            if triple.predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                continue

            # 속성 이름 추출
            if triple.predicate.startswith(self.base_uri + "property/"):
                prop_name = triple.predicate.replace(self.base_uri + "property/", "")

                if prop_name in entity_def.properties:
                    # 값 변환
                    value = self._convert_rdf_value(
                        triple.object,
                        entity_def.properties[prop_name].property_type
                    )

                    if prop_name in entity_data:
                        # 다중값 처리
                        if not isinstance(entity_data[prop_name], list):
                            entity_data[prop_name] = [entity_data[prop_name]]
                        entity_data[prop_name].append(value)
                    else:
                        entity_data[prop_name] = value

        return entity_data

    def create_rdf_graph(
        self, graph_uri: str, entities_and_relations: List[RDFTriple]
    ) -> RDFGraph:
        """RDF 그래프 생성"""
        namespaces = [
            RDFNamespace(prefix="rdf", uri="http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            RDFNamespace(prefix="rdfs", uri="http://www.w3.org/2000/01/rdf-schema#"),
            RDFNamespace(prefix="xsd", uri="http://www.w3.org/2001/XMLSchema#"),
        ]

        # 스키마의 네임스페이스 추가
        if self.domain_schema and self.domain_schema.rdf_namespaces:
            for schema_ns in self.domain_schema.rdf_namespaces:
                namespaces.append(RDFNamespace(
                    prefix=schema_ns.prefix,
                    uri=schema_ns.uri,
                    description=schema_ns.description
                ))

        return RDFGraph(
            graph_uri=graph_uri,
            triples=entities_and_relations,
            namespaces=namespaces,
            created_at=datetime.utcnow(),
            created_by="system"
        )

    def serialize_rdf(
        self, graph: RDFGraph, format: RDFFormat = RDFFormat.TURTLE
    ) -> str:
        """RDF 그래프를 문자열로 직렬화"""
        if format == RDFFormat.TURTLE:
            return self._serialize_turtle(graph)
        elif format == RDFFormat.RDF_XML:
            return self._serialize_rdf_xml(graph)
        elif format == RDFFormat.JSON_LD:
            return self._serialize_json_ld(graph)
        elif format == RDFFormat.N_TRIPLES:
            return self._serialize_n_triples(graph)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _serialize_turtle(self, graph: RDFGraph) -> str:
        """Turtle 형식 직렬화"""
        lines = []

        # 네임스페이스 선언
        for ns in graph.namespaces:
            lines.append(f"@prefix {ns.prefix}: <{ns.uri}> .")

        lines.append("")

        # 트리플
        for triple in graph.triples:
            subject = self._format_uri(triple.subject)
            predicate = self._format_uri(triple.predicate)

            if triple.object_type == "uri":
                object_str = self._format_uri(triple.object)
            else:
                # 리터럴
                object_str = f'"{triple.object}"'
                if triple.datatype:
                    object_str += f"^^{self._format_uri(triple.datatype)}"
                elif triple.language_tag:
                    object_str += f"@{triple.language_tag}"

            lines.append(f"{subject} {predicate} {object_str} .")

        return "\n".join(lines)

    def _serialize_rdf_xml(self, graph: RDFGraph) -> str:
        """RDF/XML 형식 직렬화"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<rdf:RDF')

        for ns in graph.namespaces:
            lines.append(f'  xmlns:{ns.prefix}="{ns.uri}"')

        lines.append('>')
        lines.append('</rdf:RDF>')

        return "\n".join(lines)

    def _serialize_json_ld(self, graph: RDFGraph) -> str:
        """JSON-LD 형식 직렬화"""
        import json

        context = {}
        for ns in graph.namespaces:
            context[ns.prefix] = ns.uri

        graph_dict = {
            "@context": context,
            "@graph": [
                {
                    "@id": triple.subject,
                    str(triple.predicate): {
                        "@value": triple.object if triple.object_type == "literal" else {"@id": triple.object}
                    }
                }
                for triple in graph.triples
            ]
        }

        return json.dumps(graph_dict, indent=2, ensure_ascii=False)

    def _serialize_n_triples(self, graph: RDFGraph) -> str:
        """N-Triples 형식 직렬화"""
        lines = []

        for triple in graph.triples:
            subject = f"<{triple.subject}>"

            if triple.object_type == "uri":
                object_str = f"<{triple.object}>"
            else:
                object_str = f'"{triple.object}"'

            predicate = f"<{triple.predicate}>"
            lines.append(f"{subject} {predicate} {object_str} .")

        return "\n".join(lines)

    def _format_uri(self, uri: str) -> str:
        """URI를 Turtle 형식으로 포맷"""
        for prefix, namespace_uri in self.namespaces.items():
            if uri.startswith(namespace_uri):
                local_name = uri.replace(namespace_uri, "")
                return f"{prefix}:{local_name}"

        return f"<{uri}>"

    def _get_rdf_datatype(self, prop_type: PropertyType) -> str:
        """속성 타입을 RDF 데이터 타입으로 변환"""
        mapping = {
            PropertyType.STRING: RDFDataType.STRING.value,
            PropertyType.INTEGER: RDFDataType.INTEGER.value,
            PropertyType.FLOAT: RDFDataType.FLOAT.value,
            PropertyType.BOOLEAN: RDFDataType.BOOLEAN.value,
            PropertyType.DATETIME: RDFDataType.DATETIME.value,
            PropertyType.URI: RDFDataType.URI.value,
        }
        return mapping.get(prop_type, RDFDataType.STRING.value)

    def _convert_rdf_value(self, value: str, prop_type: PropertyType) -> Any:
        """RDF 값을 속성 타입으로 변환"""
        try:
            if prop_type == PropertyType.INTEGER:
                return int(value)
            elif prop_type == PropertyType.FLOAT:
                return float(value)
            elif prop_type == PropertyType.BOOLEAN:
                return value.lower() in ("true", "1", "yes")
            elif prop_type == PropertyType.DATETIME:
                return datetime.fromisoformat(value)
            else:
                return value
        except (ValueError, TypeError):
            return value

    def sparql_query(self, graph: Any, query: str) -> List[Any]:
        """SPARQL 쿼리 실행 (캐싱 연동)"""
        if self.cache_service:
            tenant = self.domain_schema.domain_id if self.domain_schema else "default"
            cached = self.cache_service.get_query(query, tenant)
            if cached is not None:
                return cached

        import rdflib
        if hasattr(graph, "graph"):
            graph = graph.graph
        if not isinstance(graph, rdflib.Graph):
            raise TypeError("Expected rdflib.Graph or LazyRDFGraph")

        qres = graph.query(query)
        results = []

        if qres.type == "SELECT":
            for row in qres:
                row_dict = {}
                for var in qres.vars:
                    val = row[var]
                    row_dict[str(var)] = str(val) if val is not None else None
                results.append(row_dict)
        elif qres.type == "CONSTRUCT":
            for row in qres:
                results.append((str(row[0]), str(row[1]), str(row[2])))
        else:
            results = list(qres)

        if self.cache_service:
            tenant = self.domain_schema.domain_id if self.domain_schema else "default"
            self.cache_service.set_query(query, tenant, results)

        return results

    def graph_to_rdf(self, graph: Any, format: str = "turtle") -> str:
        """rdflib.Graph 객체를 RDF 포맷 문자열로 직렬화"""
        import rdflib
        if hasattr(graph, "graph"):
            graph = graph.graph
        if not isinstance(graph, rdflib.Graph):
            raise TypeError("Expected rdflib.Graph")
        return graph.serialize(format=format)

    def merge_graphs(self, graphs: List[Any]) -> rdflib.Graph:
        """여러 그래프를 단일 그래프로 병합"""
        import rdflib
        merged_graph = rdflib.Graph()
        for g in graphs:
            if hasattr(g, "graph"):
                g = g.graph
            if isinstance(g, rdflib.Graph):
                for triple in g:
                    merged_graph.add(triple)
        return merged_graph


class LazyRDFGraph:
    """온디맨드 트리플 로드"""

    def __init__(self, store_path: str):
        self.store_path = store_path
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = self._load_from_store()
        return self._graph

    def _load_from_store(self):
        """필요할 때만 로드"""
        import rdflib
        g = rdflib.Graph()
        from pathlib import Path
        path = Path(self.store_path)
        if path.exists():
            if path.suffix == '.jsonl':
                from app.services.triple_store import TripleStore
                ts = TripleStore(store_path=path)
                ts.load_from_jsonl()
                for triple in ts.get_all_triples():
                    s_ref = rdflib.URIRef(triple.subject)
                    p_ref = rdflib.URIRef(triple.predicate)
                    if triple.obj.startswith("http://") or triple.obj.startswith("https://"):
                        o_ref = rdflib.URIRef(triple.obj)
                    else:
                        o_ref = rdflib.Literal(triple.obj)
                    g.add((s_ref, p_ref, o_ref))
            else:
                g.parse(self.store_path, format=rdflib.util.guess_format(self.store_path) or 'turtle')
        return g

