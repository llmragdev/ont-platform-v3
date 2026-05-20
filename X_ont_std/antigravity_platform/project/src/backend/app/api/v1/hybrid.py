from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_identity
from app.models.identity import UserIdentity
from app.models.query_plan import QueryPlan, HybridResponse
from app.services.query_planner import QueryPlanner
from app.services.ontology_engine import OntologyQueryEngine
from app.services.search import SearchService
from app.services.hybrid_synthesizer import HybridSynthesizer
from app.models.query_plan import EngineType

router = APIRouter()

@router.post("/plan", response_model=QueryPlan)
async def generate_query_plan(
    question: str,
    identity: UserIdentity = Depends(get_current_identity)
):
    """자연어 질문에 대한 실행 계획 생성"""
    planner = QueryPlanner(identity)
    plan = await planner.generate_plan(question)
    return plan

@router.post("/ask", response_model=HybridResponse)
async def ask_hybrid_query(
    question: str,
    identity: UserIdentity = Depends(get_current_identity)
):
    """실행 계획 수립 및 엔진 실행 후 최종 답변 반환 (Full Pipeline)"""
    # 1. 계획 수립 (Planner)
    planner = QueryPlanner(identity)
    plan = await planner.generate_plan(question)
    
    # 2. 엔진별 실행 (Executor)
    ontology_engine = OntologyQueryEngine(identity)
    search_service = SearchService(identity)
    
    ontology_results = []
    vector_results = []
    
    for step in plan.steps:
        if step.engine == EngineType.ONTOLOGY:
            res = await ontology_engine.execute_step(step)
            ontology_results.append(res)
        elif step.engine == EngineType.VECTOR:
            res = await search_service.search(step.params.get("query", question))
            vector_results.extend(res)
            
    # 3. 결과 합성 (Synthesizer)
    synthesizer = HybridSynthesizer(identity)
    response = await synthesizer.synthesize(question, plan, ontology_results, vector_results)
    
    return response
