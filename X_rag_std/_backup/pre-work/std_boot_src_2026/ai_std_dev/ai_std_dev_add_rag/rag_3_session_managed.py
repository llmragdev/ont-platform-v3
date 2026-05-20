import os
import shutil
import uvicorn
import uuid
import time # latency 측정을 위해 추가
from datetime import datetime # 채번 정밀도 향상을 위해 추가
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate

# 설정 파일 임포트
from config_2_advanced import (
    get_raw_root, 
    get_vector_db_path, 
    get_project_root,
    GEMINI_API_KEY, 
    EMBEDDING_MODEL
)

app = FastAPI(title="QABot V4 - High Precision Trace API")

# [1] 업로드 및 [2] 벡터화 로직은 기존 구조를 그대로 유지합니다.
@app.post("/upload")
async def upload_file(company_id: str = Form("05_90-3"), project_id: str = Form("PROJ_0002"), mid_cat: str = Form("3001"), sub_cat: str = Form("2002"), file: UploadFile = File(...)):
    target_dir = os.path.join(get_raw_root(company_id, project_id), mid_cat, sub_cat)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, file.filename)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "path": target_path}

@app.post("/vectorize")
async def vectorize_content(company_id: str = Form("05_90-3"), project_id: str = Form("PROJ_0002"), target_v_id: str = Form("5001"), file_relative_path: str = Form("3001/2002", description="raw 기준 경로 (예: 3001/2002)")):
    vector_dir = get_vector_db_path(company_id, project_id, target_v_id)
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    vectorstore = Chroma(persist_directory=vector_dir, embedding_function=embeddings)
    full_source_path = os.path.join(get_raw_root(company_id, project_id), file_relative_path)
    file_category = file_relative_path.replace('\\', '/')
    targets = [os.path.join(full_source_path, f) for f in os.listdir(full_source_path) if f.lower().endswith(".pdf")] if os.path.isdir(full_source_path) else [full_source_path]
    for file_path in targets:
        result = vectorstore.get(where={"source": file_path})
        if result['ids']: vectorstore._collection.delete(ids=result['ids'])
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        for doc in docs: doc.metadata["file_category"] = file_category
        splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(docs)
        vectorstore.add_documents(splits)
    return {"status": "success", "target_v_db": f"V{target_v_id}"}

# [3] 질의응답: 마이크로초 채번 및 상세 결과 항목 통합
@app.get("/ask")
async def ask_bot(
    company_id: str = Query("05_90-3"), 
    project_id: str = Query("PROJ_0002"), 
    question: str = Query("온톨로지 연구의 핵심 내용은?"), 
    user_id: str = Query("eval_master"),
    target_group: str = Query(None),
    session_id: str = Query(None)
):
    start_time = time.time() # [추가] latency 측정 시작
    
    # [핵심 수정] %f(마이크로초)를 추가하여 채번 중복 방지 (확률적 무시 가능 수준)
    current_session = session_id if session_id else f"SESS_{uuid.uuid4().hex[:8].upper()}"
    chat_id = f"MSG_{datetime.now().strftime('%Y%m%d%H%M%S%f')}" 

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    relevant_docs_with_scores = []
    used_vector_dirs = []

    # 검색 시 score를 함께 가져오기 위해 similarity_search_with_score 사용
    if target_group:
        v_path = get_vector_db_path(company_id, project_id, target_group)
        if os.path.exists(v_path):
            used_vector_dirs.append(v_path)
            db = Chroma(persist_directory=v_path, embedding_function=embeddings)
            relevant_docs_with_scores = db.similarity_search_with_score(question, k=5)
    else:
        v_root = os.path.join(get_project_root(company_id, project_id), "vector_db")
        if os.path.exists(v_root):
            v_folders = [d for d in os.listdir(v_root) if d.startswith('V')]
            for v_f in v_folders:
                # 1. 기존처럼 해당 폴더의 DB 로드
                v_path = os.path.join(v_root, v_f)
                db = Chroma(persist_directory=v_path, embedding_function=embeddings)
                
                # 2. 검색 수행 (k=5)
                current_results = db.similarity_search_with_score(question, k=5)
                
                # [핵심] 찾은 문서들에 현재 폴더 ID(v_f)를 '이름표'로 붙여줌
                for doc, score in current_results:
                    doc.metadata['current_v_id'] = v_f 
                    
                # 3. 기존 구조대로 전체 리스트에 합치기 (extend 사용)
                relevant_docs_with_scores.extend(current_results)


    if not relevant_docs_with_scores:
        return {"answer": "참조 지식 없음", "session_id": current_session, "chat_id": chat_id, "latency": 0}

    # 답변 생성 (간결한 프롬프트)
    template = """당신은 요약 전문가입니다. Context를 바탕으로 3문장 이내로 답변하세요.
    Context: {context}
    질문: {question}
    답변:"""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GEMINI_API_KEY, temperature=0)
    # ==========================================
    # 모인 결과들을 유사도 점수 기준으로 재정렬 (낮은 점수가 더 유사함)
    # ==========================================
    relevant_docs_with_scores.sort(key=lambda x: x[1])

    context_text = "\n\n".join([d[0].page_content for d in relevant_docs_with_scores[:7]])
    prompt = PromptTemplate.from_template(template)
    response = llm.invoke(prompt.format(context=context_text, question=question))

    # [추가] 상세 증거 정보(content, score, page_no) 정리
    evidences = []
    for doc, score in relevant_docs_with_scores[:7]:
        evidences.append({
            "content": doc.page_content,           # [추가] 조회된 실제 원문
            "file": os.path.basename(doc.metadata.get('source', '')),
            "page_no": doc.metadata.get('page', 0) + 1, # [추가] 페이지 번호 보정
            "score": round(float(score), 4),       # [추가] 유사도 점수
            "category": doc.metadata.get('file_category', ''), 
            "target_v_id": doc.metadata.get('current_v_id', target_group) # [해결] 폴더 ID 세팅            
        })

    latency = round(time.time() - start_time, 3) # [추가] 총 소요 시간 계산

    return {
        "status": "success",
        "user_id": user_id,
        "session_id": current_session,
        "chat_id": chat_id,
        "answer": response.content,
        "evidences": evidences, # [추가] 원문 및 상세 메타데이터 포함
        "latency": latency,     # [추가] 응답 속도
        "vector_db_paths": used_vector_dirs
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8103)