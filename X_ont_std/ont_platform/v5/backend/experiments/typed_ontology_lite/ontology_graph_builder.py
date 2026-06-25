import json
import os
from typing import List, Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

class OntologyGraphBuilder:
    def __init__(self, rules_path: str):
        self.rules = self._load_rules(rules_path)
    
    def _load_rules(self, path: str) -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if yaml and path.endswith('.yaml'):
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load rules from {path}: {e}")
            return {"intent_overrides": {}, "type_policies": {}}
            
    def is_person_intent(self, query: str) -> bool:
        keywords = self.rules.get("intent_overrides", {}).get("person_lookup", [])
        lowered = query.lower()
        return any(k in lowered for k in keywords)
        
    def build_graph(self, query: str, matched_entities: List[dict], all_entities: List[dict], relationships: List[dict]) -> dict:
        is_person = self.is_person_intent(query)
        type_policies = self.rules.get("type_policies", {})
        
        seed_entity = None
        related_entities = []
        filtered_out = []
        
        entity_by_id = {e["id"]: e for e in all_entities}
        matched_ids = {e["id"] for e in matched_entities}
        
        if matched_entities:
            seed_source = matched_entities[0]
            seed_entity = {
                "name": seed_source.get("name"),
                "type": seed_source.get("type", "UNKNOWN"),
                "definition": seed_source.get("description", ""),
                "rank": 1,
                "status": "USED"
            }
            
        seen = set()
        for rel in relationships:
            from_id = rel.get("from_id")
            to_id = rel.get("to_id")
            
            if from_id not in matched_ids and to_id not in matched_ids:
                continue
                
            from_ent = entity_by_id.get(from_id)
            to_ent = entity_by_id.get(to_id)
            
            if not from_ent or not to_ent:
                continue
                
            rel_type = rel.get("relation_type", "관련")
            key = (from_id, rel_type, to_id)
            if key in seen:
                continue
            seen.add(key)
            
            # seed가 아닌 이웃(neighbor) 엔티티를 찾습니다.
            if from_id in matched_ids:
                neighbor_ent = to_ent
                # source/target 방향성 표기
                direction = f"seed -> {rel_type}"
            else:
                neighbor_ent = from_ent
                direction = f"{rel_type} -> seed"
                
            f_type = str(neighbor_ent.get("type", "")).upper()
            
            policy = type_policies.get(f_type, {"is_metadata": False})
            is_metadata = policy.get("is_metadata", False)
            
            is_filtered = False
            reason = "답변에 사용됨"
            
            if is_metadata and not is_person:
                is_filtered = True
                reason = f"YAML 설정: {f_type} 타입은 메타데이터이므로 후순위 처리"
                
            item = {
                "name": neighbor_ent.get("name"),
                "type": f_type,
                "relation_type": direction,
                "status": "FILTERED" if is_filtered else "USED",
                "reason": reason
            }
            
            if is_filtered:
                filtered_out.append(item)
            else:
                related_entities.append(item)
                
        return {
            "seed_entity": seed_entity,
            "related_entities": related_entities,
            "filtered_out": filtered_out,
            "policy": {
                "is_person_intent_detected": is_person,
                "applied_rules_count": len(type_policies),
                "source": "filter_rules.yaml"
            }
        }
