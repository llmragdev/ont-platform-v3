import os 
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
v_api_key = os.getenv("GEMINI_API_KEY")

# 발급받으신 API 키를 여기에 입력하세요
genai.configure(api_key=v_api_key)

model = 'models/gemini-embedding-001'

result = genai.embed_content(
    model=model,
    content="안녕하세요 AI백엔드 개발자 최남규입니다",
    task_type="retrieval_document"
)

# 리스트의 길이를 출력

print(result['embedding'])
print(f"임베딩 벡터의 차원 수: {len(result['embedding'])}")