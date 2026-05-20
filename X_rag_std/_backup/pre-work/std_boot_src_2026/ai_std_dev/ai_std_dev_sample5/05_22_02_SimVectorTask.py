import os
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text, is_query=False):
    # 질문과 문서의 성격에 따라 task_type을 다르게 설정하는 것이 정석입니다.
    task = "retrieval_query" if is_query else "retrieval_document"
    result = genai.embed_content(
        model='models/gemini-embedding-001',
        content=text,
        task_type=task
    )
    return result['embedding']

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# 1. 사내 기술 표준 문서 청킹 (교육용 데이터) - 5개 
chunks = [
    "인프라 보안 표준: 사내 서버에 접근하기 위해서는 반드시 2단계 인증(2FA)을 거쳐야 하며, 보안팀의 사전 승인이 필수입니다.",
    "소프트웨어 배포 절차: 모든 코드는 메인 브랜치 병합 전 최소 2인 이상의 코드 리뷰를 거친 후 CI/CD 파이프라인을 통해 배포됩니다.",
    "데이터베이스 설계 원칙: 관계형 DB 사용 시 모든 테이블은 제3정규형을 준수해야 하며, 인덱스 생성 전 DBA의 검토가 필요합니다.",
    "로그 관리 규정: 모든 API 호출 로그는 ELK 스택을 통해 90일간 보관되며, 개인정보가 포함된 데이터는 마스킹 처리가 의무화됩니다.",
    "네트워크 구성 표준: 개발 환경과 운영 환경은 가상 네트워크(VPC) 수준에서 완전히 격리되어야 하며 방화벽은 최소 권한 원칙을 따릅니다."
]

# 2. 질문 (사용자가 챗봇에 물어볼 법한 내용)
query = "보안 승인 절차"

# 3. 임베딩 생성
query_vec = get_embedding(query, is_query=True)
chunk_vecs = [get_embedding(chunk) for chunk in chunks]

# 4. 유사도 비교
print(f"질문: '{query}'\n")
print("-" * 50)
for i, c_vec in enumerate(chunk_vecs):
    sim = cosine_similarity(query_vec, c_vec)
    print(f"[청크 {i+1}] 유사도: {sim:.4f} | 내용: {chunks[i][:40]}...")