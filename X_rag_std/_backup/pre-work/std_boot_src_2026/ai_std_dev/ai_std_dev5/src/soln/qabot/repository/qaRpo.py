import os
import shutil
import gc  # 자원 해제를 위한 가비지 컬렉터
import time
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class QaRepository:
    def __init__(self):
        load_dotenv()
        self.v_api_key = os.getenv("GEMINI_API_KEY")
        
        # 절대 경로 확보
        raw_path = os.getenv("STATIC_DB_PATH", "../data/db_gemini_std")
        self.var_rag_dir = os.path.abspath(raw_path)
        
        # 설정 객체 모사
        self.st = type('obj', (object,), {
            'source_doc_dir': os.path.abspath(os.getenv("SOURCE_RAW_DIR", "./data/01_raw"))
        })
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=self.v_api_key
        )
        self.vector_db = None
        print(f"[OK] [RPO] Repository initialized (Path: {self.var_rag_dir})")

    def _get_db(self):
        if self.vector_db is None:
            self.vector_db = Chroma(
                persist_directory=self.var_rag_dir, 
                embedding_function=self.embeddings
            )
        return self.vector_db

    async def save_knowledge_assets(self, full_paths: list):
        """플랫폼 통합형 자원 해제 및 재등록 로직"""
        try:
            # 1. 인스턴스 참조 해제 (리눅스/윈도우 공통 메모리 관리)
            if self.vector_db is not None:
                self.vector_db = None
                gc.collect() 

            # 2. 물리적 폴더 삭제
            if os.path.exists(self.var_rag_dir):
                try:
                    shutil.rmtree(self.var_rag_dir)
                except Exception:
                    time.sleep(1) # OS 핸들 해제 대기
                    shutil.rmtree(self.var_rag_dir, ignore_errors=True)
            
            all_docs = []
            for path in full_paths:
                if os.path.exists(path):
                    loader = PyPDFLoader(path)
                    all_docs.extend(loader.load())
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
            texts = text_splitter.split_documents(all_docs)

            # 3. 새로운 DB 생성
            self.vector_db = Chroma.from_documents(
                documents=texts, 
                embedding=self.embeddings, 
                persist_directory=self.var_rag_dir
            )
            return True
        except Exception as e:
            print(f"[ERROR] RPO Save Error: {e}")
            return False

    async def get_scored_docs(self, query: str, k: int = 5):
        db = self._get_db()
        return db.similarity_search_with_score(query, k=k)
