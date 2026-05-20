"""15개 통합 테스트 시나리오 (하드코딩).

각 시나리오 구조:
  id         : 고유 식별자 (S01~S15)
  question   : hybrid/ask에 전송할 질문
  doc_ids    : None → 전체, 리스트 → 특정 문서
  expected_type : 기대하는 query_type (descriptive/filter/compare/calculate/hybrid)
  check      : Callable[[dict], tuple[bool, str]] — (pass, reason)
  tags       : 카테고리 태그
"""
from __future__ import annotations

from typing import Callable

from .config import SEED_DOC_ID, SNOWFLAKE_DOC_ID


def _has_answer(resp: dict, min_len: int = 50) -> tuple[bool, str]:
    ans = resp.get("answer", "")
    if not ans or len(ans) < min_len:
        return False, f"answer 길이 {len(ans)} < {min_len}"
    return True, f"answer 길이 {len(ans)}"


def _has_evidence(resp: dict, min_count: int = 1) -> tuple[bool, str]:
    ev = resp.get("evidence", [])
    if len(ev) < min_count:
        return False, f"evidence {len(ev)} < {min_count}"
    return True, f"evidence {len(ev)}건"


def _has_ontology_rows(resp: dict, min_count: int = 1) -> tuple[bool, str]:
    ont = resp.get("ontology_result", {})
    rows = ont.get("rows", [])
    if len(rows) < min_count:
        return False, f"ontology rows {len(rows)} < {min_count}"
    return True, f"ontology rows {len(rows)}개"


def _has_ontology_table(resp: dict, min_rows: int = 1) -> tuple[bool, str]:
    ont = resp.get("ontology_result", {})
    table = ont.get("table", {})
    rows = table.get("rows", []) if table else []
    if len(rows) < min_rows:
        return False, f"table rows {len(rows)} < {min_rows}"
    return True, f"table rows {len(rows)}개"


def _has_calc(resp: dict) -> tuple[bool, str]:
    ont = resp.get("ontology_result", {})
    calc = ont.get("calc", {})
    if not calc:
        return False, "ontology_result.calc 없음"
    result_val = calc.get("result")
    if result_val is None:
        return False, "calc.result 없음"
    return True, f"calc.result={result_val}"


def _has_both(resp: dict) -> tuple[bool, str]:
    ok_ev, msg_ev = _has_evidence(resp, 1)
    ont = resp.get("ontology_result", {})
    has_ont = bool(ont and (ont.get("rows") or ont.get("table") or ont.get("calc")))
    if not ok_ev and not has_ont:
        return False, "evidence 없고 ontology_result도 없음"
    if not ok_ev:
        return False, f"evidence 없음 (ontology는 있음)"
    if not has_ont:
        return False, f"ontology_result 없음 (evidence는 있음: {msg_ev})"
    return True, f"{msg_ev} + ontology 있음"


# ── 시나리오 목록 ───────────────────────────────────────────────────────────────

Scenario = dict  # type alias for readability

SCENARIOS: list[Scenario] = [
    # ── DESCRIPTIVE (5개) — RAG 중심, 문서 설명형 ──────────────────────────────
    {
        "id": "S01",
        "question": "Snowflake은 언제 설립되었고 언제 상장했나?",
        "doc_ids": [SNOWFLAKE_DOC_ID],
        "expected_type": "descriptive",
        "check": lambda r: _has_evidence(r, 1),
        "tags": ["descriptive", "rag", "history"],
        "description": "창업연도(2012)/상장(2020) — PDF p.2에 명시",
    },
    {
        "id": "S02",
        "question": "Snowflake 아키텍처의 3계층(Storage·Compute·Cloud Services)을 설명해줘",
        "doc_ids": [SNOWFLAKE_DOC_ID],
        "expected_type": "descriptive",
        "check": lambda r: _has_answer(r, 100),
        "tags": ["descriptive", "rag", "architecture"],
        "description": "3계층 아키텍처 — PDF p.7 다이어그램 기반",
    },
    {
        "id": "S03",
        "question": "Zero Copy Cloning이 스토리지 비용에 미치는 영향은?",
        "doc_ids": [SNOWFLAKE_DOC_ID],
        "expected_type": "descriptive",
        "check": lambda r: (
            any(kw in (r.get("answer") or "").lower()
                for kw in ["메타데이터", "비용", "cloning", "복제", "포인터"]),
            f"키워드 미포함: answer={r.get('answer','')[:80]}",
        ),
        "tags": ["descriptive", "rag", "cost"],
        "description": "Zero Copy Cloning — PDF p.21",
    },
    {
        "id": "S04",
        "question": "Snowflake 데이터 공유(Data Sharing)의 3가지 방식을 각각 설명해줘",
        "doc_ids": [SNOWFLAKE_DOC_ID],
        "expected_type": "descriptive",
        "check": lambda r: _has_evidence(r, 1),
        "tags": ["descriptive", "rag", "data_sharing"],
        "description": "Direct Share / Data Exchange / Marketplace — PDF p.13~14",
    },
    {
        "id": "S05",
        "question": "Virtual Warehouse의 Scale up과 Scale out은 어떻게 다른가?",
        "doc_ids": [SNOWFLAKE_DOC_ID],
        "expected_type": "descriptive",
        "check": lambda r: _has_evidence(r, 1),
        "tags": ["descriptive", "rag", "compute"],
        "description": "Scale up/out 차이 — PDF p.9",
    },

    # ── FILTER (3개) — 온톨로지 속성 필터링 ────────────────────────────────────
    {
        "id": "S06",
        "question": "NPS 점수가 40 이상인 회사를 모두 찾아줘",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "filter",
        "check": lambda r: _has_ontology_rows(r, 1),
        "tags": ["filter", "ontology", "nps"],
        "description": "ORGANIZATION 엔티티에서 nps_score >= 40 필터 → Snowflake(67), Apple(47), Google(47)",
    },
    {
        "id": "S07",
        "question": "스토리지 압축률이 70% 이상인 제품을 알려줘",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "filter",
        "check": lambda r: _has_ontology_rows(r, 1),
        "tags": ["filter", "ontology", "storage"],
        "description": "PRODUCT 엔티티에서 compression_rate >= 70 → Centralized Storage(80%)",
    },
    {
        "id": "S08",
        "question": "compute 카테고리인 제품 목록을 보여줘",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "filter",
        "check": lambda r: _has_ontology_rows(r, 1),
        "tags": ["filter", "ontology", "product"],
        "description": "PRODUCT 엔티티 category=compute → Virtual Warehouse",
    },

    # ── COMPARE (3개) — 온톨로지 엔티티 비교 ───────────────────────────────────
    {
        "id": "S09",
        "question": "Snowflake와 Oracle의 NPS 점수를 비교해줘",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "compare",
        "check": lambda r: _has_ontology_table(r, 1),
        "tags": ["compare", "ontology", "nps"],
        "description": "Snowflake(67) vs Oracle(25) — NPS 비교표",
    },
    {
        "id": "S10",
        "question": "Snowflake, IBM, Apple, Google의 NPS 점수를 비교해줘",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "compare",
        "check": lambda r: _has_ontology_table(r, 2),
        "tags": ["compare", "ontology", "nps", "multi"],
        "description": "4개 조직 NPS 비교표 — 67/27/47/47",
    },
    {
        "id": "S11",
        "question": "Virtual Warehouse와 Centralized Storage의 특성을 비교해줘",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "compare",
        "check": lambda r: (
            bool(r.get("ontology_result")),
            f"ontology_result={r.get('ontology_result')}",
        ),
        "tags": ["compare", "ontology", "product"],
        "description": "PRODUCT 2개 비교 — compute vs storage",
    },

    # ── CALCULATE (2개) — 온톨로지 수치 계산 ───────────────────────────────────
    {
        "id": "S12",
        "question": "전체 고객 수(total_customers)와 백만달러 고객 수(million_dollar_customers)를 더하면?",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "calculate",
        "check": lambda r: _has_calc(r),
        "tags": ["calculate", "ontology", "customers"],
        "description": "8537 + 402 = 8939 — METRIC 합산",
    },
    {
        "id": "S13",
        "question": "Snowflake의 NPS 점수에서 Oracle의 NPS 점수를 빼면 얼마?",
        "doc_ids": [SEED_DOC_ID],
        "expected_type": "calculate",
        "check": lambda r: _has_calc(r),
        "tags": ["calculate", "ontology", "nps"],
        "description": "67 - 25 = 42 — METRIC 차감",
    },

    # ── HYBRID (2개) — 온톨로지 + RAG 혼합 ─────────────────────────────────────
    {
        "id": "S14",
        "question": "Snowflake NPS 67점이 경쟁사 대비 어느 정도인지 문서 내용과 함께 설명해줘",
        "doc_ids": [SEED_DOC_ID, SNOWFLAKE_DOC_ID],
        "expected_type": "hybrid",
        "check": lambda r: _has_both(r),
        "tags": ["hybrid", "ontology", "rag", "nps"],
        "description": "NPS 수치(온톨로지) + 문서 설명(RAG) 혼합",
    },
    {
        "id": "S15",
        "question": "Snowflake의 설립 배경과 현재 전체 고객 수를 함께 분석해줘",
        "doc_ids": [SEED_DOC_ID, SNOWFLAKE_DOC_ID],
        "expected_type": "hybrid",
        "check": lambda r: _has_both(r),
        "tags": ["hybrid", "ontology", "rag", "history"],
        "description": "창업자 배경(RAG, p.2) + 고객 수 8537(온톨로지) 혼합",
    },
]
