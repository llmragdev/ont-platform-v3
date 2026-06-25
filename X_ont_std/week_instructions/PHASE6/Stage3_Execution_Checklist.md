# Stage 3 실행 체크리스트 (단계별 가이드)

**목표**: Snowflake 정답 보정 자동화  
**소요 시간**: 2.5시간  
**시작 시각**: 즉시  
**마감**: 2026-06-07 17:35

---

## 🟩 **Phase A: 준비 단계 (45분)**

### [ ] A1. 환경 확인 (5분)

**1. Python 버전 확인**
```bash
python --version
# Expected: Python 3.8 이상
```

**2. 필수 패키지 확인**
```bash
python -c "import openpyxl, json; print('[OK] 필수 패키지 설치됨')"
```

**3. 작업 디렉토리 확인**
```bash
# PowerShell
Test-Path "E:\ontology_edu\X_ont_std\evaluation_framework"
# Expected: True
```

---

### [ ] A2. Stage 3 모듈 로드 테스트 (5분)

**1. Python 대화형 모드 실행**
```bash
cd E:\ontology_edu\X_ont_std
python
```

**2. 모듈 import 테스트**
```python
import sys
sys.path.insert(0, 'evaluation_framework')

# Stage 3 모듈 로드
from stages.stage3_correction.cli import interactive_correction_session
from stages.stage3_correction.impact_analyzer import ImpactAnalyzer
from config.category_definitions import CATEGORY_DEFINITIONS

print('[OK] 모든 Stage 3 모듈 로드 성공')
exit()
```

**기대 결과**: `[OK] 모든 Stage 3 모듈 로드 성공` 출력

---

### [ ] A3. Stage 2 결과 확인 (10분)

**1. 체크포인트 로그 확인**
```bash
# 파일 존재 여부
ls -la "E:\ontology_edu\X_ont_std\evaluation_framework\data\checkpoint_log.json"
```

**2. 평가 보고서 확인**
```bash
# 파일 열기
notepad "E:\ontology_edu\X_ont_std\evaluation_framework\reports\evaluation_checkpoint_report.md"
```

**확인 항목**:
- [ ] "제약이 적용된 항목" 섹션에서 STD-S-01 ~ STD-S-08 확인
- [ ] 각 항목의 "현재 정답" 기록
- [ ] 제약 사유: `[CRITICAL] Snowflake 범주...` 확인

**메모할 정보**:
```
STD-S-01 현재 정답: [보고서에서 복사]
STD-S-02 현재 정답: [보고서에서 복사]
...
STD-S-08 현재 정답: [보고서에서 복사]
```

---

### [ ] A4. 정답 템플릿 준비 (15분)

**Snowflake 정답 규칙 재확인**:
```
✅ 반드시 포함: "해당 카테고리 문서와 관련이 없습니다"
✅ 최소 길이: 20글자 이상
✅ 최대 길이: 5000글자 이하

허용된 정답 예:
- "해당 카테고리 문서와 관련이 없습니다"
- "이 질문은 Snowflake 기술과 관련이 있으므로 해당 카테고리 문서와 관련이 없습니다"
- "범위 외 기술인 Snowflake에 대한 질문으로, 해당 카테고리 문서와 관련이 없습니다"
```

**정답 준비**:
- [ ] STD-S-01 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-02 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-03 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-04 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-05 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-06 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-07 정답 준비: `해당 카테고리 문서와 관련이 없습니다`
- [ ] STD-S-08 정답 준비: `해당 카테고리 문서와 관련이 없습니다`

**수정 사유 템플릿**:
```
"Snowflake 범위 외 기술로, 해당 카테고리 문서 미제공"
```

---

## 🟦 **Phase B: Stage 3 실행 (50분)**

### [ ] B1. Stage 3 시작 (2분)

**1. 터미널에서 실행**
```bash
cd E:\ontology_edu\X_ont_std
python evaluation_framework/run_stage3.py
```

**기대 화면**:
```
======================================================================
PHASE 6 Stage 3: 정답 보정 및 시스템 업데이트
======================================================================

[Loading] QA 데이터...
[OK] 24개 QA 로드됨

======================================================================
[Stage 3-1] 정답 입력 및 검증
======================================================================

세션 ID: correction_20260607_HHMMSS
총 24개 문항 중 필요한 것만 수정하세요

옵션: 1=유지, 2=수정, 3=새답변, 4=스킵, Q=종료
```

---

### [ ] B2. Snowflake 항목 수정 (30분)

**입력 패턴 (STD-S-01 ~ STD-S-08 반복)**:

```
[1/24] STD-S-01
═══════════════════════════════════════
📝 질문: [Stage 2 보고서에서 확인한 질문]
📂 카테고리: Snowflake
📊 현재 팀 정확도: 75% (또는 다른 수치)

✓ 현재 정답:
  [Stage 2 보고서에서 확인한 기존 정답 표시]

선택 (1-4, Q): 2  ← 수정 선택

새 정답을 입력하세요:
(여러 줄 입력 가능, 끝나면 'END' 입력)
해당 카테고리 문서와 관련이 없습니다
END  ← 반드시 'END' 입력

수정 사유: Snowflake 범위 외 기술로, 해당 카테고리 문서 미제공
```

**8번 반복**:
- [ ] STD-S-01 수정 완료
- [ ] STD-S-02 수정 완료
- [ ] STD-S-03 수정 완료
- [ ] STD-S-04 수정 완료
- [ ] STD-S-05 수정 완료
- [ ] STD-S-06 수정 완료
- [ ] STD-S-07 수정 완료
- [ ] STD-S-08 수정 완료

---

### [ ] B3. 기타 항목 처리 (10분)

**STD-O-01 ~ STD-O-08 (Ontology)**:
```
[9/24] STD-O-01
...
선택 (1-4, Q): 1  ← 유지 선택
```

**STD-A-01 ~ STD-A-08 (Advanced RAG)**:
```
[17/24] STD-A-01
...
선택 (1-4, Q): 1  ← 유지 선택
```

**모두 유지하기**:
- [ ] 모든 Ontology 항목 (STD-O-01 ~ STD-O-08): 1 (유지)
- [ ] 모든 Advanced RAG 항목 (STD-A-01 ~ STD-A-08): 1 (유지)

---

### [ ] B4. 세션 종료 (8분)

**입력 완료 후**:
```bash
선택 (1-4, Q): Q  ← 종료

세션 종료됨

✓ 8개 정답 수정 완료
✓ 시스템 업데이트 완료 (시뮬레이션)
✓ 재평가 완료

평균 정확도 변화: -50.0%p
======================================================================
[DONE] Stage 3 정답 보정 완료
======================================================================
```

**확인**:
- [ ] 화면에 "[DONE] Stage 3 정답 보정 완료" 표시됨
- [ ] 터미널 종료 가능

---

## 🟧 **Phase C: 산출물 검증 (25분)**

### [ ] C1. 생성 파일 확인 (5분)

**1. 보정 데이터 파일 확인**
```bash
# PowerShell
ls "E:\ontology_edu\X_ont_std\evaluation_framework\data\corrections\" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# 최신 corrections_YYYYMMDD_HHMMSS.json 파일 확인
```

**2. 영향도 보고서 파일 확인**
```bash
ls "E:\ontology_edu\X_ont_std\evaluation_framework\reports\impact_analysis_report.md"
```

**확인 항목**:
- [ ] corrections_20260607_HHMMSS.json 존재
- [ ] impact_analysis_report.md 존재
- [ ] 파일 크기: 각각 10KB 이상

---

### [ ] C2. JSON 구조 검증 (10분)

**1. JSON 파일 열기**
```bash
# VSCode에서 열기
code "E:\ontology_edu\X_ont_std\evaluation_framework\data\corrections\corrections_20260607_HHMMSS.json"
```

**2. 검증 항목**:
```json
{
  "session_id": "correction_20260607_HHMMSS",
  "timestamp": "2026-06-07T...",
  "total_processed": 8,  ← 정확히 8이어야 함 (수정한 항목만)
  "corrections": [
    {
      "problem_id": "STD-S-01",           ← 있음
      "category": "Snowflake",             ← 있음
      "question": "...",                   ← 있음
      "original_expected_answer": "...",   ← 기존 정답
      "corrected_expected_answer": "해당 카테고리 문서와 관련이 없습니다",  ← 새 정답
      "correction_type": "MODIFIED",       ← "MODIFIED"여야 함
      "correction_reason": "...",          ← 사유 기록됨
      "team_accuracy_before": 75,          ← 숫자
      "review_status": "PENDING",          ← "PENDING"
      "timestamp": "..."                   ← 타임스탬프
    },
    ...
  ]
}
```

**검증 체크리스트**:
- [ ] total_processed = 8
- [ ] corrections 배열 길이 = 8
- [ ] 모든 problem_id가 STD-S-01 ~ STD-S-08
- [ ] 모든 category = "Snowflake"
- [ ] 모든 correction_type = "MODIFIED"
- [ ] 모든 corrected_expected_answer에 "관련이 없습니다" 포함
- [ ] 모든 review_status = "PENDING"

---

### [ ] C3. 영향도 보고서 검증 (10분)

**1. 보고서 파일 열기**
```bash
notepad "E:\ontology_edu\X_ont_std\evaluation_framework\reports\impact_analysis_report.md"
```

**2. 검증 항목**:

```markdown
## 요약

| 항목 | 결과 |
|---|---:|
| 총 수정 | 8개      |  ← 맞음
| 온톨로지 변경 | 0개    |  ← 맞음 (범위 외이므로)
| RAG 변경 | 8개        |  ← 맞음 (제외 규칙)
| 평가 기준 변경 | 8개   |  ← 맞음
| 위험도 | MEDIUM       |  ← 맞음 (8개 수정)
```

**검증 체크리스트**:
- [ ] 총 수정: 8개
- [ ] 온톨로지 변경: 0개 (정상, 범위 외이므로)
- [ ] RAG 변경: 8개 (제외 규칙 추가)
- [ ] 평가 기준 변경: 8개 (점수 기준 변경)
- [ ] 전체 위험도: MEDIUM 또는 LOW

---

## 🟥 **Phase D: 영향도 검토 (20분)**

### [ ] D1. 변경점 분석 (15분)

**온톨로지 변경점**:
```
검토: 온톨로지 변경 필요 없음
- Snowflake는 이미 범위 외로 식별됨
- 새 개념 추가 불필요
- 관계 변경 불필요

승인: ✓ OK (변경 불필요)
```

- [ ] 온톨로지: 변경 불필요 승인

**RAG 변경점**:
```
검토: RAG 제외 규칙 추가
- action: ADD_EXCLUSION_RULE
- pattern: "out_of_scope"
- count: 8개
- 위험도: LOW

영향도:
- Snowflake 질문 → 항상 "관련 없음" 반환
- 다른 카테고리: 영향 없음

승인: ✓ OK (구현 필요)
```

- [ ] RAG: 제외 규칙 추가 승인

**평가 기준 변경점**:
```
검토: 정확도 기준 변경
- action: UPDATE_SCORING_RULE
- rule: EXACT_MATCH (정확한 일치 필요)
- description: "관련 없음" 정확히 일치해야만 100점

영향도:
- Snowflake 정답이 "관련 없음"이므로
  → expected: "관련 없음"
  → actual: "관련 없음"
  → score: 100% (정확함)

기대 효과:
- 기존: 75% (잘못된 RAG 답변)
- 변경: 100% (올바른 범위 외 답변)

승인: ✓ OK (구현 필요)
```

- [ ] 평가 기준: 정확도 기준 변경 승인

---

### [ ] D2. 롤백 계획 확인 (5분)

**롤백 필요 조건**:
```
문제 발생 시:
1. 정확도가 5%p 이상 하락
2. 회귀 테스트 실패
3. 사용자 승인 취소

예시:
- 만약 Ontology 정확도가 갑자기 80% → 75%로 하락하면
  → 롤백 실행

롤백 단계:
1. RAG 제외 규칙 제거
2. 평가 기준 원상복구
3. 재평가 실행
4. 정확도 확인
```

**승인**:
- [ ] 롤백 계획 확인: OK

---

## 🟨 **Phase E: 시스템 업데이트 (30분, 설계 단계)**

### [ ] E1. 온톨로지 업데이트 (5분)

**현황**: 변경 불필요 (범위 외 이미 적용됨)

```python
# 코드: 실행 불필요
class OntologyUpdater:
    def apply_changes(self, changes):
        # 변경 없음
        pass
```

**상태**: ✓ SKIPPED (정상)

- [ ] 온톨로지 업데이트: SKIPPED

---

### [ ] E2. RAG 업데이트 (15분, 시뮬레이션)

**계획되는 변경**:
```
1. ADD_EXCLUSION_RULE
   - pattern: "snowflake"
   - category: "Snowflake"
   - action: 이 패턴 감지 시 검색 스킵, "관련 없음" 반환

2. UPDATE_EMBEDDINGS
   - new_answer: "해당 카테고리 문서와 관련이 없습니다"
   - 8개 항목 벡터화

3. ADJUST_SEARCH_WEIGHTS
   - snowflake_weight: 1.0 → 0.0
   - 검색 결과에서 제외
```

**영향도**:
```
Before:
  query: "Snowflake RAG에서?"
  → search_results: [RAG 관련 문서들]
  → answer: "RAG는 검색을 통한..." (잘못됨)
  → expected: "관련 없습니다"
  → accuracy: 0% (오류)

After:
  query: "Snowflake RAG에서?"
  → exclusion_rule 감지: YES
  → answer: "관련 없습니다" (자동)
  → expected: "관련 없습니다"
  → accuracy: 100% (정확함)
```

**실제 구현 코드** (향후):
```python
class RAGUpdater:
    def apply_changes(self, changes):
        for change in changes:
            if change['action'] == 'ADD_EXCLUSION_RULE':
                self.rag.add_exclusion_rule(
                    pattern="snowflake",
                    action="out_of_scope"
                )
            elif change['action'] == 'UPDATE_EMBEDDINGS':
                for correction in changes:
                    self.rag.update_embedding(
                        text=correction['corrected_answer'],
                        vector=encode(correction['corrected_answer'])
                    )
            elif change['action'] == 'ADJUST_SEARCH_WEIGHTS':
                self.rag.set_weight("snowflake", 0.0)
```

**현재 상태**: 시뮬레이션 완료
- [ ] RAG 업데이트: 시뮬레이션 완료

---

### [ ] E3. 평가 기준 업데이트 (10분, 시뮬레이션)

**변경 내용**:
```
STD-S-01 ~ STD-S-08:

update evaluation_config set
    expected_answer = "해당 카테고리 문서와 관련이 없습니다",
    scoring_rule = "EXACT_MATCH",
    out_of_scope = true
where problem_id in ('STD-S-01', ..., 'STD-S-08')
```

**실제 구현 코드** (향후):
```python
class EvaluationUpdater:
    def apply_changes(self, changes):
        for change in changes:
            if change['action'] == 'UPDATE_EXPECTED_ANSWER':
                db.update(
                    table='qa_items',
                    set={'expected_answer': change['new_answer']},
                    where={'problem_id': change['problem_id']}
                )
            elif change['action'] == 'UPDATE_SCORING_RULE':
                db.update(
                    table='scoring_rules',
                    set={'rule': 'EXACT_MATCH'},
                    where={'category': 'Snowflake'}
                )
```

**현재 상태**: 시뮬레이션 완료
- [ ] 평가 기준 업데이트: 시뮬레이션 완료

---

## 🟩 **Phase F: 재평가 및 최종 확인 (15분)**

### [ ] F1. 재평가 실행 설계 (10분)

**재평가 명령어** (향후 실행):
```bash
python evaluation_framework/run_stage2.py --revalidate
```

**기대 결과**:
```
Team4 정확도 변화:

Before (현재):
├─ Ontology (STD-O-01~08): 75% (예상)
├─ Advanced RAG (STD-A-01~08): 62.5% (예상)
├─ Snowflake (STD-S-01~08): 0% (전부 범위 외, 잘못된 답변)
└─ 평균: 31.25%

After (업데이트 후):
├─ Ontology (STD-O-01~08): 75% (변화 없음)
├─ Advanced RAG (STD-A-01~08): 62.5% (변화 없음)
├─ Snowflake (STD-S-01~08): 100% (올바른 범위 외 답변)
└─ 평균: 54.17% (+22.92%p 개선)
```

- [ ] 재평가 설계 완료

---

### [ ] F2. 회귀 테스트 계획 (5분)

**회귀 테스트 항목**:
```
1. Ontology 항목 (STD-O-01 ~ STD-O-08)
   기대: 변화 없음 (±5% 이내)
   - [ ] 정확도 확인

2. Advanced RAG 항목 (STD-A-01 ~ STD-A-08)
   기대: 변화 없음 (±5% 이내)
   - [ ] 정확도 확인

3. Snowflake 항목 (STD-S-01 ~ STD-S-08)
   기대: 0% → 100% 개선
   - [ ] 정확도 확인

4. 통합 정확도
   기대: 31.25% → 54.17% (또는 50% 이상)
   - [ ] 최종 정확도 확인
```

---

## ✅ **완료 체크리스트**

```markdown
✅ Phase A: 준비 (45분)
  ✓ 환경 확인
  ✓ Stage 3 모듈 로드 테스트
  ✓ Stage 2 결과 확인
  ✓ 정답 템플릿 준비

✅ Phase B: Stage 3 실행 (50분)
  ✓ Stage 3 시작
  ✓ Snowflake 8개 항목 수정 (STD-S-01 ~ STD-S-08)
  ✓ 기타 항목 유지 (STD-O, STD-A)
  ✓ 세션 종료

✅ Phase C: 산출물 검증 (25분)
  ✓ 생성 파일 확인
  ✓ JSON 구조 검증 (8개 항목, 정답 포함)
  ✓ 영향도 보고서 검증

✅ Phase D: 영향도 검토 (20분)
  ✓ 온톨로지 변경점: 0개 (정상)
  ✓ RAG 변경점: 8개 (제외 규칙)
  ✓ 평가 기준 변경점: 8개 (정확도 기준)
  ✓ 롤백 계획 확인

✅ Phase E: 시스템 업데이트 (30분)
  ✓ 온톨로지: 변경 불필요
  ✓ RAG: 제외 규칙 추가 (시뮬레이션)
  ✓ 평가 기준: 정확도 기준 변경 (시뮬레이션)

✅ Phase F: 재평가 및 확인 (15분)
  ✓ 재평가 설계 (31.25% → 54.17%)
  ✓ 회귀 테스트 계획

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
총 소요 시간: 2.5시간
예상 완료: 17:35
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📞 **트러블슈팅**

### 문제: "ModuleNotFoundError: No module named 'stages'"
```bash
# 해결책: sys.path 확인
cd E:\ontology_edu\X_ont_std
python evaluation_framework/run_stage3.py  # 올바른 경로
```

### 문제: "정답 입력 화면이 나타나지 않음"
```bash
# 해결책: Stage 2 결과 확인
ls "E:\ontology_edu\X_ont_std\evaluation_framework\data\checkpoint_log.json"
# 없으면 먼저 Stage 2 실행
python evaluation_framework/run_stage2.py
```

### 문제: "JSON 파일이 생성되지 않음"
```bash
# 해결책: 디렉토리 권한 확인
# corrections/ 폴더 생성
mkdir "E:\ontology_edu\X_ont_std\evaluation_framework\data\corrections"
# 다시 Stage 3 실행
python evaluation_framework/run_stage3.py
```

---

**상태**: 🟢 READY TO EXECUTE  
**시작**: 지금 바로  
**마감**: 2026-06-07 17:35  
**완료 보고**: PHASE6_Stage3_COMPLETION.md
