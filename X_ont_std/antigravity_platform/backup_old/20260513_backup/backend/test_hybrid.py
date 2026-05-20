import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# app 경로 추가
sys.path.append(str(Path(__file__).parent))

from app.main import engine, vector_search, extractor, hybrid_engine
from app.engine import ObjectInstance

async def run_test():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY1")
    is_mock = not api_key
    
    if is_mock:
        print("Warning: GEMINI_API_KEY not found. Running in MOCK mode.")
        # Mocking extraction
        mock_extract = {
            "objects": [
                {"id": "FOUNDER_1", "type": "Person", "values": {"name": "Benoit Dageville", "specialty": "Database Architecture"}},
                {"id": "FOUNDER_2", "type": "Person", "values": {"name": "Thierry Cruanes", "specialty": "Query Optimization"}}
            ],
            "relationships": [
                {"type": "FOUNDED", "source_id": "FOUNDER_1", "target_id": "SNOWFLAKE"}
            ]
        }
        # Inject mock behavior into extractor and hybrid_engine
        extractor.extract_from_text = lambda x: mock_extract
        hybrid_engine.classify_query = lambda x: {"type": "hybrid", "reason": "Mocked"}
        
        # We also need to mock the generate_content call inside hybrid_engine.ask
        # To do this safely, we'll patch the ask method for this test run
        original_ask = hybrid_engine.ask
        async def mock_ask(question, doc_ids=None):
            return {
                "answer": f"[MOCK ANSWER] Snowflake {question}에 대한 하이브리드 분석 결과입니다. 온톨로지와 벡터 데이터를 성공적으로 결합했습니다.",
                "type": "hybrid",
                "vector_evidence": [{"filename": "Snowflake_소개서_HDC.pdf", "page": 1, "text": "Sample text", "score": 0.9}],
                "ontology_context": {"objects_count": 2}
            }
        hybrid_engine.ask = mock_ask

    print("=== 1. 문서 인제스션 테스트 ===")
    pdf_path = Path("uploads/test.pdf")
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        return

    # 인제스션은 API 키 없이도 Embedding 모델이 필요함 (여기서 실패할 수 있음)
    try:
        ingest_result = vector_search.ingest(pdf_path, pdf_path.name)
        print(f"인제스션 완료: {ingest_result}")
    except Exception as e:
        print(f"인제스션 실패 (임베딩 API 키 필요): {e}")
        if is_mock: print("임베딩을 건너뛰고 계속 진행합니다 (이미 DB가 있거나 목업 테스트 목적)...")

    print("\n=== 2. 온톨로지 추출 테스트 ===")
    print(f"추출 시작...")
    extract_result = extractor.extract_from_text("Dummy text for mock")
    print(f"추출 완료: {len(extract_result.get('objects', []))} 객체, {len(extract_result.get('relationships', []))} 관계")

    print("\n=== 3. 하이브리드 질의 테스트 (구조형 + 서술형) ===")
    questions = [
        "Snowflake의 창립자들은 누구인가요?",
        "Snowflake 아키텍처의 특징은?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        result = await hybrid_engine.ask(q)
        print(f"유형: {result['type']}")
        print(f"A: {result['answer']}")

if __name__ == "__main__":
    asyncio.run(run_test())
