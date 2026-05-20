import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

def main():
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")

    # SOURCE_RAW_DIR
    v_src_raw_dir = os.getenv("SOURCE_RAW_DIR")

    
    # 1. 경로 설정 (시니어 스타일: 절대 경로 확보)
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    # 2. 데이터 초기화 및 로드
    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)
        
    print(f"--- [Step 1] 정제된 MD 데이터 로드 중... ---")
    # PDFLoader 대신 TextLoader를 사용하여 텍스트 누락 원천 차단
    v_src_raw_file = v_src_raw_dir + "./2025년 AI바우처 사업설명회 발표자료.pdf"
    # PDF 전용 로더 사용
    loader = PyPDFLoader(v_src_raw_file)
    documents = loader.load()

    # 3. 정밀 분할 (문맥 보존을 위해 조금 더 크게 유지)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )
    texts = text_splitter.split_documents(documents)

    # 4. 벡터 자산 생성
    embeddings = GoogleGenerativeAIEmbeddings(
        # model="models/text-embedding-004",
        model="models/gemini-embedding-001",
        google_api_key=v_api_key
    )
    vector_db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings,
        persist_directory=varRagDir
    )

    # 5. 추론 엔진 설정
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
        google_api_key=v_api_key,
        temperature=0
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k":5}),
        return_source_documents=True
    )

    # 6. 테스트 질문 실행
    questions = [
        "AI바우처 지원사업의 추진 목적이 무엇인가요?",
        "바우처 지원사업의 지원 규모와 한도는 어떻게 되나요?"
    ]

    for q in questions:
        print(f"\n[질문]: {q}")
        result = qa_chain.invoke({"query": q})
        
        # [검색 내역 출력 구간 추가]
        print("\n" + "="*30 + " [MD 자산 검색 내역] " + "="*30)
        # 검색된 조각(Source Documents)을 순회하며 출력
        for i, doc in enumerate(result['source_documents']):
            print(f"\n[검색 조각 {i+1}]")
            # 텍스트 파일(MD)이므로 페이지 번호 대신 문서 내용을 출력
            print(f"내용: {doc.page_content.strip()}")
            print("-" * 80)
        print("="*85)
        
        print(f"\n[검색된 근거 문항수]: {len(result['source_documents'])}개")
        print(f"[최종 답변]:\n{result['result']}")
        print("-" * 70)

        
if __name__ == "__main__":
    main()