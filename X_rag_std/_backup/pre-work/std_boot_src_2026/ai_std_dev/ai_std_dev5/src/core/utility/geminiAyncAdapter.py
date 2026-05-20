import os
from google import genai

async def call_gemini_sdk_async(p_prompt: str, p_model: str):
    """
    최하단 비동기 기술 어댑터: 구글 SDK와의 비동기(aio) 통신을 담당합니다.
    """
    v_api_key = os.getenv("GEMINI_API_KEY")
    # 비동기 지원을 위해 클라이언트 설정 유지
    client = genai.Client(api_key=v_api_key)
    
    try:
        # [수정] aio 모듈을 사용하여 비동기 호출 수행
        response = await client.aio.models.generate_content(
            model=p_model, 
            contents=p_prompt
        )
        return response.text
    except Exception as e:
        raise Exception(f"Gemini SDK Async Error: {str(e)}")