import json

import httpx

from app.core.config import settings


def embed_text(text: str, model: str) -> list[float]:
    resp = httpx.post(
        f"{settings.gemini_api_base}/{model}:embedContent",
        params={"key": settings.gemini_api_key},
        json={"model": model, "content": {"parts": [{"text": text}]}, "taskType": "RETRIEVAL_DOCUMENT"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]["values"]


def generate_text(prompt: str, model: str, max_tokens: int) -> str:
    resp = httpx.post(
        f"{settings.gemini_api_base}/models/{model}:generateContent",
        params={"key": settings.gemini_api_key},
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    candidates = resp.json().get("candidates", [])
    return candidates[0]["content"]["parts"][0]["text"] if candidates else ""


async def stream_text(prompt: str, model: str, max_tokens: int):
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.gemini_api_base}/models/{model}:streamGenerateContent",
            params={"key": settings.gemini_api_key, "alt": "sse"},
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        for part in chunk.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                            if part.get("text"):
                                yield f"data: {part['text']}\n\n"
                    except Exception:
                        pass
