from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import datetime

from models import Customer, Order, Product, Document, AskRequest, WorkflowRequest, AskResponse, AuditEvent
from data import repo
from ontology import OntologyService
from workflow import WorkflowService
from rag import RAGService
from audit import AuditService
from policy import PolicyService

app = FastAPI(title="Ontology Workbench API - Operational")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers for "User Context" (Simplified for educational purposes)
CURRENT_USER = "AdminUser"
CURRENT_ROLE = "Admin"

# API Endpoints
@app.get("/api/objects/customers", response_model=List[Customer])
async def get_customers():
    AuditService.log_event(CURRENT_USER, "DATA_VIEW", "Viewed customer list")
    customers = repo.get_customers()
    
    # Apply masking if needed
    for c in customers:
        if PolicyService.get_masking_required(CURRENT_ROLE, "riskTier"):
            c["riskTier"] = "***"
            
    return customers

@app.get("/api/objects/orders", response_model=List[Order])
async def get_orders():
    AuditService.log_event(CURRENT_USER, "DATA_VIEW", "Viewed order list")
    return repo.get_orders()

@app.get("/api/objects/orders/{order_id}")
async def get_order_context(order_id: str):
    AuditService.log_event(CURRENT_USER, "DATA_VIEW", f"Viewed order context for {order_id}")
    context = OntologyService.get_order_context(order_id)
    if not context:
        raise HTTPException(status_code=404, detail="Order not found")
    return context

@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    AuditService.log_event(CURRENT_USER, "AI_QUERY", f"Asked: {request.question}")
    result = RAGService.generate_answer(request.question, request.selectedOrderId)
    return result

@app.post("/api/workflow/execute")
async def execute_workflow(request: WorkflowRequest):
    # Check Permission
    permission_action = "execute_approve" if "Approve" in request.action else "execute_all"
    if not PolicyService.check_permission(CURRENT_ROLE, permission_action):
        AuditService.log_event(CURRENT_USER, "PERMISSION_DENIED", f"Denied action {request.action} on {request.orderId}")
        raise HTTPException(status_code=403, detail="Permission denied")

    success, result = WorkflowService.validate_and_execute(request.orderId, request.action)
    if not success:
        AuditService.log_event(CURRENT_USER, "WORKFLOW_ERROR", f"Failed {request.action} on {request.orderId}: {result}")
        raise HTTPException(status_code=400, detail=result)
    
    AuditService.log_event(CURRENT_USER, "WORKFLOW_EXECUTE", f"Executed {request.action} on {request.orderId}, new status: {result}")
    return {"message": f"Action {request.action} executed", "newStatus": result}

@app.get("/api/audit/events", response_model=List[AuditEvent])
async def get_audit_events():
    if not PolicyService.check_permission(CURRENT_ROLE, "audit_view"):
        raise HTTPException(status_code=403, detail="Permission denied")
    return repo.get_audit_events()

@app.post("/api/system/reset")
async def reset_system():
    repo.reset()
    AuditService.log_event(CURRENT_USER, "SYSTEM_RESET", "System data reset to default")
    return {"message": "System reset successful"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
