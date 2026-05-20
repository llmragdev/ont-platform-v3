"""질문 유형 분류기.

LLM 1회 호출로 질문을 5가지 유형으로 분류:
  descriptive — 서술적 설명 (벡터 검색으로 처리)
  filter      — 특정 조건으로 필터링 ("~한 기능 목록은?")
  compare     — 두 개 이상 엔티티 비교 ("A vs B 비교")
  calculate   — 수치 계산 ("매출 합계", "비율은?")
  hybrid      — 구조형 + 서술형 혼합
"""
from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

_CLASSIFIER_PROMPT = """당신은 질문 유형을 분류하는 전문가입니다.

아래 질문을 읽고 JSON만 반환하세요 (설명 텍스트 없음).

## 질문 유형
- descriptive: 개념 설명, 배경 정보, "~란 무엇인가", "~를 설명해줘"
- filter: 특정 조건을 만족하는 항목 목록 조회. "~한 것들은?", "~에 해당하는 모든 ~"
- compare: 두 개 이상 항목의 속성을 비교. "~와 ~ 비교", "차이점은?"
- calculate: 숫자 계산, 합계, 비율, 평균 등. "총 ~는?", "비율은?", "~의 합계"
- hybrid: 구조형 데이터(필터/비교/계산)와 서술형 설명이 모두 필요

## 출력 형식 (JSON만 반환)
{{
  "type": "descriptive|filter|compare|calculate|hybrid",
  "entities": ["추출된 엔티티 이름 목록"],
  "operation": "list|compare|sum|avg|max|min|ratio|count|explain",
  "property_key": "필터 기준 속성명 (filter 유형만, 없으면 null)",
  "property_value": "필터 기준 속성값 (filter 유형만, 없으면 null)",
  "entity_type": "엔티티 유형 힌트 (PERSON/ORGANIZATION/PRODUCT/METRIC/CONCEPT/CATEGORY/EVENT/LOCATION, 모르면 null)"
}}

## 질문
{question}
"""

_FALLBACK = {
    "type": "descriptive",
    "entities": [],
    "operation": "explain",
    "property_key": None,
    "property_value": None,
    "entity_type": None,
}


def _get_api_key() -> str | None:
    for k in ("GEMINI_API_KEY", "GEMINI_API_KEY1", "GEMINI_API_KEY2", "GEMINI_API_KEY3"):
        v = os.environ.get(k)
        if v:
            return v
    return None


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


def _parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def classify(question: str) -> dict:
    """질문 유형을 분류해 딕셔너리 반환. 실패 시 descriptive 폴백."""
    try:
        prompt = _CLASSIFIER_PROMPT.format(question=question)
        raw = _call_llm(prompt)
        result = _parse(raw)
        # 필수 키 보강
        for k, v in _FALLBACK.items():
            result.setdefault(k, v)
        return result
    except Exception as exc:
        logger.warning("질문 분류 실패, descriptive 폴백: %s", exc)
        return {**_FALLBACK}
