import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

if __name__ == "__main__":
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")
    
    # 1. 경로 설정 (시니어 팁: 절대 경로를 통해 실행 환경 독립성 확보)
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    print(f"--- [Debug] 검색 대상 절대 경로: {varRagDir} ---")
    
    if not os.path.exists(varRagDir):
        print(f"!!! [Error] 해당 경로에 DB 폴더가 없습니다. 05_110을 먼저 실행하세요. !!!")

    # 2. 임베딩 모델 설정 (저장 시와 반드시 동일한 모델 사용)
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=v_api_key
    )
    
    # 3. Vector DB 로드
    vectorstore = Chroma(
        persist_directory=varRagDir,
        embedding_function=embeddings_model
    )

    # 4. LLM 설정 (Flash-Lite를 통한 비용 및 속도 최적화)
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite"),
        google_api_key=v_api_key,
        temperature=0
    )

    # 5. Chain 구성 (k=5로 설정하여 검색 범위 확장)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True
    )

    # 6. [수정] 테스트 질문 리스트 정의 (05_100 스타일 적용)
    questions = [
        "AI바우처 지원사업의 추진 목적이 무엇인가요?",
        "바우처 지원사업의 지원 규모와 한도는 어떻게 되나요?"
    ]

    # 7. 멀티 질문 실행 루프
    for i, question in enumerate(questions):
        print(f"\n" + "###" * 20)
        print(f"[테스트 케이스 {i+1}] 질문: {question}")
        print("###" * 20)
        
        result = qa_chain.invoke({"query": question})

        # 검색된 조각 확인
        if not result['source_documents']:
            print("!!! [Warning] 검색된 문서 조각이 하나도 없습니다. !!!")
        else:
            print(f"--- [Success] {len(result['source_documents'])}개의 근거 조각을 찾았습니다. ---")

            # 검색된 원천 데이터(Source Documents) 출력
            print("\n" + "="*30 + " [Vector DB 검색 내역] " + "="*30)
            for j, doc in enumerate(result['source_documents']):
                page_num = doc.metadata.get('page', 'N/A')
                # 페이지 번호가 0부터 시작하므로 사람이 읽기 편하게 +1 처리 제안
                display_page = page_num + 1 if isinstance(page_num, int) else page_num
                print(f"\n[근거 {j+1}] (원본 PDF 페이지: {display_page})")
                print(f"내용: {doc.page_content.strip()[:200]}...") # 로그 가독성을 위해 일부 생략 출력
                print("-" * 70)
            print("="*85)

        # 최종 AI 답변 출력
        print(f"\n[최종 AI 답변]:\n{result['result']}")
        print("\n" + "---" * 25)

print(f"\n###### {os.path.basename(__file__)} Standard End #######")