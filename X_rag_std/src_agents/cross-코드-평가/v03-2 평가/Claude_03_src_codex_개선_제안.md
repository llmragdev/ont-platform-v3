# src_codex 개선 제안

작성일: 2026-05-15  
작성: Claude Code  
비교 기준: `src_claud/v3` (테스트 17/17 통과, v1.3 표준 준수)

---

## 개선 우선순위 요약

| 순위 | 항목 | 영향도 | 난이도 |
|------|------|--------|--------|
| 1 | `X-Company-ID` → `X-Tenant-ID` 필수화 (400) | 🔴 치명 | 낮음 |
| 2 | `asyncio.to_thread` 비동기 파이프라인 | 🔴 치명 | 중 |
| 3 | org_id/dept_code 계층 격리 추가 | 🟠 높음 | 높음 |
| 4 | tags를 vector metadata에서 제외 | 🟠 높음 | 낮음 |
| 5 | `page_no` 실제 PDF 페이지 번호로 수정 | 🟡 중간 | 낮음 |
| 6 | RDBMS FK 선언 추가 | 🟡 중간 | 낮음 |
| 7 | Gateway 호출에 `tenant_id` 전달 | 🟡 중간 | 낮음 |
| 8 | `datetime.utcnow()` → timezone-aware | 🟡 중간 | 낮음 |
| 9 | `company_id` → `tenant_id` 전체 전환 | 🟡 중간 | 중 |
| 10 | v3 설계 코드 구현 착수 | 🟢 낮음 (단계적) | 높음 |

---

## 1. `X-Company-ID` → `X-Tenant-ID` 필수화 (최우선)

### 현재 문제

```python
# app/api/documents.py:21
def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")  # 헤더 없어도 통과

# app/api/rag.py:13
def _company_id(request: Request) -> str:
    return request.headers.get("X-Company-ID", "default")  # 동일 문제
```

v1.3 표준 §2.1: **`X-Tenant-ID` 헤더 누락 시 400 즉시 반환**. 현재 `"default"`로 폴백하므로 다른 테넌트 데이터가 섞일 수 있는 보안 결함이다.

### 개선 방법

**공통 헤더 추출 함수 교체**

```python
# app/core/deps.py (신규 또는 기존 errors.py에 추가)
from fastapi import Header, HTTPException

def get_tenant_id(x_tenant_id: str | None = Header(default=None)) -> str:
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID header is required",
        )
    return x_tenant_id
```

**모든 router에서 교체**

```python
# app/api/documents.py — 수정
from app.core.deps import get_tenant_id

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_mid: str = Form(...),
    tenant_id: str = Depends(get_tenant_id),  # ← 교체
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    ...
```

```python
# app/api/rag.py — 수정
@router.post("/search")
def search_rag(
    request_body: RagSearchRequest,
    tenant_id: str = Depends(get_tenant_id),  # ← 교체
    db: Session = Depends(get_db),
):
    ...
```

---

## 2. `asyncio.to_thread` 비동기 파이프라인

### 현재 문제

```python
# app/services/document_pipeline.py:48
async def upload_document(self, ...):
    content = await file.read()
    # ...
    self._run_pipeline(record, raw_path)  # 동기 블로킹 호출
    return self.repository.get(doc_id) or record
    # ↑ PDF 파싱 + embedding + 벡터 저장이 이벤트 루프를 점유
    # → 파일 크기가 클수록 다른 요청이 모두 대기
```

### 개선 방법

**pipeline을 별도 스레드에서 실행**

```python
# app/services/document_pipeline.py — 수정
import asyncio
from app.db.session import SessionLocal

def _run_pipeline_isolated(doc_id: str, raw_path_str: str, vector_store_dir: str):
    """독립 스레드 + 독립 Session — 이벤트 루프 블로킹 없음."""
    from pathlib import Path
    from app.repositories.document_repository import DocumentRepository

    db = SessionLocal()
    try:
        repo = DocumentRepository(db)
        record = repo.get(doc_id)
        repo.set_status(doc_id, "processing")
        raw_path = Path(raw_path_str)
        # ... 기존 _run_pipeline 로직 이전 ...
        repo.set_status(doc_id, "completed")
    except Exception as exc:
        try:
            repo.set_status(doc_id, "error", str(exc))
        except Exception:
            pass
    finally:
        db.close()


async def upload_document(self, file, category_mid, ...):
    content = await file.read()
    raw_path = settings.raw_documents_dir / f"{doc_id}_{safe_name}"
    raw_path.write_bytes(content)

    record = self.repository.create(
        doc_id=doc_id,
        pipeline_status="pending",   # 즉시 pending 반환
        ...
    )
    
    # fire-and-forget: 이벤트 루프 반환 후 스레드에서 처리
    asyncio.create_task(
        asyncio.to_thread(
            _run_pipeline_isolated,
            doc_id,
            str(raw_path),
            str(settings.vector_store_dir),
        )
    )
    
    return record  # pipeline_status == "pending"
```

**테스트를 위한 sync mode 플래그 추가** (src_claud/v3 방식)

```python
# app/core/config.py 추가
pipeline_sync_mode: bool = False  # pytest conftest에서 True로 설정
```

```python
# conftest.py
monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
```

---

## 3. org_id/dept_code 계층 격리 추가

### 현재 문제

`company_id` 1차원 격리만 존재 — 동일 회사 내 부서 간 문서 격리 불가.

```python
# app/services/document_pipeline.py:119 — org_id 저장 없음
metadata_payloads.append({
    "doc_id": record.doc_id,
    "company_id": record.company_id,
    # org_id, dept_code 없음
    ...
})
```

### 개선 방법

**모델에 org_id 추가**

```python
# app/models/db_models.py
class ProjectRagDocument(Base):
    # ... 기존 필드 ...
    org_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dept_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
```

**헤더 수신**

```python
# app/core/deps.py
def get_org_id(x_org_id: str | None = Header(default=None)) -> str | None:
    return x_org_id
```

**pipeline 메타데이터에 포함**

```python
# app/services/document_pipeline.py
metadata_payloads.append({
    "doc_id": record.doc_id,
    "tenant_id": tenant_id,              # company_id → tenant_id
    "org_id": org_id or "",              # None → "" sentinel (Chroma 호환)
    "dept_code": dept_code or "",
    "source_name": record.file_name,
    "page_no": page_no,                  # 실제 페이지 번호 (항목 5 참조)
    # tags 제외 (항목 4 참조)
})
```

**Vector adapter에 OR 조건 검색 추가**

```python
# app/services/vector_adapters.py — Chroma where clause
def _build_where(self, tenant_id: str, org_id: str | None):
    if not org_id:
        return {"tenant_id": {"$eq": tenant_id}}
    dept_code = org_id[:2] if len(org_id) >= 2 else org_id
    if org_id.endswith("00"):
        return {
            "$and": [
                {"tenant_id": {"$eq": tenant_id}},
                {"$or": [{"dept_code": {"$eq": dept_code}}, {"org_id": {"$eq": ""}}]},
            ]
        }
    return {
        "$and": [
            {"tenant_id": {"$eq": tenant_id}},
            {"$or": [{"org_id": {"$eq": org_id}}, {"org_id": {"$eq": ""}}]},
        ]
    }
```

---

## 4. tags를 vector metadata에서 제외

### 현재 문제

```python
# app/services/document_pipeline.py:123
metadata_payloads.append({
    # ...
    "tags": [],  # ← v1.3 §3.3 위반: tags는 RDBMS 전용
})
```

tags는 리스트 타입이며 Chroma metadata는 scalar만 지원한다. tags를 vector metadata에 저장하면:
- Chroma `add` 호출 시 타입 오류 발생
- 필터링도 불가능 (Chroma는 scalar `$eq`만 지원)

### 개선 방법

```python
# app/services/document_pipeline.py
metadata_payloads.append({
    "doc_id": record.doc_id,
    "tenant_id": tenant_id,
    "source_name": record.file_name,
    "source_url": record.source_url,
    "page_no": page_no,
    "category_mid": record.category_mid,
    "category_low": record.category_low or "",
    "vector_db_id": record.assigned_vector_db,
    "chunk_type": "text",
    # tags 완전 제거
})
```

tags가 필요하다면 RDBMS 별도 테이블(`wc_doc_tags`)에 저장하고 doc_id로 JOIN한다.

---

## 5. `page_no` 실제 PDF 페이지 번호로 수정

### 현재 문제

```python
# app/services/document_pipeline.py:108-125
for index, chunk in enumerate(chunks):
    metadata_payloads.append({
        "page_no": index + 1,  # ← chunk 인덱스 기반, PDF 페이지 번호 아님
    })
```

청크 100개짜리 문서의 마지막 청크가 `page_no=100`이 되지만 실제 PDF는 10페이지일 수 있음. 출처 추적 불가.

### 개선 방법

```python
# app/services/document_pipeline.py — _run_pipeline 수정
def _run_pipeline(self, record, raw_path):
    # PDF는 페이지별 텍스트 + page_no 추출
    pages = self._extract_pages(raw_path)  # [(page_no, text), ...]
    
    chunk_payloads = []
    metadata_payloads = []
    for page_no, page_text in pages:
        page_chunks = self.chunker.split_text(page_text)
        for chunk in page_chunks:
            chunk_id = f"{record.doc_id}#p{page_no}c{len(chunk_payloads)}"
            chunk_payloads.append({"chunk_id": chunk_id, "content": chunk})
            metadata_payloads.append({
                "page_no": page_no,  # 실제 PDF 페이지 번호
                # ...
            })

@staticmethod
def _extract_pages(path: Path) -> list[tuple[int, str]]:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return [
            (i + 1, page.extract_text() or "")
            for i, page in enumerate(reader.pages)
        ]
    # 텍스트 파일은 단일 페이지
    return [(1, path.read_text(encoding="utf-8", errors="replace"))]
```

---

## 6. RDBMS FK 선언 추가

### 현재 문제

```python
# app/models/db_models.py — FK 전혀 없음
class ProjectRagDocument(Base):
    project_code: Mapped[str] = mapped_column(String(6), default="000001")
    company_id: Mapped[str] = mapped_column(String(64), ...)
    # ForeignKey 없음 → 참조 무결성 없음, 고아 레코드 발생 가능
```

### 개선 방법

```python
# app/models/db_models.py
from sqlalchemy import ForeignKey, ForeignKeyConstraint

class ProjectRagDocument(Base):
    __tablename__ = "wc_project_rag_doc"

    project_code: Mapped[str] = mapped_column(
        String(6),
        ForeignKey("wc_project.project_code"),
        default="000001",
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ca_company.company_id"),
        nullable=False,
    )
    # ...

class OrganizationManagement(Base):
    __tablename__ = "ca_org_mgnt"

    company_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ca_company.company_id"),
        nullable=False,
    )
    # org_id PK 단독 → 복합 PK로 변경 (v1.3 §2.3)
    __table_args__ = (
        {"primary_key": True},  # (company_id, org_id) 복합 PK
    )
```

---

## 7. Gateway 호출에 `tenant_id` 전달

### 현재 문제

```python
# app/services/rag_service.py 내부 (추정)
# Gateway 호출 시 tenant_id 없이 "default" 하드코딩
gateway.generate_answer(query=query, tenant_id="default")
```

멀티테넌트 환경에서 테넌트별 LLM 키 분리가 불가능하다. Gateway가 테넌트별 과금·모델 선택을 지원하더라도 활용할 수 없다.

### 개선 방법

```python
# app/services/rag_service.py
def search(self, request: RagSearchRequest, tenant_id: str, org_id: str | None = None):
    # embedding 생성 시 tenant_id 전달
    query_vector = self.embedding_service.embed_text(
        request.query,
        tenant_id=tenant_id,  # ← 추가
    )
    
    # LLM 답변 생성 시도 tenant_id 전달
    answer = self.llm_client.generate_answer(
        query=request.query,
        chunks=chunks,
        tenant_id=tenant_id,  # ← 추가
    )
```

---

## 8. `datetime.utcnow()` → timezone-aware

### 현재 문제

```python
# app/models/db_models.py:16
created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
# Python 3.12+ DeprecationWarning
```

`datetime.utcnow()`는 timezone-naive datetime을 반환한다. 시스템 timezone이 다른 환경(컨테이너, 클라우드)에서 혼용 시 datetime 비교 오류 발생 가능.

### 개선 방법

```python
# app/models/db_models.py
from datetime import datetime, timezone

class Company(Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class ProjectRagDocument(Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

---

## 9. `company_id` → `tenant_id` 전체 전환

v1.3 표준은 `tenant_id`를 사용한다. 현재 코드베이스 전체가 `company_id`로 되어 있어 표준과 일치하지 않는다.

### 전환 범위

- `app/models/db_models.py`: `Company` → `Tenant`, `company_id` 컬럼명 전환
- `app/models/schemas.py`: 모든 `company_id` 필드
- `app/services/document_pipeline.py`: 파라미터명, 메타데이터 키
- `app/api/documents.py`, `app/api/rag.py`: `_company_id()` 헬퍼 삭제
- `app/repositories/*.py`: 쿼리 필터

**마이그레이션 전략**

```python
# Alembic 마이그레이션 (ALTER TABLE)
def upgrade():
    op.add_column("wc_project_rag_doc", sa.Column("tenant_id", sa.String(64)))
    op.execute("UPDATE wc_project_rag_doc SET tenant_id = company_id")
    op.alter_column("wc_project_rag_doc", "tenant_id", nullable=False)
    op.drop_column("wc_project_rag_doc", "company_id")
```

---

## 10. v3 설계 코드 구현 착수

현재 `src_codex`는 v2 코드만 존재하고 v3 설계 문서만 완성된 상태다. 설계 문서에 따르면 v3 구현 완료 시:

- **Index Swap Pattern** 추가 (src_antigravity만 현재 구현)
- **Alembic migration** 추가
- **org_id 계층** 완전 구현

위 1~9번 개선을 v2에 적용하는 것과 v3 설계를 새로 구현하는 것 중 **v3 새 구현이 더 깨끗하다**. 단, 빠른 효과를 원하면 1~4번(헤더 필수화, asyncio, tags 제거, page_no)은 v2 코드에 즉시 적용 가능하다.

---

## 개선 후 예상 점수

| 항목 | 현재 | 개선 후 |
|------|------|---------|
| X-Tenant-ID 필수화 | ❌ 선택(default) | ✅ 400 반환 |
| 비동기 파이프라인 | ❌ 동기 블로킹 | ✅ to_thread + pending |
| org_id 계층 격리 | ❌ 없음 | ✅ OR 조건 검색 |
| tags 제외 | ❌ vector에 저장 | ✅ RDBMS 전용 |
| page_no 실제 번호 | ❌ 인덱스 기반 | ✅ PDF 페이지 |
| FK 선언 | ❌ 없음 | ✅ 참조 무결성 |
| tenant_id Gateway | ❌ "default" | ✅ 전달 |
| datetime UTC | ❌ utcnow | ✅ timezone-aware |
| **종합 점수** | **6.8 / 10** | **9.0 / 10** |

> v3 설계 문서대로 구현까지 완료되면 (Index Swap + Alembic 포함) 10점에 근접한 산출물이 된다.
