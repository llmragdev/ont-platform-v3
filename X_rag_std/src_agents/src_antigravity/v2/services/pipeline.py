import os
from sqlalchemy.orm import Session
from fastapi import UploadFile
from repositories.doc_repo import DocRepository
from services.vector_db import VectorDbRouter

class DocumentPipelineService:
    def __init__(self, db: Session):
        self.doc_repo = DocRepository(db)

    def process_upload(self, file: UploadFile, category_mid: str, project_code: str = "000001"):
        # 1. RDBMS에 상태 pending으로 등록
        doc_record = self.doc_repo.create_doc(
            file_name=file.filename,
            category_mid=category_mid,
            project_code=project_code
        )
        
        self.doc_repo.update_status(doc_record.doc_id, "processing")
        
        try:
            # 2. 임시 스토리지에 파일 저장 및 텍스트 추출 (MOCK 파싱)
            content = file.file.read()
            text_content = content.decode('utf-8', errors='ignore')
            if not text_content.strip():
                text_content = "실제 PDF나 바이너리 텍스트 추출 결과입니다. (Mock)"
                
            # 3. 청킹 (단순 줄바꿈 혹은 100자 단위 분할)
            chunks = [text_content[i:i+100] for i in range(0, len(text_content), 100)]
            if not chunks:
                chunks = ["빈 문서입니다."]
            # 테스트/부하 방지를 위해 최대 10개 청크만 사용
            chunks = chunks[:10]
                
            # 4. 메타데이터 생성
            metadata_list = [
                {
                    "source_name": file.filename,
                    "category_mid": category_mid,
                    "vector_db_id": doc_record.assigned_vector_db,
                    "page_no": i + 1
                }
                for i in range(len(chunks))
            ]
            
            # 5. Vector DB에 적재
            adapter = VectorDbRouter.get_adapter(vector_db_id=doc_record.assigned_vector_db)
            adapter.add_documents(chunks, metadata_list)
            
            # 6. RDBMS 상태 업데이트 (완료)
            self.doc_repo.update_status(doc_record.doc_id, "completed")
            
        except Exception as e:
            self.doc_repo.update_status(doc_record.doc_id, "error")
            raise e
            
        return doc_record
