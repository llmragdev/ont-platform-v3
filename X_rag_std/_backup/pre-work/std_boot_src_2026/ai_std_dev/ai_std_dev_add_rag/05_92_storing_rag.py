import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
# 설정 파일에서 키와 모델명만 참조
from config_1_basic import GEMINI_API_KEY, EMBEDDING_MODEL 

# [하드코딩] 05_91과 동일한 경로 설정
PROJECT_RAW_DIR = r"F:\ai_std_dev\data\qabot\05_91\P05_91_BASIC\raw"
PROJECT_VECTOR_DIR = r"F:\ai_std_dev\data\qabot\05_91\P05_91_BASIC\vector_db"

def store_rag_with_sync():
    print(f"\n=== [05_92] 벡터 DB 저장 프로세스 (05_91_BASIC) ===")
    
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    
    # 기존 실습 DB 초기화
    if os.path.exists(PROJECT_VECTOR_DIR):
        shutil.rmtree(PROJECT_VECTOR_DIR)

    for file_name in os.listdir(PROJECT_RAW_DIR):
        file_path = os.path.join(PROJECT_RAW_DIR, file_name)
        loader = PyPDFLoader(file_path)
        data = loader.load()
        
        # 문맥 유지를 위한 청킹 전략
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        all_splits = text_splitter.split_documents(data)
        
        Chroma.from_documents(
            documents=all_splits,
            embedding=embeddings,
            persist_directory=PROJECT_VECTOR_DIR
        )
    print(f">>> 지식 자산화 완료: {PROJECT_VECTOR_DIR}")

if __name__ == "__main__":
    store_rag_with_sync()