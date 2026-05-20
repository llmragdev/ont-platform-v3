import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate

# 설정 파일 임포트 (기존 제공해주신 common_config 활용)
from config_2_advanced import (
    get_raw_root, 
    get_vector_db_path, 
    get_project_root,
    GEMINI_API_KEY, 
    EMBEDDING_MODEL
)

app = FastAPI(title="QABot V3 - Path Tracking API")

# [1] 업로드: 원천 파일 저장
@app.post("/upload")
async def upload_file(
    company_id: str = Form("05_90-2"),
    project_id: str = Form("PROJ_0002"),
    mid_cat: str = Form("3001"),
    sub_cat: str = Form("2002"),
    file: UploadFile = File(...)
):
    target_dir = os.path.join(get_raw_root(company_id, project_id), mid_cat, sub_cat)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, file.filename)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "path": target_path}

# [2] 벡터화: 폴더/파일 단위 저장 및 '저장 카테고리' 메타데이터 주입
@app.post("/vectorize")
async def vectorize_content(
    company_id: str = Form("05_90-2"),
    project_id: str = Form("PROJ_0002"),
    target_v_id: str = Form(..., description="저장될 벡터 DB ID (예: 5001)"),
    file_relative_path: str = Form(..., description="raw 기준 경로 (예: 3001/2002)")
):
    """
    파일의 실제 저장 위치(예: 3001/2002)를 'file_category' 메타데이터로 저장합니다.
    """
    vector_dir = get_vector_db_path(company_id, project_id, target_v_id)
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    vectorstore = Chroma(persist_directory=vector_dir, embedding_function=embeddings)
    
    full_source_path = os.path.join(get_raw_root(company_id, project_id), file_relative_path)
    if not os.path.exists(full_source_path):
        raise HTTPException(status_code=404, detail="경로를 찾을 수 없습니다.")

    # 파일 카테고리 추출 (경로에서 상위 폴더 구조만 추출)
    # 예: 3001/2002/test.pdf -> 3001/2002
    file_category = file_relative_path.replace('\\', '/')
    if not os.path.isdir(full_source_path):
        file_category = os.path.dirname(file_category)

    targets = []
    if os.path.isdir(full_source_path):
        targets = [os.path.join(full_source_path, f) for f in os.listdir(full_source_path) if f.lower().endswith(".pdf")]
    else:
        targets = [full_source_path] if full_source_path.lower().endswith(".pdf") else []

    for file_path in targets:
        # 기존 데이터 삭제
        result = vectorstore.get(where={"source": file_path})
        if result['ids']:
            vectorstore._collection.delete(ids=result['ids'])

        # 문서 로드 및 '저장 카테고리' 주입
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["file_category"] = file_category # 예: 3001/2002
            
        splits = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(docs)
        vectorstore.add_documents(splits)

    return {"status": "success", "target_v_db": f"V{target_v_id}", "category_tagged": file_category}

# [3] 질의응답: 답변 시 벡터 DB 경로 포함 및 원천 카테고리 표시
@app.get("/ask")
async def ask_bot(
    company_id: str, 
    project_id: str, 
    question: str, 
    target_group: str = Query(None, description="검색할 V-ID (예: 5001)")
):
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    relevant_docs = []
    used_vector_dirs = [] # 실제 사용된 벡터 DB 경로 저장용

    # A. 특정 타겟 그룹 검색
    if target_group:
        v_path = get_vector_db_path(company_id, project_id, target_group)
        if os.path.exists(v_path):
            used_vector_dirs.append(v_path)
            db = Chroma(persist_directory=v_path, embedding_function=embeddings)
            relevant_docs = db.as_retriever(search_kwargs={"k": 5}).invoke(question)
    
    # B. 전체 통합 검색
    else:
        v_root = os.path.join(get_project_root(company_id, project_id), "vector_db")
        if os.path.exists(v_root):
            v_folders = [d for d in os.listdir(v_root) if d.startswith('V')]
            for v_f in v_folders:
                db_p = os.path.join(v_root, v_f)
                used_vector_dirs.append(db_p)
                db = Chroma(persist_directory=db_p, embedding_function=embeddings)
                relevant_docs.extend(db.as_retriever(search_kwargs={"k": 3}).invoke(question))

    if not relevant_docs:
        return {"answer": "참조할 지식이 없습니다.", "sources": [], "vector_db_paths": used_vector_dirs}

    # [수정] 간결한 답변을 위한 프롬프트 템플릿 적용
    template = """당신은 요약 전문가입니다. 제공된 Context를 바탕으로 질문에 답하세요.
    지침:
    1. 답변은 반드시 3문장 이내의 핵심 요약으로만 작성하세요.
    2. 불필요한 인사말이나 서론은 생략하세요.
    
    Context: {context}
    질문: {question}
    답변:"""

    # 답변 생성
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GEMINI_API_KEY, temperature=0)
    context_text = "\n\n".join([d.page_content for d in relevant_docs[:7]])
    prompt = PromptTemplate.from_template(template)
    response = llm.invoke(prompt.format(context=context_text, question=question))

    # 출처 및 카테고리 정리
    sources = []
    seen = set()
    for d in relevant_docs[:7]:
        f_name = os.path.basename(d.metadata.get('source', 'Unknown'))
        # 벡터화 시점에 주입했던 '파일 저장 카테고리'를 가져옴
        file_cat = d.metadata.get('file_category', 'Unclassified')
        
        if f"{file_cat}|{f_name}" not in seen:
            sources.append({"category": file_cat, "file": f_name})
            seen.add(f"{file_cat}|{f_name}")

    return {
        "answer": response.content,
        "vector_db_paths": used_vector_dirs, # 답변에 사용된 벡터 DB 물리 경로 추가
        "sources": sources
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8102)