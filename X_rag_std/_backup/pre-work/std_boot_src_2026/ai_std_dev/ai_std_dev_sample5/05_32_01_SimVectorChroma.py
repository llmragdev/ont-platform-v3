import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def main():
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")

    # 1. 경로 설정 (기존과 동일한 DB 경로 사용)
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    # 2. 데이터 초기화 및 로드
    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)
        
    print(f"--- [Step 1] 정제된 MD 데이터 로드 및 벡터 DB 생성 중... ---")
    v_src_raw_file = "사내기술표준문서.md"
    loader = TextLoader(v_src_raw_file, encoding="utf-8")
    documents = loader.load()

    # 3. 정밀 분할 (강의용 가독성을 위해 chunk_size 조정 가능)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        length_function=len
    )
    texts = text_splitter.split_documents(documents)

    # 4. 벡터 자산 생성 (Gemini Embedding 사용)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=v_api_key
    )
    vector_db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings,
        persist_directory=varRagDir
    )

    # 5. 리트리버 설정 (검색 기능 정의)
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # 6. 테스트 질문 실행
    query = "보안 승인 절차"
    print(f"\n[질문]: {query}")
    
    # 검색 수행
    docs = retriever.get_relevant_documents(query)
    
    for i, doc in enumerate(docs):
        print(f"\n--- [검색 결과 {i+1}] ---")
        print(doc.page_content)

if __name__ == "__main__":
    main()