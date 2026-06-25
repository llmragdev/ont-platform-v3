# Team0 검증 프로젝트 - 상세 실행 계획서

**문서명**: PLAN.md  
**버전**: 1.0  
**작성일**: 2026-06-07  
**상태**: 📋 준비 완료

---

## 📋 목차

1. [Phase별 상세 계획](#phase별-상세-계획)
2. [각 모듈별 개발 가이드](#각-모듈별-개발-가이드)
3. [테스트 전략](#테스트-전략)
4. [예상 문제 및 해결책](#예상-문제-및-해결책)
5. [성공 지표](#성공-지표)

---

## 🎯 Phase별 상세 계획

### Phase 1: 준비 단계 (Day 1, 2026-06-07)

#### 1.1 환경 설정 (1시간)

**목표**: 기본 설정 파일 작성

**작업**:
```bash
# 1. config.py 작성
- 경로 설정
  * BASE_DIR: E:\ai_lab_SIT\team0_validator
  * TARGET_DOC_DIR: E:\ai_lab_SIT\target_doc
  * RESULTS_DIR: results/
  
- API 설정
  * TEAM0_BASE_URL: http://localhost:8002
  * TEAM0_SEARCH_ENDPOINT: /api/v1/rag/search
  
- 모델 설정
  * GEMINI_EMBEDDING_DIM: 3072
  * CHUNK_SIZE: 512
  * TOP_K: 5
  
- 평가 기준
  * ACCURACY_THRESHOLD: 0.5
  * KEYWORD_THRESHOLD: 0.6
```

**산출물**:
- `config.py` (완성)

**체크리스트**:
- [ ] config.py 작성
- [ ] 모든 경로 확인
- [ ] 상수 정의 완료

---

#### 1.2 폴더 구조 생성 (15분)

**목표**: 프로젝트 디렉토리 구조 생성

```bash
mkdir -p loaders extractors builders evaluators clients results
touch loaders/__init__.py
touch extractors/__init__.py
touch builders/__init__.py
touch evaluators/__init__.py
touch clients/__init__.py
```

**체크리스트**:
- [ ] 모든 폴더 생성
- [ ] __init__.py 파일 생성

---

#### 1.3 테스트 쿼리셋 정의 (45분)

**목표**: 30개 표준 테스트 쿼리 정의

**쿼리 분류** (총 30개):

**카테고리 1: 온톨로지** (12개)
```python
[
    "온톨로지란 무엇인가?",
    "온톨로지와 지식그래프의 관계는?",
    "온톨로지 매칭이란 무엇인가?",
    "온톨로지 이질성 문제는?",
    "도메인 온톨로지 모델링 방법은?",
    "온톨로지 기반 의미 속성 판별이란?",
    "온톨로지 학습 기반 지식 그래프 구축 방법은?",
    "RDF는 무엇인가?",
    "온톨로지 관리 및 유지보수 방법은?",
    "온톨로지의 평가 지표는?",
    "온톨로지 재사용 전략은?",
    "온톨로지 국제 표준은?"
]
```

**카테고리 2: NLP & 생성형AI** (12개)
```python
[
    "자연어처리(NLP)란?",
    "정적 언어모델과 생성형AI의 차이는?",
    "생성형AI의 발전 과정은?",
    "텍스트를 다시 쓰는 기술(Paraphrasing)이란?",
    "한국근대문인 데이터베이스 구축 방법은?",
    "실시간 문맥 인식 감성 분석이란?",
    "감성 분석의 모듈형 아키텍처 설계란?",
    "NLP에서의 감정 판별 기법은?",
    "언어모델의 문맥 이해 방식은?",
    "대규모 언어모델의 학습 방식은?",
    "NLP의 주요 응용 분야는?",
    "자연어 이해와 생성의 차이는?"
]
```

**카테고리 3: 국방 & 지식통합** (6개)
```python
[
    "국방 분야에서 온톨로지를 어떻게 활용하는가?",
    "국방 지휘통제 데이터 통합 방법은?",
    "온톨로지와 지식그래프를 국방에 적용하는 방법은?",
    "해외 온톨로지 현황은?",
    "한국군 온톨로지 개발 방안은?",
    "지식그래프 기반 국방 정보 통합은?"
]
```

**산출물**:
- `test_queries.json` (30개 쿼리)

**체크리스트**:
- [ ] 온톨로지 카테고리 12개 정의
- [ ] NLP 카테고리 12개 정의
- [ ] 국방 카테고리 6개 정의
- [ ] test_queries.json 저장

---

#### 1.4 의존성 파일 작성 (15분)

**목표**: requirements.txt 작성

```
# requirements.txt
PyPDF2>=3.0
httpx>=0.24
numpy>=1.24
scikit-learn>=1.3
pandas>=2.0
python-dotenv>=1.0
tqdm>=4.65
```

**체크리스트**:
- [ ] requirements.txt 작성
- [ ] 모든 라이브러리 버전 확인

---

### Phase 2: 핵심 모듈 개발 (Day 2-3)

#### 2.1 PDF 로더 개발 (Day 2 오전, 2시간)

**목표**: 8개 PDF에서 텍스트 추출

**구현 파일**: `loaders/pdf_loader.py`

**클래스 구조**:
```python
class PDFLoader:
    def __init__(self, pdf_dir: Path):
        self.pdf_dir = pdf_dir
        self.documents = []
    
    def load_all_pdfs(self) -> List[Dict]:
        """모든 PDF 로드"""
        
    def _load_single_pdf(self, pdf_path: Path) -> Dict:
        """단일 PDF 처리"""
        
    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        
    def _extract_metadata(self, filename: str, text: str) -> Dict:
        """메타데이터 추출"""
        
    def save_documents(self, output_path: Path):
        """결과 저장"""
```

**주요 기능**:
- PDF 텍스트 추출 (PyPDF2)
- 텍스트 정제 (공백, 특수문자 제거)
- 메타데이터 자동 추출 (제목, 연도, 카테고리)
- JSON 저장

**예상 산출물**:
```json
{
    "id": "doc_001",
    "filename": "NLP - [03] 온톨로지이질성문제...",
    "num_pages": 15,
    "text": "온톨로지는...",
    "text_length": 45000,
    "metadata": {
        "category": "NLP",
        "title": "온톨로지이질성문제...",
        "year": 2024,
        "keywords": ["온톨로지", "매칭"]
    }
}
```

**테스트**:
```bash
python -c "
from loaders.pdf_loader import PDFLoader
from config import TARGET_DOC_DIR, RESULTS_DIR

loader = PDFLoader(TARGET_DOC_DIR)
docs = loader.load_all_pdfs()
assert len(docs) == 8
loader.save_documents(RESULTS_DIR / 'documents.json')
print('✅ PDF 로드 완료')
"
```

**체크리스트**:
- [ ] pdf_loader.py 작성
- [ ] 8개 PDF 모두 로드 성공
- [ ] documents.json 생성 (8개 항목)
- [ ] 각 문서 텍스트 길이 > 10,000 확인

---

#### 2.2 메타데이터 추출기 개발 (Day 2 오후, 1.5시간)

**목표**: 모든 문서의 메타데이터 체계적으로 추출

**구현 파일**: `extractors/metadata_extractor.py`

**클래스 구조**:
```python
class MetadataExtractor:
    def __init__(self, documents: List[Dict]):
        self.documents = documents
    
    def extract_all_metadata(self) -> Dict:
        """전체 메타데이터 추출"""
        
    def extract_keywords(self, text: str) -> List[str]:
        """키워드 추출 (정규표현식 기반)"""
        
    def extract_authors(self, text: str) -> List[str]:
        """저자 추출"""
        
    def classify_document_type(self, text: str) -> str:
        """문서 유형 분류"""
        
    def classify_category(self, filename: str, text: str) -> str:
        """카테고리 분류 (NLP, 국방 등)"""
```

**예상 산출물**:
```json
{
    "doc_001": {
        "title": "온톨로지이질성문제를해결하기위한온톨로지매칭방법",
        "category": "NLP",
        "document_type": "research_paper",
        "year": 2024,
        "keywords": ["온톨로지", "매칭", "이질성"],
        "authors": ["Author1", "Author2"],
        "pages": 15,
        "abstract_extracted": True
    }
}
```

**체크리스트**:
- [ ] metadata_extractor.py 작성
- [ ] 8개 문서 모두 메타데이터 추출
- [ ] 키워드 추출율 > 80%
- [ ] metadata_analysis.json 저장

---

#### 2.3 청크 분할기 개발 (Day 2 저녁, 1.5시간)

**목표**: 텍스트를 의미 있는 단위로 분할

**구현 파일**: `extractors/chunk_extractor.py`

**클래스 구조**:
```python
class ChunkExtractor:
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = chunk_size
    
    def split_into_chunks(self, text: str, doc_id: str) -> List[Dict]:
        """의미 단위 청크 분할"""
        
    def _find_sentence_boundaries(self, text: str) -> List[int]:
        """문장 경계 찾기"""
        
    def assign_chunk_metadata(self, chunks: List[Dict], doc_metadata: Dict) -> List[Dict]:
        """청크에 메타데이터 할당"""
        
    def merge_chunks(self, chunks: List[Dict], output_path: Path):
        """모든 청크 통합"""
```

**주요 기능**:
- 문장 경계 기반 분할 (overlap 고려)
- 청크 크기 관리 (512 토큰 목표)
- 메타데이터 상속

**예상 산출물**:
```json
{
    "id": "chunk_001",
    "doc_id": "doc_001",
    "text": "온톨로지는 지식 표현의 명시적 명세입니다...",
    "start_char": 0,
    "end_char": 512,
    "metadata": {
        "doc_title": "온톨로지이질성문제...",
        "category": "NLP",
        "keywords": ["온톨로지"]
    }
}
```

**예상**: 300-400개 청크 생성

**체크리스트**:
- [ ] chunk_extractor.py 작성
- [ ] 전체 청크 수 300+ 확인
- [ ] 평균 청크 크기 500±50 확인
- [ ] chunks.json 저장

---

#### 2.4 벡터 빌더 개발 (Day 3 오전, 2시간)

**목표**: Gemini Embedding으로 모든 청크 벡터화

**구현 파일**: `builders/vector_builder.py`

**클래스 구조**:
```python
class VectorBuilder:
    def __init__(self, embedding_url: str = "http://localhost:8011"):
        self.embedding_url = embedding_url
    
    async def vectorize_all_chunks(self, chunks: List[Dict]) -> Dict:
        """모든 청크 벡터화"""
        
    async def _call_embedding_api(self, text: str) -> List[float]:
        """Gemini Embedding API 호출"""
        
    def save_vector_db(self, vectors: Dict, output_path: Path):
        """벡터 DB 저장"""
        
    async def test_connection(self) -> bool:
        """연결 테스트"""
```

**주요 기능**:
- Gemini Embedding API 호출 (3072차원)
- 배치 처리 (병렬 요청)
- 에러 처리 및 재시도
- 진행률 표시

**예상 산출물**:
```json
{
    "vectors": [
        {
            "id": "chunk_001",
            "embedding": [0.123, 0.456, ...],  // 3072차원
            "text": "온톨로지는...",
            "metadata": {...}
        }
    ]
}
```

**예상 소요 시간**: 5-10분 (300-400개 청크)

**체크리스트**:
- [ ] vector_builder.py 작성
- [ ] LLM Gateway 연결 확인 (포트 8011)
- [ ] 모든 청크 벡터화 완료
- [ ] 3072차원 확인
- [ ] vectors.json 저장 (크기: ~50-100MB)

---

#### 2.5 온톨로지 빌더 개발 (Day 3 오후, 2.5시간)

**목표**: 문서 간 의미론적 관계 그래프 구축

**구현 파일**: `builders/ontology_builder.py`

**클래스 구조**:
```python
class OntologyBuilder:
    def __init__(self, vectors: Dict, metadata: Dict):
        self.vectors = vectors
        self.metadata = metadata
    
    def build_concept_graph(self) -> Dict:
        """개념 그래프 구축"""
        
    def extract_concepts(self) -> List[Dict]:
        """문서에서 핵심 개념 추출"""
        
    def find_document_relationships(self) -> List[Dict]:
        """문서 간 유사도 기반 관계 찾기"""
        
    def find_concept_relationships(self) -> List[Dict]:
        """개념 간 관계 찾기"""
        
    def build_full_ontology(self) -> Dict:
        """전체 온톨로지 구축"""
        
    def save_ontology(self, output_path: Path):
        """온톨로지 저장"""
```

**주요 기능**:
- 개념 추출 (메타데이터 + 텍스트 기반)
- 벡터 유사도 기반 관계 찾기 (threshold: 0.7)
- 그래프 구조화

**예상 산출물**:
```json
{
    "concepts": [
        {"id": "온톨로지", "type": "concept", "frequency": 45},
        {"id": "지식그래프", "type": "concept", "frequency": 32},
        {"id": "RDF", "type": "concept", "frequency": 28}
    ],
    "relationships": [
        {
            "from": "doc_001",
            "to": "doc_007",
            "type": "related_topic",
            "strength": 0.85,
            "shared_concepts": ["온톨로지", "지식"]
        }
    ],
    "concept_relationships": [
        {
            "from": "온톨로지",
            "to": "지식그래프",
            "type": "related",
            "strength": 0.88
        }
    ]
}
```

**예상**: 25+ 문서 관계, 40+ 개념, 50+ 개념 관계

**체크리스트**:
- [ ] ontology_builder.py 작성
- [ ] 개념 추출 > 30개
- [ ] 문서 관계 > 20개
- [ ] 개념 관계 > 40개
- [ ] ontology.json 저장

---

### Phase 3: Team0 테스트 & 평가 (Day 4)

#### 3.1 Team0 클라이언트 개발 (30분)

**구현 파일**: `clients/team0_client.py`

```python
class Team0Client:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def health_check(self) -> bool:
        """Team0 연결 확인"""
        
    async def search(self, query: str, top_k: int = 5) -> Dict:
        """단일 쿼리 검색"""
        
    async def batch_search(self, queries: List[str]) -> List[Dict]:
        """배치 검색"""
        
    async def close(self):
        """연결 종료"""
```

**체크리스트**:
- [ ] team0_client.py 작성
- [ ] 포트 8002 연결 확인
- [ ] 테스트 쿼리 1개 실행 성공

---

#### 3.2 정확도 평가기 개발 (1시간)

**구현 파일**: `evaluators/accuracy_evaluator.py`

```python
class AccuracyEvaluator:
    def evaluate_single_query(
        self,
        query: str,
        team0_answer: str,
        golden_keywords: List[str]
    ) -> Dict:
        """
        평가 항목:
        1. 키워드 포함율 (0-1.0)
        2. 답변 길이 (문자 수)
        3. 문장 수
        4. 종합 정확도 (0-1.0)
        """
        
    def evaluate_all_queries(self, results: List[Dict]) -> Dict:
        """30개 쿼리 모두 평가"""
        
    def calculate_statistics(self, scores: List[float]) -> Dict:
        """통계 계산 (평균, 분산 등)"""
```

**평가 기준**:
```python
score = (
    keyword_presence_ratio * 0.4 +  # 40%: 필수 키워드 포함
    answer_completeness * 0.3 +     # 30%: 답변 완성도
    answer_relevance * 0.3          # 30%: 관련성
)
```

**체크리스트**:
- [ ] accuracy_evaluator.py 작성
- [ ] 평가 기준 정의 완료
- [ ] 샘플 쿼리 1개 평가 테스트

---

#### 3.3 성능 평가기 개발 (30분)

**구현 파일**: `evaluators/performance_evaluator.py`

```python
class PerformanceEvaluator:
    def analyze_response_time(self, results: List[Dict]) -> Dict:
        """
        측정:
        - 평균 응답시간
        - 최소/최대
        - P50, P95, P99
        """
        
    def analyze_success_rate(self, results: List[Dict]) -> Dict:
        """성공률 분석"""
        
    def analyze_answer_quality(self, results: List[Dict]) -> Dict:
        """답변 품질 분석"""
```

**체크리스트**:
- [ ] performance_evaluator.py 작성
- [ ] 성능 지표 정의 완료

---

#### 3.4 30개 쿼리 실행 (2-3시간)

**실행 스크립트**:
```python
# test_suite.py의 일부
async def run_team0_tests():
    client = Team0Client()
    
    # 건강 확인
    assert await client.health_check()
    
    # 30개 쿼리 실행
    results = await client.batch_search(test_queries)
    
    # 결과 저장
    save_results(results, "test_results.json")
```

**예상 소요 시간**:
- 30개 쿼리 × ~5-10초/쿼리 = 2.5-5분
- 총 3시간 (대기 및 저장 포함)

**체크리스트**:
- [ ] 30개 쿼리 모두 실행
- [ ] 성공률 100%
- [ ] test_results.json 저장

---

### Phase 4: 평가 & 분석 (Day 4-5)

#### 4.1 정확도 분석 (1시간)

```python
accuracy_evaluator = AccuracyEvaluator()
accuracy_report = accuracy_evaluator.evaluate_all_queries(results)

# 산출물
{
    "overall_accuracy": 0.5854,  # 58.54%
    "by_category": {
        "ontology": 0.65,
        "nlp": 0.58,
        "defense": 0.52
    },
    "by_query": [...]
}
```

**체크리스트**:
- [ ] 정확도 분석 완료
- [ ] accuracy_report.json 저장

---

#### 4.2 성능 분석 (30분)

```python
perf_evaluator = PerformanceEvaluator()
perf_report = perf_evaluator.analyze_response_time(results)

# 산출물
{
    "avg_response_time_ms": 500,
    "p95_response_time_ms": 600,
    "p99_response_time_ms": 800,
    "success_rate": 1.0
}
```

**체크리스트**:
- [ ] 성능 분석 완료
- [ ] performance_report.json 저장

---

#### 4.3 메타데이터 분석 (30분)

```python
# evaluators/metadata_analyzer.py
metadata_analysis = MetadataAnalyzer().analyze_potential(
    metadata,
    results
)

# 산출물
{
    "extractable_fields": ["title", "year", "keywords", "author"],
    "extraction_rate": 1.0,
    "potential_improvement": 0.10,
    "estimated_accuracy": 0.6854  # 58.54% + 10%
}
```

**체크리스트**:
- [ ] 메타데이터 분석 완료
- [ ] metadata_analysis.json 저장

---

#### 4.4 온톨로지 분석 (30분)

```python
# evaluators/ontology_analyzer.py
ontology_analysis = OntologyAnalyzer().analyze_potential(
    ontology,
    results
)

# 산출물
{
    "relationships_found": 25,
    "concept_clusters": 4,
    "potential_improvement": 0.15,
    "estimated_accuracy": 0.8354  # 58.54% + 10% + 15%
}
```

**체크리스트**:
- [ ] 온톨로지 분석 완료
- [ ] ontology_analysis.json 저장

---

### Phase 5: 최종 보고서 생성 (Day 5)

#### 5.1 데이터 통합 및 분석 (1시간)

```python
# 모든 결과 통합
final_data = {
    "baseline": accuracy_report,
    "performance": perf_report,
    "metadata_analysis": metadata_analysis,
    "ontology_analysis": ontology_analysis,
    "raw_results": results
}
```

#### 5.2 마크다운 리포트 생성 (1시간)

**파일**: `results/validation_report.md`

**구조**:
```markdown
# Team0 RAG 검증 보고서

## Executive Summary
- 테스트 규모: 8개 PDF, 30개 쿼리
- 현재 정확도: 58.54%
- 개선 기회: +30% (메타데이터 +10%, 온톨로지 +15%, 하이브리드 +5%)
- 추정 최대 정확도: 88%

## 1. 테스트 개요
[테스트 설정, 환경 등]

## 2. Baseline 결과
[정확도, 응답시간, 성공률]

## 3. 카테고리별 분석
[온톨로지, NLP, 국방별 성능]

## 4. 메타데이터 활용 분석
[메타데이터로 얻을 수 있는 개선]

## 5. 온톨로지 활용 분석
[온톨로지 그래프로 얻을 수 있는 개선]

## 6. 종합 평가
[최종 권고사항]
```

**체크리스트**:
- [ ] validation_report.md 작성
- [ ] 모든 섹션 완성
- [ ] 표, 그래프 포함

---

#### 5.3 JSON 상세 결과 저장 (30분)

**파일**: `results/detailed_results.json`

```json
{
    "metadata": {
        "test_date": "2026-06-07",
        "pdf_count": 8,
        "query_count": 30,
        "chunk_count": 350
    },
    "results": {
        "baseline_accuracy": 0.5854,
        "performance": {...},
        "by_category": {...},
        "by_query": [...]
    },
    "analysis": {
        "metadata_potential": {...},
        "ontology_potential": {...}
    }
}
```

**체크리스트**:
- [ ] detailed_results.json 작성
- [ ] 모든 데이터 포함
- [ ] 형식 검증

---

## 🧪 테스트 전략

### 단위 테스트

#### 1. PDF 로더 테스트
```bash
python -m pytest tests/test_pdf_loader.py -v
```

**테스트 항목**:
- ✓ PDF 파일 로드 성공
- ✓ 텍스트 추출 완료
- ✓ 메타데이터 추출 완료

---

#### 2. 메타데이터 추출 테스트
```bash
python -m pytest tests/test_metadata_extractor.py -v
```

**테스트 항목**:
- ✓ 키워드 추출율 > 80%
- ✓ 카테고리 분류 정확도 > 90%

---

#### 3. 청크 분할 테스트
```bash
python -m pytest tests/test_chunk_extractor.py -v
```

**테스트 항목**:
- ✓ 청크 수 > 300
- ✓ 평균 청크 크기 500±50

---

#### 4. 벡터화 테스트
```bash
python -m pytest tests/test_vector_builder.py -v
```

**테스트 항목**:
- ✓ API 연결 성공
- ✓ 벡터 차원 = 3072
- ✓ 벡터 수 = 청크 수

---

#### 5. Team0 클라이언트 테스트
```bash
python -m pytest tests/test_team0_client.py -v
```

**테스트 항목**:
- ✓ 포트 8002 연결 성공
- ✓ 테스트 쿼리 1개 응답 수신
- ✓ 응답 형식 검증

---

### 통합 테스트

#### 전체 파이프라인 테스트
```bash
python test_suite.py --dry-run
```

**테스트 단계**:
1. PDF 로드 → ✓
2. 메타데이터 추출 → ✓
3. 청크 분할 → ✓
4. 벡터화 → ✓
5. 온톨로지 구축 → ✓
6. Team0 쿼리 → ✓
7. 평가 → ✓

---

## ⚠️ 예상 문제 및 해결책

### 문제 1: Team0 서버 연결 실패

**증상**: `Connection refused on port 8002`

**원인**: Team0 서버가 실행 중이 아님

**해결책**:
```bash
# 1. Team0 서버 확인
ps aux | grep "port 8002"

# 2. Team0 서버 시작
cd E:\ai_lab_SIT\team0_rag_source
python app/main.py --port 8002

# 3. 연결 테스트
curl http://localhost:8002/api/health
```

---

### 문제 2: Gemini Embedding API 연결 실패

**증상**: `Connection refused on port 8011`

**원인**: LLM Gateway가 실행 중이 아님

**해결책**:
```bash
# LLM Gateway 시작
cd E:\ai_lab_SIT\team0_rag_source/llm_gateway
uvicorn app.main:app --port 8011
```

---

### 문제 3: 메모리 부족

**증상**: `MemoryError` 벡터화 중

**원인**: 3072차원 벡터 × 350개 청크 = 용량 큼

**해결책**:
- 청크 수 줄이기
- 배치 처리 크기 조정
- 메모리 증가 (가능하면)

---

### 문제 4: PDF 텍스트 추출 실패

**증상**: 일부 PDF에서 텍스트 추출 안 됨

**원인**: 스캔된 이미지 PDF (OCR 필요)

**해결책**:
- 해당 PDF 스킵 (count 줄이기)
- OCR 라이브러리 추가 (tesseract)

---

### 문제 5: Team0 응답 시간 초과

**증상**: 일부 쿼리 응답 없음 (timeout)

**원인**: Team0 서버 부하 높음

**해결책**:
- 쿼리 간 대기 시간 증가
- 타임아웃 값 조정 (기본 30초)
- 배치 크기 줄이기

---

## ✅ 성공 지표

### 최소 성공 조건

| 항목 | 기준 | 상태 |
|------|------|------|
| **PDF 로드** | 8개 모두 로드 | 필수 |
| **메타데이터** | 추출율 > 80% | 필수 |
| **청크 분할** | 청크 수 > 300 | 필수 |
| **벡터화** | 모든 청크 벡터화 | 필수 |
| **온톨로지** | 관계 > 20개 | 필수 |
| **Team0 테스트** | 30개 쿼리 모두 응답 | 필수 |
| **보고서** | Markdown 생성 | 필수 |

### 성능 목표

| 항목 | 목표 | 현재 예상 |
|------|-----|---------|
| 정확도 기준값 | 58.54% | ✓ 확인 |
| 메타데이터 개선 | +10% | 예상 |
| 온톨로지 개선 | +15% | 예상 |
| 하이브리드 개선 | +5% | 예상 |

---

## 📝 일일 진행 상황 기록

**Day 1 (2026-06-07)**
- [ ] 09:00-10:00: config.py 작성
- [ ] 10:00-10:15: 폴더 구조 생성
- [ ] 10:15-11:00: 테스트 쿼리 정의
- [ ] 11:00-11:15: requirements.txt 작성

**Day 2 (2026-06-08)**
- [ ] 09:00-11:00: PDF 로더 개발 & 테스트
- [ ] 11:00-12:30: 메타데이터 추출기 개발
- [ ] 13:30-15:00: 청크 분할기 개발

**Day 3 (2026-06-09)**
- [ ] 09:00-11:00: 벡터 빌더 개발 & 벡터화
- [ ] 11:00-13:30: 온톨로지 빌더 개발
- [ ] 14:00-15:00: 통합 테스트

**Day 4 (2026-06-10)**
- [ ] 09:00-10:00: Team0 클라이언트 개발
- [ ] 10:00-11:00: 정확도 평가기 개발
- [ ] 11:00-15:00: 30개 쿼리 실행 & 평가

**Day 5 (2026-06-11)**
- [ ] 09:00-10:00: 데이터 분석
- [ ] 10:00-12:00: 최종 보고서 작성
- [ ] 12:00-15:00: 검수 및 최종화

---

## 🎯 마일스톤

| 마일스톤 | 날짜 | 산출물 |
|---------|------|--------|
| **MP1** | 2026-06-07 | config.py, test_queries.json |
| **MP2** | 2026-06-08 | documents.json, chunks.json |
| **MP3** | 2026-06-09 | vectors.json, ontology.json |
| **MP4** | 2026-06-10 | test_results.json |
| **MP5** | 2026-06-11 | validation_report.md ✅ |

---

**문서 버전**: 1.0  
**마지막 수정**: 2026-06-07  
**상태**: 📋 실행 준비 완료
