"""LLM Gateway with key rotation.

전략:
1. `.env`의 `GEMINI_API_KEY`, `GEMINI_API_KEY1`, `GEMINI_API_KEY2`, `GEMINI_API_KEY3` 을 모두 수집해
   순차적으로 사용한다.
2. 호출 실패 시:
   - 429/RESOURCE_EXHAUSTED → 다음 키로 자동 전환 후 재시도 (최대 키 개수만큼)
   - 그 외 예외 → 동일 키로 1회만 시도, 실패 시 다음 키
3. 모든 키가 실패하면 규칙 기반 폴백으로 자동 대체하고 `warning` 필드에 마지막 오류 노출.

응답은 어떤 경로/모델/키가 사용됐는지 (`provider`, `model`, `key_used`)를 함께 반환한다.
"""

from __future__ import annotations

import os
from typing import Any

from .errors import AppError


DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_QUOTA_HINTS = ("RESOURCE_EXHAUSTED", "429", "quota", "rate limit")


def _collect_keys() -> list[tuple[str, str]]:
    """환경에서 사용 가능한 (label, key) 쌍을 우선순위 순으로 수집."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label in ("GEMINI_API_KEY", "GEMINI_API_KEY1", "GEMINI_API_KEY2", "GEMINI_API_KEY3", "GEMINI_API_KEY4"):
        value = os.environ.get(label)
        if value and value not in seen:
            pairs.append((label, value))
            seen.add(value)
    return pairs


def _is_quota_error(exc: Exception) -> bool:
    message = str(exc)
    return any(hint in message for hint in _QUOTA_HINTS)


class LLMGateway:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self.keys = _collect_keys()
        self.stats: dict[str, dict[str, int]] = {label: {"success": 0, "quota_fail": 0, "other_fail": 0} for label, _ in self.keys}
        self.last_used_label: str | None = None
        try:
            from google import genai  # type: ignore

            self._genai = genai
        except Exception:
            self._genai = None

    @property
    def provider(self) -> str:
        return "gemini" if self._genai is not None and self.keys else "rule-based"

    @property
    def configured_keys(self) -> list[str]:
        return [label for label, _ in self.keys]

    def health(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "keys": self.configured_keys,
            "last_used_key": self.last_used_label,
            "stats": self.stats,
        }

    def generate(
        self,
        prompt: str,
        context: dict,
        search_results: list[dict],
        available_actions: list[str],
    ) -> dict[str, Any]:
        if not search_results:
            raise AppError("DOCUMENT_NOT_FOUND", "답변에 필요한 근거 문서를 찾지 못했습니다.", 404)

        if self._genai is None or not self.keys:
            return {
                "answer": self._fallback(context, search_results, available_actions),
                "provider": "rule-based",
                "model": "fallback",
                "key_used": None,
            }

        errors: list[str] = []
        for label, key in self.keys:
            try:
                client = self._genai.Client(api_key=key)
                response = client.models.generate_content(model=self.model, contents=prompt)
                text = getattr(response, "text", None)
                if not text:
                    raise RuntimeError("empty response text")
                self.stats[label]["success"] += 1
                self.last_used_label = label
                return {
                    "answer": text,
                    "provider": "gemini",
                    "model": self.model,
                    "key_used": label,
                }
            except Exception as exc:  # noqa: BLE001 - SDK는 다양한 예외 타입 사용
                if _is_quota_error(exc):
                    self.stats[label]["quota_fail"] += 1
                    errors.append(f"{label}: 429/quota")
                    continue  # 다음 키 즉시 시도
                self.stats[label]["other_fail"] += 1
                errors.append(f"{label}: {exc.__class__.__name__}: {exc}")
                continue

        return {
            "answer": self._fallback(context, search_results, available_actions),
            "provider": "rule-based",
            "model": "fallback",
            "key_used": None,
            "warning": "모든 Gemini 키 실패, 규칙 기반 응답으로 대체: " + " | ".join(errors[-3:]),
        }

    def generate_text(self, prompt: str) -> dict[str, Any]:
        """search_results 없이 순수 프롬프트만으로 LLM 호출.

        하이브리드 질의처럼 온톨로지 데이터를 직접 프롬프트에 포함할 때 사용.
        API 키 없으면 rule-based 폴백 답변 반환.
        """
        if self._genai is None or not self.keys:
            return {
                "answer": "규칙 기반 폴백: API 키가 없어 LLM을 호출할 수 없습니다. 온톨로지 구조형 데이터를 확인하세요.",
                "provider": "rule-based",
                "model": "fallback",
                "key_used": None,
            }
        errors: list[str] = []
        for label, key in self.keys:
            try:
                client = self._genai.Client(api_key=key)
                response = client.models.generate_content(model=self.model, contents=prompt)
                text = getattr(response, "text", None)
                if not text:
                    raise RuntimeError("empty response text")
                self.stats[label]["success"] += 1
                self.last_used_label = label
                return {"answer": text, "provider": "gemini", "model": self.model, "key_used": label}
            except Exception as exc:  # noqa: BLE001
                if _is_quota_error(exc):
                    self.stats[label]["quota_fail"] += 1
                    errors.append(f"{label}: 429/quota")
                    continue
                self.stats[label]["other_fail"] += 1
                errors.append(f"{label}: {exc.__class__.__name__}: {exc}")
                continue
        return {
            "answer": "규칙 기반 폴백: 모든 Gemini 키가 실패했습니다.",
            "provider": "rule-based",
            "model": "fallback",
            "key_used": None,
            "warning": "모든 키 실패: " + " | ".join(errors[-3:]),
        }

    @staticmethod
    def _fallback(context: dict, search_results: list[dict], available_actions: list[str]) -> str:
        customer = context.get("customer", {})
        order = context.get("order", {})
        if not order:
            docs = ", ".join(item["document"]["title"] for item in search_results)
            return f"규칙 기반 폴백 (온톨로지 컨텍스트 없음). 참조 문서: {docs or '없음'}"
        if order.get("status") not in ["Submitted", "Review"]:
            decision = "Not ready"
            evidence = f"Order status is {order['status']}."
        elif customer["risk_tier"] == "High":
            decision = "Additional review required"
            evidence = "Customer risk tier is High."
        elif order["amount"] >= 5000:
            decision = "Finance manager approval required"
            evidence = "Order amount is equal to or above 5000."
        else:
            decision = "Approval is likely allowed"
            evidence = "Order is Submitted, customer risk is Low, and amount is below 5000."

        action_text = ", ".join(available_actions) if available_actions else "No executable action for current user."
        docs = ", ".join(item["document"]["title"] for item in search_results)
        return (
            f"Decision: {decision}\n"
            f"Evidence: {evidence} Retrieved documents: {docs}.\n"
            f"Required follow-up: Enterprise customers should validate contract terms before fulfillment.\n"
            f"Available actions: {action_text}"
        )
