import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def main():
    # 1. 환경 변수 로드 및 API 키 설정
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")

    # 경로 설정 (기존과 동일한 DB 경로 사용)
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    # 2. 데이터 초기화 및 로드
    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)
        
    print(f"--- [Step 1] 정제된 MD 데이터 로드 및 벡터 DB 생성 중... ---")
    v_src_raw_file = "사내기술표준문서.md"
    
    # 파일 존재 여부 체크
    if not os.path.exists(v_src_raw_file):
        print(f"Error: {v_src_raw_file} 파일이 없습니다.")
        return

    loader = TextLoader(v_src_raw_file, encoding="utf-8")
    documents = loader.load()

    # 3. 정밀 분할 (문맥 유지를 위한 Chunking 전략)
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
    
    # Chroma DB 생성 및 데이터 저장
    vector_db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings,
        persist_directory=varRagDir
    )

    # 5. 테스트 질문 실행
    query = "보안 승인 절차"
    print(f"\n[질문]: {query}")
    
    # [핵심] retriever 대신 similarity_search_with_score를 사용하여 거리 점수 획득
    # k=3: 상위 3개의 유사 문맥을 가져옴
    docs_with_score = vector_db.similarity_search_with_score(query, k=3)

    print("\n" + "="*30 + " [Vector DB 검색 결과 분석] " + "="*30)

    # 6. 결과 출력 (문서 내용과 L2 거리 점수 표시)
    for i, (doc, score) in enumerate(docs_with_score):
        # 줄바꿈 제거 및 내용 정리
        content = doc.page_content.replace("\n", " ").strip()
        
        print(f"[검색 결과 {i+1}]")
        print(f"- L2 거리 점수: {score:.4f} (0에 가까울수록 문맥 일치도 높음)")
        print(f"- 관련 문맥: {content[:150]}...")
        print("-" * 85)

    print(f"\n[검색된 근거 문항수]: {len(docs_with_score)}개")
    print("="*85)

if __name__ == "__main__":
    main()