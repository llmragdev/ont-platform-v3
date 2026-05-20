"""온톨로지 JSON 영속성 계층.

ontology_db/ 폴더의 파일 IO를 전담.
extractor / query_engine / main 은 이 모듈을 통해서만 파일 접근.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

ONTOLOGY_DB_DIR = Path(__file__).resolve().parent.parent / "ontology_db"
REGISTRY_FILE = ONTOLOGY_DB_DIR / "ontology_registry.json"
SCHEMA_FILE = ONTOLOGY_DB_DIR / "domain_config.json"

BUILTIN_ENTITY_TYPES = [
    {"name": "PERSON",       "description": "인물, 직책, 역할",            "is_builtin": True, "properties": []},
    {"name": "ORGANIZATION", "description": "회사, 기관, 단체",            "is_builtin": True, "properties": []},
    {"name": "PRODUCT",      "description": "제품, 서비스, 기능",          "is_builtin": True, "properties": []},
    {"name": "METRIC",       "description": "수치, 지표, 통계 (value+unit)", "is_builtin": True, "properties": ["value", "unit", "period"]},
    {"name": "CONCEPT",      "description": "개념, 방법론, 아키텍처",      "is_builtin": True, "properties": []},
    {"name": "CATEGORY",     "description": "분류, 그룹, 태그",            "is_builtin": True, "properties": []},
    {"name": "EVENT",        "description": "사건, 일정, 이정표",          "is_builtin": True, "properties": ["date"]},
    {"name": "LOCATION",     "description": "지역, 클라우드 리전",         "is_builtin": True, "properties": []},
]


def _ensure_dir() -> None:
    ONTOLOGY_DB_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _write_json(path: Path, data) -> None:
    _ensure_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 레지스트리 ────────────────────────────────────────────────────────────────

def _load_registry() -> dict:
    return _read_json(REGISTRY_FILE, {})


def _save_registry(reg: dict) -> None:
    _write_json(REGISTRY_FILE, reg)


# ── 온톨로지 문서 CRUD ────────────────────────────────────────────────────────

def save_ontology(doc_id: str, data: dict) -> None:
    _ensure_dir()
    path = ONTOLOGY_DB_DIR / f"{doc_id}_ontology.json"
    _write_json(path, data)
    reg = _load_registry()
    reg[doc_id] = {
        "doc_id": doc_id,
        "filename": data.get("filename", ""),
        "entity_count": len(data.get("entities", [])),
        "relation_count": len(data.get("relationships", [])),
    }
    _save_registry(reg)


def load_ontology(doc_id: str) -> dict | None:
    path = ONTOLOGY_DB_DIR / f"{doc_id}_ontology.json"
    return _read_json(path, None)


def list_ontologies() -> list[dict]:
    return list(_load_registry().values())


def delete_ontology(doc_id: str) -> bool:
    path = ONTOLOGY_DB_DIR / f"{doc_id}_ontology.json"
    if path.exists():
        path.unlink()
    reg = _load_registry()
    existed = doc_id in reg
    reg.pop(doc_id, None)
    _save_registry(reg)
    return existed


# ── 엔티티 CRUD ───────────────────────────────────────────────────────────────

def upsert_entity(doc_id: str, entity: dict) -> dict:
    data = load_ontology(doc_id) or {"doc_id": doc_id, "entities": [], "relationships": []}
    entities: list = data.setdefault("entities", [])
    if not entity.get("id"):
        entity["id"] = f"E{uuid.uuid4().hex[:6].upper()}"
    for i, e in enumerate(entities):
        if e["id"] == entity["id"]:
            entities[i] = entity
            save_ontology(doc_id, data)
            return entity
    entities.append(entity)
    save_ontology(doc_id, data)
    return entity


def delete_entity(doc_id: str, entity_id: str) -> bool:
    data = load_ontology(doc_id)
    if not data:
        return False
    before = len(data["entities"])
    data["entities"] = [e for e in data["entities"] if e["id"] != entity_id]
    data["relationships"] = [
        r for r in data.get("relationships", [])
        if r.get("from_id") != entity_id and r.get("to_id") != entity_id
    ]
    save_ontology(doc_id, data)
    return len(data["entities"]) < before


# ── 관계 CRUD ─────────────────────────────────────────────────────────────────

def add_relationship(doc_id: str, rel: dict) -> dict:
    data = load_ontology(doc_id) or {"doc_id": doc_id, "entities": [], "relationships": []}
    rels: list = data.setdefault("relationships", [])
    if not rel.get("id"):
        rel["id"] = f"R{uuid.uuid4().hex[:6].upper()}"
    rels.append(rel)
    save_ontology(doc_id, data)
    return rel


def delete_relationship(doc_id: str, rel_id: str) -> bool:
    data = load_ontology(doc_id)
    if not data:
        return False
    before = len(data.get("relationships", []))
    data["relationships"] = [r for r in data.get("relationships", []) if r.get("id") != rel_id]
    save_ontology(doc_id, data)
    return len(data["relationships"]) < before


# ── 스키마 (domain_config) ────────────────────────────────────────────────────

def get_schema() -> dict:
    saved = _read_json(SCHEMA_FILE, {})
    domain_types = saved.get("entity_types", [])
    relation_types = saved.get("relation_types", [])
    return {
        "entity_types": BUILTIN_ENTITY_TYPES + domain_types,
        "relation_types": relation_types,
    }


def save_schema(schema: dict) -> None:
    domain_types = [t for t in schema.get("entity_types", []) if not t.get("is_builtin")]
    _write_json(SCHEMA_FILE, {
        "entity_types": domain_types,
        "relation_types": schema.get("relation_types", []),
    })


def add_entity_type(entry: dict) -> dict:
    schema = get_schema()
    domain = [t for t in schema["entity_types"] if not t.get("is_builtin")]
    entry["is_builtin"] = False
    domain.append(entry)
    save_schema({"entity_types": domain, "relation_types": schema["relation_types"]})
    return entry


def delete_entity_type(name: str) -> bool:
    schema = get_schema()
    domain = [t for t in schema["entity_types"] if not t.get("is_builtin")]
    before = len(domain)
    domain = [t for t in domain if t["name"] != name]
    save_schema({"entity_types": domain, "relation_types": schema["relation_types"]})
    return len(domain) < before


def add_relation_type(entry: dict) -> dict:
    schema = get_schema()
    schema["relation_types"].append(entry)
    save_schema(schema)
    return entry


def delete_relation_type(name: str) -> bool:
    schema = get_schema()
    before = len(schema["relation_types"])
    schema["relation_types"] = [r for r in schema["relation_types"] if r["name"] != name]
    save_schema(schema)
    return len(schema["relation_types"]) < before


# ── 그래프 뷰용 ───────────────────────────────────────────────────────────────

def get_graph(doc_id: str) -> dict:
    data = load_ontology(doc_id)
    if not data:
        return {"nodes": [], "edges": []}
    nodes = [
        {"id": e["id"], "label": e["name"], "type": e["type"], "properties": e.get("properties", {})}
        for e in data.get("entities", [])
    ]
    edges = [
        {"id": r.get("id", f"r_{i}"), "from": r["from_id"], "to": r["to_id"], "label": r["relation"]}
        for i, r in enumerate(data.get("relationships", []))
    ]
    return {"nodes": nodes, "edges": edges}
