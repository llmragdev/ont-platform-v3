import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

if __name__ == "__main__":
    load_dotenv()
    
    # [시니어 스타일] 환경 변수가 있으면 쓰고, 없으면 기본 상대 경로 사용
    # 하지만 내부적으로는 abspath를 써서 실행 위치에 상관없이 고정시킵니다.
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path) 
    
    print(f"--- [Target Path] {varRagDir} ---")

    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)

    loader = PyPDFLoader("2025년 AI바우처 사업설명회 발표자료.pdf")
    pages = loader.load_and_split()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50, length_function=len
    )
    texts = text_splitter.split_documents(pages)

    embeddings_model = GoogleGenerativeAIEmbeddings(
        # model="models/text-embedding-004",
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings_model,
        persist_directory=varRagDir
    )
    print(f"--- [Indexing] {len(texts)} 조각 저장 완료 ---")