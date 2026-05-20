import json
from typing import List, Dict, Any, Optional
from app.models.identity import UserIdentity
from app.models.query_plan import QueryPlan, QueryAction, EngineType, ActionType
from app.services.audit import AuditService
from app.services.ontology_schema import OntologySchemaService

class QueryPlanner:
    """사용자 질문을 분석하여 하이브리드 실행 계획을 수립하는 서비스"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.audit = AuditService(identity)
        self.schema_service = OntologySchemaService(identity)

    async def generate_plan(self, question: str) -> QueryPlan:
        """자연어 질문을 분석하여 실행 계획 생성"""
        
        # 1. 현재 테넌트의 스키마 정보 로드 (프롬프트 주입용)
        schema_summary = self.schema_service.get_prompt_summary()
        
        # 2. 룰베이스 기초 분류 (향후 이곳에 LLM 호출 및 schema_summary 주입 로직 추가)
        intent = "UNKNOWN"
        steps = []
        
        lower_q = question.lower()
        if "목록" in lower_q or "찾아" in lower_q:
            intent = "ENTITY_SEARCH"
            steps.append(QueryAction(
                engine=EngineType.ONTOLOGY,
                action=ActionType.FILTER,
                params={"q": question},
                description="질문에 부합하는 엔티티를 온톨로지에서 필터링함"
            ))
        else:
            intent = "DOCUMENT_RAG"
            steps.append(QueryAction(
                engine=EngineType.VECTOR,
                action=ActionType.SEARCH,
                params={"query": question, "top_k": 5},
                description="관련 문서를 벡터 데이터베이스에서 검색함"
            ))

        # 2. 결과 생성
        plan = QueryPlan(
            question=question,
            intent=intent,
            steps=steps,
            needs_hybrid_merge=len(steps) > 1
        )

        # 3. 감사 로그 기록
        self.audit.log_action("GENERATE_PLAN", "system", {"question": question, "intent": intent})
        
        return plan

    def validate_plan(self, plan: QueryPlan) -> bool:
        """생성된 계획이 현재 테넌트의 스키마와 부합하는지 검증"""
        # TODO: 실제 온톨로지 스키마와 대조하여 존재하지 않는 타입/속성 필터링
        return True
