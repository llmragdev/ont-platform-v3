"""LlmClient — Gemini API wrapper for v3.0.

All LLM calls go through this class.
  - enabled=False when GEMINI_API_KEY is not set → all methods return empty/None
  - Retry: up to 3 attempts with exponential backoff
  - Timeout: 30s per call (enforced by google-generativeai SDK)
"""
from __future__ import annotations

import json
import logging
import os
import time

logger = logging.getLogger(__name__)


class LlmClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY1")
        self._model = model or os.getenv("LLM_MODEL_NAME") or "gemini-2.5-flash-lite"
        self._enabled = False
        self._client = None

        if self._api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai.GenerativeModel(model_name=self._model)
                self._enabled = True
                logger.info("[LLM] Gemini initialized model=%s", self._model)
            except Exception as exc:
                logger.warning("[LLM] Failed to initialize Gemini: %s", exc)
        else:
            logger.info("[LLM] GEMINI_API_KEY not set — running in fallback mode")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str | None:
        """Generate text. Returns None if disabled or all retries fail."""
        if not self._enabled:
            return None
        for attempt in range(3):
            try:
                logger.info(
                    "[LLM] generate attempt=%d model=%s prompt_len=%d",
                    attempt + 1, self._model, len(prompt),
                )
                response = self._client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )
                text = response.text
                logger.info("[LLM] generate ok chars=%d", len(text))
                return text
            except Exception as exc:
                logger.warning("[LLM] generate attempt=%d failed: %s", attempt + 1, exc)
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None

    def classify(self, prompt: str) -> dict:
        """Classify with JSON response. Returns {} on failure."""
        if not self._enabled:
            return {}
        text = self.generate(prompt, temperature=0.1, max_tokens=256)
        if not text:
            return {}
        cleaned = text.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else cleaned
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned.strip())
        except Exception:
            logger.warning("[LLM] classify JSON parse failed: %r", text[:200])
            return {}
