import json
from typing import Dict, List

class AccuracyEvaluator:
    # 30개 평가 쿼리에 대한 골든 키워드 사전정의
    GOLDEN_KEYWORDS = {
        # 온톨로지 카테고리
        "온톨로지란 무엇인가?": ["온톨로지", "지식", "개념", "관계", "명세"],
        "온톨로지와 지식그래프의 관계는?": ["온톨로지", "지식그래프", "의미", "관계", "시맨틱"],
        "온톨로지 매칭이란 무엇인가?": ["매칭", "이질성", "매핑", "유사도", "정렬"],
        "온톨로지 이질성 문제는?": ["이질성", "구문", "의미", "해결", "스키마"],
        "도메인 온톨로지 모델링 방법은?": ["모델링", "도메인", "구축", "설계", "단계"],
        "온톨로지 기반 의미 속성 판별이란?": ["의미", "속성", "판별", "감성", "텍스트"],
        "온톨로지 학습 기반 지식 그래프 구축 방법은?": ["학습", "지식그래프", "구축", "자동", "추출"],
        "RDF는 무엇인가?": ["RDF", "자원", "기술", "트리플", "주어"],
        "온톨로지 관리 및 유지보수 방법은?": ["관리", "유지보수", "갱신", "버전", "일관성"],
        "온톨로지의 평가 지표는?": ["평가", "지표", "품질", "일관성", "완전성"],
        "온톨로지 재사용 전략은?": ["재사용", "전략", "모듈", "가져오기", "표준"],
        "온톨로지 국제 표준은?": ["표준", "OWL", "W3C", "RDF", "국제"],
        
        # NLP & 생성형AI 카테고리
        "자연어처리(NLP)란?": ["자연어처리", "NLP", "텍스트", "언어", "이해"],
        "정적 언어모델과 생성형AI의 차이는?": ["정적", "생성형", "차이", "맥락", "확률"],
        "생성형AI의 발전 과정은?": ["생성형", "발전", "GPT", "트랜스포머", "모델"],
        "텍스트를 다시 쓰는 기술(Paraphrasing)이란?": ["다시", "Paraphrasing", "문장", "재작성", "의미"],
        "한국근대문인 데이터베이스 구축 방법은?": ["근대문인", "데이터베이스", "구축", "인물", "아카이브"],
        "실시간 문맥 인식 감성 분석이란?": ["문맥", "실시간", "감성", "분석", "모듈"],
        "감성 분석의 모듈형 아키텍처 설계란?": ["모듈", "아키텍처", "설계", "감성", "유연성"],
        "NLP에서의 감정 판별 기법은?": ["감정", "판별", "기법", "사전", "기계학습"],
        "언어모델의 문맥 이해 방식은?": ["문맥", "이해", "어텐션", "트랜스포머", "의미"],
        "대규모 언어모델의 학습 방식은?": ["대규모", "학습", "사전학습", "미세조정", "가중치"],
        "NLP의 주요 응용 분야는?": ["응용", "번역", "챗봇", "요약", "검색"],
        "자연어 이해와 생성의 차이는?": ["이해", "생성", "차이", "NLU", "NLG"],
        
        # 국방 & 지식통합 카테고리
        "국방 분야에서 온톨로지를 어떻게 활용하는가?": ["국방", "지휘통제", "데이터", "통합", "의사결정"],
        "국방 지휘통제 데이터 통합 방법은?": ["지휘통제", "데이터", "통합", "온톨로지", "상호운용성"],
        "온톨로지와 지식그래프를 국방에 적용하는 방법은?": ["국방", "온톨로지", "지식그래프", "적용", "체계"],
        "해외 온톨로지 현황은?": ["해외", "현황", "미국", "국방성", "NATO"],
        "한국군 온톨로지 개발 방안은?": ["한국군", "개발", "방안", "표준화", "국방"],
        "지식그래프 기반 국방 정보 통합은?": ["지식그래프", "국방", "정보", "통합", "상호운용"]
    }

    def evaluate_single_query(self, query: str, answer: str, similarity_scores: List[float]) -> Dict:
        """단일 쿼리 답변에 대한 평가 점수를 구합니다."""
        # 1. 키워드 포함율 (40%)
        golden_kws = self.GOLDEN_KEYWORDS.get(query, [])
        if not golden_kws:
            # 매칭 검색어 폴백
            golden_kws = [query[:4], query[4:8]]
            
        included_count = 0
        for kw in golden_kws:
            if kw in answer:
                included_count += 1
        keyword_presence_ratio = included_count / len(golden_kws) if golden_kws else 0.0

        # 2. 답변 완성도 (30%) - 길이 기준
        ans_len = len(answer)
        if ans_len >= 300:
            answer_completeness = 1.0
        elif ans_len >= 150:
            answer_completeness = 0.7
        elif ans_len >= 50:
            answer_completeness = 0.4
        else:
            answer_completeness = 0.1

        # 3. 관련성 (30%) - 리트리벌 유사도 점수 평균 기준
        if similarity_scores:
            avg_sim = sum(similarity_scores) / len(similarity_scores)
            if avg_sim >= 0.4:
                answer_relevance = 1.0
            elif avg_sim >= 0.3:
                answer_relevance = 0.8
            elif avg_sim >= 0.2:
                answer_relevance = 0.6
            else:
                answer_relevance = 0.4
        else:
            answer_relevance = 0.3

        # 종합 정확도 점수
        score = (
            keyword_presence_ratio * 0.4 +
            answer_completeness * 0.3 +
            answer_relevance * 0.3
        )

        return {
            "query": query,
            "keyword_presence_ratio": round(keyword_presence_ratio, 3),
            "answer_completeness": round(answer_completeness, 3),
            "answer_relevance": round(answer_relevance, 3),
            "accuracy_score": round(score, 4)
        }

    def evaluate_all(self, results: List[Dict]) -> Dict:
        """모든 결과를 통계적으로 평가합니다."""
        evaluated_items = []
        scores = []
        
        # 카테고리별 통계
        cat_scores = {"ontology": [], "nlp": [], "defense": []}
        
        for item in results:
            query = item["query"]
            answer = item.get("answer", "")
            
            # 유사도 스코어들 추출
            chunks = item.get("used_chunks", [])
            similarity_scores = [c.get("similarity_score", 0.0) for c in chunks]
            
            evaluation = self.evaluate_single_query(query, answer, similarity_scores)
            
            # 카테고리 분류 판단
            category = "ontology"
            for q_text in self.GOLDEN_KEYWORDS:
                if q_text == query:
                    # 30개 표준 질문을 통해 카테고리 판정
                    index = list(self.GOLDEN_KEYWORDS.keys()).index(q_text)
                    if index < 12:
                        category = "ontology"
                    elif index < 24:
                        category = "nlp"
                    else:
                        category = "defense"
                    break
            
            evaluation["category"] = category
            evaluated_items.append(evaluation)
            scores.append(evaluation["accuracy_score"])
            cat_scores[category].append(evaluation["accuracy_score"])

        overall_accuracy = sum(scores) / len(scores) if scores else 0.0
        
        by_category = {}
        for cat, cat_list in cat_scores.items():
            by_category[cat] = sum(cat_list) / len(cat_list) if cat_list else 0.0

        return {
            "overall_accuracy": round(overall_accuracy, 4),
            "by_category": {cat: round(val, 4) for cat, val in by_category.items()},
            "queries": evaluated_items
        }
