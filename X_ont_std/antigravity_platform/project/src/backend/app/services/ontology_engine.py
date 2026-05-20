from typing import List, Dict, Any, Optional
from app.models.query_plan import QueryPlan, QueryAction, ActionType, EngineType
from app.repositories.ontology import OntologyRepository
from app.models.identity import UserIdentity

class OntologyQueryEngine:
    """Query Plan을 받아 온톨로지 데이터를 결정론적으로 처리하는 엔진"""

    def __init__(self, identity: UserIdentity):
        self.identity = identity
        self.repo = OntologyRepository(identity.company_id, identity.current_project_id)

    async def execute_step(self, action: QueryAction) -> Dict[str, Any]:
        """개별 온톨로지 액션 실행"""
        params = action.params
        
        if action.action == ActionType.FILTER:
            return self._execute_filter(params)
        elif action.action == ActionType.AGGREGATE:
            return self._execute_aggregate(params)
        
        return {"error": f"Unsupported action type: {action.action}"}

    def _execute_filter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """필터 조건에 따른 엔티티 목록 조회"""
        etype = params.get("type")
        filters = params.get("filters", [])
        
        entities = self.repo.list_entities(etype)
        
        # 룰베이스 필터링 적용
        filtered = []
        for e in entities:
            match = True
            for f in filters:
                prop = f.get("prop")
                op = f.get("op")
                val = f.get("val")
                
                e_val = e.get("values", {}).get(prop)
                if op == "==" and e_val != val: match = False
                elif op == "contains" and val not in str(e_val): match = False
            
            if match:
                filtered.append(e)
                
        return {"results": filtered, "count": len(filtered)}

    def _execute_aggregate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """집계 연산(Count, Sum, Avg) 수행"""
        etype = params.get("type")
        func = params.get("function")
        field = params.get("field")
        
        entities = self.repo.list_entities(etype)
        
        if func == "count":
            return {"result": len(entities), "unit": "items"}
            
        # TODO: Sum, Avg 등 수치 연산 추가 예정
        return {"result": 0, "message": f"Function {func} not yet implemented"}
