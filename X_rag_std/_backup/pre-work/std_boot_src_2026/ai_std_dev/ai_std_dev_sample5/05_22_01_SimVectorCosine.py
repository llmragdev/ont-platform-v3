import os
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = genai.embed_content(
        model='models/gemini-embedding-001',
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def cosine_similarity(v1, v2):
    # 두 벡터의 내적을 구하고, 각 벡터의 크기(L2 Norm)로 나누어줍니다.
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

# 테스트 데이터
text_a = "AI 백엔드 개발자 최남규입니다."
text_b = "인공지능 RAG 커뮤니티를 운영하고 있는 최남규입니다."
text_c = "오늘 점심에는 맛있는 돈가스를 먹었습니다."

# 1. 각 문장을 3072차원 벡터로 변환
vec_a = get_embedding(text_a)
vec_b = get_embedding(text_b)
vec_c = get_embedding(text_c)

# 2. 유사도 계산
sim_ab = cosine_similarity(vec_a, vec_b)
sim_ac = cosine_similarity(vec_a, vec_c)

print(f"문장 A: {text_a}")
print(f"문장 B: {text_b}")
print(f"문장 C: {text_c}")
print("-" * 30)
print(f"A와 B의 유사도 (비슷한 의미): {sim_ab:.4f}")
print(f"A와 C의 유사도 (다른 의미): {sim_ac:.4f}")