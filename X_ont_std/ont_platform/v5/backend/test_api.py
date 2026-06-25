#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test adaptive_query API"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

API_BASE = "http://127.0.0.1:8001"
PROJECT_ID = "proj-deafe1fe"

test_questions = [
    "Class와 Property의 차이점은?",
    "온톨로지 매칭 성능은 어떤 지표로 평가할 수 있는가?",
    "Snowflake 기반 QA 테스트에서 응답 시간과 운영 제약을 함께 봐야 하는 이유는?",
]

for i, q in enumerate(test_questions, 1):
    print(f"\n[{i}/3] 질문: {q}")
    print("-" * 60)

    url = f"{API_BASE}/api/v1/projects/{PROJECT_ID}/query/stream"
    params = {
        "project_id": PROJECT_ID,
        "session_id": f"test-q{i}",
        "query": q,
        "mode": "expert_mode",
        "hide_irrelevant": "true",
        "allow_partial": "true",
        "separate_sources": "true",
        "allow_general": "true",
    }

    try:
        with requests.get(url, params=params, stream=True, timeout=10) as response:
            answer_text = ""
            events_received = []

            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        event = data.get('event', 'unknown')
                        events_received.append(event)

                        if event == 'answer_chunk':
                            answer_text += data.get('data', {}).get('token', '')
                        elif event == 'sources':
                            sources = data.get('data', {})
                            rag_count = len(sources.get('rag', []))
                            ont_count = len(sources.get('ontology', []))
                            print(f"  RAG: {rag_count}, Ontology: {ont_count}")
                    except:
                        pass

            print(f"  답변: {answer_text[:100]}...")
            print(f"  Events: {set(events_received)}")

    except Exception as e:
        print(f"  ERROR: {str(e)}")

print("\n" + "=" * 60)
print("테스트 완료")
