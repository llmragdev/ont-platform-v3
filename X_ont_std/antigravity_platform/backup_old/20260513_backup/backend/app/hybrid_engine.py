import json
import os
from typing import Dict, List, Any, Optional

from google import genai
from .engine import OntologyEngine
from .vector_search import VectorSearchService

class HybridQueryEngine:
    def __init__(self, engine: OntologyEngine, vector_search: VectorSearchService):
        self.engine = engine
        self.vector_search = vector_search
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY1")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def classify_query(self, question: str) -> dict:
        """질문 유형 분류: descriptive, structural, or hybrid."""
        prompt = f"""Classify the following user question into one of these types:
1. 'descriptive': General explanation, "how to", "what is" (Best for Vector RAG)
2. 'structural': Filtering, comparison, calculation, relationship tracing (Best for Ontology)
3. 'hybrid': Complex questions requiring both data sources.

Question: {question}

Return ONLY a JSON object: {{"type": "descriptive|structural|hybrid", "reason": "..."}}
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        try:
            return json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        except:
            return {"type": "hybrid", "reason": "Fallback"}

    async def ask(self, question: str, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        # 1. 유형 분류
        classification = self.classify_query(question)
        q_type = classification["type"]

        vector_results = []
        ontology_context = {}

        # 2. 검색 수행
        if q_type in ["descriptive", "hybrid"]:
            vector_results = self.vector_search.search(question, k=5, doc_ids=doc_ids)

        if q_type in ["structural", "hybrid"]:
            # 질문에서 관련 엔티티 ID 추출 (간단한 매칭 또는 LLM 추출)
            # 여기서는 간단히 모든 객체 컨텍스트를 보내거나 검색어 기반 필터링 가능
            # 실제로는 'Query Planner'가 필요한 부분
            ontology_context = {"objects_count": len(self.engine.objects)} 

        # 3. 답변 합성 프롬프트
        context_str = ""
        if vector_results:
            context_str += "\n### Document Excerpts (Vector):\n"
            for r in vector_results:
                context_str += f"- [{r['filename']} p.{r['page']}] {r['text']}\n"
        
        # 4. 최종 답변 생성
        prompt = f"""You are a helpful assistant. Answer the question using the context below.
If the context has structured data (Ontology) and unstructured text (Vector), combine them.
Prioritize Ontology for numerical or structural facts.

Question: {question}

Context:
{context_str}

Answer in Korean.
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        return {
            "answer": response.text,
            "type": q_type,
            "vector_evidence": vector_results,
            "ontology_context": ontology_context
        }
