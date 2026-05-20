import json
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_document_pipeline_integration():
    """
    업로드 API를 테스트하고, 실제로 파이프라인(청킹->VectorDB)이
    작동했는지 그리고 검색 시 해당 청크가 반환되는지 엄격히 검증합니다.
    """
    
    # ==========================================
    # 1. 문서 업로드 (파이프라인 통과 검증)
    # ==========================================
    file_path = r"E:\ontology_edu\ont_platform\docs\ref_data\01_raw\2025년 AI바우처 사업설명회 발표자료.pdf"
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": ("2025_AI바우처.pdf", f, "application/pdf")}
            data = {"category_mid": "사업"}
            
            upload_response = client.post("/api/v1/documents/upload", files=files, data=data)
            
            # HTTP 200 검증
            assert upload_response.status_code == 200, "업로드 API 호출 실패"
            
            res_json = upload_response.json()
            assert res_json["status"] == "success"
            
            doc_data = res_json["data"]
            assert doc_data["doc_id"] is not None
            # pending이 아니라 실제로 파이프라인을 다 돌고 completed로 떨어졌는지 검증
            assert doc_data["pipeline_status"] == "completed", "파이프라인이 정상 완료되지 않았습니다."
            assert doc_data["assigned_vector_db"] == "vdb_사업_01"
            
    except FileNotFoundError:
        pytest.skip(f"테스트용 PDF 파일을 찾을 수 없어 스킵합니다: {file_path}")

    # ==========================================
    # 2. RAG 검색 (실제 업로드된 문서가 나오는지 검증)
    # ==========================================
    search_payload = {
        "query": "AI바우처 지원 대상이 어떻게 되나요?",
        "top_k": 3,
        "debug_mode": True,
        "filters": {
            "vector_db_id": "vdb_사업_01"
        }
    }
    
    search_response = client.post("/api/v1/rag/search", json=search_payload)
    assert search_response.status_code == 200
    
    search_json = search_response.json()
    assert search_json["status"] == "success"
    
    data = search_json["data"]
    # 껍데기 응답이 아니라 실제로 청크가 하나라도 반환되었는지 검증
    assert len(data["used_chunks"]) > 0, "검색된 청크가 없습니다! 파이프라인 적재 실패 의심."
    
    # 첫 번째 청크가 아까 업로드한 파일에서 온 것인지 메타데이터 검증
    first_chunk = data["used_chunks"][0]
    assert first_chunk["metadata"]["source_name"] == "2025_AI바우처.pdf"
    assert first_chunk["metadata"]["vector_db_id"] == "vdb_사업_01"
    
    # 디버그 모드가 켜져있으므로 debug_info가 null이 아니어야 함
    assert data["debug_info"] is not None
    assert "execution_time_ms" in data["debug_info"]
    assert len(data["debug_info"]["candidate_chunks"]) > 0

if __name__ == "__main__":
    pytest.main(["-v", "test_endpoints_v2.py"])
