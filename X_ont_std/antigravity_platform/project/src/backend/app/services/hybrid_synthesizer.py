from typing import List, Dict, Any, Optional
from app.models.query_plan import QueryPlan, HybridResponse
from app.models.identity import UserIdentity

class HybridSynthesizer:
    """온톨로지 결과와 벡터 결과를 결합하여 최종 답변을 생성하는 서비스"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity

    async def synthesize(
        self, 
        question: str, 
        plan: QueryPlan, 
        ontology_results: List[Dict[str, Any]], 
        vector_results: List[Dict[str, Any]]
    ) -> HybridResponse:
        """
        다양한 소스의 데이터를 결합하여 최종 응답 생성.
        현재는 기초 단계로 룰베이스 합성을 수행하며, 향후 LLM이 최종 답변 생성을 담당함.
        """
        
        # 1. 답변 초안 작성 (Rule-based)
        answer_parts = []
        
        # 온톨로지 결과 요약
        if ontology_results:
            for res in ontology_results:
                if "count" in res:
                    answer_parts.append(f"Found {res['count']} matching items in ontology.")
                if "result" in res:
                    answer_parts.append(f"Calculated result: {res['result']}.")

        # 벡터 검색 결과 요약
        if vector_results:
            answer_parts.append(f"Found {len(vector_results)} related document references.")

        # 2. 결과 합성
        final_answer = " ".join(answer_parts)
        if not final_answer:
            final_answer = "I couldn't find any specific data to answer your question."

        # 3. 증거(Evidence) 및 트레이스 구성
        evidence = []
        for vr in vector_results:
            evidence.append({
                "type": "DOCUMENT",
                "source": vr.get("filename"),
                "snippet": vr.get("text_snippet")
            })

        return HybridResponse(
            question=question,
            query_plan=plan,
            answer=final_answer,
            structured_data={"ontology": ontology_results},
            evidence=evidence,
            trace=["Ontology data fetched", "Vector search completed", "Results synthesized"]
        )
