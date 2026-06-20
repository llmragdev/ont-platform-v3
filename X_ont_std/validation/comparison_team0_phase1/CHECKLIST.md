# Team0 검증 프로젝트 - 실행 체크리스트

**문서명**: CHECKLIST.md  
**버전**: 1.0  
**작성일**: 2026-06-07

---

## 📋 사전 준비 (실행 전)

### 환경 확인
- [ ] Python 3.8+ 설치 확인
- [ ] Team0 서버 포트 8002 확인 가능
- [ ] LLM Gateway 포트 8011 확인 가능
- [ ] 인터넷 연결 확인 (Gemini API)

### 폴더 구조 확인
- [ ] E:\ai_lab_SIT 폴더 존재
- [ ] E:\ai_lab_SIT\target_doc 폴더 존재
- [ ] 8개 PDF 파일 확인
- [ ] E:\ai_lab_SIT\team0_validator 폴더 생성 (이미 됨)

### 문서 확인
- [ ] README.md 읽음
- [ ] PLAN.md 읽음
- [ ] 이 체크리스트 읽음

---

## 🛠️ Day 1: 준비 단계 (2026-06-07)

### 1.1 환경 설정

**목표**: config.py 작성 (30분)

**작업**:
```bash
cd E:\ai_lab_SIT\team0_validator
# config.py 작성
```

**체크리스트**:
- [ ] config.py 파일 생성
- [ ] BASE_DIR 설정 확인
- [ ] TARGET_DOC_DIR 설정 확인 (= E:\ai_lab_SIT\target_doc)
- [ ] TEAM0_BASE_URL 설정 확인 (= http://localhost:8002)
- [ ] RESULTS_DIR 설정 확인

**완료 기준**: config.py 파일 생성, Python import 가능

---

### 1.2 폴더 구조 생성

**목표**: 디렉토리 생성 (15분)

```bash
mkdir loaders extractors builders evaluators clients results
touch loaders/__init__.py
touch extractors/__init__.py
touch builders/__init__.py
touch evaluators/__init__.py
touch clients/__init__.py
```

**체크리스트**:
- [ ] loaders 폴더 생성
- [ ] extractors 폴더 생성
- [ ] builders 폴더 생성
- [ ] evaluators 폴더 생성
- [ ] clients 폴더 생성
- [ ] results 폴더 생성
- [ ] 모든 __init__.py 파일 생성

**완료 기준**: 모든 폴더 및 파일 존재 확인

---

### 1.3 테스트 쿼리셋 정의

**목표**: test_queries.json 작성 (45분)

**파일**: `test_queries.json`

**구조**:
```json
{
    "ontology": [12개 쿼리],
    "nlp": [12개 쿼리],
    "defense": [6개 쿼리]
}
```

**체크리스트**:
- [ ] test_queries.json 파일 생성
- [ ] 온톨로지 카테고리: 12개 쿼리 추가
- [ ] NLP 카테고리: 12개 쿼리 추가
- [ ] 국방 카테고리: 6개 쿼리 추가
- [ ] JSON 형식 검증

**완료 기준**: 총 30개 쿼리, JSON 형식 정상

---

### 1.4 의존성 파일 작성

**목표**: requirements.txt 작성 (15분)

**파일**: `requirements.txt`

**내용**:
```
PyPDF2>=3.0
httpx>=0.24
numpy>=1.24
scikit-learn>=1.3
pandas>=2.0
python-dotenv>=1.0
tqdm>=4.65
```

**체크리스트**:
- [ ] requirements.txt 파일 생성
- [ ] 모든 라이브러리 나열
- [ ] 버전 명시

**완료 기준**: requirements.txt 파일 생성, pip install 테스트 성공

---

### Day 1 최종 확인

**산출물**:
- [ ] config.py (설정)
- [ ] loaders/, extractors/, builders/, evaluators/, clients/, results/ (폴더)
- [ ] test_queries.json (30개 쿼리)
- [ ] requirements.txt (의존성)
- [ ] __init__.py (모듈 초기화)

**시간**: 2시간 (9:00 ~ 11:00)

---

## 🔧 Day 2: 핵심 모듈 개발 1 (2026-06-08)

### 2.1 PDF 로더 개발

**파일**: `loaders/pdf_loader.py`

**체크리스트**:
- [ ] PDFLoader 클래스 작성
- [ ] load_all_pdfs() 메서드 구현
- [ ] _load_single_pdf() 메서드 구현
- [ ] _clean_text() 메서드 구현
- [ ] _extract_metadata() 메서드 구현
- [ ] save_documents() 메서드 구현

**테스트**:
```bash
python -c "
from loaders.pdf_loader import PDFLoader
from config import TARGET_DOC_DIR, RESULTS_DIR
loader = PDFLoader(TARGET_DOC_DIR)
docs = loader.load_all_pdfs()
print(f'Loaded {len(docs)} documents')
assert len(docs) == 8
"
```

**체크리스트**:
- [ ] 8개 PDF 모두 로드 성공
- [ ] 각 문서 텍스트 길이 > 10,000
- [ ] documents_metadata.json 생성

**완료 기준**: 8개 PDF 로드, documents_metadata.json 생성

---

### 2.2 메타데이터 추출기 개발

**파일**: `extractors/metadata_extractor.py`

**체크리스트**:
- [ ] MetadataExtractor 클래스 작성
- [ ] extract_all_metadata() 메서드 구현
- [ ] extract_keywords() 메서드 구현
- [ ] extract_authors() 메서드 구현
- [ ] classify_document_type() 메서드 구현
- [ ] classify_category() 메서드 구현

**테스트**:
```bash
python -c "
from extractors.metadata_extractor import MetadataExtractor
from loaders.pdf_loader import PDFLoader
from config import TARGET_DOC_DIR
loader = PDFLoader(TARGET_DOC_DIR)
docs = loader.load_all_pdfs()
extractor = MetadataExtractor(docs)
metadata = extractor.extract_all_metadata()
print(f'Extracted metadata for {len(metadata)} documents')
"
```

**체크리스트**:
- [ ] 8개 문서 메타데이터 추출
- [ ] 키워드 추출율 > 80%
- [ ] metadata_analysis.json 생성

**완료 기준**: metadata_analysis.json 생성, 8개 항목 완성

---

### 2.3 청크 분할기 개발

**파일**: `extractors/chunk_extractor.py`

**체크리스트**:
- [ ] ChunkExtractor 클래스 작성
- [ ] split_into_chunks() 메서드 구현
- [ ] _find_sentence_boundaries() 메서드 구현
- [ ] assign_chunk_metadata() 메서드 구현
- [ ] merge_chunks() 메서드 구현

**테스트**:
```bash
python -c "
from extractors.chunk_extractor import ChunkExtractor
from loaders.pdf_loader import PDFLoader
from config import TARGET_DOC_DIR
loader = PDFLoader(TARGET_DOC_DIR)
docs = loader.load_all_pdfs()
extractor = ChunkExtractor()
chunks = []
for doc in docs:
    chunks.extend(extractor.split_into_chunks(doc['text'], doc['id']))
print(f'Created {len(chunks)} chunks')
assert len(chunks) > 300
"
```

**체크리스트**:
- [ ] 청크 수 300+ 생성
- [ ] 평균 청크 크기 500±50
- [ ] chunks.json 생성

**완료 기준**: chunks.json 생성, 300+ 청크 확인

---

### Day 2 최종 확인

**산출물**:
- [ ] loaders/pdf_loader.py
- [ ] extractors/metadata_extractor.py
- [ ] extractors/chunk_extractor.py
- [ ] documents_metadata.json
- [ ] metadata_analysis.json
- [ ] chunks.json

**시간**: 4.5시간 (9:00 ~ 13:30)

---

## ⚙️ Day 3: 핵심 모듈 개발 2 (2026-06-09)

### 3.1 벡터 빌더 개발

**파일**: `builders/vector_builder.py`

**체크리스트**:
- [ ] VectorBuilder 클래스 작성
- [ ] vectorize_all_chunks() 메서드 구현
- [ ] _call_embedding_api() 메서드 구현
- [ ] save_vector_db() 메서드 구현
- [ ] test_connection() 메서드 구현

**사전 확인**:
- [ ] LLM Gateway가 포트 8011에서 실행 중
- [ ] Gemini API 접근 가능

**테스트**:
```bash
# 먼저 LLM Gateway 시작
cd E:\ai_lab_SIT\team0_rag_source\llm_gateway
uvicorn app.main:app --port 8011

# 다른 터미널에서
python -c "
from builders.vector_builder import VectorBuilder
from config import RESULTS_DIR
import json
with open(RESULTS_DIR / 'chunks.json') as f:
    chunks = json.load(f)
builder = VectorBuilder()
vectors = asyncio.run(builder.vectorize_all_chunks(chunks))
print(f'Vectorized {len(vectors)} chunks')
"
```

**체크리스트**:
- [ ] 모든 청크 벡터화
- [ ] 벡터 차원 = 3072
- [ ] vectors.json 생성 (크기: 50-100MB)

**완료 기준**: vectors.json 생성, 3072차원 확인

**예상 소요 시간**: 5-10분 (벡터화) + 30분 (개발/테스트)

---

### 3.2 온톨로지 빌더 개발

**파일**: `builders/ontology_builder.py`

**체크리스트**:
- [ ] OntologyBuilder 클래스 작성
- [ ] build_concept_graph() 메서드 구현
- [ ] extract_concepts() 메서드 구현
- [ ] find_document_relationships() 메서드 구현
- [ ] find_concept_relationships() 메서드 구현
- [ ] build_full_ontology() 메서드 구현
- [ ] save_ontology() 메서드 구현

**테스트**:
```bash
python -c "
from builders.ontology_builder import OntologyBuilder
from config import RESULTS_DIR
import json
with open(RESULTS_DIR / 'vectors.json') as f:
    vectors = json.load(f)
with open(RESULTS_DIR / 'metadata_analysis.json') as f:
    metadata = json.load(f)
builder = OntologyBuilder(vectors, metadata)
ontology = builder.build_full_ontology()
print(f'Built ontology with {len(ontology[\"concepts\"])} concepts')
print(f'Found {len(ontology[\"relationships\"])} document relationships')
"
```

**체크리스트**:
- [ ] 개념 수 30+
- [ ] 문서 관계 수 20+
- [ ] 개념 관계 수 40+
- [ ] ontology.json 생성

**완료 기준**: ontology.json 생성, 관계 20+ 확인

**예상 소요 시간**: 30분 (개발/테스트)

---

### 3.3 통합 테스트

**목표**: 전체 파이프라인 테스트

**스크립트**:
```bash
python -c "
from loaders.pdf_loader import PDFLoader
from extractors.metadata_extractor import MetadataExtractor
from extractors.chunk_extractor import ChunkExtractor
from builders.vector_builder import VectorBuilder
from builders.ontology_builder import OntologyBuilder
from config import TARGET_DOC_DIR, RESULTS_DIR

# 1. PDF 로드
loader = PDFLoader(TARGET_DOC_DIR)
docs = loader.load_all_pdfs()
print(f'✓ Loaded {len(docs)} documents')

# 2. 메타데이터 추출
metadata = MetadataExtractor(docs).extract_all_metadata()
print(f'✓ Extracted metadata')

# 3. 청크 분할
extractor = ChunkExtractor()
chunks = []
for doc in docs:
    chunks.extend(extractor.split_into_chunks(doc['text'], doc['id']))
print(f'✓ Created {len(chunks)} chunks')

# 4. 벡터화
# vectors = await VectorBuilder().vectorize_all_chunks(chunks)
# print(f'✓ Vectorized {len(vectors)} chunks')

# 5. 온톨로지
# ontology = OntologyBuilder(vectors, metadata).build_full_ontology()
# print(f'✓ Built ontology')
"
```

**체크리스트**:
- [ ] 단계 1 통과: PDF 로드
- [ ] 단계 2 통과: 메타데이터 추출
- [ ] 단계 3 통과: 청크 분할
- [ ] 단계 4 통과: 벡터화 (LLM Gateway 필요)
- [ ] 단계 5 통과: 온톨로지 구축

**완료 기준**: 모든 단계 통과, 오류 없음

---

### Day 3 최종 확인

**산출물**:
- [ ] builders/vector_builder.py
- [ ] builders/ontology_builder.py
- [ ] vectors.json (3072D, 350+ 청크)
- [ ] ontology.json (30+ 개념, 20+ 관계)

**시간**: 4시간 (9:00 ~ 13:00)

---

## 🧪 Day 4: Team0 테스트 & 평가 (2026-06-10)

### 4.1 Team0 클라이언트 개발

**파일**: `clients/team0_client.py`

**체크리스트**:
- [ ] Team0Client 클래스 작성
- [ ] __init__() 메서드 구현
- [ ] health_check() 메서드 구현
- [ ] search() 메서드 구현
- [ ] batch_search() 메서드 구현
- [ ] close() 메서드 구현

**테스트**:
```bash
# 먼저 Team0 서버 시작
cd E:\ai_lab_SIT\team0_rag_source
python app/main.py --port 8002

# 다른 터미널에서
python -c "
from clients.team0_client import Team0Client
import asyncio

async def test():
    client = Team0Client()
    health = await client.health_check()
    print(f'Team0 health: {health}')
    result = await client.search('온톨로지란?')
    print(f'Result: {result}')
    await client.close()

asyncio.run(test())
"
```

**체크리스트**:
- [ ] 포트 8002 연결 성공
- [ ] health_check() 통과
- [ ] 테스트 쿼리 1개 응답 받음
- [ ] 응답 형식 검증

**완료 기준**: Team0와 통신 가능 확인

---

### 4.2 평가기 개발

**파일들**:
- `evaluators/accuracy_evaluator.py`
- `evaluators/performance_evaluator.py`
- `evaluators/metadata_analyzer.py`
- `evaluators/ontology_analyzer.py`

**체크리스트** (각각):
- [ ] Evaluator 클래스 작성
- [ ] 주요 메서드 구현
- [ ] 평가 기준 정의
- [ ] 통계 계산 기능

**완료 기준**: 모든 평가기 작성 완료

---

### 4.3 30개 쿼리 실행

**파일**: `test_suite.py` (메인 프로그램)

**체크리스트**:
- [ ] test_suite.py 작성
- [ ] load_test_queries() 구현
- [ ] run_team0_tests() 구현
- [ ] save_results() 구현

**실행**:
```bash
# Team0 서버 확인
curl http://localhost:8002/api/health

# 쿼리 실행
python test_suite.py --queries 30 --output test_results.json
```

**체크리스트**:
- [ ] 30개 쿼리 모두 실행 (예상: 2.5-5분)
- [ ] 성공률 100%
- [ ] test_results.json 생성 (100+MB)
- [ ] 응답 시간 기록

**완료 기준**: test_results.json 생성, 30개 응답 모두 수집

---

### 4.4 평가 실행

**프로세스**:
```bash
python -c "
import json
from evaluators.accuracy_evaluator import AccuracyEvaluator
from evaluators.performance_evaluator import PerformanceEvaluator
from evaluators.metadata_analyzer import MetadataAnalyzer
from evaluators.ontology_analyzer import OntologyAnalyzer

# 결과 로드
with open('test_results.json') as f:
    results = json.load(f)

# 평가 실행
acc_report = AccuracyEvaluator().evaluate_all(results)
perf_report = PerformanceEvaluator().analyze(results)
meta_analysis = MetadataAnalyzer().analyze_potential()
onto_analysis = OntologyAnalyzer().analyze_potential()

# 저장
with open('accuracy_report.json', 'w') as f:
    json.dump(acc_report, f)
with open('performance_report.json', 'w') as f:
    json.dump(perf_report, f)
# ... 나머지 저장
"
```

**체크리스트**:
- [ ] accuracy_report.json 생성
- [ ] performance_report.json 생성
- [ ] metadata_analysis.json 생성
- [ ] ontology_analysis.json 생성

**완료 기준**: 모든 평가 리포트 생성

---

### Day 4 최종 확인

**산출물**:
- [ ] clients/team0_client.py
- [ ] evaluators/accuracy_evaluator.py
- [ ] evaluators/performance_evaluator.py
- [ ] evaluators/metadata_analyzer.py
- [ ] evaluators/ontology_analyzer.py
- [ ] test_suite.py
- [ ] test_results.json
- [ ] accuracy_report.json
- [ ] performance_report.json
- [ ] metadata_analysis.json
- [ ] ontology_analysis.json

**시간**: 6-8시간 (9:00 ~ 17:00)

---

## 📊 Day 5: 최종 보고서 (2026-06-11)

### 5.1 데이터 통합 & 분석

**목표**: 모든 데이터 통합 및 분석

**체크리스트**:
- [ ] 모든 리포트 파일 확인
- [ ] 정확도 통계 확인 (58.54% 예상)
- [ ] 성능 통계 확인 (응답시간, P95 등)
- [ ] 메타데이터 분석 확인
- [ ] 온톨로지 분석 확인

---

### 5.2 마크다운 리포트 생성

**파일**: `results/validation_report.md`

**체크리스트**:
- [ ] Executive Summary 섹션 작성
- [ ] Test Overview 섹션 작성
- [ ] Baseline Results 섹션 작성
- [ ] Category Analysis 섹션 작성
- [ ] Metadata Analysis 섹션 작성
- [ ] Ontology Analysis 섹션 작성
- [ ] Comprehensive Assessment 섹션 작성
- [ ] Recommendations 섹션 작성

**형식**:
- [ ] 마크다운 문법 정확
- [ ] 표 포함
- [ ] 모든 수치 포함
- [ ] 그래프/차트 참조 (선택)

**완료 기준**: validation_report.md 생성, 모든 섹션 완성

---

### 5.3 JSON 상세 결과 저장

**파일**: `results/detailed_results.json`

**구조**:
```json
{
    "metadata": {...},
    "baseline_accuracy": 0.5854,
    "performance": {...},
    "analysis": {...},
    "by_category": {...},
    "by_query": [...]
}
```

**체크리스트**:
- [ ] detailed_results.json 생성
- [ ] 모든 데이터 포함
- [ ] JSON 형식 검증

---

### 5.4 최종 검수

**체크리스트**:
- [ ] README.md 최신화 (필요시)
- [ ] validation_report.md 검수
- [ ] detailed_results.json 검수
- [ ] 모든 산출물 목록화

---

### Day 5 최종 확인

**산출물**:
- [ ] results/validation_report.md (공개용)
- [ ] results/detailed_results.json (상세 데이터)
- [ ] results/summary.txt (요약)

**시간**: 4시간 (9:00 ~ 13:00)

---

## ✅ 최종 산출물 목록

### 필수 산출물

| # | 파일명 | 설명 | 크기 |
|---|--------|------|------|
| 1 | config.py | 프로젝트 설정 | ~2KB |
| 2 | loaders/pdf_loader.py | PDF 로더 | ~3KB |
| 3 | extractors/metadata_extractor.py | 메타데이터 추출기 | ~3KB |
| 4 | extractors/chunk_extractor.py | 청크 분할기 | ~3KB |
| 5 | builders/vector_builder.py | 벡터 빌더 | ~4KB |
| 6 | builders/ontology_builder.py | 온톨로지 빌더 | ~5KB |
| 7 | clients/team0_client.py | Team0 클라이언트 | ~2KB |
| 8 | evaluators/*.py | 평가기들 (4개) | ~8KB |
| 9 | test_suite.py | 메인 테스트 프로그램 | ~5KB |
| 10 | results/validation_report.md | 최종 보고서 (공개용) | ~30KB |
| 11 | results/detailed_results.json | 상세 데이터 | ~50KB |
| 12 | requirements.txt | 의존성 파일 | ~500B |

### 생성 데이터

| # | 파일명 | 설명 | 크기 |
|---|--------|------|------|
| 1 | test_queries.json | 30개 테스트 쿼리 | ~5KB |
| 2 | documents_metadata.json | 문서 메타데이터 | ~10KB |
| 3 | chunks.json | 분할된 청크 (~350개) | ~500KB |
| 4 | vectors.json | 벡터 DB (3072차원) | ~100MB |
| 5 | ontology.json | 온톨로지 그래프 | ~50KB |
| 6 | test_results.json | Team0 테스트 결과 | ~100KB |
| 7 | accuracy_report.json | 정확도 분석 | ~50KB |
| 8 | performance_report.json | 성능 분석 | ~20KB |
| 9 | metadata_analysis.json | 메타데이터 분석 | ~10KB |
| 10 | ontology_analysis.json | 온톨로지 분석 | ~10KB |

---

## 🎯 전체 일정

| Day | 날짜 | Phase | 소요시간 | 누적시간 |
|-----|------|-------|---------|---------|
| 1 | 06-07 | 준비 | 2시간 | 2시간 |
| 2 | 06-08 | 개발1 | 4.5시간 | 6.5시간 |
| 3 | 06-09 | 개발2 | 4시간 | 10.5시간 |
| 4 | 06-10 | 테스트 | 6-8시간 | 16.5-18.5시간 |
| 5 | 06-11 | 보고서 | 4시간 | 20.5-22.5시간 |

**총 소요 시간**: 20.5-22.5시간 (5일, 일일 4-5시간)

---

## ✨ 성공 조건 확인표

### 최소 성공 조건

- [ ] **정확도 측정**: Team0 기준값 58.54% 확인
- [ ] **성능 측정**: 응답시간, P95, P99 측정
- [ ] **메타데이터 분석**: +10% 개선 가능성 입증
- [ ] **온톨로지 분석**: +15% 개선 가능성 입증
- [ ] **최종 보고서**: Markdown 형식으로 생성
- [ ] **공개 가능**: Team0 소스 포함 안 함

### 성능 목표

- [ ] **정확도**: 58.54% 기준값 재확인
- [ ] **응답시간**: 평균 500ms, P95 600ms, P99 800ms
- [ ] **메모리**: 벡터 DB < 100MB
- [ ] **청크**: 300+ 개 생성
- [ ] **온톨로지**: 20+ 문서 관계 발견

---

## 🚀 준비 완료!

**모든 준비가 완료되었습니다.**

다음 명령어로 시작하세요:

```bash
cd E:\ai_lab_SIT\team0_validator
pip install -r requirements.txt
python test_suite.py
```

**행운을 빕니다! 💪**

---

**문서 버전**: 1.0  
**마지막 수정**: 2026-06-07  
**상태**: 📋 실행 준비 완료 ✅
