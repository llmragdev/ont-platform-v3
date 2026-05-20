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

    # 1. 경로 설정 (시니어 스타일: os.path.join으로 경로 오류 원천 차단)
    v_src_raw_dir = os.getenv("SOURCE_RAW_DIR", "./data/01_raw")
    v_src_raw_file = os.path.join(v_src_raw_dir, "2025년 AI바우처 사업설명회 발표자료.pdf")
    
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    # 2. 데이터 초기화 및 로드
    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)
        
    print(f"--- [Step 1] PDF 데이터 로드 및 벡터 DB 구축 중... ---")
    if not os.path.exists(v_src_raw_file):
        print(f"에러: 파일을 찾을 수 없습니다 -> {v_src_raw_file}")
        return

    loader = PyPDFLoader(v_src_raw_file)
    documents = loader.load()

    # 3. 문서 분할 (문맥 보존을 위해 chunk_size 유지)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=100,
        length_function=len
    )
    texts = text_splitter.split_documents(documents)

    # 4. 벡터 자산 생성 (Gemini Embedding)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=v_api_key
    )
    vector_db = Chroma.from_documents(
        documents=texts, 
        embedding=embeddings,
        persist_directory=varRagDir
    )

    # 5. 추론 엔진 및 QA 체인 설정 (k=5로 더 많은 근거 확보)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=v_api_key,
        temperature=0
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 10}),
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
        
        # 7. [핵심] 검색된 조각들을 페이지 순서대로 재정렬
        # metadata 내의 'page' 번호를 기준으로 오름차순 정렬 (0페이지부터 시작)
        sequential_docs = sorted(
            result['source_documents'], 
            key=lambda x: x.metadata.get('page', 0)
        )

        print("\n" + "="*30 + " [페이지 순서별 검색 근거] " + "="*30)
        for i, doc in enumerate(sequential_docs):
            page_num = doc.metadata.get('page', 0) + 1 # 사용자 인지를 위해 +1
            print(f"\n[조각 {i+1}] (원본 PDF {page_num}페이지)")
            # 글자수 제한 없이 전체 내용 출력
            print(f"내용:\n{doc.page_content.strip()}")
            print("-" * 85)
        print("="*85)
        
        print(f"\n[검색된 근거 문항수]: {len(sequential_docs)}개")
        print(f"[최종 답변]:\n{result['result']}")
        print("-" * 75)

if __name__ == "__main__":
    main()