#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gemini API 키 유효성 테스트"""

import httpx
import json
from pathlib import Path

LLM_GATEWAY_URL = "http://localhost:8010"

def test_health():
    """Health check — Gemini 연결 상태"""
    print("=" * 80)
    print("1️⃣  HEALTH CHECK")
    print("=" * 80)

    try:
        response = httpx.get(f"{LLM_GATEWAY_URL}/api/v1/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 서버 연결 성공")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        else:
            print(f"❌ 상태 코드: {response.status_code}")
            print(response.text[:500])
            return False
    except Exception as exc:
        print(f"❌ 연결 실패: {exc}")
        return False


def test_embed():
    """임베딩 테스트 — 텍스트 임베딩"""
    print("\n" + "=" * 80)
    print("2️⃣  EMBEDDING TEST (text embedding)")
    print("=" * 80)

    payload = {
        "text": "온톨로지 설계",
        "model": None,  # 기본 모델 사용
        "tenant_id": "default",
    }

    try:
        response = httpx.post(
            f"{LLM_GATEWAY_URL}/api/v1/embed",
            json=payload,
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding", [])
            print(f"✅ 임베딩 성공")
            print(f"  - 차원: {data.get('dimension')}")
            print(f"  - 모델: {data.get('model')}")
            print(f"  - 캐시됨: {data.get('cached')}")
            print(f"  - 벡터 샘플: {embedding[:3]}...")
            return True
        else:
            print(f"❌ 상태 코드: {response.status_code}")
            print(response.text[:500])
            return False
    except Exception as exc:
        print(f"❌ 임베딩 실패: {exc}")
        return False


def test_generate():
    """생성 테스트 — LLM 응답 생성"""
    print("\n" + "=" * 80)
    print("3️⃣  GENERATION TEST (LLM response)")
    print("=" * 80)

    payload = {
        "prompt": "대한민국의 수도는?",
        "model": None,  # 기본 모델 사용
        "max_tokens": 100,
        "tenant_id": "default",
        "stream": False,
    }

    try:
        response = httpx.post(
            f"{LLM_GATEWAY_URL}/api/v1/generate",
            json=payload,
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 생성 성공")
            print(f"  - 모델: {data.get('model')}")
            print(f"  - 응답: {data.get('answer')}")
            return True
        else:
            print(f"❌ 상태 코드: {response.status_code}")
            print(response.text[:500])
            return False
    except Exception as exc:
        print(f"❌ 생성 실패: {exc}")
        return False


def main():
    print("\n🔧 Gemini API 키 유효성 테스트\n")
    print(f"대상: {LLM_GATEWAY_URL}\n")

    results = {
        "health": test_health(),
        "embed": test_embed(),
        "generate": test_generate(),
    }

    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"통과: {passed}/{total}")

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  - {test_name}: {status}")

    if passed == total:
        print("\n🎉 모든 API 테스트 성공!")
    else:
        print("\n⚠️  일부 테스트 실패. 에러 메시지를 확인하세요.")


if __name__ == "__main__":
    main()
