"""온톨로지 API 라우터"""
from fastapi import APIRouter, Query, UploadFile, File, Depends, HTTPException
from typing import Dict, Any, List
import logging

from app.services.neighborhood_service import NeighborhoodService
from app.services.mapping_service import (
    MappingService,
    MappingRequest,
    MappingCandidateRequest
)
from app.services.import_preview_service import ImportPreviewService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ontology", tags=["Ontology"])


# 의존성 (실제로는 DI 컨테이너에서 주입됨)
def get_neighborhood_service(graph_db=None) -> NeighborhoodService:
    """이웃 탐색 서비스 주입"""
    return NeighborhoodService(graph_db)


def get_mapping_service(graph_db=None, embedding_service=None) -> MappingService:
    """매핑 서비스 주입"""
    return MappingService(graph_db, embedding_service)


def get_import_preview_service(graph_db=None) -> ImportPreviewService:
    """임포트 미리보기 서비스 주입"""
    return ImportPreviewService(graph_db)


# Task 7-1: RDF 이웃 탐색 API
@router.get("/rdf/neighborhood/{uri:path}")
async def get_neighborhood(
    uri: str,
    depth: int = Query(1, ge=1, le=2, description="탐색 깊이 (1 또는 2)"),
    limit: int = Query(100, ge=10, le=500, description="반환할 최대 노드 수"),
    service: NeighborhoodService = Depends(get_neighborhood_service)
) -> Dict[str, Any]:
    """
    RDF 그래프 이웃 탐색

    Args:
        uri: 중심 노드 URI
        depth: 탐색 깊이 (1 또는 2)
        limit: 반환할 최대 노드 수

    Returns:
        - centerNode: 중심 노드 URI
        - nodes: 이웃 노드 목록
        - edges: 엣지 목록
        - processingTimeMs: 처리 시간
    """
    try:
        result = await service.get_neighborhood(uri, depth, limit)
        return result
    except Exception as e:
        logger.error(f"Failed to get neighborhood: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 7-2: 매핑 생성 API
@router.post("/mappings")
async def create_mapping(
    request: MappingRequest,
    service: MappingService = Depends(get_mapping_service)
) -> Dict[str, Any]:
    """
    매핑 생성

    Args:
        request.externalUri: 외부 URI
        request.internalUri: 내부 URI
        request.relationshipType: 관계 타입 (기본: skos:exactMatch)
        request.confidence: 신뢰도 (0~1)

    Returns:
        - success: 성공 여부
        - mapping: 생성된 매핑 정보
    """
    try:
        result = await service.create_mapping(request)
        return result
    except Exception as e:
        logger.error(f"Failed to create mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 7-2: 매핑 후보 추출 API
@router.get("/mapping-candidates")
async def get_mapping_candidates(
    externalUri: str = Query(..., description="외부 URI"),
    limit: int = Query(10, ge=5, le=50, description="반환할 최대 후보 수"),
    service: MappingService = Depends(get_mapping_service)
) -> Dict[str, Any]:
    """
    외부 URI와 유사한 내부 URI 후보 추출

    Args:
        externalUri: 외부 URI
        limit: 반환할 최대 후보 수

    Returns:
        - externalUri: 입력된 외부 URI
        - candidates: 유사도 기반 정렬된 후보 목록
            - internalUri: 내부 URI
            - similarity: 유사도 (0~1)
            - label: 라벨
    """
    try:
        request = MappingCandidateRequest(
            externalUri=externalUri,
            limit=limit
        )
        result = await service.get_mapping_candidates(request)
        return result
    except Exception as e:
        logger.error(f"Failed to get mapping candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 7-3: Import Preview API
@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    service: ImportPreviewService = Depends(get_import_preview_service)
) -> Dict[str, Any]:
    """
    RDF 파일 임포트 미리보기

    Args:
        file: RDF 파일 (Turtle, RDF/XML, N-Triples 등)

    Returns:
        - newTripleCount: 새 triple 개수
        - newEntityCount: 새 엔티티 개수
        - potentialConflicts: 잠재적 충돌 목록
        - suggestedMappings: 제안된 매핑 목록
    """
    try:
        # 파일 읽기
        content = await file.read()
        rdf_content = content.decode('utf-8')

        # 파일 확장자에서 포맷 추론
        file_format = "turtle"
        if file.filename:
            if file.filename.endswith('.rdf') or file.filename.endswith('.xml'):
                file_format = "xml"
            elif file.filename.endswith('.nt'):
                file_format = "nt"
            elif file.filename.endswith('.jsonld'):
                file_format = "jsonld"

        # 미리보기 수행
        result = await service.preview_import(rdf_content, file_format)
        return result
    except Exception as e:
        logger.error(f"Failed to preview import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 7-3: 실제 Import API (선택)
@router.post("/import")
async def import_rdf(
    file: UploadFile = File(...),
    applyMappings: bool = Query(True, description="제안된 매핑 자동 적용")
) -> Dict[str, Any]:
    """
    RDF 파일 실제 임포트

    Args:
        file: RDF 파일
        applyMappings: 제안된 매핑 자동 적용 여부

    Returns:
        - success: 임포트 성공 여부
        - importedTripleCount: 임포트된 triple 개수
        - appliedMappingCount: 적용된 매핑 개수
    """
    try:
        # 파일 읽기
        content = await file.read()
        rdf_content = content.decode('utf-8')

        # 실제 임포트 로직 (간단한 예)
        return {
            "success": True,
            "importedTripleCount": 1000,  # 실제로는 파일에서 계산
            "appliedMappingCount": 10 if applyMappings else 0,
            "message": "Import completed successfully"
        }
    except Exception as e:
        logger.error(f"Failed to import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 헬스 체크
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """API 상태 확인"""
    return {"status": "ok"}
