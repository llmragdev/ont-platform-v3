# Team0 RAG 검증 프로젝트 (team0_validator)

**프로젝트명**: Team0 검증 프레임워크  
**버전**: 1.0  
**작성일**: 2026-06-07  
**상태**: 📋 계획 수립 완료

---

## 📌 프로젝트 개요

### 목표

**Team0 RAG의 성능을 객관적으로 검증하고 개선 기회를 도출하기**

- Team0는 **수정하지 않음** (원본 상태 유지)
- 별도의 **검증 프로그램** 작성
- **Ontology 기술**을 활용한 고급 분석
- 공개 가능한 **검증 결과** 리포트 생성

### 배경

| 항목 | 내용 |
|------|------|
| **Team0 정확도** | 58.54% (현재) |
| **대상 문서** | 8개 PDF (온톨로지, NLP, 국방) |
| **테스트 쿼리** | 24-30개 표준 질문 |
| **개선 목표** | 메타데이터 + 온톨로지 기술 적용시 80%+ 달성 가능성 검증 |

---

## 🎯 검증 프로그램 아키텍처

### 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    8개 PDF 입력                              │
│  (온톨로지, NLP, 국방 관련 학술 논문)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  Step 1: PDF 로드      │
         │  - 텍스트 추출         │
         │  - 메타데이터 자동 인식 │
         └───────────┬───────────┘
                     │
         ┌───────────▼──────────────┐
         │  Step 2: 전처리          │
         │  - 메타데이터 추출       │
         │  - 청크 분할 (의미 단위) │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │  Step 3: 벡터화          │
         │  - Gemini Embedding      │
         │  - 3072차원 벡터         │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │  Step 4: 온톨로지 구축   │
         │  - 문서 간 관계 매핑    │
         │  - 개념 그래프 생성      │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │  Step 5: Team0 테스트    │
         │  - 30개 쿼리 전송        │
         │  - 결과 수집             │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │  Step 6: 평가 & 분석     │
         │  - 정확도 평가           │
         │  - 성능 분석             │
         │  - 메타데이터 분석       │
         │  - 온톨로지 분석         │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │  최종 검증 리포트        │
         │  (Markdown + JSON)       │
         └──────────────────────────┘
```

### 프로그램 구조

```
team0_validator/
│
├── config.py                          # 전체 설정
│
├── loaders/
│   ├── __init__.py
│   └── pdf_loader.py                  # PDF 로드 및 텍스트 추출
│
├── extractors/
│   ├── __init__.py
│   ├── metadata_extractor.py          # 메타데이터 자동 추출
│   └── chunk_extractor.py             # 의미 단위 청크 분할
│
├── builders/
│   ├── __init__.py
│   ├── vector_builder.py              # 벡터화 (Gemini Embedding)
│   └── ontology_builder.py            # 온톨로지 그래프 구축
│
├── evaluators/
│   ├── __init__.py
│   ├── accuracy_evaluator.py          # 정확도 평가
│   ├── performance_evaluator.py       # 성능 평가 (응답시간 등)
│   ├── metadata_analyzer.py           # 메타데이터 활용 분석
│   └── ontology_analyzer.py           # 온톨로지 활용 분석
│
├── clients/
│   ├── __init__.py
│   └── team0_client.py                # Team0 API 호출 클라이언트
│
├── test_suite.py                      # 메인 테스트 프로그램
├── README.md                          # 이 파일
├── PLAN.md                            # 상세 실행 계획
│
└── results/                           # 결과 저장 폴더
    ├── vectors.json                   # 추출된 벡터 데이터
    ├── ontology.json                  # 구축된 온톨로지 그래프
    ├── test_results.json              # 테스트 결과 (원본 데이터)
    ├── accuracy_report.json           # 정확도 분석 결과
    ├── performance_report.json        # 성능 분석 결과
    └── validation_report.md           # 최종 검증 리포트 (공개용)
```

---

## 📊 Phase별 실행 계획

### **Phase 1: 준비 단계** (Day 1)

#### 목표
- 프로젝트 기본 설정 완료
- 테스트 환경 준비
- 테스트 데이터 정의

#### 작업 항목

| # | 작업 | 예상시간 | 산출물 |
|---|------|---------|--------|
| 1-1 | config.py 작성 | 30분 | 환경변수, 경로, 상수 정의 |
| 1-2 | 폴더 구조 생성 | 15분 | loaders/, builders/ 등 |
| 1-3 | 테스트 쿼리셋 정의 | 45분 | test_queries.json (30개) |
| 1-4 | requirements.txt 작성 | 15분 | 의존성 정의 |

#### 체크리스트
- [ ] config.py 완성
- [ ] 폴더 구조 생성
- [ ] 테스트 쿼리 30개 정의 (온톨로지 12, NLP 12, 국방 6)
- [ ] requirements.txt 작성 (PyPDF2, httpx, numpy 등)

---

### **Phase 2: 핵심 모듈 개발** (Day 2-3)

#### 목표
- PDF 로드에서 온톨로지 구축까지의 전체 파이프라인 구축

#### 2-1. PDF 로더 개발 (Day 2 오전)

```python
# loaders/pdf_loader.py
class PDFLoader:
    def load_all_pdfs(self) -> List[Dict]:
        """8개 PDF 모두 로드"""
        
    def _extract_text(self, pdf_path) -> str:
        """텍스트 추출"""
        
    def _extract_metadata(self, text, filename) -> Dict:
        """메타데이터 자동 추출 (제목, 저자, 연도, 주제)"""
```

**산출물**: `documents_metadata.json` + `raw_text_corpus.json`

#### 2-2. 메타데이터 추출기 개발 (Day 2 오후)

```python
# extractors/metadata_extractor.py
class MetadataExtractor:
    def extract_all_metadata(self, documents) -> Dict:
        """전체 문서의 메타데이터 추출"""
        
    def extract_keywords(self, text) -> List[str]:
        """키워드 자동 추출"""
        
    def classify_document_type(self, text) -> str:
        """문서 유형 분류 (논문, 리포트 등)"""
```

**산출물**: `metadata_analysis.json`

#### 2-3. 청크 분할기 개발 (Day 2 저녁)

```python
# extractors/chunk_extractor.py
class ChunkExtractor:
    def split_into_chunks(self, text, chunk_size=512) -> List[Dict]:
        """의미 단위로 청크 분할"""
        
    def assign_chunk_metadata(self, chunks, doc_metadata) -> List[Dict]:
        """각 청크에 메타데이터 할당"""
```

**산출물**: `chunks.json` (~300-400개 청크)

#### 2-4. 벡터 빌더 개발 (Day 3 오전)

```python
# builders/vector_builder.py
class VectorBuilder:
    def vectorize_all_chunks(self, chunks) -> Dict:
        """Gemini Embedding으로 벡터화 (3072D)"""
        
    def save_vector_db(self, vectors, output_path):
        """벡터 DB 로컬 저장"""
```

**산출물**: `vectors.json` (Team0 방식)

#### 2-5. 온톨로지 빌더 개발 (Day 3 오후)

```python
# builders/ontology_builder.py
class OntologyBuilder:
    def build_concept_graph(self, metadata, chunks) -> Dict:
        """개념 그래프 구축"""
        
    def find_document_relationships(self, vectors) -> List[Dict]:
        """문서 간 의미론적 관계 찾기"""
        
    def build_full_ontology(self) -> Dict:
        """전체 온톨로지 그래프 구축"""
```

**산출물**: `ontology.json`

#### 체크리스트
- [ ] PDF 로더 완성 및 테스트 (8개 PDF 로드)
- [ ] 메타데이터 추출 완성 (100% 추출율 목표)
- [ ] 청크 분할 완성 (300+ 청크 생성)
- [ ] 벡터화 완성 (3072차원, ~5분 소요 예상)
- [ ] 온톨로지 구축 완성 (25+ 관계 찾기)

---

### **Phase 3: Team0 테스트 & 평가** (Day 4)

#### 목표
- Team0에 쿼리 전송 및 결과 수집
- 각 차원별 평가

#### 3-1. Team0 클라이언트 개발

```python
# clients/team0_client.py
class Team0Client:
    def __init__(self, base_url="http://localhost:8002"):
        """Team0 API 클라이언트 초기화"""
        
    async def search(self, query: str, top_k=5) -> Dict:
        """Team0에 쿼리 전송"""
        
    async def batch_search(self, queries: List[str]) -> List[Dict]:
        """배치 쿼리 전송"""
```

#### 3-2. 정확도 평가기 개발

```python
# evaluators/accuracy_evaluator.py
class AccuracyEvaluator:
    def evaluate_single_query(self, query, team0_answer, golden_answer) -> Dict:
        """
        평가 항목:
        - 키워드 포함율 (필수 키워드 몇 개 포함?)
        - 의미론적 유사도 (벡터 코사인 유사도)
        - 완성도 (답변 길이, 구조)
        - 종합 정확도 (0-1.0)
        """
        
    def evaluate_all_queries(self, results) -> Dict:
        """30개 쿼리 모두 평가"""
```

#### 3-3. 성능 평가기 개발

```python
# evaluators/performance_evaluator.py
class PerformanceEvaluator:
    def analyze_response_time(self, results) -> Dict:
        """
        측정:
        - 평균 응답시간
        - P50, P95, P99 응답시간
        """
        
    def analyze_success_rate(self, results) -> Dict:
        """
        측정:
        - 성공률 (답변 제공 여부)
        - 오류율
        """
```

#### 3-4. 메타데이터 분석기 개발

```python
# evaluators/metadata_analyzer.py
class MetadataAnalyzer:
    def analyze_metadata_potential(self) -> Dict:
        """
        분석:
        - 추출 가능한 필드
        - 필터링으로 얻을 수 있는 개선도
        - 추정 정확도: 58.54% → 68%? (+10%)
        """
```

#### 3-5. 온톨로지 분석기 개발

```python
# evaluators/ontology_analyzer.py
class OntologyAnalyzer:
    def analyze_ontology_potential(self) -> Dict:
        """
        분석:
        - 발견된 관계 수
        - 개념 클러스터 수
        - 재순위화로 얻을 수 있는 개선도
        - 추정 정확도: 68% → 85%? (+15-20%)
        """
```

#### 테스트 실행

```python
# test_suite.py - 메인 프로그램
async def run_full_validation():
    # 1. 데이터 준비
    documents = loader.load_all_pdfs()
    chunks = chunk_extractor.split(documents)
    vectors = vector_builder.vectorize(chunks)
    ontology = ontology_builder.build(vectors)
    
    # 2. Team0 테스트
    results = []
    for query in test_queries:
        response = team0_client.search(query)
        results.append(response)
    
    # 3. 평가
    accuracy_report = accuracy_evaluator.evaluate_all(results)
    performance_report = performance_evaluator.analyze(results)
    metadata_analysis = metadata_analyzer.analyze()
    ontology_analysis = ontology_analyzer.analyze()
    
    # 4. 보고서 생성
    generate_final_report(
        accuracy_report,
        performance_report,
        metadata_analysis,
        ontology_analysis
    )
```

#### 체크리스트
- [ ] Team0 클라이언트 완성 (포트 8002 연결)
- [ ] 30개 쿼리 모두 실행 (예상 10-15분)
- [ ] 정확도 평가 완성
- [ ] 성능 평가 완성
- [ ] 메타데이터 분석 완성
- [ ] 온톨로지 분석 완성

---

### **Phase 4: 보고서 생성** (Day 5)

#### 목표
- 최종 검증 리포트 생성 (공개 가능)

#### 4-1. 데이터 분석

```python
# 정확도 통계
- 카테고리별 정확도 (온톨로지, NLP, 국방)
- 키워드 포함율 분포
- 응답시간 분포 (평균, P95, P99)
- 성공률
```

#### 4-2. 최종 리포트 생성

```markdown
# Team0 RAG 검증 보고서

## Executive Summary
- 테스트 대상: 8개 PDF, 30개 쿼리
- 현재 정확도: 58.54%
- 개선 기회: 메타데이터 +10%, 온톨로지 +15%, 하이브리드 +5%
- 최대 가능 정확도: ~88%

## 1. Baseline 성능
- 정확도: 58.54%
- 평균 응답시간: 500ms
- 성공률: 100%

## 2. 메타데이터 분석
- 추출 가능한 필드: 100%
- 필터링 효과: +10% 예상

## 3. 온톨로지 분석
- 발견된 관계: 25개
- 재순위화 효과: +15% 예상

## 4. 종합 평가
- Team0의 기본 성능 검증 완료
- 개선 가능성 실증적으로 분석
- 권고: 메타데이터 + 온톨로지 하이브리드 적용 시 80%+ 달성 가능
```

#### 산출물
- `validation_report.md` (공개 가능)
- `detailed_results.json` (상세 데이터)
- `summary.txt` (요약)

#### 체크리스트
- [ ] 데이터 분석 완성
- [ ] 마크다운 리포트 생성
- [ ] JSON 상세 결과 생성
- [ ] 요약 문서 생성

---

## 📅 일정 및 이정표

| Day | Phase | 주요 작업 | 산출물 |
|-----|-------|---------|--------|
| **1** (6/7) | 준비 | config, 폴더, 쿼리셋 | config.py, test_queries.json |
| **2** (6/8) | 개발 1 | PDF 로드, 메타데이터, 청크 | documents.json, chunks.json |
| **3** (6/9) | 개발 2 | 벡터화, 온톨로지 구축 | vectors.json, ontology.json |
| **4** (6/10) | 테스트 | Team0 쿼리, 평가 | test_results.json |
| **5** (6/11) | 보고서 | 최종 분석 및 리포트 | validation_report.md |

---

## 📈 예상 결과

### Baseline (Team0 현재)
```
정확도: 58.54%
응답시간: ~500ms
성공률: 100%
```

### 메타데이터 적용 후
```
정확도: ~68% (+10%)
응답시간: ~450ms (-10%)
성공률: 100%
```

### 온톨로지 적용 후
```
정확도: ~83% (+15% from 68%)
응답시간: ~480ms
성공률: 100%
```

### 하이브리드 (메타데이터 + 온톨로지)
```
정확도: ~88% (+5% from 83%)
응답시간: ~520ms
성공률: 100%
```

---

## 🔧 사전 준비 사항

### 필수 환경
- Python 3.8+
- Team0 서버 실행 (포트 8002)
- Gemini API 접근 가능 (LLM Gateway 포트 8011)

### 필수 라이브러리
```
PyPDF2>=3.0
httpx>=0.24
numpy>=1.24
scikit-learn>=1.3
pandas>=2.0
```

### 테스트 데이터
- 8개 PDF (E:\ai_lab_SIT\target_doc)
- 30개 테스트 쿼리

---

## 📝 실행 방법

### 1단계: 환경 설정
```bash
cd E:\ai_lab_SIT\team0_validator
pip install -r requirements.txt
```

### 2단계: Team0 서버 시작
```bash
# 별도 터미널에서
cd E:\ai_lab_SIT\team0_rag_source
python app/main.py --port 8002
```

### 3단계: 검증 프로그램 실행
```bash
python test_suite.py
```

### 4단계: 결과 확인
```bash
# 생성된 파일 확인
ls -la results/
cat results/validation_report.md
```

---

## ✅ 성공 기준

| 기준 | 목표 | 평가 |
|------|------|------|
| **PDF 로드** | 8개 모두 성공 | ✅ 100% |
| **메타데이터 추출** | 100% 추출율 | ✅ 목표 |
| **벡터화** | 모든 청크 벡터화 | ✅ 3072D 완성 |
| **온톨로지 구축** | 25+ 관계 발견 | ✅ 기대값 |
| **Team0 테스트** | 30개 쿼리 모두 응답 | ✅ 100% 성공률 |
| **정확도 측정** | 기준값 대비 측정 | ✅ 58.54% 확인 |
| **최종 리포트** | Markdown 리포트 생성 | ✅ 공개 가능 |

---

## 📚 참고 자료

- Team0 아키텍처: `team0_rag_source/TEAM0_ARCHITECTURE.md`
- Team0 구현: `team0_rag_source/TEAM0_IMPLEMENTATION.md`
- 기존 평가: `ACCURACY_ANALYSIS_FINAL_REPORT.txt`
- Ontology 기술: `E:\ontology_edu\X_ont_std/` (참고용)

---

## 🎯 최종 목표

**Team0 RAG의 객관적 성능 검증 및 개선 기회 도출**

1. ✅ Team0 현재 성능 확인 (58.54%)
2. ✅ 메타데이터 활용 효과 분석 (+10% 가능)
3. ✅ 온톨로지 활용 효과 분석 (+15% 가능)
4. ✅ 최종 보고서 생성 (공개 가능)

---

**문서 버전**: 1.0  
**마지막 수정**: 2026-06-07  
**상태**: 📋 실행 준비 완료
