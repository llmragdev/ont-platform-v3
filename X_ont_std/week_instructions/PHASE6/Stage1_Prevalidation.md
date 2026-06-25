# PHASE 6 Stage 1: 평가 전 검증 (Prevalidation)

**목표**: 평가 시작 전에 모든 Q&A 쌍이 유효한지 검증  
**기간**: Week 3-4 (07-12 ~ 07-22)  
**담당**: Claude  
**산출물**: validated_qa_set_v1.xlsx + qa_validation_report.md

---

## 📋 Stage 1 개요

### 검증 목적

Snowflake 평가 실패 같은 문제를 **평가 전에 미리 발견**

```
평가 전 검증 ← Stage 1
  · 예상답변이 문서 기반인가? ✓
  · 질문 범위가 명확한가? ✓
  · 카테고리와 일치하는가? ✓
    ↓ [검증 통과]
평가 실행
```

### 검증 체크리스트

```markdown
□ Q&A 일관성 검증
  ├─ 예상답변이 제공 문서에 있는가?
  ├─ 질문과 예상답변이 관련성 있는가?
  └─ 예상답변이 단편적이지 않은가?

□ 범위 명시성 검증
  ├─ 질문이 특정 기술을 언급하는가? (예: Snowflake)
  ├─ 예상답변이 그 기술에 대한 것인가?
  └─ 문서에 그 기술이 있는가?

□ 카테고리 일관성 검증
  ├─ 예상답변의 주제가 선언된 카테고리와 일치하는가?
  ├─ 문서가 그 카테고리를 포함하는가?
  └─ 다른 카테고리에 속하지 않는가?

□ 문서 기반 검증
  ├─ 예상답변이 일반 지식인가?
  ├─ 예상답변이 추정/해석인가?
  └─ 예상답변이 제공 문서에서 직접 추출 가능한가?
```

---

## 🔍 Stage 1 구현

### Task 1: Q&A 일관성 검증

**파일**: `stages/stage1_prevalidation/qa_validator.py`

```python
class QAConsistencyValidator:
    """Q&A 쌍의 일관성 검증"""
    
    def validate_pair(self, question, expected_answer, category, documents):
        """
        Q&A 쌍 검증
        
        Args:
            question: 질문 텍스트
            expected_answer: 예상 답변
            category: 카테고리 (Ontology, Advanced RAG, Snowflake, ...)
            documents: 평가 대상 문서 리스트
        
        Returns:
            {
                'is_valid': bool,
                'issues': [
                    {'type': 'ERROR|WARNING', 'message': str, 'severity': 'HIGH|MEDIUM|LOW'}
                ],
                'score': 0-100,
                'recommendation': str
            }
        """
        issues = []
        
        # 1. 길이 검증
        if len(question) < 20:
            issues.append({
                'type': 'WARNING',
                'message': '질문이 너무 짧음 (20글자 미만)',
                'severity': 'LOW'
            })
        
        if len(expected_answer) < 50:
            issues.append({
                'type': 'ERROR',
                'message': '예상답변이 너무 짧음 (50글자 미만)',
                'severity': 'HIGH'
            })
        
        # 2. 키워드 추출
        question_keywords = self.extract_keywords(question)
        answer_keywords = self.extract_keywords(expected_answer)
        doc_keywords = self.extract_doc_keywords(documents)
        
        # 3. 관련성 검증
        keyword_overlap = set(question_keywords) & set(answer_keywords)
        if not keyword_overlap:
            issues.append({
                'type': 'WARNING',
                'message': '질문과 예상답변의 키워드 겹침 없음',
                'severity': 'MEDIUM'
            })
        
        # 4. 문서 기반 검증
        answer_in_docs = self.check_answer_in_documents(
            expected_answer, documents
        )
        
        if not answer_in_docs:
            issues.append({
                'type': 'ERROR',
                'message': '예상답변이 제공 문서에 없음 - 일반 지식인가?',
                'severity': 'HIGH'
            })
        
        # 5. 문체 검증
        if self.is_too_generic(expected_answer):
            issues.append({
                'type': 'WARNING',
                'message': '예상답변이 너무 일반적임 (특이성 낮음)',
                'severity': 'MEDIUM'
            })
        
        # 점수 계산
        score = 100
        for issue in issues:
            if issue['severity'] == 'HIGH':
                score -= 30
            elif issue['severity'] == 'MEDIUM':
                score -= 15
            elif issue['severity'] == 'LOW':
                score -= 5
        
        return {
            'is_valid': len([i for i in issues if i['severity'] == 'HIGH']) == 0,
            'issues': issues,
            'score': max(0, score),
            'errors': len([i for i in issues if i['type'] == 'ERROR']),
            'warnings': len([i for i in issues if i['type'] == 'WARNING']),
            'recommendation': self._recommend(issues)
        }
    
    def _recommend(self, issues):
        """권장사항 생성"""
        if not issues:
            return "✓ 검증 통과"
        
        high_severity = [i for i in issues if i['severity'] == 'HIGH']
        if high_severity:
            return f"❌ {len(high_severity)}개 심각한 문제 수정 필요"
        
        return "⚠️ 경고 항목 검토 권장"
```

### Task 2: 범위 명시성 검증

**파일**: `stages/stage1_prevalidation/scope_analyzer.py`

```python
class ScopeAnalyzer:
    """질문과 답변의 범위 일관성 검증"""
    
    def analyze_scope(self, question, expected_answer, category):
        """
        범위 분석
        
        예: 질문에 "Snowflake"가 있으면
           1. 예상답변도 Snowflake여야 함
           2. 또는 "관련 없음"이어야 함
        """
        issues = []
        
        # 특정 기술 언급 감지
        specific_techs = self._detect_specific_mentions(question)
        
        for tech in specific_techs:
            # 예상답변에 같은 기술이 있는가?
            if tech.lower() not in expected_answer.lower():
                # 그럼 "관련 없음"이어야 함
                if not self._is_out_of_scope_answer(expected_answer):
                    issues.append({
                        'type': 'ERROR',
                        'message': f'질문에 "{tech}"가 있으나 답변에 없음. '
                                  f'"관련 없음"이거나 "{tech}"에 대한 답변이어야 함',
                        'severity': 'HIGH',
                        'detected_tech': tech
                    })
        
        return {
            'has_scope_issues': len(issues) > 0,
            'issues': issues,
            'specific_mentions': specific_techs
        }
    
    def _detect_specific_mentions(self, question):
        """질문에서 특정 기술 언급 감지"""
        specific_techs = [
            'Snowflake', 'Elasticsearch', 'MongoDB', 'PostgreSQL',
            'Kafka', 'Spark', 'Hadoop', 'CUDA', 'TensorFlow'
        ]
        
        found = [tech for tech in specific_techs 
                if tech.lower() in question.lower()]
        return found
    
    def _is_out_of_scope_answer(self, answer):
        """답변이 "관련 없음"을 명시하는가?"""
        out_of_scope_phrases = [
            '관련이 없습니다',
            '해당 카테고리',
            '관련 없음',
            '포함되지 않음',
            '다루지 않음'
        ]
        
        return any(phrase in answer for phrase in out_of_scope_phrases)
```

### Task 3: 카테고리 일관성 검증

**파일**: `stages/stage1_prevalidation/category_validator.py`

```python
class CategoryConsistencyValidator:
    """카테고리 일관성 검증"""
    
    def validate_category(self, question, expected_answer, 
                         declared_category, category_definitions):
        """
        카테고리 일관성 검증
        
        예: Snowflake 질문 → Snowflake 카테고리여야 함
        """
        issues = []
        
        # 1. 답변에서 카테고리 추론
        inferred_category = self._infer_category(
            expected_answer, category_definitions
        )
        
        if inferred_category != declared_category:
            issues.append({
                'type': 'WARNING',
                'message': f'예상답변이 {inferred_category} 범주로 추론됨 '
                          f'(선언: {declared_category})',
                'severity': 'MEDIUM',
                'inferred': inferred_category,
                'declared': declared_category
            })
        
        # 2. 질문에서 카테고리 추론
        question_category = self._infer_category_from_question(
            question, category_definitions
        )
        
        if question_category and question_category != declared_category:
            issues.append({
                'type': 'ERROR',
                'message': f'질문이 {question_category} 범주임에도 '
                          f'{declared_category}로 선언됨',
                'severity': 'HIGH',
                'question_suggests': question_category
            })
        
        # 3. 카테고리별 필수 개념 검증
        required_concepts = category_definitions[declared_category]['required_concepts']
        answer_has_concepts = any(
            concept.lower() in expected_answer.lower()
            for concept in required_concepts
        )
        
        if not answer_has_concepts:
            issues.append({
                'type': 'WARNING',
                'message': f'{declared_category} 범주의 필수 개념이 '
                          f'예상답변에 없음',
                'severity': 'MEDIUM',
                'required_concepts': required_concepts
            })
        
        return {
            'is_consistent': len([i for i in issues if i['severity'] == 'HIGH']) == 0,
            'issues': issues,
            'inferred_category': inferred_category,
            'declared_category': declared_category
        }
```

---

## 📊 Stage 1 산출 방식

### 1. 검증 결과 저장

```python
# evaluation_framework/data/qa_pairs/qa_validation_log.json

{
  "validation_session_id": "validation_20260615_claude",
  "timestamp": "2026-06-15T10:00:00Z",
  "total_qa_pairs": 24,
  
  "validation_results": [
    {
      "problem_id": "STD-O-01",
      "category": "Ontology",
      "question": "온톨로지 기반 질의응답에서...",
      "expected_answer": "온톨로지는 도메인 개념을...",
      
      "consistency_check": {
        "is_valid": true,
        "score": 95,
        "issues": []
      },
      
      "scope_check": {
        "has_scope_issues": false,
        "specific_mentions": [],
        "issues": []
      },
      
      "category_check": {
        "is_consistent": true,
        "inferred_category": "Ontology",
        "declared_category": "Ontology",
        "issues": []
      },
      
      "overall_score": 95,
      "validation_status": "PASS",
      "review_status": "APPROVED"
    },
    
    {
      "problem_id": "STD-S-01",
      "category": "Snowflake",
      "question": "Snowflake RAG에서...",
      "expected_answer": "[원본 잘못된 답변]",
      
      "consistency_check": {
        "is_valid": false,
        "score": 30,
        "issues": [
          {
            "type": "ERROR",
            "message": "예상답변이 제공 문서에 없음",
            "severity": "HIGH"
          }
        ]
      },
      
      "scope_check": {
        "has_scope_issues": true,
        "specific_mentions": ["Snowflake"],
        "issues": [
          {
            "type": "ERROR",
            "message": "Snowflake 문서가 없는데 답변 요구",
            "severity": "HIGH"
          }
        ]
      },
      
      "category_check": {
        "is_consistent": false,
        "issues": [
          {
            "type": "ERROR",
            "message": "Snowflake 범주에 필수 문서 없음",
            "severity": "HIGH"
          }
        ]
      },
      
      "overall_score": 15,
      "validation_status": "FAIL",
      "required_action": "MODIFY_EXPECTED_ANSWER",
      "suggested_fix": "해당 카테고리 문서와 관련이 없습니다"
    }
  ],
  
  "summary": {
    "total_validated": 24,
    "passed": 20,
    "failed": 4,
    "pass_rate": "83.3%",
    "critical_issues": [
      "STD-S-01 ~ STD-S-08 (Snowflake 범주 전체 실패)"
    ]
  }
}
```

### 2. 마크다운 보고서

```markdown
# Q&A 검증 보고서

생성일: 2026-06-15
대상: 24개 문항

## 요약

| 항목 | 결과 |
|---|---:|
| 총 문항 | 24 |
| 검증 통과 | 20 (83.3%) |
| 검증 실패 | 4 (16.7%) |

## 검증 실패 항목

### STD-S-01 ~ STD-S-08 (Snowflake 범주)

**문제**: Snowflake 문서가 없는데 기술적 답변 요구

**현재 상태**:
- 예상답변: "RAG 답변 기준에 대한..." ❌
- 제공 문서: Snowflake 관련 없음

**권장사항**:
- 예상답변 수정: "해당 카테고리 문서와 관련이 없습니다"
- 이유: Snowflake 기술 문서가 평가 범위에 없음

## 검증 통과 항목

### STD-O-01 ~ STD-O-05, STD-A-01 ~ STD-A-11

모두 검증 통과 ✓
- 예상답변이 제공 문서에 있음
- 카테고리 일치함
- 범위가 명확함

## 조치 사항

1. [수정] STD-S-01 ~ STD-S-08 예상답변 수정
2. [재검증] 수정 후 재검증 실행
3. [승인] 모든 항목 검증 통과 후 평가 진행
```

---

## ✅ Stage 1 완료 조건

```markdown
✓ 모든 Q&A 쌍 검증 완료
✓ 검증 실패 항목 수정 완료
✓ 재검증 통과 (100% 통과율)
✓ 검증 보고서 작성 완료
✓ validated_qa_set_v1.xlsx 생성
```

---

**Stage 1 산출물**: 
- ✅ `qa_validator.py` (검증 로직)
- ✅ `qa_validation_report.md` (검증 보고서)
- ✅ `validated_qa_set_v1.xlsx` (검증된 Q&A)
- ✅ `qa_validation_log.json` (검증 로그)

**예상 완료일**: 2026-07-22
