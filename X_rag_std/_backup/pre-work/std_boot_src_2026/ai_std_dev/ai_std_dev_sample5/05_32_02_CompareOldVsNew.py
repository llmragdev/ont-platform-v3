import os
import shutil
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def main():
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")

    # 1. 경로 설정 및 초기화
    raw_path = os.getenv("STATIC_DB_PATH", "./db_gemini_std")
    varRagDir = os.path.abspath(raw_path)
    
    if os.path.exists(varRagDir):
        shutil.rmtree(varRagDir)
        
    # 2. 데이터 준비 (사내 기술 표준 문서 5개 청크)
    chunks_content = [
        "인프라 보안 표준: 사내 서버에 접근하기 위해서는 반드시 2단계 인증(2FA)을 거쳐야 하며, 보안팀의 사전 승인이 필수입니다.",
        "소프트웨어 배포 절차: 모든 코드는 메인 브랜치 병합 전 최소 2인 이상의 코드 리뷰를 거친 후 CI/CD 파이프라인을 통해 배포됩니다.",
        "데이터베이스 설계 원칙: 관계형 DB 사용 시 모든 테이블은 제3정규형을 준수해야 하며, 인덱스 생성 전 DBA의 검토가 필요합니다.",
        "로그 관리 규정: 모든 API 호출 로그는 ELK 스택을 통해 90일간 보관되며, 개인정보가 포함된 데이터는 마스킹 처리가 의무화됩니다.",
        "네트워크 구성 표준: 개발 환경과 운영 환경은 가상 네트워크(VPC) 수준에서 완전히 격리되어야 하며 방화벽은 최소 권한 원칙을 따릅니다."
    ]
    # 메타데이터에 ID를 부여하여 정렬 후에도 출처 확인 가능하게 구성
    documents = [Document(page_content=text, metadata={"id": i+1}) for i, text in enumerate(chunks_content)]

    # 3. 벡터 자산 생성 (Gemini Embedding 모델)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=v_api_key
    )
    vector_db = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings,
        persist_directory=varRagDir
    )

    # 4. 테스트 질문 및 검색 (전체 순위 확인을 위해 k=5 설정)
    # Chroma DB는 내부적으로 '거리'가 짧은 순서대로 자동 정렬(Ranking)하여 반환합니다.
    query = "보안 승인 절차"
    results = vector_db.similarity_search_with_score(query, k=5)

    print("유사도 기반 검색: 거리가 짧을수록 유사함 ")
    print(f"질문: '{query}'\n")
    print("-" * 85)
    print(f"{'순위':<4} | {'청크 번호':<6} | {'L2 거리 점수':<10} | {'문맥 내용'}")
    print("-" * 85)

    # 5. 출력 형식 지정 (전문 용어 반영: 유사도 -> L2 거리 점수)
    for i, (doc, score) in enumerate(results):
        chunk_num = doc.metadata["id"]
        content = doc.page_content.replace("\n", " ")
        # 가독성을 위해 본문 길이 40자로 제한
        short_content = content[:40] + "..." if len(content) > 40 else content
        
        # [핵심] 값이 작을수록 문맥적으로 더 가까움을 강조하기 위해 점수(score) 출력
        print(f"[{i+1}위] | 청크 {chunk_num:<5} | {score:12.4f} | {short_content}")

    print("-" * 85)
    print("[Insight] 점수가 가장 낮은(0에 가까운) 항목이 질문과 가장 유사한 문맥입니다.")

if __name__ == "__main__":
    main()