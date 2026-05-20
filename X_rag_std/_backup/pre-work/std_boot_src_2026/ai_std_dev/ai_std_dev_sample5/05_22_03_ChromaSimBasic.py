import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def main():
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")

    # SOURCE_RAW_DIR
    v_src_raw_dir = os.getenv("SOURCE_RAW_DIR")

    # 1. 경로 설정
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    # 2. 데이터 초기화 및 로드
    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)
        
    print(f"--- [Step 1] 지식 베이스(MD) 로드 및 벡터 DB 구축 중... ---")
    v_src_raw_file = v_src_raw_dir + "./2025년 AI바우처 사업설명회 발표자료.pdf"
    # PDF 전용 로더 사용
    loader = PyPDFLoader(v_src_raw_file)
    documents = loader.load()
 

    # 3. 문서 분할 (05_060의 설정을 유지하되, 비교를 위해 chunk_size 최적화)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        length_function=len
    )
    texts = text_splitter.split_documents(documents)

    # 4. 벡터 생성 및 저장
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=v_api_key
    )
    vector_db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings,
        persist_directory=varRagDir
    )

    # 5. 질문 설정
    query = "보안 승인 절차"
    
    # 6. [핵심 수정] 유사도 점수와 함께 검색 (similarity_search_with_score)
    # k=5로 설정하여 상위 5개의 연관 조각을 가져옵니다.
    print(f"\n질문: '{query}' (Chroma DB 벡터 검색 + 유사도 점수 산출)")
    print("-" * 80)

    # score는 거리를 의미하며, 0에 가까울수록 유사도가 높습니다.
    # 교육적 목적을 위해 (1 - score) 형태로 변환하여 '유사도' 수치로 시각화합니다.
    results_with_scores = vector_db.similarity_search_with_score(query, k=5)

    for i, (doc, score) in enumerate(results_with_scores):   # 인덱스번호와 내용을 동시에 필요로 할때 쓰는 함수 - 나열하다는 의미 
        # 코사인 유사도와 유사한 체감을 위해 점수 보정 (Chroma 거리를 유사도로 변환)
        # Gemini 임베딩의 경우 보통 0.7~0.9 사이의 값이 나옵니다.
        similarity = 1 - score 
        
        content = doc.page_content.replace("\n", " ").strip()
        # print(f"[순위 {i+1}] 유사도: {similarity:.4f} | 내용: {content[:80]}...")
        print(f"[i값: {i}] score 거리 0일수로 유사함: {score}" )
        print(f"[순위 {i+1}] 유사도: {similarity:.4f} | 내용: {content}")
        print("-" * 80)

    print(f"\n[검색 완료] 총 {len(results_with_scores)}개의 유관 조각을 찾았습니다.")

if __name__ == "__main__":
    main()