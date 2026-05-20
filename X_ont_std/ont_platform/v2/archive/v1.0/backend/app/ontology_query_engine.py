"""온톨로지 JSON 기반 구조형 질의 엔진.

모든 메서드는 doc_ids=None 이면 전체 ontology_db를 검색.
entity_type 은 범용(PERSON 등)과 도메인 유형 모두 허용.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from . import ontology_store


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _all_entities(doc_ids: list[str] | None = None) -> list[dict]:
    """지정 문서(또는 전체)에서 모든 엔티티를 평탄화."""
    if doc_ids:
        docs = [d for d in ontology_store.list_ontologies() if d["doc_id"] in doc_ids]
    else:
        docs = ontology_store.list_ontologies()
    result: list[dict] = []
    for doc in docs:
        data = ontology_store.load_ontology(doc["doc_id"])
        if data:
            for e in data.get("entities", []):
                result.append({**e, "_doc_id": doc["doc_id"], "_filename": doc.get("filename", "")})
    return result


def _all_relationships(doc_ids: list[str] | None = None) -> list[dict]:
    if doc_ids:
        docs = [d for d in ontology_store.list_ontologies() if d["doc_id"] in doc_ids]
    else:
        docs = ontology_store.list_ontologies()
    result: list[dict] = []
    for doc in docs:
        data = ontology_store.load_ontology(doc["doc_id"])
        if data:
            for r in data.get("relationships", []):
                result.append({**r, "_doc_id": doc["doc_id"]})
    return result


def _fuzzy(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _prop_value(entity: dict, key: str) -> Any:
    props = entity.get("properties", {})
    if isinstance(props, dict):
        # 정확 일치 우선, 그 다음 대소문자 무시
        if key in props:
            return props[key]
        for k, v in props.items():
            if k.lower() == key.lower():
                return v
    return None


# ── 공개 API ──────────────────────────────────────────────────────────────────

def filter_by_property(
    entity_type: str,
    property_key: str,
    property_value: str,
    doc_ids: list[str] | None = None,
) -> list[dict]:
    """특정 유형의 엔티티 중 property_key == property_value 인 것만 반환.

    property_value 는 fuzzy match(임계값 0.6) 적용.
    """
    entities = _all_entities(doc_ids)
    result = []
    for e in entities:
        if e.get("type", "").upper() != entity_type.upper():
            continue
        val = _prop_value(e, property_key)
        if val is None:
            continue
        if _fuzzy(str(val), str(property_value)) >= 0.6:
            result.append(e)
    return result


def find_by_name(name_hint: str, doc_ids: list[str] | None = None) -> list[dict]:
    """이름 기반 fuzzy 검색 (유형 무관)."""
    entities = _all_entities(doc_ids)
    scored = [(e, _fuzzy(e.get("name", ""), name_hint)) for e in entities]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, score in scored if score >= 0.5]


def find_by_category(
    entity_type: str,
    category_hint: str,
    doc_ids: list[str] | None = None,
) -> list[dict]:
    """entity_type 중 이름 또는 임의 속성에 category_hint가 포함된 항목 반환."""
    entities = _all_entities(doc_ids)
    result = []
    hint_l = category_hint.lower()
    for e in entities:
        if e.get("type", "").upper() != entity_type.upper():
            continue
        # 이름 포함 여부
        if hint_l in e.get("name", "").lower():
            result.append(e)
            continue
        # 속성값 포함 여부
        props = e.get("properties", {})
        if isinstance(props, dict):
            for v in props.values():
                if hint_l in str(v).lower():
                    result.append(e)
                    break
    return result


def compare_entities(
    names: list[str],
    doc_ids: list[str] | None = None,
) -> dict:
    """이름 목록으로 엔티티를 찾아 속성 교집합 기반 비교표 반환.

    Returns:
      {
        "headers": ["속성1", "속성2", ...],
        "rows": [{"name": "...", "props": {"속성1": val, ...}}, ...]
      }
    """
    entities = _all_entities(doc_ids)

    # 이름 → 최적 엔티티 매핑
    matched: list[dict] = []
    for name in names:
        scored = [(e, _fuzzy(e.get("name", ""), name)) for e in entities]
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored and scored[0][1] >= 0.5:
            matched.append(scored[0][0])

    if not matched:
        return {"headers": [], "rows": []}

    # 모든 속성 키 수집 후 공통 헤더 결정 (출현 2회 이상)
    from collections import Counter
    key_counter: Counter = Counter()
    for e in matched:
        props = e.get("properties", {})
        if isinstance(props, dict):
            key_counter.update(props.keys())
    common_keys = [k for k, cnt in key_counter.items() if cnt >= max(2, len(matched) // 2)]
    if not common_keys:
        # fallback: 모든 키 포함
        common_keys = list({k for e in matched for k in (e.get("properties") or {}).keys()})

    rows = []
    for e in matched:
        props = e.get("properties", {}) or {}
        rows.append({
            "id": e.get("id", ""),
            "name": e.get("name", ""),
            "type": e.get("type", ""),
            "props": {k: props.get(k, "-") for k in common_keys},
        })

    return {"headers": common_keys, "rows": rows}


def calculate(
    metric_names: list[str],
    operation: str,
    doc_ids: list[str] | None = None,
) -> dict:
    """METRIC 유형 엔티티에서 value를 추출해 operation 적용.

    operation: sum | ratio | avg | max | min | count
    Returns: {"operation": ..., "result": ..., "unit": ..., "operands": [...]}
    """
    entities = _all_entities(doc_ids)
    metrics = [e for e in entities if e.get("type", "").upper() == "METRIC"]

    # 이름 힌트로 대상 METRIC 찾기
    targets: list[dict] = []
    for name_hint in metric_names:
        scored = [(e, _fuzzy(e.get("name", ""), name_hint)) for e in metrics]
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored and scored[0][1] >= 0.4:
            targets.append(scored[0][0])

    def _extract_number(val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(re.sub(r"[^\d.\-]", "", str(val)))
        except (ValueError, TypeError):
            return None

    values: list[float] = []
    units: list[str] = []
    operands: list[dict] = []
    for t in targets:
        props = t.get("properties", {}) or {}
        raw_val = props.get("value") or _prop_value(t, "value")
        num = _extract_number(raw_val)
        if num is not None:
            values.append(num)
            units.append(str(props.get("unit", "")))
            operands.append({"name": t.get("name", ""), "value": num, "unit": props.get("unit", "")})

    if not values:
        return {"operation": operation, "result": None, "unit": "", "operands": operands, "error": "수치 추출 실패"}

    op = operation.lower()
    if op == "sum":
        result_val: Any = sum(values)
    elif op == "avg":
        result_val = sum(values) / len(values)
    elif op == "max":
        result_val = max(values)
    elif op == "min":
        result_val = min(values)
    elif op == "count":
        result_val = len(values)
    elif op == "ratio" and len(values) >= 2:
        result_val = values[0] / values[1] if values[1] != 0 else None
    else:
        result_val = values[0] if len(values) == 1 else values

    unit = units[0] if len(set(units)) == 1 else ""
    return {"operation": operation, "result": result_val, "unit": unit, "operands": operands}


def search_relations(
    from_name: str,
    relation_hint: str | None = None,
    doc_ids: list[str] | None = None,
) -> list[dict]:
    """from_name에 해당하는 엔티티에서 뻗어나가는(또는 들어오는) 관계 목록 반환."""
    entities = _all_entities(doc_ids)
    relationships = _all_relationships(doc_ids)

    # 이름으로 엔티티 찾기
    scored = [(e, _fuzzy(e.get("name", ""), from_name)) for e in entities]
    scored.sort(key=lambda x: x[1], reverse=True)
    if not scored or scored[0][1] < 0.4:
        return []
    target_ids = {scored[0][0]["id"]}

    result = []
    for r in relationships:
        if r.get("from_id") not in target_ids and r.get("to_id") not in target_ids:
            continue
        if relation_hint and _fuzzy(r.get("relation", ""), relation_hint) < 0.4:
            continue
        # 상대 엔티티 이름 보강
        other_id = r.get("to_id") if r.get("from_id") in target_ids else r.get("from_id")
        other = next((e for e in entities if e.get("id") == other_id), {})
        result.append({
            **r,
            "from_name": scored[0][0].get("name", r.get("from_id", "")),
            "to_name": other.get("name", other_id),
        })
    return result
