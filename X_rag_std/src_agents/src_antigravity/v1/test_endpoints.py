from fastapi.testclient import TestClient
import json
from main import app

client = TestClient(app)

def run_tests():
    print("="*50)
    print("[TEST 1] 문서 업로드 API 테스트 (/api/v1/documents/upload)")
    print("="*50)
    
    # 실제 PDF 파일 테스트
    file_path = r"E:\ontology_edu\ont_platform\docs\ref_data\01_raw\2025년 AI바우처 사업설명회 발표자료.pdf"
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": ("2025_AI바우처_사업설명회.pdf", f, "application/pdf")}
            data = {
                "category_mid": "사업",
                "category_low": "AI바우처"
            }
            upload_response = client.post("/api/v1/documents/upload", files=files, data=data)
            
        print("Status Code:", upload_response.status_code)
        print("Response JSON:")
        print(json.dumps(upload_response.json(), indent=2, ensure_ascii=False))
        print("\n")
    except FileNotFoundError:
        print(f"[ERROR] 테스트용 파일을 찾을 수 없습니다: {file_path}")
        print("업로드 테스트를 건너뜁니다.\n")
    
    print("="*50)
    print("[TEST 2] RAG 검색 API 테스트 - 일반 모드 (/api/v1/rag/search)")
    print("="*50)
    
    search_payload = {
        "query": "2026년 인사 규정에 대해 알려줘",
        "top_k": 3,
        "debug_mode": False,
        "filters": {
            "category_mid": "규정"
        }
    }
    
    search_response = client.post("/api/v1/rag/search", json=search_payload)
    print("Status Code:", search_response.status_code)
    print("Response JSON:")
    print(json.dumps(search_response.json(), indent=2, ensure_ascii=False))
    print("\n")
    
    print("="*50)
    print("[TEST 3] RAG 검색 API 테스트 - 디버그 모드 (/api/v1/rag/search)")
    print("="*50)
    
    search_payload["debug_mode"] = True
    debug_search_response = client.post("/api/v1/rag/search", json=search_payload)
    print("Status Code:", debug_search_response.status_code)
    print("Response JSON (디버그 모드 작동 확인):")
    print(json.dumps(debug_search_response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_tests()
