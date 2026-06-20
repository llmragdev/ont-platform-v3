#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Team5 v5 시스템 24문항 평가 (백엔드 직접 테스트)
모드: 전문가모드 (expert_mode)
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import asyncio
from datetime import datetime

# 설정
API_BASE = "http://127.0.0.1:8001"
PROJECT_ID = "proj-deafe1fe"  # demo-co의 프로젝트

# 24개 평가 질문
EVALUATION_QUESTIONS = [
    # Ontology 관련 (8개)
    {
        "id": 1,
        "category": "Ontology",
        "text": "온톨로지 기반 질의응답에서 온톨로지는 어떤 역할을 하는가?",
        "expected_items": ["개념분류", "관계모델링", "Class/Property/Instance", "의미적통합", "상호운용성"]
    },
    {
        "id": 2,
        "category": "Ontology",
        "text": "온톨로지의 Class와 Property의 차이점은 무엇인가?",
        "expected_items": ["Class", "Property", "정의", "인스턴스"]
    },
    {
        "id": 3,
        "category": "Ontology",
        "text": "온톨로지에서 관계(Relationship)의 중요성은?",
        "expected_items": ["관계", "의미", "연결", "추론"]
    },
    {
        "id": 4,
        "category": "Ontology",
        "text": "온톨로지 기반 검색의 장점은 무엇인가?",
        "expected_items": ["의미기반", "정확성", "구조화", "확장성"]
    },
    {
        "id": 5,
        "category": "Ontology",
        "text": "온톨로지 설계 시 고려해야 할 사항은?",
        "expected_items": ["일관성", "확장성", "유지보수", "성능"]
    },
    {
        "id": 6,
        "category": "Ontology",
        "text": "온톨로지 기반 질의응답 시스템의 구성 요소는?",
        "expected_items": ["검색", "매칭", "추론", "답변생성"]
    },
    {
        "id": 7,
        "category": "Ontology",
        "text": "온톨로지의 한계점과 극복 방안은?",
        "expected_items": ["한계", "극복", "해결", "개선"]
    },
    {
        "id": 8,
        "category": "Ontology",
        "text": "온톨로지와 지식그래프의 관계는?",
        "expected_items": ["온톨로지", "지식그래프", "관계", "구조"]
    },

    # Advanced RAG 관련 (8개)
    {
        "id": 9,
        "category": "Advanced RAG",
        "text": "RAG 시스템에서 검색 정확도를 높이는 방법은?",
        "expected_items": ["질의확장", "메타데이터", "청킹", "재순위화"]
    },
    {
        "id": 10,
        "category": "Advanced RAG",
        "text": "벡터 검색과 키워드 검색의 차이점은?",
        "expected_items": ["벡터", "키워드", "의미", "문법"]
    },
    {
        "id": 11,
        "category": "Advanced RAG",
        "text": "청킹 전략이 RAG 성능에 미치는 영향은?",
        "expected_items": ["청킹", "성능", "정확도", "효율성"]
    },
    {
        "id": 12,
        "category": "Advanced RAG",
        "text": "다단계 검색(Multi-hop search)의 개념은?",
        "expected_items": ["다단계", "검색", "정확성", "복잡도"]
    },
    {
        "id": 13,
        "category": "Advanced RAG",
        "text": "RAG 시스템의 환각(Hallucination) 문제와 해결책은?",
        "expected_items": ["환각", "검증", "근거", "신뢰도"]
    },
    {
        "id": 14,
        "category": "Advanced RAG",
        "text": "임베딩 모델 선택 시 고려사항은?",
        "expected_items": ["성능", "속도", "차원", "호환성"]
    },
    {
        "id": 15,
        "category": "Advanced RAG",
        "text": "RAG에서 문서 전처리의 중요성은?",
        "expected_items": ["정제", "정규화", "품질", "효율"]
    },
    {
        "id": 16,
        "category": "Advanced RAG",
        "text": "하이브리드 검색(Hybrid Search)의 개념은?",
        "expected_items": ["벡터", "키워드", "결합", "최적화"]
    },

    # Snowflake 관련 (8개)
    {
        "id": 17,
        "category": "Snowflake",
        "text": "Snowflake 기반 RAG 평가에서 정확도를 높이는 방법은?",
        "expected_items": ["데이터", "쿼리", "정확도", "최적화"]
    },
    {
        "id": 18,
        "category": "Snowflake",
        "text": "데이터 웨어하우스에서 질의응답 시스템 구축의 장점은?",
        "expected_items": ["확장성", "성능", "데이터", "분석"]
    },
    {
        "id": 19,
        "category": "Snowflake",
        "text": "대규모 데이터셋에서 효율적인 검색 방법은?",
        "expected_items": ["인덱싱", "파티셔닝", "캐싱", "최적화"]
    },
    {
        "id": 20,
        "category": "Snowflake",
        "text": "Snowflake의 성능 최적화 전략은?",
        "expected_items": ["병렬화", "클러스터링", "압축", "비용"]
    },
    {
        "id": 21,
        "category": "Snowflake",
        "text": "데이터 품질이 QA 시스템 성능에 미치는 영향은?",
        "expected_items": ["품질", "정확도", "신뢰", "영향"]
    },
    {
        "id": 22,
        "category": "Snowflake",
        "text": "실시간 데이터 처리와 배치 처리의 trade-off는?",
        "expected_items": ["실시간", "배치", "지연", "비용"]
    },
    {
        "id": 23,
        "category": "Snowflake",
        "text": "데이터 거버넌스와 QA 시스템의 관계는?",
        "expected_items": ["거버넌스", "품질", "규정", "감시"]
    },
    {
        "id": 24,
        "category": "Snowflake",
        "text": "멀티테넌트 환경에서 데이터 격리와 성능 관리는?",
        "expected_items": ["격리", "성능", "보안", "관리"]
    },
]

def evaluate_single_question(question_id: int, question_text: str, mode: str = "expert_mode") -> dict:
    """단일 질문 평가"""
    try:
        url = f"{API_BASE}/api/v1/projects/{PROJECT_ID}/query/stream"
        params = {
            "project_id": PROJECT_ID,
            "session_id": f"eval-q{question_id}-{mode}",
            "query": question_text,
            "mode": mode,
            "hide_irrelevant": "true",
            "allow_partial": "true",
            "separate_sources": "true",
            "allow_general": "true",
        }

        # SSE 스트림으로 응답 수집
        answer = ""
        with requests.get(url, params=params, stream=True, timeout=30) as response:
            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if 'token' in data:
                            answer += data.get('token', '')
                    except:
                        pass

        # Two scores are kept:
        # - score_conservative: early Team5 keyword-only smoke score
        # - score_v12_comparable: Team4 workbook-compatible score with Snowflake trap rules
        score_conservative = 50 if answer else 0
        score_v12_comparable = score_conservative
        matched_items = []
        if answer:
            category = EVALUATION_QUESTIONS[question_id - 1].get('category')
            expected_items = EVALUATION_QUESTIONS[question_id - 1].get('expected_items', [])
            matched_items = [item for item in expected_items if item in answer]
            score_conservative = min(100, 50 + (len(matched_items) * 10))
            
            # v1.2 특별 규칙 반영 (Snowflake 함정 질문)
            if category == "Snowflake":
                # 함정 감지 성공 조건 (백엔드의 실제 응답 문구 반영)
                if any(phrase in answer for phrase in ["관련 없음", "문서에 없음", "근거 없음", "없습니다", "확인하지 못했습니다"]):
                    score_v12_comparable = 100
                elif "Snowflake" in answer or "스노우플레이크" in answer:
                    score_v12_comparable = max(0, score_conservative - 50)
                else:
                    score_v12_comparable = score_conservative
            else:
                score_v12_comparable = score_conservative

        return {
            "question_id": question_id,
            "question": question_text,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "score": score_v12_comparable,
            "score_v12_comparable": score_v12_comparable,
            "score_conservative": score_conservative,
            "matched_items": matched_items,
            "scoring_note": "v1.2 Snowflake trap rule applied" if EVALUATION_QUESTIONS[question_id - 1].get('category') == "Snowflake" else "keyword match",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Q{question_id} 평가 실패: {str(e)}")
        return {
            "question_id": question_id,
            "question": question_text,
            "score": 0,
            "error": str(e)
        }

def main():
    """24문항 평가 실행"""
    print("🧪 v5 시스템 24문항 전문가모드 평가 시작...")
    print(f"📊 모드: expert_mode")
    print(f"📍 프로젝트: {PROJECT_ID}")
    print(f"⏱️  시작: {datetime.now().isoformat()}")
    print()

    results = []

    # 24문항 순차 평가
    for i, question in enumerate(EVALUATION_QUESTIONS, 1):
        print(f"[{i}/24] 평가 중: {question['text'][:50]}...")
        result = evaluate_single_question(question['id'], question['text'], "expert_mode")
        result['category'] = question['category']
        results.append(result)

    # 결과 저장
    output_file = "eval_results_team5_24qa.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 통계
    scores = [r.get('score', 0) for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0

    print()
    print("=" * 60)
    print("📊 평가 완료!")
    print(f"평균 점수: {avg_score:.1f}")
    print(f"최고 점수: {max(scores)}")
    print(f"최저 점수: {min(scores)}")
    print(f"결과 저장: {output_file}")
    print("=" * 60)

    return results

if __name__ == "__main__":
    main()
