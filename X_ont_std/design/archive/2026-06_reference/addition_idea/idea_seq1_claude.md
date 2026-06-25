# PHASE 8 추가 아이디어 Seq 1: Claude 제시

**작성일**: 2026-06-07  
**작성자**: Claude Code  
**상태**: 검토 대기  
**우선순위**: P1 (설계 검토 개선) / P2-3 (구현 개선)

---

## 1. Threshold Calibration을 P0으로 승격

### 현재 상태
```
위치: PHASE8_MASTER_TECHNICAL_REPORT.md Section 9.1
우선순위: P2 (검색/랭킹 개선)
```

### 제안
```
변경: P0 (v5 MVP) 또는 Week 0 (선행 작업)
```

### 근거

```text
EvidenceGate 동작의 필수 전제조건:

1. EvidenceGate는 relevance threshold를 기반으로 판정
2. threshold 값이 없으면 gate가 정상 동작 불가
3. 초기 설정값이 임의적이면 성능 불확실

현재 문제:
- "known-positive 10개 수집" 명시되지 않음
- 실제로 어떻게 수집할 것인지 불명확
- P2까지 기다리면 v5 MVP 성능 제약

영향도:
- PHASE 8 수용 기준 달성 불가능 (STD-S 90%)
- P0 구현 진행 차단
- Week 1-2 시간 낭비 가능성
```

### 실행 계획

```text
Week 0 (선행, 2-3시간):
1. v4 평가에서 positive 10개 선정
   (STD-O, STD-A 중 높은 점수 항목)

2. negative 10개 선정
   (범위 외 또는 검색 실패 항목)

3. vector score 분포 분석
   - positive 평균: X
   - negative 평균: Y
   - 중간값: (X+Y)/2 시작값

4. threshold 후보 3개 산출
   - 보수적 (낮은 false positive)
   - 중간값
   - 공격적 (높은 recall)

Week 1: 실제 EvidenceGate 구현 시
→ threshold 선택 후 적용
```

---

## 2. API 버전 관리 전략 명확화

### 현재 상태
```
PHASE8_MASTER_TECHNICAL_REPORT.md Section 2.2
- /api/v5/hybrid/ask (신규)
- 기존 /api/hybrid/ask (기존)

하지만 세부 전략이 명확하지 않음
```

### 제안

#### Option A: 버전 기반 분리 (권장)
```
POST /api/v4/hybrid/ask     (기존, 유지)
POST /api/v5/hybrid/ask     (신규, PHASE 8)

장점:
- 명확한 버전 구분
- 로그/메트릭 분리 용이
- 클라이언트 마이그레이션 명확

단점:
- API 엔드포인트 2개 유지
- 클라이언트 업그레이드 필요

구현:
- v4: 기존 코드 그대로 유지
- v5: 새로 구현
- 라우터: query param 또는 URL path로 버전 선택
```

#### Option B: query param 기반
```
POST /api/hybrid/ask?version=v4  (기존)
POST /api/hybrid/ask?version=v5  (신규)
POST /api/hybrid/ask             (v5로 기본값)

장점:
- 단일 엔드포인트
- 클라이언트 점진적 마이그레이션 가능

단점:
- 기본값이 v5면 실수 위험
- 로그 필터링 복잡

구현: 조건부 라우팅
```

### 권장

```
Option A (버전 기반)를 권장하는 이유:

1. 명확성: API 경로만으로 버전 알 수 있음
2. 안정성: 실수로 v4→v5 자동 변환 없음
3. 모니터링: 로그에서 버전 추적 용이
4. 테스트: v4/v5 동시 테스트 간단

마이그레이션 전략:
- Phase 1 (Week 4+): /api/v5만 테스트
- Phase 2 (Week 8+): 클라이언트에 v5 권장
- Phase 3 (Month 3+): /api/v4 deprecated (선택)
```

---

## 3. Hybrid Fusion의 단계화 명시

### 현재 상태
```
PHASE8_MASTER_TECHNICAL_REPORT.md Section 8
- P0: concat만 사용
- P1: RRF 추가
- P2: weighted fusion, category-aware reranking

하지만 "initial MVP"의 성능 제약이 명확하지 않음
```

### 제안

#### 초기 MVP (P0)의 한계 명시

```text
현재 설계 (concat):

ontology_results = [
  {text: "A", confidence: 0.95},
  {text: "B", confidence: 0.85}
]

vector_results = [
  {text: "X", similarity: 0.92},
  {text: "Y", similarity: 0.88},
  {text: "Z", similarity: 0.75}
]

→ concat 결과: A, B, X, Y, Z

문제:
1. 순서가 의미 없음 (ontology 우선순위 없음)
2. ontology와 vector의 점수 스케일 다름
3. 최상의 결과가 순서 뒤에 올 수 있음

성능 영향:
- Hybrid 모드의 정확도가 초기에는 제한적
- RRF 없으면 약 5-10% 성능 저하 예상
```

#### P1/P2 로드맵 명시

```text
Week 4+ (P1):
- RRF (Reciprocal Rank Fusion) 구현
  → 순서 기반 합성으로 성능 +5-10%
  
Week 8+ (P2):
- Score normalization + weighted fusion
  - ontology와 vector를 같은 스케일로
  - 가중치 최적화 (5:5, 6:4, 등)
  → 성능 +3-5% (누적 +8-15%)

Week 12+ (P3):
- Category-aware reranking
  - 온톨로지 관계 가중치 적용
  → 성능 +2-3% (누적 +10-18%)
```

### 권장

```text
추가 문서: PHASE8_MASTER_TECHNICAL_REPORT.md Section 8에 추가

"초기 MVP (P0)의 제약":
- concat으로 인한 순서 무의미성
- 예상 성능 영향: 5-10% 정확도 저하
- RRF 추가 (P1)로 회복 가능

이를 통해:
1. Codex가 초기 예상치 조정 가능
2. 성능 목표 재조정 가능
3. P1 로드맵이 더 명확해짐
```

---

## 4. Question Analyzer의 진화 단계 구체화

### 현재 상태
```
PHASE8_MASTER_TECHNICAL_REPORT.md Section 5
Stage A: regex/rule
Stage B: ontology schema mapping
Stage C: lightweight LLM classifier

하지만 각 단계의 구체적 구현이 명확하지 않음
```

### 제안

#### Stage A: Rule 기반 (P0)

```text
구현:
class QuestionAnalyzerStageA:
    KEYWORDS = {
        'Snowflake': ['snowflake', 'warehouse', 'table', 'sql', ...],
        'Ontology': ['온톨로지', '지식그래프', '클래스', '속성', ...],
        'Advanced RAG': ['rag', 'bm25', 'chunk', 'rerank', ...]
    }
    
    def classify(question: str) -> Category:
        for category, keywords in self.KEYWORDS.items():
            if any(kw in question.lower() for kw in keywords):
                return Category[category]
        return Category.UNKNOWN

정확도 예상: 80-85%
구현 시간: 2-3시간
유지비용: 낮음 (규칙만 추가)
```

#### Stage B: Ontology Schema (P1)

```text
개선점:
- 온톨로지에서 직접 concept 읽음
- 동의어/별칭 자동 생성
- 개념 간 관계 활용

구현:
class QuestionAnalyzerStageB:
    def __init__(self, ontology):
        self.concepts = ontology.get_all_concepts()
        self.aliases = ontology.get_aliases()
    
    def classify(question: str) -> Category:
        # 온톨로지 concept 매칭
        # 동의어 확장 검색
        # 상위/하위 개념 고려

정확도 예상: 88-92%
구현 시간: 1-2주
유지비용: 중간 (온톨로지와 동기화)
```

#### Stage C: LLM Classifier (P2)

```text
개선점:
- 문맥 이해 기반 분류
- 모호한 질문도 처리
- 의도 추론 가능

구현:
class QuestionAnalyzerStageC:
    def classify(question: str) -> Category:
        prompt = f"""
        질문을 다음 카테고리로 분류:
        - Ontology: 온톨로지, 관계, 그래프 관련
        - Advanced RAG: 검색, 랭킹 관련
        - Snowflake: Snowflake 데이터 관련
        
        질문: {question}
        카테고리:
        """
        response = llm.complete(prompt)
        return parse_category(response)

정확도 예상: 95%+
구현 시간: 3-5시간 (프롬프트 최적화)
유지비용: 낮음 (LLM이 자동 학습)
비용: LLM API 호출 비용
```

---

## 5. Document Metadata 추가 자동화

### 현재 상태
```
PHASE8_MASTER_TECHNICAL_REPORT.md Section 8
- 파일명 기반 임시 분류 명시
- 추후 사용자 지정 가능하게 확장

하지만 "파일명 기반" 규칙이 구체적이지 않음
```

### 제안

#### 파일명 패턴 매칭 규칙

```text
현재 문서 명명 규칙 분석:

"NLP - [NUMBER] [DESC] - YYYY.pdf"

예:
- NLP - [03] 온톨로지질성문제를 해결하기 위한... - 2024.pdf
  → Category: Ontology

- NLP - [06] 정적 언어모델부터 생성형AI까지... - 2025.pdf
  → Category: Advanced RAG (또는 NLP 일반)

- "...Snowflake..." 포함 시
  → Category: Snowflake

규칙 정의:
```

```python
class DocumentCategoryExtractor:
    PATTERNS = {
        'Ontology': [
            r'온톨로지',
            r'knowledge\s*graph',
            r'지식그래프',
            r'클래스|속성|인스턴스',
        ],
        'Advanced RAG': [
            r'RAG|검색증강생성',
            r'BM25|벡터|임베딩',
            r'chunk|rerank|검색',
        ],
        'Snowflake': [
            r'Snowflake|snowflake',
            r'warehouse|table|SQL',
        ],
    }
    
    def extract_category(filename: str) -> str:
        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return category
        return 'Unknown'
```

#### 자동 적용 전략

```text
Week 1 (P0):
1. 기존 모든 문서에 메타데이터 추가
   - 파일명 규칙으로 자동 분류
   - 검증 후 저장

2. Vector DB 청크에 category metadata 추가
   chunk = {
       text: "...",
       metadata: {
           doc_id: "doc-001",
           category: "Ontology",  ← 자동 추가
           filename: "...",
           page: 3
       }
   }

Week 2+ (P0/P1):
1. EvidenceGate에서 category 검증
2. 불일치 문서는 수동 검토
3. 이상 패턴 수집 → 규칙 개선
```

---

## 6. Score Calibration의 구체적 선행 작업

### 현재 상태
```
PHASE8_MASTER_TECHNICAL_REPORT.md Section 9
- known-positive 10개, known-negative 10개 명시
- 하지만 구체적 작업 절차가 없음
```

### 제안

#### Week 0 선행 작업 (3시간)

```text
1단계: Positive 샘플 선정 (30분)
   v4 평가에서 정확도 높은 문항 10개 선정
   조건: 정확도 ≥ 80%
   
   예시:
   - STD-O-01: 75.62% (Ontology 평균)
   - STD-A-02: 62.5% (Advanced RAG 평균)
   → 실제 수치에서 선정

2단계: Negative 샘플 선정 (30분)
   조건: 정확도 ≤ 20% 또는 범위 외
   
   예시:
   - STD-S 항목 (모두 범위 외)
   - STD-O/A 중 낮은 점수 항목
   
3단계: Vector Score 분석 (1시간)
   ```python
   positive_scores = [
       get_vector_score(q1, doc1),  # 0.92
       get_vector_score(q2, doc2),  # 0.88
       ...
   ]
   negative_scores = [
       get_vector_score(q1, wrong_doc),  # 0.45
       get_vector_score(q2, wrong_doc),  # 0.38
       ...
   ]
   
   threshold_candidates = [
       percentile_75(positive_scores) - percentile_25(negative_scores),
       (avg_positive + avg_negative) / 2,
       percentile_50(negative_scores) + 0.1
   ]
   ```

4단계: Threshold 후보 산출 (1시간)
   - 보수적: high precision (false positive 적음)
   - 중간값: balanced
   - 공격적: high recall (false negative 적음)
   
   문서화:
   - positive 평균: X
   - negative 평균: Y
   - 권장 threshold: Z
```

#### 산출물

```text
week0_threshold_calibration/
├─ positive_samples.json
│  └─ 10개 문항 + 점수
├─ negative_samples.json
│  └─ 10개 문항 + 점수
├─ analysis.md
│  ├─ 점수 분포
│  ├─ threshold 후보
│  └─ 권장사항
└─ implementation_guide.md
   └─ Week 1에 적용 방법
```

---

## 7. 평가 기준 세분화

### 현재 상태
```
PHASE8_MASTER_TECHNICAL_REPORT.md Section 11
Acceptance Criteria는 명확하지만
평가 방법이 구체적이지 않음
```

### 제안

#### STD-S no-answer 정확도 측정

```text
방법:
1. STD-S 8개 문항 평가
2. 각 응답이 다음을 만족하는지 확인:
   - "질문은 해당 카테고리 문서와 관련이 없습니다"
   - 완전 일치 (부분 일치 불가)
   - LLM 호출이 0회 (로그 검증)

자동화:
```python
def measure_no_answer_accuracy(results) -> float:
    total = len(results)
    correct = 0
    
    for result in results:
        if result['problem_id'].startswith('STD-S'):
            response = result['actual_answer']
            expected = "질문은 해당 카테고리 문서와 관련이 없습니다."
            
            if response == expected and result['llm_calls'] == 0:
                correct += 1
    
    return correct / total if total > 0 else 0
```

#### Hallucination Rate 측정

```text
정의:
범위 외 기술에 대해 LLM이 생성한 답변

예시:
- STD-S 문항에 "Snowflake warehouse는..."으로 시작하는 답변
- 기술 설명이 있으면 hallucination

자동화:
```python
def detect_hallucination(result) -> bool:
    if not result['problem_id'].startswith('STD-S'):
        return False
    
    answer = result['actual_answer']
    
    # Snowflake 관련 기술 설명 감지
    hallucination_patterns = [
        r'warehouse|table|SQL|join|query',  # Snowflake 기술
        r'RAG|retrieval|embedding|chunk',   # RAG 기술
    ]
    
    for pattern in hallucination_patterns:
        if re.search(pattern, answer, re.IGNORECASE):
            return True
    
    return False
```

---

## 8. v4/v5 비교 보고서 템플릿

### 제안

```text
PHASE8_V4_V5_COMPARISON.xlsx 구조:

시트 1: Summary
├─ v4 baseline: 67.50% (24문항)
├─ v5 개선: TBD
├─ 개선도: TBD
└─ 항목별 비교 (표)

시트 2: Ontology 비교
├─ v4: 75.62%
├─ v5: 예상 76%+ (1-3% 개선, 또는 유지)
└─ 개별 문항 비교

시트 3: Advanced RAG 비교
├─ v4: 62.5% (추정)
├─ v5: 예상 65%+ (2-5% 개선)
└─ 개별 문항 비교

시트 4: Snowflake 비교 (신규 평가)
├─ v4: 0.00% (범위 외)
├─ v5: 예상 90%+ (no-answer 정확도)
└─ 개별 문항 비교

시트 5: Routing 검증 (신규)
├─ ontology_only: VECTOR step 호출 0회
├─ vector_only: ONTOLOGY step 호출 0회
└─ hybrid: 두 경로 모두 호출 확인

시트 6: 상세 분석
└─ 항목별 v4/v5 비교, 개선 이유
```

---

## 우선순위 정렬

```
Priority 1 (필수):
☐ 아이디어 1: Threshold Calibration P0 승격
  → 구현 차단 위험, 해결 시간 짧음
  
☐ 아이디어 2: API 버전 관리 전략
  → 초기 아키텍처 결정, 나중에 변경 어려움

Priority 2 (권장):
☐ 아이디어 3: Hybrid Fusion 단계화 명시
  → 성능 기대치 조정 필요

☐ 아이디어 4: Question Analyzer 진화 단계
  → 초기 Rule 구현 명확화

☐ 아이디어 6: Score Calibration 구체화
  → P0 선행 작업 상세화

Priority 3 (선택):
☐ 아이디어 5: Document Metadata 자동화
  → P0 구현에 포함 가능

☐ 아이디어 7: 평가 기준 세분화
  → 실행 중 조정 가능

☐ 아이디어 8: 비교 보고서 템플릿
  → 실행 후 작성 가능
```

---

## 다음 단계

```
1. 이 아이디어들을 팀에 제시
2. Priority 1-2 아이디어는 PHASE8_MASTER_TECHNICAL_REPORT 업데이트
3. 구현 시작 전에 확정
4. Codex에 전달
```

---

**상태**: 검토 대기  
**대상**: Codex, Team Leadership  
**효과**: PHASE 8 설계 명확화 및 구현 위험 감소
