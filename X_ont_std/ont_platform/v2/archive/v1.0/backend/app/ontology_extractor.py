"""PDF 텍스트 → LLM → 엔티티/관계 JSON 추출.

범용 8종 유형 + domain_config 선택 주입 방식.
어떤 도메인의 문서든 동일한 파이프라인으로 처리.
"""
from __future__ import annotations

import json
import logging
import os

from . import ontology_store

logger = logging.getLogger(__name__)

_BUILTIN_TYPE_NAMES = [t["name"] for t in ontology_store.BUILTIN_ENTITY_TYPES]

_EXTRACTION_PROMPT = """당신은 문서에서 구조화된 지식 그래프를 추출하는 전문가입니다.

아래 문서 텍스트에서 엔티티와 관계를 추출하여 JSON으로 반환하세요.

## 엔티티 유형 목록
{entity_types}

## 추출 규칙
1. 문서에 명시된 내용만 추출 (추측·추가 금지)
2. METRIC 유형은 반드시 value(숫자), unit(단위), period(기준 시점) 속성 포함
3. 같은 엔티티가 여러 번 등장해도 1개만 생성
4. 관계는 from_id → to_id 방향 명시
5. 엔티티 id는 E001, E002... 순서로 부여

## 출력 형식 (JSON만 반환, 다른 텍스트 없음)
{{
  "entities": [
    {{
      "id": "E001",
      "type": "유형명",
      "name": "엔티티명",
      "properties": {{}}
    }}
  ],
  "relationships": [
    {{
      "id": "R001",
      "from_id": "E001",
      "relation": "관계명",
      "to_id": "E002"
    }}
  ]
}}

## 문서 텍스트
{text}
"""


def _get_api_key() -> str | None:
    for k in ("GEMINI_API_KEY", "GEMINI_API_KEY1", "GEMINI_API_KEY2", "GEMINI_API_KEY3"):
        v = os.environ.get(k)
        if v:
            return v
    return None


def _build_type_list() -> str:
    schema = ontology_store.get_schema()
    lines = []
    for t in schema["entity_types"]:
        marker = "(범용)" if t.get("is_builtin") else "(도메인)"
        lines.append(f"- {t['name']} {marker}: {t['description']}")
    return "\n".join(lines)


def _call_llm(prompt: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY를 찾을 수 없습니다.")
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        contents=prompt,
    )
    return response.text


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def extract(text: str, doc_id: str, filename: str = "") -> dict:
    """문서 텍스트에서 엔티티와 관계를 추출해 ontology_db에 저장."""
    type_list = _build_type_list()
    prompt = _EXTRACTION_PROMPT.format(entity_types=type_list, text=text[:12000])

    raw = _call_llm(prompt)
    try:
        extracted = _parse_json_response(raw)
    except Exception:
        logger.warning("JSON 파싱 실패, 재시도")
        raw2 = _call_llm(prompt + "\n\n반드시 JSON만 반환하세요. 설명 텍스트 없이.")
        extracted = _parse_json_response(raw2)

    entities = [e for e in extracted.get("entities", []) if e.get("name")]
    relationships = extracted.get("relationships", [])

    ids = set()
    deduped = []
    for e in entities:
        if e["id"] not in ids:
            ids.add(e["id"])
            deduped.append(e)

    data = {
        "doc_id": doc_id,
        "filename": filename,
        "entities": deduped,
        "relationships": relationships,
    }
    ontology_store.save_ontology(doc_id, data)
    logger.info("온톨로지 추출 완료: doc=%s entities=%d rels=%d",
                doc_id, len(deduped), len(relationships))
    return data
