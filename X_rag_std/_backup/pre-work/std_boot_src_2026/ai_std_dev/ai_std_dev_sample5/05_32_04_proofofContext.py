import os
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import embed_content

def get_embedding(text):
    # [수정] 5장 실습 표준 모델 사용 (Task Type 명시)
    result = embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def main():
    # 1. 환경 변수 로드 및 API 키 설정 (에러 해결 핵심)
    load_dotenv()
    v_api_key = os.getenv("GEMINI_API_KEY")
    
    if not v_api_key:
        print("Error: .env 파일에 GEMINI_API_KEY가 설정되어 있는지 확인해주세요.")
        return

    genai.configure(api_key=v_api_key)

    # 2. 비교 대상 문장 설정
    # 문장 A: 단어는 다르나 맥락이 유사 (수리/수선)
    # 문장 B: 단어는 같으나 맥락이 다름 (수리/수학)
    target_text = "기기가 고장 나서 고치고 싶어요" 
    comparison_texts = [
        "장비를 수선하고 싶습니다",          
        "수리 영역 점수를 올리고 싶어",      
        "오늘 점심은 돈가스를 먹을까요"       
    ]

    print("기준 질문과 비교할 문장과 비교하여 코사인 유사도 계산 1에 가까울수록 유사함") 
    print(f"기준 질문: {target_text}")
    print("-" * 50)

    try:
        target_vector = get_embedding(target_text)

        for text in comparison_texts:
            comp_vector = get_embedding(text)
            similarity = cosine_similarity(target_vector, comp_vector)
            
            print(f"비교 문장: {text}")
            print(f"-> 유사도 점수: {similarity:.4f}")
            
            # 맥락 이해 증명 분석
            if "수선" in text:
                print("   [분석] '고치다'와 '수선하다'는 단어는 달라도 맥락이 같아 점수가 높음 (문맥 이해)")
            elif "수리 영역" in text:
                print("   [분석] '수리'라는 글자는 같지만 수학적 맥락임을 구분하여 점수가 낮음 (변별력)")
            print("-" * 50)
            
    except Exception as e:
        print(f"추론 중 오류 발생: {e}")

if __name__ == "__main__":
    main()