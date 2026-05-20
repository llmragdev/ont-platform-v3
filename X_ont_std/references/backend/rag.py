from typing import List, Dict, Any
from ontology import OntologyService
from search import SearchService
from data import repo
from workflow import WorkflowService

class RAGService:
    @staticmethod
    def generate_answer(question: str, selected_order_id: str = None) -> Dict[str, Any]:
        trace = []
        
        # 1. Detect objects
        detected = OntologyService.detect_objects(question)
        trace.append("objects_detected")
        
        # 2. Context Extraction
        order_id = next((obj for obj in detected if obj.startswith("O")), selected_order_id or "O001")
        order_context = OntologyService.get_order_context(order_id)
        trace.append("context_extracted")
        
        # 3. Relationship Verification (if multiple objects)
        customer_id = next((obj for obj in detected if obj.startswith("C")), None)
        rel_verified = True
        if customer_id and order_id:
            rel_verified = OntologyService.verify_relationship(customer_id, order_id)
            trace.append("relation_verified")
            
        # 4. Document Search (BM25)
        evidence = SearchService.search(question)
        trace.append("documents_retrieved")
        
        # 5. Answer Generation (Heuristic for now, but using retrieved data)
        answer = ""
        if not rel_verified:
            answer = f"주의: 요청하신 고객({customer_id})과 주문({order_id}) 간의 관계를 온톨로지에서 확인할 수 없습니다. 정확한 정보를 위해 다시 확인해 주세요."
        else:
            if order_context:
                order = order_context["order"]
                customer = order_context["customer"]
                
                if "승인" in question or "approve" in question:
                    if order["amount"] < 5000 and customer["riskTier"] == "Low":
                        answer = f"{order_id} 주문은 승인이 권장됩니다. 정책 D001에 따라 5,000 미만이며 리스크 등급이 {customer['riskTier']}입니다."
                    else:
                        answer = f"{order_id} 주문은 추가 검토가 필요합니다. 금액({order['amount']}) 또는 리스크({customer['riskTier']})가 기준을 초과합니다."
                else:
                    answer = f"주문 {order_id}에 대한 온톨로지 분석 결과, 고객 {customer['name']}의 {order['status']} 상태인 주문입니다. 관련 근거 문서를 참고하세요."
            else:
                answer = "요청하신 주문 정보를 시스템에서 찾을 수 없습니다."

        available_actions = WorkflowService.get_available_actions(order_context["order"]["status"]) if order_context else []
        
        return {
            "answer": answer,
            "detected_objects": detected,
            "ontology_context": order_context or {},
            "evidence": evidence,
            "available_actions": available_actions,
            "trace": trace
        }
