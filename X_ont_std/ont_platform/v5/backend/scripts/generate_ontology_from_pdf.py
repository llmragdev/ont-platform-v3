#!/usr/bin/env python3
"""
Batch Ontology Generation from PDF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

목표: PDF → 온톨로지 엔티티/관계 자동 추출 (배치 프로세스)

사용법:
  python generate_ontology_from_pdf.py <pdf_path> <doc_id> [--company <company_id>] [--project <project_id>]

예시:
  python generate_ontology_from_pdf.py "./uploads/report.pdf" "doc-ai-voucher" --company "test-company" --project "test-project"

출력:
  - 추출된 엔티티 수
  - 추출된 관계 수
  - 온톨로지 저장 완료 메시지
"""

import sys
import json
import logging
from pathlib import Path
import argparse
import time
from contextlib import contextmanager

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.tenant_context import TenantContext
from app.services.ontology import OntologyService
from app.dependencies import get_llm_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


@contextmanager
def registry_lock(lock_path: Path):
    """Serialize registry writes across concurrent batch processes."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        if sys.platform == "win32":
            import msvcrt

            deadline = time.time() + 30
            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() >= deadline:
                        raise TimeoutError(f"registry lock timeout: {lock_path}")
                    time.sleep(0.1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def update_document_status(ctx: TenantContext, doc_id: str, status: str) -> bool:
    from app.services.document import DocumentService

    doc_svc = DocumentService(embeddings=None)
    lock_path = doc_svc._registry_path(ctx).with_suffix(".lock")
    with registry_lock(lock_path):
        registry = doc_svc._load_registry(ctx)
        if doc_id not in registry:
            return False
        registry[doc_id]["status"] = status
        doc_svc._save_registry(ctx, registry)
        return True


def extract_pdf_text(pdf_path: str) -> str:
    """PyPDFLoader를 사용하여 PDF 텍스트 추출"""
    from langchain_community.document_loaders import PyPDFLoader

    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        text = "\n\n".join([page.page_content for page in pages])
        logger.info(f"✅ PDF 로드 완료: {len(pages)} 페이지, {len(text)} 글자")
        return text
    except Exception as e:
        logger.error(f"❌ PDF 로드 실패: {e}")
        raise


def extract_ontology_from_text(text: str) -> dict:
    """
    LLM을 사용하여 텍스트에서 엔티티와 관계 추출

    응답 형식:
    {
      "entities": [
        {"id": "E001", "name": "...", "type": "PERSON", "description": "..."},
        ...
      ],
      "relationships": [
        {"id": "R001", "from_id": "E001", "to_id": "E002", "relation": "..."},
        ...
      ]
    }
    """
    llm = get_llm_client()

    # 텍스트가 너무 길면 첫 4000자로 제한 (JSON 절단 방지)
    text_truncated = text[:4000]

    prompt = f"""다음 텍스트에서 핵심 엔티티(개인, 조직, 제품 등)와 그 관계를 JSON 형식으로 추출해줘.

텍스트:
{text_truncated}

JSON 형식 (큰따옴표로 감싼 유효한 JSON):
{{
  "entities": [
    {{"id": "E001", "name": "이름", "type": "PERSON|ORGANIZATION|PRODUCT|CONCEPT", "description": "설명"}}
  ],
  "relationships": [
    {{"id": "R001", "from_id": "E001", "to_id": "E002", "relation": "관계이름"}}
  ]
}}

제약:
- entities는 최대 5개만 추출해.
- relationships는 최대 5개만 추출해.
- description은 80자 이내로 짧게 작성해.
- 유효한 JSON만 응답해. 다른 텍스트는 제외."""

    try:
        response_text = llm.generate(prompt, temperature=0.1, max_tokens=4096)
        if not response_text:
            logger.warning("⚠️  LLM이 비활성화되었거나 응답이 없습니다")
            raise ValueError("LLM returned empty response")

        data = _parse_llm_json_response(response_text)
        logger.info(f"✅ LLM 추출 완료: 엔티티 {len(data.get('entities', []))}개, 관계 {len(data.get('relationships', []))}개")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 파싱 실패: {e}")
        raise ValueError(f"LLM JSON parsing failed: {e}") from e
    except Exception as e:
        logger.error(f"❌ LLM 호출 실패: {e}")
        raise


def _parse_llm_json_response(response_text: str) -> dict:
    cleaned = response_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]

    cleaned = cleaned.strip()
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        if start >= 0:
            cleaned = cleaned[start:]
    if not cleaned.endswith("}"):
        end = cleaned.rfind("}")
        if end >= 0:
            cleaned = cleaned[: end + 1]

    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM JSON root must be an object")
    data.setdefault("entities", [])
    data.setdefault("relationships", [])
    if not isinstance(data["entities"], list) or not isinstance(data["relationships"], list):
        raise ValueError("LLM JSON entities/relationships must be lists")
    return data


def save_to_ontology(
    doc_id: str,
    entities: list,
    relationships: list,
    ctx: TenantContext
) -> int:
    """
    추출된 엔티티와 관계를 온톨로지에 저장

    반환: (저장된 엔티티 수, 저장된 관계 수)
    """
    svc = OntologyService()
    saved_entities = 0
    saved_relationships = 0

    # 엔티티 저장
    for entity in entities:
        try:
            e = {
                "name": entity.get("name", "Unknown"),
                "type": entity.get("type", "CONCEPT"),
                "description": entity.get("description", ""),
                "status": "active"
            }
            if entity.get("id"):
                e["id"] = entity["id"]
            svc.upsert_entity(doc_id, e, ctx)
            saved_entities += 1
            logger.info(f"  → 엔티티 저장: {e['name']} ({e['type']})")
        except Exception as e:
            logger.warning(f"  ⚠️  엔티티 저장 실패: {e}")

    # 관계 저장
    for rel in relationships:
        try:
            r = {
                "from_id": rel.get("from_id"),
                "to_id": rel.get("to_id"),
                "relation": rel.get("relation", "related_to")
            }
            if rel.get("id"):
                r["id"] = rel["id"]
            svc.add_relationship(doc_id, r, ctx)
            saved_relationships += 1
            logger.info(f"  → 관계 저장: {r['from_id']} → {r['to_id']} ({r['relation']})")
        except Exception as e:
            logger.warning(f"  ⚠️  관계 저장 실패: {e}")

    return saved_entities, saved_relationships


def main():
    parser = argparse.ArgumentParser(
        description="PDF에서 온톨로지 엔티티/관계 자동 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python generate_ontology_from_pdf.py "./uploads/report.pdf" "doc-ai-2025" --company "company-1" --project "project-1"
        """
    )
    parser.add_argument("pdf_path", help="PDF 파일 경로")
    parser.add_argument("doc_id", help="온톨로지 문서 ID (e.g., doc-ai-2025)")
    parser.add_argument("--company", default="default", help="회사 ID (기본값: default)")
    parser.add_argument("--project", default="default", help="프로젝트 ID (기본값: default)")
    parser.add_argument("--user", default="batch-service", help="사용자 ID (기본값: batch-service)")

    args = parser.parse_args()

    # 입력 검증
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        logger.error(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return 1

    logger.info(f"🚀 온톨로지 배치 생성 시작")
    logger.info(f"   PDF: {pdf_path}")
    logger.info(f"   Doc ID: {args.doc_id}")
    logger.info(f"   Company: {args.company}, Project: {args.project}")

    try:
        # 1. PDF 텍스트 추출
        logger.info("\n[Step 1] PDF 텍스트 추출 중...")
        text = extract_pdf_text(str(pdf_path))

        # 2. LLM으로 엔티티/관계 추출
        logger.info("\n[Step 2] LLM으로 엔티티/관계 추출 중...")
        ontology_data = extract_ontology_from_text(text)

        # 3. 온톨로지에 저장
        logger.info("\n[Step 3] 온톨로지에 저장 중...")
        ctx = TenantContext(
            user_id=args.user,
            company_id=args.company,
            project_id=args.project,
            role="Admin"
        )
        saved_entities, saved_relationships = save_to_ontology(
            args.doc_id,
            ontology_data.get("entities", []),
            ontology_data.get("relationships", []),
            ctx,
        )
        if saved_entities == 0:
            raise ValueError("No ontology entities were saved; marking generation as failed")

        # 4. 문서 상태 업데이트 (완료)
        logger.info("\n[Step 4] 문서 상태 업데이트 중...")
        update_document_status(ctx, args.doc_id, "complete")

        logger.info(f"\n✅ 온톨로지 생성 완료!")
        logger.info(f"   저장된 엔티티: {saved_entities}개")
        logger.info(f"   저장된 관계: {saved_relationships}개")
        logger.info(f"   다음 단계: VectorDB 동기화 자동 진행 (Async)")

        return 0

    except Exception as e:
        logger.error(f"\n❌ 온톨로지 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        
        # 문서 상태 업데이트 (에러)
        try:
            ctx = TenantContext(
                user_id=args.user,
                company_id=args.company,
                project_id=args.project,
                role="Admin"
            )
            update_document_status(ctx, args.doc_id, "error")
        except Exception as status_error:
            logger.warning(f"⚠️ 문서 상태 error 업데이트 실패: {status_error}")
            
        return 1


if __name__ == "__main__":
    sys.exit(main())
