from typing import Dict, Any

def evaluate_answerability(
    ontology_overlap: float, 
    chunk_overlap: float, 
    mode: str = "restrict",
    matched_query_entities_count: int = 0,
) -> Dict[str, Any]:
    """
    지시서의 Threshold 규칙에 따라 응답 모드(NO_ANSWER, PARTIAL, NORMAL, GENERAL_ONLY) 판정.
    """
    status = "NO_ANSWER"
    decision = "blocked"
    
    if mode in ["restrict", "document_only"]:
        if ontology_overlap >= 0.40 or (chunk_overlap >= 0.50 and matched_query_entities_count >= 2):
            # 완벽한 Threshold 초과 시 NORMAL, 아슬아슬하면 PARTIAL
            status = "NORMAL" if ontology_overlap >= 0.60 or chunk_overlap >= 0.70 else "PARTIAL"
    elif mode in ["partial_allowed", "document_with_limits"]:
        if ontology_overlap >= 0.20 or chunk_overlap >= 0.30:
            status = "PARTIAL"
    elif mode in ["expert", "expert_mode"]:
        status = "GENERAL_ONLY"  # 전문가 모드는 근거 부족 시에도 일반 설명으로 분리한다.
    else:
        # Default fallback
        if ontology_overlap >= 0.40 or (chunk_overlap >= 0.50 and matched_query_entities_count >= 2):
            status = "NORMAL"

    if status == "NORMAL":
        decision = "pass"
    elif status in {"PARTIAL", "GENERAL_ONLY"}:
        decision = "partial"
            
    return {
        "answer_status": status,
        "decision": decision,
        "thresholds": {
            "restrict": {
                "ontology_overlap": 0.40,
                "chunk_overlap": 0.50,
                "matched_query_entities_count": 2,
            },
            "partial_allowed": {
                "ontology_overlap": 0.20,
                "chunk_overlap": 0.30,
            },
            "expert": {
                "ontology_overlap": 0.10,
                "chunk_overlap": 0.10,
            },
        },
        "gate_status": {
            "entity_lexical_gate": "PASS" if status != "NO_ANSWER" else "FAIL",
            "ontology_boundary_gate": "PASS" if ontology_overlap >= 0.20 else "FAIL",
            "answerability_gate": "PASS" if status != "NO_ANSWER" else "FAIL"
        }
    }
