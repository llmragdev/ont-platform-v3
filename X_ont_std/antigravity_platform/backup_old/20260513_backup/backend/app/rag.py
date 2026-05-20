import asyncio
import json
from typing import AsyncGenerator, Dict, List
from .engine import OntologyEngine

class RAGService:
    def __init__(self, engine: OntologyEngine):
        self.engine = engine

    async def ask_stream(self, question: str, object_id: str, role: str) -> AsyncGenerator[str, None]:
        """온톨로지 컨텍스트를 활용한 스트리밍 답변 생성 (Mock)"""
        # 1. 온톨로지 컨텍스트 추출
        context = self.engine.get_object_with_context(object_id)
        if not context:
            yield f"data: {json.dumps({'error': 'Object not found'})}\n\n"
            return

        # 2. 프롬프트 구성 (실제로는 LLM 호출)
        obj_name = context["object"]["values"].get("name") or object_id
        yield f"data: {json.dumps({'event': 'started', 'object': obj_name})}\n\n"
        await asyncio.sleep(0.5)

        # 3. 답변 생성 시뮬레이션
        full_answer = f"온톨로지 분석 결과, {obj_name} 주문은 현재 정상 범주에 있습니다. " \
                      f"연결된 고객의 리스크 등급이 {context['object']['values'].get('risk_tier', 'Unknown')}이므로 승인이 권장됩니다."
        
        for word in full_answer.split():
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            await asyncio.sleep(0.1)

        # 4. 근거 정보 송신
        evidence = [
            {"id": "DOC-001", "title": "주문 승인 가이드라인", "score": 0.95},
            {"id": "DOC-002", "title": "고객 리스크 평가 기준", "score": 0.88}
        ]
        yield f"data: {json.dumps({'event': 'finished', 'evidence': evidence})}\n\n"
