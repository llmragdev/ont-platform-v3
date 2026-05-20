import time
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.db_models import ProjectRagDoc, Project
from services.vector_db import VectorDbRouter, LocalJsonVectorDbAdapter
from services.pipeline import DocumentPipelineService
import os

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def perform_index_swap(self, tenant_id: str, project_code: str):
        """
        Index Swap 패턴 구현:
        1. 새 임시 컬렉션 생성
        2. 해당 프로젝트의 모든 문서를 재색인
        3. 라우팅 전환 (본 구현에서는 파일명 변경으로 시뮬레이션)
        """
        start_time = time.time()
        
        # 1. 프로젝트 정보 및 문서 목록 조회
        project = self.db.query(Project).filter(
            and_(Project.tenant_id == tenant_id, Project.project_code == project_code)
        ).first()
        if not project:
            raise ValueError("Project not found")

        docs = self.db.query(ProjectRagDoc).filter(
            and_(ProjectRagDoc.tenant_id == tenant_id, ProjectRagDoc.project_code == project_code, ProjectRagDoc.pipeline_status == "completed")
        ).all()

        current_vdb = project.vector_db_id or "vdb_default_01"
        swap_vdb = f"{current_vdb}_swap"
        
        logger.info(f"Starting Index Swap for {project_code}: {current_vdb} -> {swap_vdb}")

        # 2. 새 어댑터 준비 (기존 데이터 초기화)
        swap_adapter = LocalJsonVectorDbAdapter(swap_vdb)
        if os.path.exists(swap_adapter.storage_path):
            os.remove(swap_adapter.storage_path)

        # 3. 재색인 수행 (실제 파일이 서버에 보관되어 있다는 가정하에 재처리 로직이 필요하나, 
        # 여기서는 기존 Vector 데이터를 새 구조로 마이그레이션하거나 RDBMS 메타데이터를 갱신하는 로직으로 시뮬레이션)
        # 실제 운영 환경에서는 S3 등에서 원본 파일을 다시 읽어 process_upload를 호출함.
        
        for doc in docs:
            # 시뮬레이션: 기존 문서 정보를 바탕으로 새 컬렉션에 적재
            # (이 과정에서 조직 개편 등으로 변경된 org_id, dept_code 등이 반영됨)
            logger.info(f"Re-indexing doc: {doc.file_name} (org_id: {doc.org_id})")
            
            # 실제로는 파일 본문을 다시 읽어야 하지만, 구조상 메타데이터 갱신 적재로 대체
            # dummy content for simulation
            swap_adapter.add_documents(
                texts=[f"Re-indexed content of {doc.file_name}"],
                metadatas=[{
                    "doc_id": doc.doc_id,
                    "tenant_id": doc.tenant_id,
                    "org_id": doc.org_id,
                    "dept_code": doc.org_id[:2] if doc.org_id else None,
                    "vector_db_id": swap_vdb,
                    "source_name": doc.file_name,
                    "page_no": 1,
                    "created_at": doc.created_at.isoformat(),
                    "swapped_at": time.ctime()
                }]
            )

        # 4. Atomic Swap: 프로젝트의 vector_db_id를 swap_vdb로 변경
        project.vector_db_id = swap_vdb
        self.db.commit()

        # 5. 기존 컬렉션 삭제 (Cleanup)
        old_storage = f"storage/{current_vdb}.json"
        if os.path.exists(old_storage):
            # os.remove(old_storage) # 안전을 위해 백업 폴더로 이동 권장
            os.rename(old_storage, f"{old_storage}.bak_{int(time.time())}")

        duration = time.time() - start_time
        return {
            "status": "success",
            "project_code": project_code,
            "new_vector_db": swap_vdb,
            "processed_docs": len(docs),
            "duration_sec": round(duration, 2)
        }
