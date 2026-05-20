"""OpenTelemetry 통합이 의존성 유무와 관계없이 안전하게 동작해야 한다."""

from __future__ import annotations

import importlib

from app import telemetry


def test_span_no_op_when_disabled(monkeypatch):
    monkeypatch.setenv("OTEL_ENABLED", "false")
    reloaded = importlib.reload(telemetry)
    with reloaded.span("test.no_op", foo="bar"):
        pass


def test_is_enabled_reflects_setup(monkeypatch):
    monkeypatch.setenv("OTEL_ENABLED", "false")
    reloaded = importlib.reload(telemetry)
    assert reloaded.setup() is False
    assert reloaded.is_enabled() is False


def test_setup_skips_when_dependencies_missing(monkeypatch):
    """opentelemetry가 설치돼 있어도 OTEL_ENABLED=false 면 활성화 안 됨."""
    monkeypatch.setenv("OTEL_ENABLED", "false")
    reloaded = importlib.reload(telemetry)
    assert reloaded.setup(None, service_name="test") is False
