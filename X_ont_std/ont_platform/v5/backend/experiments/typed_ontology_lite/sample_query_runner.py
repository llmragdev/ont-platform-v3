import json
import os
from ontology_graph_builder import OntologyGraphBuilder

def load_json(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf-8') as f:
        return json.load(f)

def run():
    # 1. 목업 데이터 및 룰 로드
    entities = load_json("fixtures/sample_entities.json")
    relationships = load_json("fixtures/sample_relationships.json")
    rules_path = os.path.join(os.path.dirname(__file__), "filter_rules.yaml")
    
    builder = OntologyGraphBuilder(rules_path)
    matched_entities = [e for e in entities if e["id"] == "e1"]
    
    # ---------------------------------------------------------
    # Test Case: 일반 개념 질의 (의도: CONCEPT)
    # ---------------------------------------------------------
    query = "온톨로지란 무엇입니까?"
    result = builder.build_graph(query, matched_entities, entities, relationships)
    
    # PM/Claude 계약 요구사항에 맞춰 provenance 모의 추가
    result["provenance"] = {"query_id": "test_12345", "timestamp": "2026-06-20T23:15:00Z"}
    
    # 전체 응답 페이로드 스펙 (Fallback 포함)
    final_payload = {
        "ontology_contract_version": "v2",
        "ontology_graph": result,
        "ontology": [] # 기존 평탄화 배열 (fallback 용도로 빈 리스트 mock)
    }
    
    # 결과 출력 (터미널 증빙용)
    print(json.dumps(final_payload, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
