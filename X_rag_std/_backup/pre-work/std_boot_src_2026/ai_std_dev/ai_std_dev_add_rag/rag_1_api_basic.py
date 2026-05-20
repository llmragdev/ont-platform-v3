import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from config_1_basic import get_raw_path, get_vector_db_path, GEMINI_API_KEY, EMBEDDING_MODEL

app = FastAPI(title="QABot Multi-Tenant API")

@app.post("/upload")
async def upload_file(
    company_id: str = Form("05_90-1"),
    project_id: str = Form("PROJ_0001"),
    mid_cat: str = Form(...),
    sub_cat: str = Form(...),
    file: UploadFile = File(...)
):
    target_dir = get_raw_path(company_id, project_id, mid_cat, sub_cat)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    target_path = os.path.join(target_dir, file.filename)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"status": "success", "assembled_path": target_path}

@app.post("/vectorize")
async def vectorize_documents(
    company_id: str = Form("05_90"),
    project_id: str = Form("PROJ_0001"),
    mid_cat: str = Form(...),
    sub_cat: str = Form(...)
):
    source_dir = get_raw_path(company_id, project_id, mid_cat, sub_cat)
    vector_dir = get_vector_db_path(company_id, project_id)

    if not os.path.exists(source_dir):
        raise HTTPException(status_code=404, detail="원천 폴더가 존재하지 않습니다.")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    vectorstore = Chroma(persist_directory=vector_dir, embedding_function=embeddings)

    for file_name in os.listdir(source_dir):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(source_dir, file_name)
            
            # 1. 기존 데이터 삭제 (중복 방지)
            result = vectorstore.get(where={"source": file_path})
            if result['ids']:
                vectorstore._collection.delete(ids=result['ids'])

            # 2. 문서 로드 및 카테고리 메타데이터 주입
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # 각 문서 조각에 카테고리 정보 추가
            for doc in documents:
                doc.metadata["mid_cat"] = mid_cat
                doc.metadata["sub_cat"] = sub_cat

            splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(documents)
            
            # 3. 벡터 DB에 추가 (기존 인스턴스 활용)
            vectorstore.add_documents(splits)

    return {"status": "success", "msg": f"{mid_cat}/{sub_cat} 카테고리 동기화 완료"}

@app.get("/ask")
async def ask_bot(company_id: str, project_id: str, question: str):
    vector_dir = get_vector_db_path(company_id, project_id)
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    
    if not os.path.exists(vector_dir):
        return {"answer": "학습된 지식이 없습니다.", "sources": []}

    vectorstore = Chroma(persist_directory=vector_dir, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 7})
    relevant_docs = retriever.invoke(question)

    # 답변 생성
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GEMINI_API_KEY, temperature=0)
    context = "\n\n".join([d.page_content for d in relevant_docs])
    response = llm.invoke(f"Context: {context}\n\n질문: {question}\n답변:")

    # 4. 출처 정보 보완 (중복 제거 및 카테고리 결합)
    seen_sources = set()
    source_details = []
    
    for d in relevant_docs:
        file_name = os.path.basename(d.metadata.get('source', 'Unknown'))
        mid = d.metadata.get('mid_cat', 'N/A')
        sub = d.metadata.get('sub_cat', 'N/A')
        
        source_key = f"{mid}|{sub}|{file_name}"
        if source_key not in seen_sources:
            source_details.append({
                "category": f"{mid} > {sub}",
                "file_name": file_name
            })
            seen_sources.add(source_key)

    return {
        "answer": response.content, 
        "sources": source_details
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8101)