# 상세설계 02: 벡터 DB 분리 및 라우팅 관리 (v1.2)

## 1. 개요
본 문서는 기본 설계의 핵심인 "Vector DB의 물리적/논리적 분리"를 시스템 내에서 어떻게 설정하고 라우팅할 것인지에 대한 상세 명세서입니다.
* **핵심 목표**: 단일 거대 DB의 부하를 막고, 카테고리(`category_mid`) 혹은 테넌트별로 안정적인 벡터 DB 환경(ChromaDB, FAISS 등)을 제공하는 것.

---

## 2. 라우팅 레지스트리(Registry) 구조 설계
애플리케이션(FastAPI 백엔드)은 코딩 내에 DB 접속 정보를 하드코딩하지 않고, 설정 파일이나 RDBMS의 라우팅 테이블을 통해 동적으로 커넥션을 맺습니다.

### 2.1. Vector DB Routing Config 예시 (JSON/YAML)
```json
{
  "routing_rules": [
    {
      "vector_db_id": "vdb_policy_01",
      "target_category_mid": ["규정", "지침", "매뉴얼"],
      "engine_type": "chroma",
      "connection": {
        "host": "chroma-policy-service.internal",
        "port": 8000,
        "collection_name": "hr_policy_dim768"
      }
    },
    {
      "vector_db_id": "vdb_tech_01",
      "target_category_mid": ["IT", "개발표준", "아키텍처"],
      "engine_type": "qdrant",
      "connection": {
        "host": "qdrant-tech-service.internal",
        "port": 6333,
        "collection_name": "tech_docs_dim768"
      }
    }
  ]
}
```

---

## 3. 라우팅 로직 상세 플로우

### 3.1. 문서 임베딩 적재 시 (Write)
1. 클라이언트가 `category_mid: "IT"`로 문서를 업로드.
2. 백엔드 라우터(Router) 객체가 레지스트리를 조회하여 `vdb_tech_01` 설정값을 찾음.
3. 해당 호스트(`qdrant-tech-service.internal`)로 접속하는 `VectorDbClient` 객체를 동적으로 생성하여 임베딩된 청크를 Insert. **이때 `embeddings=` 파라미터 명시 필수 (5항 참조).**

### 3.2. RAG 검색 질의 시 (Read)
1. 프론트엔드가 쿼리와 함께 `filters: {"category_mid": "IT"}`를 전송.
2. 백엔드 라우터가 역시 동일하게 `vdb_tech_01`에 연결을 맺고, 해당 인스턴스의 `tech_docs_dim768` 컬렉션에서만 검색(Search) 수행.
3. **검색 필터에 `tenant_id`를 반드시 강제 주입**하여 타 테넌트 문서가 결과에 포함되지 않도록 합니다. `org_id` 또는 `dept_code`가 있는 경우 조직 단위 격리도 추가 주입합니다. (기본설계 2.5항)
4. 이를 통해 불필요한 타 도메인의 벡터 공간까지 유사도 검색을 할 필요가 없어 응답 속도가 비약적으로 상승함.

---

## 4. 엔진별 인터페이스 어댑터 설계 (Adapter Pattern)
ChromaDB, FAISS, Qdrant 등 다양한 DB 엔진을 유연하게 교체하기 위해 어댑터 패턴을 파이썬 표준에 맞게 적용합니다.

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVectorDbAdapter(ABC):
    @abstractmethod
    def add_documents(self, chunks: List[Dict[str, Any]], metadata: List[Dict[str, Any]]) -> bool:
        """청크 텍스트와 메타데이터를 벡터 DB에 저장.
        반드시 embeddings= 파라미터로 외부 임베딩 서비스 결과를 명시 전달해야 합니다. (5항 참조)"""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """query_vector로 유사도 검색.
        filters에 tenant_id를 반드시 포함하여 테넌트 격리를 보장합니다."""
        pass

    @abstractmethod
    def delete_by_doc_id(self, doc_id: str) -> int:
        """doc_id 메타데이터 필터로 해당 문서의 모든 청크를 삭제합니다.
        증분 업데이트(상세설계 01 4.2) 수행 전 반드시 호출합니다.
        반환값: 삭제된 청크 수"""
        pass

    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 이름, 벡터 차원, 총 문서 수 등 메타 정보를 반환합니다.
        헬스체크 및 임베딩 차원 정합성 검증에 활용합니다."""
        pass
```

* 실제 연동 시 `ChromaAdapter`, `FaissAdapter`, `QdrantAdapter` 클래스가 위 기본 클래스를 상속받아 각각의 드라이버 스펙에 맞게 구현됩니다.

---

## 5. 벡터 저장 임베딩 일관성 규칙

### 5.1. Chroma/Qdrant 문서 저장 시 embeddings= 명시 필수
ChromaDB는 `add()` 호출 시 `embeddings=` 파라미터를 생략하면 **Chroma 내부 기본 임베딩 함수**를 사용합니다. 이 경우 검색 시 사용하는 외부 임베딩 서비스 벡터와 공간이 달라져 검색 품질이 크게 저하됩니다.

**규칙: 문서 저장 시 반드시 외부 임베딩 서비스로 직접 생성 후 명시 전달**

```python
# 금지 — Chroma 자체 임베딩 사용 → 쿼리 임베딩과 벡터 공간 불일치
collection.add(ids=ids, documents=texts, metadatas=metadata)  # ❌

# 필수 — 외부 임베딩 서비스(LLM Gateway) 결과를 명시 전달
embeddings = [embedding_service.embed_text(t) for t in texts]
collection.add(
    ids=ids,
    documents=texts,
    embeddings=embeddings,   # ✅ 동일 임베딩 서비스 → 공간 일치 보장
    metadatas=metadata
)
```

### 5.2. 컬렉션 명명 규칙
임베딩 차원을 컬렉션 이름에 포함하여 차원 혼재를 방지합니다.

```
{project_code}_{category_mid}_dim{dimension}
예: 000001_hr_policy_dim768, 000001_tech_doc_dim1536
```

임베딩 모델 변경 시 기존 컬렉션과 **별도의 새 컬렉션**을 생성하고 마이그레이션합니다. 기존 컬렉션에 다른 차원 벡터를 혼재하지 않습니다.
