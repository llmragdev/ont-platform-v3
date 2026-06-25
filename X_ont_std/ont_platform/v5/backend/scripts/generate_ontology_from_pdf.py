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
from typing import Any

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


def chunk_text(text: str, chunk_size: int = 8000, overlap: int = 800, max_chunks: int | None = None) -> list[dict[str, Any]]:
    """Split long text into overlapping chunks for ontology extraction."""
    if chunk_size <= 0:
        return [{"chunk_id": "chunk-001", "text": text, "start": 0, "end": len(text)}]

    chunks: list[dict[str, Any]] = []
    start = 0
    index = 1
    text_len = len(text)
    step = max(1, chunk_size - max(0, overlap))

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "chunk_id": f"chunk-{index:03d}",
                "text": chunk,
                "start": start,
                "end": end,
            })
            index += 1
        if max_chunks and len(chunks) >= max_chunks:
            break
        if end >= text_len:
            break
        start += step

    return chunks


def _normalize_key(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _merge_ontology_chunks(chunk_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge chunk-level ontology JSON while preserving stable IDs."""
    merged_entities: list[dict[str, Any]] = []
    merged_relationships: list[dict[str, Any]] = []
    entity_key_to_id: dict[tuple[str, str], str] = {}
    old_to_new_id: dict[tuple[str, str], str] = {}
    relationship_keys: set[tuple[str, str, str]] = set()

    for result in chunk_results:
        chunk_id = result.get("_chunk_id", "")
        for entity in result.get("entities", []):
            name = entity.get("name")
            if not name:
                continue
            entity_type = str(entity.get("type") or "UNKNOWN").upper()
            key = (_normalize_key(name), entity_type)
            old_id = str(entity.get("id") or "")

            if key not in entity_key_to_id:
                new_id = f"E{len(merged_entities) + 1:04d}"
                entity_key_to_id[key] = new_id
                merged = dict(entity)
                merged["id"] = new_id
                merged["type"] = entity_type
                merged.setdefault("role", "contextual_entity")
                merged.setdefault("source", {})
                if isinstance(merged["source"], dict):
                    merged["source"].setdefault("chunk_id", chunk_id)
                merged_entities.append(merged)
            else:
                new_id = entity_key_to_id[key]
                existing = next((e for e in merged_entities if e["id"] == new_id), None)
                if existing:
                    if not existing.get("description") and entity.get("description"):
                        existing["description"] = entity.get("description")
                    if not existing.get("role") and entity.get("role"):
                        existing["role"] = entity.get("role")

            if old_id:
                old_to_new_id[(chunk_id, old_id)] = new_id

    for result in chunk_results:
        chunk_id = result.get("_chunk_id", "")
        for rel in result.get("relationships", []):
            from_id = old_to_new_id.get((chunk_id, str(rel.get("from_id") or "")))
            to_id = old_to_new_id.get((chunk_id, str(rel.get("to_id") or "")))
            relation = str(rel.get("relation") or rel.get("relation_type") or "related_to")
            if not from_id or not to_id or from_id == to_id:
                continue
            key = (from_id, relation, to_id)
            if key in relationship_keys:
                continue
            relationship_keys.add(key)

            merged_rel = dict(rel)
            merged_rel["id"] = f"R{len(merged_relationships) + 1:04d}"
            merged_rel["from_id"] = from_id
            merged_rel["to_id"] = to_id
            merged_rel["relation"] = relation
            merged_rel.setdefault("source", {})
            if isinstance(merged_rel["source"], dict):
                merged_rel["source"].setdefault("chunk_id", chunk_id)
            merged_relationships.append(merged_rel)

    return {"entities": merged_entities, "relationships": merged_relationships}


def extract_ontology_from_text(
    text: str,
    *,
    chunk_size: int = 8000,
    chunk_overlap: int = 800,
    max_chunks: int | None = None,
    max_entities_per_chunk: int = 30,
    max_relationships_per_chunk: int = 60,
) -> dict:
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
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap, max_chunks=max_chunks)
    logger.info(f"🧩 텍스트 분할 완료: {len(chunks)}개 chunk (chunk_size={chunk_size}, overlap={chunk_overlap})")

    chunk_results: list[dict[str, Any]] = []
    for chunk in chunks:
        prompt = f"""다음 텍스트에서 질의응답과 데이터 통합에 유용한 의미 온톨로지 엔티티와 관계를 JSON 형식으로 추출해줘.

중요 원칙:
- 저자, 소속, 논문명 같은 문헌 메타데이터보다 개념, 절차, 방법, 시스템, 평가항목, 지표, 데이터 객체, 속성, 제약 조건을 우선 추출해.
- PERSON, ORGANIZATION, PUBLICATION도 고정적으로 제외하지 말고, 문맥상 핵심 행위자/대상인지 메타데이터인지 role로 구분해.
- entity.type만으로 판단하지 말고 role과 relation을 함께 표현해.
- 관계는 질의응답에 쓸 수 있는 의미 관계를 우선 추출해.

권장 entity.type 예시:
CONCEPT, SYSTEM, METHOD, PROCESS, PROPERTY, METRIC, EVALUATION_CRITERION, DATA_OBJECT, RULE, ACTOR, ORGANIZATION, PERSON, PUBLICATION, UNKNOWN

권장 entity.role 예시:
core_concept, domain_actor, method, process_step, evaluation_target, evaluation_criterion, quality_metric, data_schema, data_field, constraint, rule, evidence_source, metadata_author, metadata_publication, metadata_affiliation, contextual_entity

권장 relation 예시:
defines, composes, requires, evaluates, measures, constrains, transforms, contains, maps_to, supports, grounds, has_property, has_step, has_metric, is_part_of

텍스트 chunk_id: {chunk["chunk_id"]}
텍스트:
{chunk["text"]}

JSON 형식 (큰따옴표로 감싼 유효한 JSON):
{{
  "entities": [
    {{
      "id": "E001",
      "name": "엔티티명",
      "type": "CONCEPT",
      "role": "core_concept",
      "description": "문서 근거 기반 설명",
      "source": {{"chunk_id": "{chunk["chunk_id"]}"}},
      "confidence": 0.8
    }}
  ],
  "relationships": [
    {{
      "id": "R001",
      "from_id": "E001",
      "to_id": "E002",
      "relation": "supports",
      "relation_label": "지원한다",
      "description": "관계 설명",
      "source": {{"chunk_id": "{chunk["chunk_id"]}"}},
      "confidence": 0.8
    }}
  ]
}}

제약:
- entities는 최대 {max_entities_per_chunk}개까지 추출해.
- relationships는 최대 {max_relationships_per_chunk}개까지 추출해.
- 유효한 JSON만 응답해. 다른 텍스트는 제외."""

        try:
            response_text = llm.generate(prompt, temperature=0.1, max_tokens=8192)
            if not response_text:
                logger.warning("⚠️  LLM이 비활성화되었거나 응답이 없습니다")
                raise ValueError("LLM returned empty response")

            data = _parse_llm_json_response(response_text)
            data["_chunk_id"] = chunk["chunk_id"]
            logger.info(
                f"✅ {chunk['chunk_id']} 추출 완료: "
                f"엔티티 {len(data.get('entities', []))}개, 관계 {len(data.get('relationships', []))}개"
            )
            chunk_results.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ {chunk['chunk_id']} JSON 파싱 실패: {e}")
            raise ValueError(f"LLM JSON parsing failed: {e}") from e
        except Exception as e:
            logger.error(f"❌ {chunk['chunk_id']} LLM 호출 실패: {e}")
            raise

    merged = _merge_ontology_chunks(chunk_results)
    logger.info(
        f"✅ LLM 추출 병합 완료: 엔티티 {len(merged.get('entities', []))}개, "
        f"관계 {len(merged.get('relationships', []))}개"
    )
    return merged


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
            for optional_key in ("role", "source", "confidence", "aliases", "properties"):
                if optional_key in entity:
                    e[optional_key] = entity[optional_key]
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
            for optional_key in ("relation_label", "description", "source", "confidence", "properties"):
                if optional_key in rel:
                    r[optional_key] = rel[optional_key]
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
    parser.add_argument("--chunk-size", type=int, default=8000, help="LLM 추출 chunk 크기 (기본값: 8000자)")
    parser.add_argument("--chunk-overlap", type=int, default=800, help="chunk 간 중복 글자 수 (기본값: 800자)")
    parser.add_argument("--max-chunks", type=int, default=0, help="처리할 최대 chunk 수 (0이면 전체)")
    parser.add_argument("--max-entities-per-chunk", type=int, default=30, help="chunk당 최대 엔티티 수")
    parser.add_argument("--max-relationships-per-chunk", type=int, default=60, help="chunk당 최대 관계 수")

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
        ontology_data = extract_ontology_from_text(
            text,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            max_chunks=args.max_chunks or None,
            max_entities_per_chunk=args.max_entities_per_chunk,
            max_relationships_per_chunk=args.max_relationships_per_chunk,
        )

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
