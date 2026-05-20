"""OpenTelemetry 통합 (#8).

설계 원칙:
1. ``opentelemetry-*`` 패키지가 설치되어 있으면 자동 활성화, 없으면 no-op fallback.
2. ``OTEL_ENABLED=false`` 환경변수로 강제 비활성 가능.
3. ``OTEL_EXPORTER_OTLP_ENDPOINT`` 가 있으면 OTLP/HTTP exporter (Jaeger/Tempo/Collector).
4. 없으면 콘솔(stdout) exporter — 교육 환경에서 즉시 trace 확인 가능.
5. AppContext의 ``ask()`` 8단계가 자동으로 child span 생성.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator


_otel_enabled = False
_tracer = None


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def setup(app: Any | None = None, service_name: str = "claud-tonghap-backend") -> bool:
    """OpenTelemetry SDK + FastAPI instrumentation 활성화.

    의존성이 없거나 ``OTEL_ENABLED=false`` 면 no-op.
    """
    global _otel_enabled, _tracer

    if not _bool_env("OTEL_ENABLED", True):
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )
    except ImportError:
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")))
        except ImportError:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        # 콘솔 출력은 시끄러우니 기본은 비활성. 명시적으로 켤 때만 사용.
        if _bool_env("OTEL_CONSOLE_EXPORTER", False):
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("claud_tonghap")
    _otel_enabled = True

    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except ImportError:
            pass

    return True


def is_enabled() -> bool:
    return _otel_enabled


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    """OpenTelemetry span을 만들거나, 미활성 시 no-op.

    사용:
        with span("rag.build_prompt", question=q):
            ...
    """
    if _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            try:
                current.set_attribute(key, value)
            except Exception:
                # 직렬화 불가 속성은 건너뜀
                pass
        yield current
