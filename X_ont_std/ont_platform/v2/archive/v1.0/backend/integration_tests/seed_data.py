"""Snowflake 소개서 기반 온톨로지 시드 데이터.

PDF(doc-ff68a066)에서 확인된 수치를 하드코딩하여 결정론적 테스트 환경을 구성.
`inject()` 를 호출하면 SEED_DOC_ID 문서에 엔티티+관계를 주입하고 기존 항목은 삭제.
"""
from __future__ import annotations

import requests

from .config import BASE_URL, DEFAULT_USER, HEADERS, SEED_DOC_ID

# ── 엔티티 정의 ────────────────────────────────────────────────────────────────
# PDF 수치 출처: Snowflake_소개서_HDC.pdf (Q2 FY24, p.3)

ENTITIES: list[dict] = [
    # ── METRIC (p.3 수치) ─────────────────────────────────────────────────────
    {
        "id": "M001", "type": "METRIC", "name": "product_revenue",
        "properties": {"value": 640.2, "unit": "M USD", "yoy_growth": 37,
                        "period": "Q2 FY24"},
    },
    {
        "id": "M002", "type": "METRIC", "name": "total_customers",
        "properties": {"value": 8537, "unit": "개", "yoy_growth": 25},
    },
    {
        "id": "M003", "type": "METRIC", "name": "million_dollar_customers",
        "properties": {"value": 402, "unit": "개", "yoy_growth": 62,
                        "description": "$1M 이상 고객 수"},
    },
    {
        "id": "M004", "type": "METRIC", "name": "marketplace_listings",
        "properties": {"value": 2149, "unit": "개"},
    },
    {
        "id": "M005", "type": "METRIC", "name": "storage_compression_rate",
        "properties": {"value": 80, "unit": "%",
                        "description": "Centralized Storage 평균 압축률"},
    },
    {
        "id": "M006", "type": "METRIC", "name": "nps_score_snowflake",
        "properties": {"value": 67, "unit": "점",
                        "description": "Net Promoter Score (as of July 2023)"},
    },
    # ── ORGANIZATION (NPS 비교용) ─────────────────────────────────────────────
    {
        "id": "O001", "type": "ORGANIZATION", "name": "Snowflake",
        "properties": {"nps_score": 67, "founded": 2012, "ipo_year": 2020,
                        "db_rank": 11, "headquarters": "USA"},
    },
    {
        "id": "O002", "type": "ORGANIZATION", "name": "Oracle",
        "properties": {"nps_score": 25, "db_rank": 1},
    },
    {
        "id": "O003", "type": "ORGANIZATION", "name": "IBM",
        "properties": {"nps_score": 27},
    },
    {
        "id": "O004", "type": "ORGANIZATION", "name": "Apple",
        "properties": {"nps_score": 47},
    },
    {
        "id": "O005", "type": "ORGANIZATION", "name": "Google",
        "properties": {"nps_score": 47},
    },
    # ── PRODUCT (Snowflake 주요 제품/기능) ────────────────────────────────────
    {
        "id": "P001", "type": "PRODUCT", "name": "Virtual Warehouse",
        "properties": {"billing": "second", "scale_up": True,
                        "scale_out": True, "category": "compute"},
    },
    {
        "id": "P002", "type": "PRODUCT", "name": "Centralized Storage",
        "properties": {"compression_rate": 80, "encryption": "automatic",
                        "category": "storage"},
    },
    {
        "id": "P003", "type": "PRODUCT", "name": "Data Sharing",
        "properties": {"modes": "Direct/Exchange/Marketplace",
                        "category": "feature"},
    },
    {
        "id": "P004", "type": "PRODUCT", "name": "Snowpark",
        "properties": {"languages": "Python/Java/Scala",
                        "category": "developer_framework"},
    },
    # ── CONCEPT (Snowflake 핵심 개념) ─────────────────────────────────────────
    {
        "id": "C001", "type": "CONCEPT", "name": "Time Travel",
        "properties": {"mechanism": "MVCC",
                        "description": "과거 특정 시점 데이터 복원"},
    },
    {
        "id": "C002", "type": "CONCEPT", "name": "Zero Copy Cloning",
        "properties": {"billing": "incremental",
                        "description": "메타데이터 포인터만 복사, 물리 복사 없음",
                        "storage_saving": True},
    },
    # ── PERSON (창업자) ───────────────────────────────────────────────────────
    {
        "id": "PR001", "type": "PERSON", "name": "Benoit Dageville",
        "properties": {"role": "Co-founder", "background": "Lead architect Oracle",
                        "expertise": "parallel query execution"},
    },
    {
        "id": "PR002", "type": "PERSON", "name": "Thierry Curanes",
        "properties": {"role": "Co-founder", "background": "Lead architect Oracle",
                        "expertise": "query optimization"},
    },
]

# ── 관계 정의 ──────────────────────────────────────────────────────────────────
RELATIONSHIPS: list[dict] = [
    {"from_id": "O001", "relation": "HAS_METRIC",   "to_id": "M001"},
    {"from_id": "O001", "relation": "HAS_METRIC",   "to_id": "M002"},
    {"from_id": "O001", "relation": "HAS_METRIC",   "to_id": "M003"},
    {"from_id": "O001", "relation": "HAS_METRIC",   "to_id": "M006"},
    {"from_id": "O001", "relation": "HAS_PRODUCT",  "to_id": "P001"},
    {"from_id": "O001", "relation": "HAS_PRODUCT",  "to_id": "P002"},
    {"from_id": "O001", "relation": "HAS_PRODUCT",  "to_id": "P003"},
    {"from_id": "O001", "relation": "FOUNDED_BY",   "to_id": "PR001"},
    {"from_id": "O001", "relation": "FOUNDED_BY",   "to_id": "PR002"},
]


# ── 주입 함수 ──────────────────────────────────────────────────────────────────

def _url(path: str) -> str:
    return f"{BASE_URL}{path}?user={DEFAULT_USER}"


def _delete_existing() -> None:
    """기존 시드 문서 삭제 (있을 경우)."""
    resp = requests.get(_url(f"/api/ontology/{SEED_DOC_ID}/entities"), headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        entities = resp.json().get("entities", [])
        for e in entities:
            requests.delete(_url(f"/api/ontology/{SEED_DOC_ID}/entities/{e['id']}"),
                            headers=HEADERS, timeout=10)
    # 관계도 삭제
    resp2 = requests.get(_url(f"/api/ontology/{SEED_DOC_ID}/relationships"), headers=HEADERS, timeout=10)
    if resp2.status_code == 200:
        rels = resp2.json().get("relationships", [])
        for r in rels:
            requests.delete(_url(f"/api/ontology/{SEED_DOC_ID}/relationships/{r['id']}"),
                            headers=HEADERS, timeout=10)


def inject(verbose: bool = True) -> dict:
    """엔티티 + 관계를 서버 API를 통해 SEED_DOC_ID에 주입.

    Returns:
        {"entities": N, "relationships": N, "errors": [...]}
    """
    if verbose:
        print(f"[seed] 기존 데이터 삭제 중 ({SEED_DOC_ID})...")
    _delete_existing()

    errors: list[str] = []
    entity_count = 0
    rel_count = 0

    if verbose:
        print(f"[seed] 엔티티 {len(ENTITIES)}개 주입 중...")
    for entity in ENTITIES:
        resp = requests.post(
            _url(f"/api/ontology/{SEED_DOC_ID}/entities"),
            json={"type": entity["type"], "name": entity["name"],
                  "properties": entity.get("properties", {})},
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            # 반환된 id(자동생성)를 덮어쓰기 위해 PUT으로 id 고정
            created_id = resp.json().get("id")
            if created_id and created_id != entity["id"]:
                # id를 원하는 값으로 재설정 (properties에 orig_id 태그)
                pass  # 서버가 자동 생성한 id 사용 (쿼리는 name 기반)
            entity_count += 1
        else:
            errors.append(f"entity {entity['id']}: {resp.status_code} {resp.text[:80]}")

    if verbose:
        print(f"[seed] 관계 {len(RELATIONSHIPS)}개 주입 중...")
    # 관계는 name 기반이므로 실제 주입된 entity 목록에서 id 매핑
    resp_list = requests.get(_url(f"/api/ontology/{SEED_DOC_ID}/entities"),
                              params={"size": 100}, headers=HEADERS, timeout=10)
    name_to_id: dict[str, str] = {}
    if resp_list.status_code == 200:
        for e in resp_list.json().get("entities", []):
            name_to_id[e["name"]] = e["id"]

    # ENTITIES의 논리 id → 서버 실제 id 매핑
    logic_to_server: dict[str, str] = {}
    for entity in ENTITIES:
        sid = name_to_id.get(entity["name"])
        if sid:
            logic_to_server[entity["id"]] = sid

    for rel in RELATIONSHIPS:
        from_server = logic_to_server.get(rel["from_id"])
        to_server   = logic_to_server.get(rel["to_id"])
        if not from_server or not to_server:
            errors.append(f"rel {rel['relation']}: id 매핑 실패 ({rel['from_id']}→{rel['to_id']})")
            continue
        resp = requests.post(
            _url(f"/api/ontology/{SEED_DOC_ID}/relationships"),
            json={"from_id": from_server, "relation": rel["relation"], "to_id": to_server},
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            rel_count += 1
        else:
            errors.append(f"rel {rel['relation']}: {resp.status_code} {resp.text[:80]}")

    summary = {"entities": entity_count, "relationships": rel_count,
               "errors": errors, "doc_id": SEED_DOC_ID}
    if verbose:
        print(f"[seed] 완료: 엔티티 {entity_count}개 / 관계 {rel_count}개 / 오류 {len(errors)}건")
        for e in errors:
            print(f"  ⚠ {e}")
    return summary
