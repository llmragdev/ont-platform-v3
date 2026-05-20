from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Customer(BaseModel):
    id: str
    name: str
    segment: str
    region: str
    riskTier: str

class Order(BaseModel):
    id: str
    customerId: str
    status: str
    amount: int
    productIds: List[str]

class Product(BaseModel):
    id: str
    name: str
    category: str

class Document(BaseModel):
    id: str
    title: str
    text: str
    score: Optional[float] = 0.0

class AuditEvent(BaseModel):
    id: str
    timestamp: datetime
    user: str
    event_type: str
    description: str
    metadata: Optional[dict] = None

class AskRequest(BaseModel):
    question: str
    selectedOrderId: Optional[str] = None

class WorkflowRequest(BaseModel):
    orderId: str
    action: str

class AskResponse(BaseModel):
    answer: str
    detected_objects: List[str]
    ontology_context: dict
    evidence: List[Document]
    available_actions: List[str]
    trace: List[str]
