import re
from typing import List, Dict, Any

# 한국어 불용어 (조사 및 서술어/부사)
STOPWORDS = {
    # 조사
    "은", "는", "이", "가", "을", "를", "에서", "와", "과", "로", "으로", "에", "의", "도", "만", "부터", "까지",
    # 서술어/부사 파편 (Phase 0 발견)
    "함께", "관리", "필요한", "어떤", "이유", "무엇", "어떻게", "왜", "하는가", "하는", "할", "때", "있는",
    "없다", "있다", "이다", "아니다", "해야", "위한", "위해", "대해", "대한", "무슨", "어느"
}

def _remove_suffix_particles(word: str) -> str:
    for particle in sorted(STOPWORDS, key=len, reverse=True):
        if word.endswith(particle) and len(word) > len(particle):
            return word[:-len(particle)]
    return word

def extract_query_entity_candidates(query: str) -> List[str]:
    """
    질문에서 불용어와 조사를 제거하고 핵심 엔티티 후보 명사구를 추출합니다.
    """
    # 1. 원본에서 주요 어절(2~3단어 조합)을 먼저 추출하여 보존
    words = query.split()
    candidates = []
    
    for i in range(len(words)):
        # 1-gram
        candidates.append(words[i])
        # 2-gram
        if i < len(words) - 1:
            candidates.append(words[i] + " " + words[i+1])
            
    cleaned_candidates = set()
    for c in candidates:
        # 구두점 제거
        clean_c = re.sub(r'[^\w\s]', '', c).strip()
        if not clean_c:
            continue
            
        # 어절 단위 조사 제거
        parts = clean_c.split()
        if parts:
            parts[-1] = _remove_suffix_particles(parts[-1])
            clean_token = " ".join(parts)
            
            # 길이 2 이상이거나 영문/숫자 포함 시 보존 (완전 불용어 일치 시 제외)
            if clean_token not in STOPWORDS and (re.search(r'[a-zA-Z0-9]', clean_token) or len(clean_token.replace(" ", "")) >= 2):
                cleaned_candidates.add(clean_token)
                
    return list(cleaned_candidates)

def calculate_ontology_entity_overlap(query_entities: List[str], ontology_entities: List[str]) -> float:
    if not query_entities:
        return 0.0
        
    matched_count = 0
    ont_lower = [e.lower() for e in ontology_entities]
    
    for qe in query_entities:
        qe_lower = qe.lower()
        if any(qe_lower in ont_e or ont_e in qe_lower for ont_e in ont_lower):
            matched_count += 1
            
    return matched_count / len(query_entities)

def calculate_chunk_entity_overlap(query_entities: List[str], chunk_text: str, chunk_metadata: Dict[str, Any]) -> float:
    """
    chunk_metadata에 엔티티가 없으므로(Phase 0 분석 결과), chunk_text 직접 포함 여부로 fallback 계산.
    """
    if not query_entities:
        return 0.0
        
    chunk_lower = chunk_text.lower()
    matched_count = 0
    
    for qe in query_entities:
        qe_lower = qe.lower()
        if qe_lower in chunk_lower:
            matched_count += 1
            
    return matched_count / len(query_entities)

def evaluate_chunk_entity_match(query_entities: List[str], chunk_text: str, chunk_metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Return detailed chunk-text match diagnostics. Current vector chunks do not
    carry extracted_entities metadata, so this intentionally records text
    fallback usage for downstream audit.
    """
    if not query_entities:
        return {
            "chunk_entity_overlap": 0.0,
            "matched_query_entities": [],
            "missing_query_entities": [],
            "matched_query_entities_count": 0,
            "metadata_absent_fallback_used": True,
        }

    metadata = chunk_metadata or {}
    metadata_entities = metadata.get("extracted_entities") or metadata.get("entities") or []
    metadata_absent = not bool(metadata_entities)

    chunk_lower = (chunk_text or "").lower()
    matched: List[str] = []
    missing: List[str] = []

    for entity in query_entities:
        entity_lower = entity.lower()
        if entity_lower in chunk_lower:
            matched.append(entity)
        else:
            missing.append(entity)

    return {
        "chunk_entity_overlap": len(matched) / len(query_entities),
        "matched_query_entities": matched,
        "missing_query_entities": missing,
        "matched_query_entities_count": len(matched),
        "metadata_absent_fallback_used": metadata_absent,
    }
