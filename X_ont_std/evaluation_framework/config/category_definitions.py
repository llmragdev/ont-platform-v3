"""
카테고리 정의 및 범위 설정

평가 대상 카테고리별 범위, 필수 개념, 문서를 명시하여
평가 시 자동으로 검증할 수 있게 함.
"""

CATEGORY_DEFINITIONS = {
    "Ontology": {
        "scope": "온톨로지 개념, 온톨로지 기반 시스템, 지식 그래프, 의미 웹",
        "required_concepts": [
            "ontology", "concept", "relationship", "knowledge_graph",
            "semantic", "rdf", "owl", "entity", "class", "property",
            "개념", "관계", "지식", "그래프", "온톨로지"
        ],
        "required_documents": [
            "NLP - [03] 온톨로지이질성문제를해결하기위한온톨로지매칭방법-2024.pdf",
            "NLP - [07] NLP - 온톨로지 학습 기반 지식 그래프 구축 - 2022.pdf",
            "국방 - [01] 온톨로지와지식그래프를활용한국방지휘통제데이터통합방법연구-2025.pdf",
            "국방 - [02] 해외 온톨로지 현황과 한국군 온톨로지 개발방안_202306.pdf"
        ],
        "out_of_scope": [
            "snowflake", "elasticsearch", "mongodb", "postgresql",
            "kafka", "spark", "hadoop", "cuda", "tensorflow"
        ],
        "fallback_answer": None  # Ontology는 범위 외 질문 없음
    },

    "Advanced RAG": {
        "scope": "RAG 기법, 검색 기반 생성, 메타데이터 활용, 벡터 검색",
        "required_concepts": [
            "rag", "retrieval", "augmented", "generation", "embedding",
            "vector", "metadata", "retrieval_model", "ranking",
            "검색", "생성", "증강", "메타데이터", "벡터", "임베딩"
        ],
        "required_documents": [
            "NLP - [06] 정적 언어모델부터 생성형AI까지, 텍스트를 다시 쓰는 기술에 대하여 - 2025.pdf",
            "NLP - [08] NLP - 한국근대문인 데이터베이스 구축 방법탐색-2025.pdf",
            "NLP - [09] NLP - 실시간 문맥 인식 감성 분석을 위한 모듈형 아키텍처 설계-2025.pdf"
        ],
        "out_of_scope": [
            "snowflake", "일반 db 설계", "데이터베이스 성능"
        ],
        "fallback_answer": None
    },

    "Snowflake": {
        "scope": "Snowflake 플랫폼 관련 기술",
        "required_concepts": [
            "snowflake", "snowflake_rag", "snowflake_specific"
        ],
        "required_documents": [],  # Snowflake 문서 없음
        "out_of_scope": [],
        "fallback_answer": "해당 카테고리 문서와 관련이 없습니다"
    }
}

# 역매핑: 문서 → 카테고리
DOCUMENT_TO_CATEGORY = {}
for category, definition in CATEGORY_DEFINITIONS.items():
    for doc in definition['required_documents']:
        DOCUMENT_TO_CATEGORY[doc] = category


def get_category_definition(category: str) -> dict:
    """카테고리 정의 조회"""
    if category not in CATEGORY_DEFINITIONS:
        raise ValueError(f"Unknown category: {category}")
    return CATEGORY_DEFINITIONS[category]


def get_required_concepts(category: str) -> list:
    """카테고리의 필수 개념 조회"""
    return CATEGORY_DEFINITIONS[category]['required_concepts']


def get_required_documents(category: str) -> list:
    """카테고리의 필수 문서 조회"""
    return CATEGORY_DEFINITIONS[category]['required_documents']


def is_out_of_scope_for_category(keyword: str, category: str) -> bool:
    """키워드가 카테고리 범위 외인지 확인"""
    out_of_scope = CATEGORY_DEFINITIONS[category]['out_of_scope']
    return any(
        kw.lower() in keyword.lower()
        for kw in out_of_scope
    )


def get_fallback_answer(category: str) -> str:
    """카테고리의 기본 답변 조회"""
    return CATEGORY_DEFINITIONS[category]['fallback_answer']
