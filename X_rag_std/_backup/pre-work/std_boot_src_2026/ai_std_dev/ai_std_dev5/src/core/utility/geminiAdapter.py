import os
from google import genai

def call_gemini_sdk(p_prompt: str, p_model: str):
    """
    최하단 기술 어댑터: 구글 SDK와의 직접적인 통신만 담당합니다.
    """
    v_api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=v_api_key)
    
    try:
        response = client.models.generate_content(model=p_model, contents=p_prompt)
        return response.text
    except Exception as e:
        raise Exception(f"Gemini SDK Error: {str(e)}")