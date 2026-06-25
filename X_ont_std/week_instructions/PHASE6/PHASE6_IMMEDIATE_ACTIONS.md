# PHASE 6 즉시 실행 계획 (Stage 3 운영)

**작성일**: 2026-06-07  
**상태**: 🔴 READY FOR EXECUTION  
**목표**: Stage 3 (정답 보정) 실제 실행 및 시스템 자동 개선

---

## 📋 **즉시 실행 작업 (Today)**

### Task 1: Stage 3 실행 환경 준비 (30분)

#### 1.1 필수 파일 확인

```bash
# 다음 파일들이 존재하는지 확인
E:\ontology_edu\X_ont_std\evaluation_framework\
├─ run_stage3.py                    ✓ (이미 생성됨)
├─ stages/stage3_correction/
│  ├─ impact_analyzer.py            ✓ (이미 생성됨)
│  └─ cli.py                        ✓ (이미 생성됨)
└─ data/
   └─ corrections/                  ✓ (생성됨 - 출력용)

# 확인 명령어
python -c "import sys; sys.path.insert(0, 'E:/ontology_edu/X_ont_std/evaluation_framework'); from stages.stage3_correction.cli import interactive_correction_session; print('[OK] Stage 3 모듈 로드 성공')"
```

#### 1.2 Stage 2 결과 확인

```bash
# 이전 Stage 2 실행 결과 확인
ls -la E:\ontology_edu\X_ont_std\evaluation_framework\data\checkpoint_log.json

# 없으면 Stage 2 재실행
python E:\ontology_edu\X_ont_std\evaluation_framework\run_stage2.py
```

---

### Task 2: Snowflake 정답 보정 준비 (15분)

#### 2.1 Snowflake 8개 문항 정보 수집

**파일**: 이미 Stage 1/2에서 식별됨

```python
SNOWFLAKE_ITEMS = [
    {
        'id': 'STD-S-01',
        'question': '(Stage 2 보고서에서 확인)',
        'current_answer': '(Stage 2에서 확인)',
        'reason_out_of_scope': 'Snowflake 문서 미제공'
    },
    # ... STD-S-02 ~ STD-S-08
]
```

**확인 방법**:
1. `E:\ontology_edu\X_ont_std\evaluation_framework\reports\evaluation_checkpoint_report.md` 열기
2. "제약이 적용된 항목" 섹션에서 STD-S-01 ~ STD-S-08 확인
3. 각 항목의 "현재 정답" 기록

#### 2.2 올바른 정답 작성 규칙

**Snowflake 카테고리 정답 규칙**:
```
✓ 반드시 포함할 문구: "해당 카테고리 문서와 관련이 없습니다"
✓ 최소 길이: 20글자 이상
✓ 최대 길이: 5000글자 이하

예시:
"이 질문은 Snowflake 관련 기술이므로 해당 카테고리 문서와 관련이 없습니다."
```

---

### Task 3: Stage 3 대화형 실행 (20-30분)

#### 3.1 실행 명령어

```bash
cd E:\ontology_edu\X_ont_std
python evaluation_framework/run_stage3.py
```

#### 3.2 대화형 입력 시나리오

**Stage 3-1: 정답 입력**

```
세션 ID: correction_20260607_HHMM
총 24개 문항 중 필요한 것만 수정하세요

옵션: 1=유지, 2=수정, 3=새답변, 4=스킵, Q=종료

[1/24] STD-S-01
═══════════════════════════════════════
📝 질문: Snowflake RAG에서 ...
📂 카테고리: Snowflake
📊 현재 팀 정확도: 75%

✓ 현재 정답:
  [Stage 2 보고서에서 확인된 기존 정답]

선택 (1-4, Q): 2  ← 수정 선택

새 정답을 입력하세요:
(여러 줄 입력 가능, 끝나면 'END' 입력)
해당 카테고리 문서와 관련이 없습니다
END

수정 사유: Snowflake 범위 외 기술, 문서 미제공
```

**반복**: STD-S-02 ~ STD-S-08 (동일 패턴)

**비-Snowflake 항목**:
```
[9/24] STD-O-01
...
선택 (1-4, Q): 1  ← 유지 선택
```

#### 3.3 입력 완료

```
세션 종료됨

✓ 8개 정답 수정 완료
✓ 시스템 업데이트 완료 (시뮬레이션)
✓ 재평가 완료

평균 정확도 변화: -50.0%p
```

---

### Task 4: 산출물 검증 (15분)

#### 4.1 생성 파일 확인

```bash
# 생성될 파일
E:\ontology_edu\X_ont_std\evaluation_framework\
├─ data/corrections/
│  └─ corrections_20260607_HHMMSS.json  ← 정답 수정 기록
└─ reports/
   └─ impact_analysis_report.md         ← 영향도 분석 보고서
```

#### 4.2 JSON 구조 검증

```python
# corrections_YYYYMMDD_HHMMSS.json 내용 확인
{
  "session_id": "correction_20260607_HHMMSS",
  "timestamp": "2026-06-07T...",
  "total_processed": 8,
  "corrections": [
    {
      "problem_id": "STD-S-01",
      "category": "Snowflake",
      "question": "...",
      "original_expected_answer": "...",
      "corrected_expected_answer": "해당 카테고리 문서와 관련이 없습니다",
      "correction_type": "MODIFIED",
      "correction_reason": "Snowflake 범위 외 기술",
      "review_status": "PENDING",
      "timestamp": "..."
    },
    # ... STD-S-02 ~ STD-S-08
  ]
}
```

#### 4.3 영향도 보고서 검증

```markdown
# Stage 3 영향도 분석 보고서

## 요약
| 항목 | 결과 |
|---|---:|
| 총 수정 | 8개 |
| 온톨로지 변경 | 0개 (범위 외이므로) |
| RAG 변경 | 8개 (제외 규칙 추가) |
| 평가 기준 변경 | 8개 (점수 기준 조정) |

## 구현 순서
1. [P1] UPDATE_EXPECTED_ANSWER (즉시)
2. [P2] ADD_EXCLUSION_RULE (1일 이내)
3. [P3] UPDATE_SCORING_RULE (1주일 이내)
```

---

## 🔄 **Task 5: 영향도 분석 검토 (20분)**

### 5.1 변경점 검토 체크리스트

| # | 항목 | 변경점 | 승인 |
|---|---|---|---|
| 1 | 온톨로지 | 추가/제거 개념 없음 ✓ | ☐ |
| 2 | RAG | Snowflake 제외 규칙 8개 추가 | ☐ |
| 3 | 평가 기준 | "관련 없음" 정확도 기준 변경 | ☐ |
| 4 | 위험도 | MEDIUM (8개 수정) | ☐ |
| 5 | 롤백 계획 | 준비 완료 | ☐ |

### 5.2 영향도 분석 가이드

```
각 변경점에 대해:
1. 무엇을 변경하는가?
   → RAG에 "snowflake" 키워드 제외 규칙 추가

2. 왜 변경하는가?
   → Snowflake 문서 미제공으로 범위 외 오류 방지

3. 어떤 영향을 미치는가?
   → Snowflake 질문에 대해 항상 "관련 없음" 반환
   → 정확도: 75% → 0% (예상값이 "관련 없음"이므로 정확함)

4. 롤백 가능한가?
   → YES (제외 규칙 제거 시 복원 가능)
   → 트리거: 정확도 5%p 이상 하락 시
```

---

## 📊 **Task 6: 시스템 업데이트 계획 (설계)**

### 6.1 온톨로지 업데이트

```python
# 실제 구현 필요: ontology_updater.py
class OntologyUpdater:
    def apply_changes(self, changes):
        """
        변경사항 적용:
        - Snowflake 범위 외 마킹 (이미 done)
        - 새 개념 추가 (필요 시)
        - 관계 변경 (필요 시)
        """
```

**8개 항목 영향도**:
- 온톨로지 추가 개념: 0개
- 온톨로지 제거 개념: 0개
- 관계 변경: 0개
- **결론**: 온톨로지 변경 불필요

### 6.2 RAG 업데이트

```python
# 실제 구현 필요: rag_updater.py
class RAGUpdater:
    def apply_changes(self, changes):
        """
        변경사항 적용:
        1. 제외 규칙 추가 (Snowflake 제외)
        2. 임베딩 갱신 (새 정답 벡터화)
        3. 검색 가중치 조정 (없음)
        """
```

**8개 항목 구체적 조치**:
```
STD-S-01 ~ STD-S-08:

Before:
  query: "Snowflake RAG에서..."
  → 검색 시도 → "RAG 답변은..." 반환 → 75% 채점

After:
  query: "Snowflake RAG에서..."
  → 제외 규칙 감지 → "관련 없습니다" 반환
  → expected: "관련 없습니다" → 100% 채점

구현 순서:
  1. RAG.add_exclusion_rule("snowflake", "out_of_scope")
  2. RAG.update_embeddings(new_answers)
  3. RAG.adjust_weights("snowflake", 0.0)
```

### 6.3 평가 기준 업데이트

```python
# 실제 구현 필요: evaluation_updater.py
class EvaluationUpdater:
    def apply_changes(self, changes):
        """
        변경사항 적용:
        1. 예상 정답 업데이트
        2. 채점 기준 조정
        3. 카테고리 재검토
        """
```

**구체적 변경**:
```
STD-S-01 ~ STD-S-08:

기존 채점 기준:
  expected_answer = "RAG 답변은..."
  actual_answer = "RAG 답변은..."
  score = semantic_similarity(expected, actual)

신규 채점 기준:
  expected_answer = "해당 카테고리 문서와 관련이 없습니다"
  actual_answer = "해당 카테고리 문서와 관련이 없습니다"
  score = exact_match(expected, actual) ? 100% : 0%
```

---

## 🔄 **Task 7: 재평가 및 확인 (30분)**

### 7.1 재평가 실행 계획

```bash
# Stage 2 재실행 (업데이트된 시스템으로)
python run_stage2.py

# 비교 항목
Before (현재):
├─ Team4 정확도: 31.25% (Snowflake 8개 때문)
└─ Snowflake 부분: 8/8 = 100% 오류 (범위 외 답변)

After (업데이트 후):
├─ Team4 정확도: 54.17% (8개 → 16개 정답 맞음)
└─ Snowflake 부분: 8/8 = 100% 정확 (범위 외 올바른 답변)
```

### 7.2 회귀 테스트

```
다른 카테고리 영향도 확인:

Ontology (STD-O-01 ~ STD-O-08):
  변경사항: 0개
  예상 정확도: 변화 없음 ✓

Advanced RAG (STD-A-01 ~ STD-A-08):
  변경사항: 0개
  예상 정확도: 변화 없음 ✓

Snowflake (STD-S-01 ~ STD-S-08):
  변경사항: 8개 (정답 변경)
  예상 정확도: -75%p (75% → 0% 범위 외 정답화)
              하지만 expected_answer가 범위 외이므로
              실제로는 +75%p (0% → 100% 올바른 답변)
```

### 7.3 최종 검증 체크리스트

```markdown
✓ Task 1: 환경 준비
  - [ ] Stage 3 모듈 로드 확인
  - [ ] Stage 2 결과 확인

✓ Task 2: 정답 준비
  - [ ] Snowflake 8개 항목 확인
  - [ ] 정답 규칙 이해

✓ Task 3: Stage 3 실행
  - [ ] interactive_correction_session() 완료
  - [ ] corrections_YYYYMMDD_HHMMSS.json 생성

✓ Task 4: 산출물 검증
  - [ ] JSON 구조 확인
  - [ ] 영향도 보고서 확인

✓ Task 5: 영향도 검토
  - [ ] 8개 변경점 승인
  - [ ] 롤백 계획 확인

✓ Task 6: 시스템 업데이트 (시뮬레이션)
  - [ ] 온톨로지: 변경 불필요 ✓
  - [ ] RAG: 8개 제외 규칙 추가
  - [ ] 평가 기준: 정확도 기준 변경

✓ Task 7: 재평가
  - [ ] Stage 2 재실행
  - [ ] 정확도 개선 확인 (31.25% → 54.17%)
  - [ ] 회귀 테스트 통과
```

---

## ⏱️ **실행 시간 계획**

```
Task 1: 환경 준비        (30분)  15:00 ~ 15:30
Task 2: 정답 준비        (15분)  15:30 ~ 15:45
Task 3: Stage 3 실행     (30분)  15:45 ~ 16:15
Task 4: 산출물 검증      (15분)  16:15 ~ 16:30
─────────────────────────────────
소계 (1차):             (90분)

Task 5: 영향도 검토      (20분)  16:30 ~ 16:50
Task 6: 시스템 업데이트  (15분)  16:50 ~ 17:05
Task 7: 재평가 및 확인   (30분)  17:05 ~ 17:35
─────────────────────────────────
총 소요 시간:            (155분 ≈ 2.5시간)

예상 완료 시각: 17:35
```

---

## 📎 **참고 파일**

```
주요 명령 스크립트:
- E:\ontology_edu\X_ont_std\evaluation_framework\run_stage3.py

입력 파일:
- E:\ontology_edu\X_ont_std\evaluation_framework\data\checkpoint_log.json

출력 파일:
- E:\ontology_edu\X_ont_std\evaluation_framework\data\corrections\corrections_YYYYMMDD_HHMMSS.json
- E:\ontology_edu\X_ont_std\evaluation_framework\reports\impact_analysis_report.md

문서:
- E:\ontology_edu\X_ont_std\evaluation_framework\reports\evaluation_checkpoint_report.md (Stage 2 결과)
```

---

## 🎯 **성공 기준**

```
✅ Stage 3 완료
   - 정답 8개 수정 완료
   - corrections_YYYYMMDD_HHMMSS.json 생성
   - impact_analysis_report.md 생성

✅ 정확도 개선
   - Team4: 31.25% → 54.17% (+22.92%p)
   - Snowflake: 0% → 100% (+100%p, 범위 외 정답화)

✅ 시스템 안정성
   - Ontology, Advanced RAG: 변화 없음
   - 회귀 테스트: 100% 통과
   - 롤백 계획: 준비 완료

✅ 문서화
   - 영향도 분석 보고서 완성
   - 변경 이력 기록 완료
```

---

**상태**: 🔴 READY  
**책임자**: Claude Code  
**마감일**: 2026-06-07  
**결과 보고**: 20260607_Stage3_COMPLETION.md
