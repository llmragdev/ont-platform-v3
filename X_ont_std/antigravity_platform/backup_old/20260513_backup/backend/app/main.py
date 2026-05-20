from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .engine import OntologyEngine, ObjectInstance
from .policy import PolicyEngine
from .rag import RAGService
from .vector_search import VectorSearchService, UPLOAD_DIR
from .ontology_extractor import OntologyExtractor
from .hybrid_engine import HybridQueryEngine
from pathlib import Path
from pydantic import BaseModel
import shutil

app = FastAPI(title="Antigravity Ontology Workbench")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 엔진 및 서비스 초기화
SCHEMA_PATH = Path(__file__).parent.parent / "schema.json"
engine = OntologyEngine(SCHEMA_PATH)
policy_engine = PolicyEngine(engine)
rag_service = RAGService(engine)
vector_search = VectorSearchService()
extractor = OntologyExtractor(engine)
hybrid_engine = HybridQueryEngine(engine, vector_search)

# 초기 목 데이터 로드
def seed_data():
    # ... (생략 가능하지만 유지)
    engine.register_object(ObjectInstance(id="C001", type="Customer", values={
        "name": "Alpha Manufacturing", "segment": "Enterprise", "region": "Seoul", "risk_tier": "Low"
    }))
    engine.register_object(ObjectInstance(id="C002", type="Customer", values={
        "name": "Beta Systems", "segment": "SMB", "region": "Busan", "risk_tier": "Medium"
    }))
    
    engine.register_object(ObjectInstance(id="O001", type="Order", values={
        "status": "Submitted", "amount": 3200.0, "order_date": "2024-05-12"
    }))
    
    engine.register_object(ObjectInstance(id="P001", type="Product", values={
        "name": "Cloud Server A", "category": "Infrastructure", "unit_price": 1000.0
    }))
    
    engine.link("PLACED_ORDER", "C001", "O001")
    engine.link("CONTAINS_PRODUCT", "O001", "P001")

seed_data()

@app.get("/api/health")
async def health():
    return {
        "status": "ok", 
        "engine": "Antigravity-Flex", 
        "objects_count": len(engine.objects),
        "vector_db": vector_search.health()
    }

# --- 문서 관리 및 온톨로지 추출 ---

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    info = vector_search.ingest(dest, file.filename)
    return {"status": "ok", **info}

@app.get("/api/documents")
async def list_documents():
    return {"documents": vector_search.list_documents()}

@app.post("/api/documents/{filename}/extract")
async def extract_ontology(filename: str):
    # 간단하게 파일에서 텍스트 추출 (여기서는 Vector DB에 저장된 내용을 활용하거나 파일을 다시 읽음)
    # 실제 구현에서는 Vector DB의 text를 가져오는 것이 효율적
    docs = vector_search.vector_store.get(where={"filename": filename})
    all_text = "\n".join(docs.get("documents", []))
    
    if not all_text:
        raise HTTPException(status_code=404, detail="Document text not found in vector store")
        
    result = extractor.extract_from_text(all_text)
    return {"status": "ok", "extracted": result}

# --- 질의 시스템 ---

class HybridAskRequest(BaseModel):
    question: str
    doc_ids: list[str] | None = None

@app.post("/api/hybrid/ask")
async def ask_hybrid(body: HybridAskRequest):
    result = await hybrid_engine.ask(body.question, body.doc_ids)
    return result

# --- 기존 엔드포인트 유지 ---

@app.get("/api/ontology/schema")
async def get_schema():
    return engine.schema

@app.get("/api/objects/{object_id}")
async def get_object(object_id: str, user: str = Query("viewer")):
    obj = engine.objects.get(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    filtered_obj = policy_engine.filter_object(obj, user)
    related = engine.find_related(object_id)
    filtered_related = [policy_engine.filter_object(r, user) for r in related]
    
    return {
        "object": filtered_obj,
        "related_objects": filtered_related
    }

@app.get("/api/ontology/graph")
async def get_full_graph(user: str = Query("viewer")):
    nodes = []
    for obj in engine.objects.values():
        filtered = policy_engine.filter_object(obj, user)
        nodes.append({
            "id": obj.id,
            "type": obj.type,
            "label": filtered["values"].get("name") or filtered["values"].get("status") or obj.id,
            "icon": filtered["display_info"].get("icon", "Box"),
            "data": filtered["values"]
        })
        
    edges = []
    for idx, rel in enumerate(engine.relationships):
        edges.append({
            "id": f"e{idx}",
            "source": rel.source_id,
            "target": rel.target_id,
            "label": rel.type
        })
        
    return {"nodes": nodes, "edges": edges}
