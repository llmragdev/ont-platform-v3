from __future__ import annotations

import importlib
import os

import pytest


@pytest.fixture()
def gateway_module(monkeypatch):
    # 환경에서 키를 미리 정해 테스트의 결정성 확보
    monkeypatch.setenv("GEMINI_API_KEY", "key-a")
    monkeypatch.setenv("GEMINI_API_KEY1", "key-b")
    monkeypatch.setenv("GEMINI_API_KEY2", "key-c")
    monkeypatch.delenv("GEMINI_API_KEY3", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY4", raising=False)
    from app import llm_gateway

    return importlib.reload(llm_gateway)


def _make_search_results():
    return [{"document": {"id": "D001", "title": "P", "text": "t"}, "score": 1.0}]


def _make_context():
    return {
        "customer": {"id": "C001", "risk_tier": "Low"},
        "order": {"id": "O001", "status": "Submitted", "amount": 3200},
        "products": [],
    }


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


def test_collect_keys_dedup_and_order(gateway_module):
    keys = gateway_module._collect_keys()
    labels = [label for label, _ in keys]
    assert labels == ["GEMINI_API_KEY", "GEMINI_API_KEY1", "GEMINI_API_KEY2"]


def test_no_genai_falls_back_to_rules(gateway_module):
    gateway = gateway_module.LLMGateway()
    gateway._genai = None  # SDK 미설치 시뮬레이션
    result = gateway.generate("prompt", _make_context(), _make_search_results(), ["ApproveOrder"])
    assert result["provider"] == "rule-based"
    assert result["key_used"] is None
    assert "Decision:" in result["answer"]


def test_first_key_success(gateway_module, monkeypatch):
    calls: list[str] = []

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            calls.append(api_key)
            self.models = self

        def generate_content(self, model: str, contents: str):
            return _FakeResponse("LLM ANSWER")

    class FakeGenai:
        Client = FakeClient

    gateway = gateway_module.LLMGateway()
    gateway._genai = FakeGenai
    result = gateway.generate("prompt", _make_context(), _make_search_results(), [])
    assert result["provider"] == "gemini"
    assert result["key_used"] == "GEMINI_API_KEY"
    assert result["answer"] == "LLM ANSWER"
    assert calls == ["key-a"]
    assert gateway.stats["GEMINI_API_KEY"]["success"] == 1


def test_quota_error_rotates_to_next_key(gateway_module):
    attempts: list[str] = []

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            attempts.append(api_key)
            self.models = self

        def generate_content(self, model: str, contents: str):
            if attempts[-1] == "key-a":
                raise RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded")
            return _FakeResponse("FROM KEY B")

    class FakeGenai:
        Client = FakeClient

    gateway = gateway_module.LLMGateway()
    gateway._genai = FakeGenai
    result = gateway.generate("p", _make_context(), _make_search_results(), [])
    assert result["provider"] == "gemini"
    assert result["key_used"] == "GEMINI_API_KEY1"
    assert result["answer"] == "FROM KEY B"
    assert attempts == ["key-a", "key-b"]
    assert gateway.stats["GEMINI_API_KEY"]["quota_fail"] == 1
    assert gateway.stats["GEMINI_API_KEY1"]["success"] == 1


def test_all_keys_quota_falls_back_with_warning(gateway_module):
    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.models = self

        def generate_content(self, model: str, contents: str):
            raise RuntimeError("429 RESOURCE_EXHAUSTED")

    class FakeGenai:
        Client = FakeClient

    gateway = gateway_module.LLMGateway()
    gateway._genai = FakeGenai
    result = gateway.generate("p", _make_context(), _make_search_results(), [])
    assert result["provider"] == "rule-based"
    assert result["key_used"] is None
    assert "warning" in result
    assert "429" in result["warning"]
    for label in ("GEMINI_API_KEY", "GEMINI_API_KEY1", "GEMINI_API_KEY2"):
        assert gateway.stats[label]["quota_fail"] == 1


def test_no_search_results_raises(gateway_module):
    from app.errors import AppError

    gateway = gateway_module.LLMGateway()
    with pytest.raises(AppError) as excinfo:
        gateway.generate("p", _make_context(), [], [])
    assert excinfo.value.code == "DOCUMENT_NOT_FOUND"
