import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from config_1_basic import GEMINI_API_KEY, EMBEDDING_MODEL

# [하드코딩] 05_92에서 생성한 DB 경로 참조
PROJECT_VECTOR_DIR = r"F:\ai_std_dev\data\qabot\05_91\P05_91_BASIC\vector_db"

def predict_gemini_qa(question):
    print(f"\n=== [05_93] 제미나이 질의응답 (05_91_BASIC) ===")
    
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    
    if not os.path.exists(PROJECT_VECTOR_DIR):
        return "실습용 벡터 DB가 없습니다. 05_92를 실행하세요.", []

    vectorstore = Chroma(persist_directory=PROJECT_VECTOR_DIR, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    relevant_docs = retriever.invoke(question)
    
    # 프롬프트 및 답변 생성 로직
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GEMINI_API_KEY, temperature=0)
    context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    template = "Context: {context}\n질문: {question}\n답변:"
    prompt = PromptTemplate.from_template(template)
    response = llm.invoke(prompt.format(context=context_text, question=question))
    
    return response.content

if __name__ == "__main__":
    query = "AI바우처 지원사업의 추진 목적이 무엇인가요?"
    ans = predict_gemini_qa(query)
    print(f"\n[AI 답변]:\n{ans}")