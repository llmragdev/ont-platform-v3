# PHASE4 평가 개선 계획: Snowflake 교훈 및 정답 보정 메커니즘

**작성일**: 2026-06-07  
**목적**: ont_platform v4 평가에서 발견된 Snowflake 문제를 교훈 삼아 질의응답 정확도 향상  
**대상**: Claude (평가 담당자)  
**범위**: 현재 평가 개선 + 미래 평가 자동화

---

## 📊 Part 1: 현재 문제 분석

### 1.1 Snowflake 평가 실패 원인

```
발견된 문제:
┌─────────────────────────────────────────────────────────────┐
│ 1. 설계 결함: "문서 내용만 사용" 제약이 없음                 │
│ 2. 온톨로지 부재: Snowflake 개념이 온톨로지에 미포함        │
│ 3. LLM 보정 부재: Gemini LLM이 일반 RAG로 "해석" 후 답변    │
│ 4. 검증 로직 부재: 카테고리별 필수 개념 검증 없음            │
└─────────────────────────────────────────────────────────────┘

결과:
- Team4 (ont_platform v4): 31.25% (Snowflake)
- 전체 점수: 67.50% → 58.54% (수정 후, -8.96%p)
- 순위: 2위 → 3위 하락
```

### 1.2 근본 원인: 설계 관점

| 계층 | 문제 | 영향 |
|---|---|---|
| **평가 설계** | 예상답변이 질문과 모순 | 평가 기준 왜곡 |
| **온톨로지** | Snowflake 개념 미포함 | 시스템이 관련 없음 감지 불가 |
| **검색** | 일반 개념(RAG)으로만 검색 | 잘못된 근거 제시 |
| **LLM 판단** | "문서 있음 = 답변 가능" 가정 | 범위 외 질문 답변 |
| **검증** | 사후 검증 프로세스 없음 | 오류 누적 |

---

## 🎯 Part 2: 질의응답 정확도 향상 계획

### 2.1 3단계 개선 전략

```
┌──────────────────────────────────────────────────────────┐
│ Stage 1: 평가 설계 검증 (평가 전)                        │
├──────────────────────────────────────────────────────────┤
│ ✓ 예상답변 검증: 질문과 일관성 확인                     │
│ ✓ 카테고리 정의: 범위 내/외 명시                        │
│ ✓ 제약사항 명시: "문서에만 기반" 원칙 정의              │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Stage 2: 평가 실행 중 검증 (평가 진행)                  │
├──────────────────────────────────────────────────────────┤
│ ✓ 온톨로지 검증: 필수 개념 존재 확인                    │
│ ✓ 범위 검증: 카테고리별 제약 자동 적용                  │
│ ✓ 근거 검증: 검색 근거의 관련성 확인                    │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ Stage 3: 평가 후 정답 보정 (평가 완료 후)               │
├──────────────────────────────────────────────────────────┤
│ ✓ 정답 입력: 실제 정답 피드백 수집                      │
│ ✓ 시스템 반영: 온톨로지/RAG 업데이트                    │
│ ✓ 재평가: 보정 후 점수 재계산                           │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Stage 1: 평가 설계 검증

#### Task 1-1: 예상답변 검증 프로세스

**목표**: 평가 전에 모든 Q&A쌍이 유효한지 확인

```python
# 구현: validate_qa_consistency.py

def validate_question_answer_pair(question, expected_answer, category, documents):
    """
    질문과 예상답변의 일관성 검증
    
    검증 항목:
    1. 예상답변이 제공 문서에서 답변 가능한가?
    2. 질문에서 요구하는 범위가 명확한가?
    3. 카테고리와 질문이 일치하는가?
    4. 예상답변의 깊이가 적절한가?
    """
    issues = []
    
    # 1. 문서 범위 검증
    answer_keywords = extract_key_terms(expected_answer)
    doc_keywords = extract_doc_keywords(documents)
    
    if not has_overlap(answer_keywords, doc_keywords):
        issues.append({
            'type': 'ANSWER_OUT_OF_SCOPE',
            'severity': 'ERROR',
            'message': f'예상답변의 핵심 개념이 문서에 없음: {answer_keywords}'
        })
    
    # 2. 범주 일관성 검증
    answer_category = infer_category(expected_answer)
    if answer_category != category:
        issues.append({
            'type': 'CATEGORY_MISMATCH',
            'severity': 'WARNING',
            'message': f'예상답변이 {answer_category} 범주로 추론됨 (선언: {category})'
        })
    
    # 3. 범위 명시성 검증
    if 'snowflake' in question.lower():
        if 'snowflake' not in expected_answer.lower() and \
           'not' not in expected_answer.lower() and \
           'none' not in expected_answer.lower():
            issues.append({
                'type': 'SCOPE_AMBIGUITY',
                'severity': 'ERROR',
                'message': '특정 기술 언급 있으나 범위 외 가능성 있음'
            })
    
    return {
        'is_valid': len([i for i in issues if i['severity'] == 'ERROR']) == 0,
        'issues': issues,
        'recommendation': recommend_fix(issues) if issues else None
    }

# 평가 시작 전 실행
validation_report = validate_all_qa_pairs(
    qa_file='data/3팀_정확도_비교.xlsx',
    documents=provided_docs,
    output_file='reports/qa_validation_report.md'
)

if validation_report['error_count'] > 0:
    print(f"경고: {validation_report['error_count']}개의 Q&A 쌍에 문제 발견")
    print("평가를 진행하기 전에 수정하세요.")
```

#### Task 1-2: 카테고리별 범위 정의

**목표**: 평가 대상 범위를 명확히 정의

```python
# config/evaluation_categories.py

CATEGORY_DEFINITIONS = {
    "Ontology": {
        "scope": "온톨로지 개념, 온톨로지 기반 시스템, 지식 그래프",
        "required_concepts": [
            "ontology", "concept", "relationship", "knowledge_graph",
            "semantic", "rdf", "owl", "entity", "class", "property"
        ],
        "required_documents": [
            "NLP - [03] 온톨로지이질성문제...",
            "NLP - [07] 온톨로지 학습 기반...",
            "국방 - [01] 온톨로지와지식그래프..."
        ],
        "out_of_scope": ["Snowflake", "Elasticsearch", "특정 DB 기술"],
    },
    
    "Advanced RAG": {
        "scope": "RAG 기법, 검색 기반 생성, 메타데이터 활용",
        "required_concepts": [
            "rag", "retrieval", "augmented", "generation", "embedding",
            "vector", "metadata", "retrieval_model", "ranking"
        ],
        "required_documents": [
            "NLP - [06] 정적 언어모델부터...",
            "NLP - [08] 한국근대문인 데이터베이스..."
        ],
        "out_of_scope": ["Snowflake", "일반 DB 설계"],
    },
    
    "Snowflake": {
        "scope": "Snowflake 플랫폼 관련 기술",
        "required_concepts": ["snowflake", "snowflake_rag", "snowflake_specific"],
        "required_documents": [],  # Snowflake 문서 없음
        "fallback": "해당 카테고리 문서와 관련이 없습니다",
    }
}

def validate_question_scope(question, category):
    """질문이 카테고리 범위 내인지 확인"""
    definition = CATEGORY_DEFINITIONS[category]
    
    # 범위 외 키워드 검사
    out_of_scope_found = [
        kw for kw in definition['out_of_scope']
        if kw.lower() in question.lower()
    ]
    
    if out_of_scope_found:
        return {
            'is_valid': False,
            'reason': f'범위 외 키워드: {out_of_scope_found}',
            'recommendation': 'Q&A 쌍 재검토 필요'
        }
    
    return {'is_valid': True}
```

### 2.3 Stage 2: 평가 실행 중 검증

#### Task 2-1: 온톨로지 기반 범위 검증

**목표**: 평가 중에 자동으로 범위 제약 적용

```python
# src/ontology_constraint_enforcer.py

class OntologyConstraintEnforcer:
    """온톨로지 기반 답변 범위 제약 적용"""
    
    def __init__(self, ontology, category_definitions):
        self.ontology = ontology
        self.categories = category_definitions
    
    def validate_answer_scope(self, question, category, retrieved_docs):
        """
        답변 범위 검증:
        1. 카테고리의 필수 개념이 온톨로지에 있는가?
        2. 검색된 문서가 해당 카테고리에 속하는가?
        3. 답변이 범위를 벗어나지 않는가?
        """
        category_def = self.categories[category]
        
        # 1. 필수 개념 검증
        required_concepts = category_def['required_concepts']
        ontology_concepts = [c['name'] for c in self.ontology.get_concepts()]
        
        has_required = any(
            concept in ontology_concepts 
            for concept in required_concepts
        )
        
        if not has_required:
            return {
                'should_answer': False,
                'reason': f'{category} 범주의 필수 개념이 온톨로지에 없음',
                'fallback_answer': category_def.get('fallback', 'N/A')
            }
        
        # 2. 검색 문서 검증
        doc_categories = [self.get_doc_category(doc) for doc in retrieved_docs]
        if not any(doc_category == category for doc_category in doc_categories):
            return {
                'should_answer': False,
                'reason': f'{category} 카테고리 문서 없음',
                'retrieved_categories': doc_categories,
                'fallback_answer': category_def.get('fallback')
            }
        
        return {'should_answer': True}
    
    def enforce_constraints_on_response(self, response, question, category):
        """
        생성된 응답에 제약 적용:
        - 범위 검증
        - 필수 개념 확인
        - 근거 검증
        """
        validation = self.validate_answer_scope(
            question, category, response['sources']
        )
        
        if not validation['should_answer']:
            # 범위 외 질문 → 기본 답변 반환
            return {
                **response,
                'answer': validation['fallback_answer'],
                'accuracy': 100 if validation['fallback_answer'] in response['answer'] else 0,
                'constrained': True,
                'constraint_reason': validation['reason']
            }
        
        return {**response, 'constrained': False}
```

#### Task 2-2: 자동 검증 체크포인트

```python
# src/evaluation_checkpoints.py

class EvaluationCheckpoints:
    """평가 과정의 검증 지점"""
    
    def checkpoint_1_answer_generation(self, question, category, answer):
        """
        Checkpoint 1: 답변 생성 직후
        - 답변이 범위를 벗어나지 않았는가?
        - 필수 근거가 있는가?
        """
        checks = {
            'has_fallback_answer': '관련이 없습니다' in answer,
            'has_sources': len(sources) > 0,
            'sources_are_relevant': self.validate_source_relevance(answer, sources),
            'answer_length_reasonable': 50 < len(answer) < 2000,
        }
        
        if checks['has_fallback_answer'] and not checks['sources_are_relevant']:
            return {'status': 'PASS', 'action': 'USE_FALLBACK'}
        
        if not checks['sources_are_relevant']:
            return {'status': 'FAIL', 'action': 'REVIEW_NEEDED'}
        
        return {'status': 'PASS', 'action': 'CONTINUE'}
    
    def checkpoint_2_accuracy_scoring(self, expected_answer, actual_answer, sources):
        """
        Checkpoint 2: 정확도 채점 전
        - 기대값과 실제값이 범주가 같은가?
        - 채점 기준이 적절한가?
        """
        if '관련이 없습니다' in expected_answer:
            if '관련이 없습니다' in actual_answer:
                return {'accuracy': 100, 'method': 'EXACT_MATCH'}
            elif self.contains_technical_answer(actual_answer):
                return {'accuracy': 0, 'method': 'SCOPE_VIOLATION'}
            else:
                return {'accuracy': 50, 'method': 'PARTIAL_MATCH'}
        
        # 일반 답변 채점
        similarity = self.calculate_semantic_similarity(expected_answer, actual_answer)
        return {'accuracy': int(similarity * 100), 'method': 'SEMANTIC_SIMILARITY'}
    
    def checkpoint_3_qa_validity(self, qa_pair_id, expected_answer, actual_answer, accuracy):
        """
        Checkpoint 3: 평가 결과 검증
        - 이 Q&A 쌍이 유효한가?
        - 정답이 정말 정답인가?
        """
        flags = {
            'expected_answer_valid': self.is_valid_answer(expected_answer),
            'actual_answer_relevant': self.is_relevant(actual_answer),
            'accuracy_suspicious': accuracy > 80 and '관련이 없습니다' in expected_answer,
        }
        
        if flags['accuracy_suspicious']:
            return {
                'status': 'FLAGGED_FOR_REVIEW',
                'reason': '범위 외 질문에 높은 점수 → 검토 필요'
            }
        
        return {'status': 'VALID'}
```

---

## 🔄 Part 3: 테스트 후 정답 보정 메커니즘

### 3.1 정답 보정 프로세스 개요

```
평가 완료
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 정답 입력 인터페이스                                │
│ - 각 문항별 정답 확인 / 수정                                │
│ - 정답 근거 제시                                            │
│ - 카테고리별 검토                                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 시스템 반영 분석                                    │
│ - 어느 부분을 업데이트할 것인가?                           │
│   · 온톨로지? (개념/관계)                                  │
│   · RAG DB? (문서/임베딩)                                  │
│   · 평가 기준? (정답 정의)                                 │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: 시스템 업데이트                                     │
│ - 온톨로지에 새 개념/관계 추가                              │
│ - 벡터 DB에 문서 추가 / 임베딩 갱신                        │
│ - 평가 기준 데이터 업데이트                                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: 재평가                                              │
│ - 보정된 시스템으로 같은 질문 재평가                        │
│ - 정확도 개선 확인                                         │
│ - 회귀(Regression) 검증                                    │
└─────────────────────────────────────────────────────────────┘
    ↓
정답 보정 완료 + 시스템 개선
```

### 3.2 Step 1: 정답 입력 인터페이스

#### 3.2.1 CLI 기반 정답 입력

```python
# tools/answer_correction_cli.py

class AnswerCorrectionCLI:
    """정답 보정 대화형 인터페이스"""
    
    def run_correction_session(self, evaluation_excel_path):
        """
        평가 결과 기반 정답 보정 세션 시작
        """
        wb = load_workbook(evaluation_excel_path)
        ws = wb['문항별 비교 상세']
        
        flagged_items = self.identify_flagged_items(ws)
        
        for item_idx, item in enumerate(flagged_items, 1):
            print(f"\n{'='*70}")
            print(f"[{item_idx}/{len(flagged_items)}] {item['problem_id']}")
            print(f"{'='*70}")
            
            # 1. 현재 상태 표시
            print(f"\n📝 질문: {item['question'][:100]}...")
            print(f"\n✓ 현재 예상답변: {item['current_expected'][:100]}...")
            print(f"정확도: Team0={item['team0_acc']}%, Team1={item['team1_acc']}%, "
                  f"Team2={item['team2_acc']}%, Team4={item['team4_acc']}%")
            
            # 2. 정답 입력
            print(f"\n🔧 옵션:")
            print("  1) 현재 정답 유지")
            print("  2) 예상답변 수정")
            print("  3) 새로운 정답 입력")
            print("  4) 스킵")
            
            choice = input("\n선택: ").strip()
            
            if choice == '1':
                # 유지
                item['correction_status'] = 'KEPT'
                
            elif choice == '2':
                # 예상답변 수정
                print("\n새로운 예상답변을 입력하세요 (여러 줄, 끝나면 'END'):")
                new_answer = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    new_answer.append(line)
                
                new_answer_text = '\n'.join(new_answer)
                
                # 수정 내용 검증
                validation = self.validate_answer_correction(
                    question=item['question'],
                    old_answer=item['current_expected'],
                    new_answer=new_answer_text,
                    category=item['category']
                )
                
                if validation['is_valid']:
                    item['new_expected_answer'] = new_answer_text
                    item['correction_status'] = 'MODIFIED'
                    item['correction_reason'] = input("\n수정 사유: ")
                    print("✅ 저장됨")
                else:
                    print(f"⚠️ 검증 실패: {validation['message']}")
                    item['correction_status'] = 'VALIDATION_FAILED'
            
            elif choice == '3':
                # 새로운 정답 제시
                print("\n예상답변과 다른 새로운 정답을 입력하세요:")
                new_answer = input().strip()
                
                item['new_answer'] = new_answer
                item['reason_for_new_answer'] = input("새 정답 근거: ")
                item['correction_status'] = 'NEW_ANSWER'
            
            elif choice == '4':
                item['correction_status'] = 'SKIPPED'
        
        # 보정 결과 저장
        self.save_correction_results(flagged_items)
        return flagged_items
```

#### 3.2.2 구조화된 정답 보정 데이터

```python
# 저장 형식: corrections/qa_corrections_20260607.json

{
  "session_id": "correction_20260607_claude",
  "timestamp": "2026-06-07T16:00:00Z",
  "corrections": [
    {
      "problem_id": "STD-S-01",
      "category": "Snowflake",
      "question": "Snowflake RAG에서...",
      
      "original_expected_answer": "RAG 답변 기준에 대한...",
      "correction_type": "MODIFIED",  # MODIFIED | NEW_ANSWER | KEPT
      
      "new_expected_answer": "해당 카테고리 문서와 관련이 없습니다",
      "correction_reason": "Snowflake 문서 미제공 - 범위 외",
      
      "evidence": {
        "supporting_docs": [],
        "ontology_analysis": "Snowflake 개념 온톨로지에 미포함",
        "team_performance_before": {
          "Team0": 50, "Team1": 60, "Team2": 50, "Team4": 75
        }
      },
      
      "impact_analysis": {
        "teams_affected": ["Team0", "Team1", "Team2", "Team4"],
        "expected_accuracy_change": {
          "Team0": {"before": 50, "after": 75},
          "Team1": {"before": 60, "after": 75},
          "Team2": {"before": 50, "after": 75},
          "Team4": {"before": 75, "after": 75}
        }
      },
      
      "review_status": "APPROVED",
      "reviewed_by": "User",
      "review_timestamp": "2026-06-07T16:05:00Z"
    },
    ...
  ]
}
```

### 3.3 Step 2: 시스템 반영 분석

#### 3.3.1 영향도 분석

```python
# src/impact_analyzer.py

class ImpactAnalyzer:
    """정답 보정의 시스템 영향도 분석"""
    
    def analyze_correction_impact(self, correction):
        """
        정답 보정이 어느 부분을 변경해야 하는지 분석
        """
        impact = {
            'ontology_updates': [],
            'rag_updates': [],
            'evaluation_criteria_updates': [],
            'estimated_accuracy_improvement': 0
        }
        
        # 1. 온톨로지 분석
        if correction['correction_type'] in ['MODIFIED', 'NEW_ANSWER']:
            old_concepts = self.extract_concepts(correction['original_expected_answer'])
            new_concepts = self.extract_concepts(correction['new_expected_answer'])
            
            # 제거할 개념
            removed = set(old_concepts) - set(new_concepts)
            if removed:
                impact['ontology_updates'].append({
                    'action': 'REMOVE_CONCEPTS',
                    'concepts': list(removed),
                    'reason': correction['correction_reason']
                })
            
            # 추가할 개념
            added = set(new_concepts) - set(old_concepts)
            if added:
                impact['ontology_updates'].append({
                    'action': 'ADD_CONCEPTS',
                    'concepts': list(added),
                    'reason': correction['correction_reason']
                })
        
        # 2. RAG DB 분석
        if '관련이 없습니다' in correction['new_expected_answer']:
            # 범위 외 질문 → 검색 범위 제약 필요
            impact['rag_updates'].append({
                'action': 'ADD_EXCLUSION_RULE',
                'pattern': self.extract_exclusion_pattern(correction['question']),
                'category': correction['category']
            })
        else:
            # 새로운 개념이 추가됨 → 임베딩 갱신 필요
            impact['rag_updates'].append({
                'action': 'UPDATE_EMBEDDINGS',
                'keywords': self.extract_keywords(correction['new_expected_answer']),
                'category': correction['category']
            })
        
        # 3. 정확도 개선 추정
        improvement = correction['impact_analysis']['expected_accuracy_change']
        total_improvement = sum(
            v['after'] - v['before'] 
            for v in improvement.values()
        ) / len(improvement)
        impact['estimated_accuracy_improvement'] = total_improvement
        
        return impact
    
    def estimate_system_impact(self, corrections_list):
        """전체 보정의 시스템 영향도 통합 분석"""
        consolidated = {
            'total_corrections': len(corrections_list),
            'ontology_changes': {
                'concepts_to_add': set(),
                'concepts_to_remove': set(),
                'relationships_to_add': []
            },
            'rag_changes': {
                'embeddings_to_update': [],
                'exclusion_rules_to_add': []
            },
            'estimated_overall_improvement': 0,
            'risk_assessment': []
        }
        
        for correction in corrections_list:
            impact = self.analyze_correction_impact(correction)
            
            # 온톨로지 변경 통합
            for update in impact['ontology_updates']:
                if update['action'] == 'ADD_CONCEPTS':
                    consolidated['ontology_changes']['concepts_to_add'].update(
                        update['concepts']
                    )
                elif update['action'] == 'REMOVE_CONCEPTS':
                    consolidated['ontology_changes']['concepts_to_remove'].update(
                        update['concepts']
                    )
            
            # RAG 변경 통합
            consolidated['rag_changes']['embeddings_to_update'].extend(
                [u for u in impact['rag_updates'] 
                 if u['action'] == 'UPDATE_EMBEDDINGS']
            )
            consolidated['rag_changes']['exclusion_rules_to_add'].extend(
                [u for u in impact['rag_updates'] 
                 if u['action'] == 'ADD_EXCLUSION_RULE']
            )
            
            # 개선도 누적
            consolidated['estimated_overall_improvement'] += \
                impact['estimated_accuracy_improvement']
        
        # 위험도 평가
        consolidated['risk_assessment'] = self.assess_risks(consolidated)
        
        return consolidated
```

### 3.4 Step 3: 시스템 업데이트

#### 3.4.1 온톨로지 업데이트

```python
# src/ontology_updater.py

class OntologyUpdater:
    """온톨로지 자동 업데이트"""
    
    def apply_ontology_changes(self, impact, ontology_graph):
        """
        분석된 영향도를 바탕으로 온톨로지 업데이트
        """
        changes_log = []
        
        # 1. 개념 추가
        for concept in impact['ontology_changes']['concepts_to_add']:
            # 개념을 온톨로지에 추가
            ontology_graph.add_concept(
                name=concept,
                category=self.infer_category(concept),
                source='answer_correction',
                timestamp=datetime.now()
            )
            changes_log.append({
                'action': 'ADD_CONCEPT',
                'concept': concept,
                'status': 'SUCCESS'
            })
        
        # 2. 개념 제거
        for concept in impact['ontology_changes']['concepts_to_remove']:
            # 고아 개념 확인 (다른 곳에서 참조되지 않는지 확인)
            if self.is_safe_to_remove(concept, ontology_graph):
                ontology_graph.remove_concept(concept)
                changes_log.append({
                    'action': 'REMOVE_CONCEPT',
                    'concept': concept,
                    'status': 'SUCCESS'
                })
            else:
                changes_log.append({
                    'action': 'REMOVE_CONCEPT',
                    'concept': concept,
                    'status': 'SKIPPED',
                    'reason': '다른 관계에서 참조됨'
                })
        
        # 3. 관계 추가
        for rel in impact['ontology_changes']['relationships_to_add']:
            ontology_graph.add_relationship(
                source=rel['source'],
                target=rel['target'],
                relationship_type=rel['type'],
                source_correction=True
            )
            changes_log.append({
                'action': 'ADD_RELATIONSHIP',
                'relationship': f"{rel['source']} --{rel['type']}--> {rel['target']}",
                'status': 'SUCCESS'
            })
        
        return changes_log
    
    def validate_ontology_consistency(self, ontology_graph):
        """
        업데이트 후 온톨로지 일관성 검증
        """
        issues = []
        
        # 순환 참조 검사
        cycles = self.find_cycles(ontology_graph)
        if cycles:
            issues.append({
                'type': 'CIRCULAR_REFERENCE',
                'cycles': cycles
            })
        
        # 고아 노드 검사
        orphans = self.find_orphan_nodes(ontology_graph)
        if orphans:
            issues.append({
                'type': 'ORPHAN_NODES',
                'nodes': orphans
            })
        
        return {
            'is_consistent': len(issues) == 0,
            'issues': issues
        }
```

#### 3.4.2 RAG 임베딩 업데이트

```python
# src/rag_updater.py

class RAGUpdater:
    """RAG DB 자동 업데이트"""
    
    def update_embeddings(self, rag_changes, embedding_model):
        """
        새로운 개념과 키워드의 임베딩 계산 및 저장
        """
        update_log = []
        
        for embedding_update in rag_changes['embeddings_to_update']:
            keywords = embedding_update['keywords']
            category = embedding_update['category']
            
            # 각 키워드마다 임베딩 계산
            for keyword in keywords:
                embedding = embedding_model.encode(keyword)
                
                # 벡터 DB에 저장
                vector_id = self.save_embedding(
                    keyword=keyword,
                    embedding=embedding,
                    category=category,
                    source='answer_correction'
                )
                
                update_log.append({
                    'keyword': keyword,
                    'category': category,
                    'vector_id': vector_id,
                    'status': 'SUCCESS'
                })
        
        return update_log
    
    def add_exclusion_rules(self, rag_changes):
        """
        범위 외 질문을 감지하는 제외 규칙 추가
        
        예: Snowflake 질문은 해당 카테고리 문서가 없으므로
            검색 전에 자동으로 "관련 없음" 반환
        """
        rules_log = []
        
        for rule in rag_changes['exclusion_rules_to_add']:
            exclusion_rule = {
                'pattern': rule['pattern'],
                'category': rule['category'],
                'action': 'RETURN_OUT_OF_SCOPE',
                'response_template': 'answer_correction'
            }
            
            # 규칙 저장
            self.save_exclusion_rule(exclusion_rule)
            
            rules_log.append({
                'pattern': rule['pattern'],
                'category': rule['category'],
                'status': 'SUCCESS'
            })
        
        return rules_log
```

### 3.5 Step 4: 재평가

#### 3.5.1 보정 후 재평가

```python
# src/revalidation.py

class RevalidationEngine:
    """보정된 시스템으로 재평가"""
    
    def revalidate_qa_pairs(self, corrected_system, qa_pairs, original_results):
        """
        보정된 시스템으로 같은 Q&A 쌍 재평가
        """
        revalidation_results = []
        
        for qa_pair in qa_pairs:
            problem_id = qa_pair['problem_id']
            
            # 보정된 시스템으로 재평가
            new_result = corrected_system.evaluate(
                question=qa_pair['question'],
                expected_answer=qa_pair['corrected_expected_answer'],
                category=qa_pair['category']
            )
            
            original_result = original_results[problem_id]
            
            # 변화 분석
            comparison = {
                'problem_id': problem_id,
                'category': qa_pair['category'],
                
                'before': {
                    'team0_accuracy': original_result['team0_accuracy'],
                    'team1_accuracy': original_result['team1_accuracy'],
                    'team2_accuracy': original_result['team2_accuracy'],
                    'team4_accuracy': original_result['team4_accuracy'],
                    'average_accuracy': original_result['average_accuracy']
                },
                
                'after': {
                    'team0_accuracy': new_result['team0_accuracy'],
                    'team1_accuracy': new_result['team1_accuracy'],
                    'team2_accuracy': new_result['team2_accuracy'],
                    'team4_accuracy': new_result['team4_accuracy'],
                    'average_accuracy': new_result['average_accuracy']
                },
                
                'improvement': {
                    'team0': new_result['team0_accuracy'] - original_result['team0_accuracy'],
                    'team1': new_result['team1_accuracy'] - original_result['team1_accuracy'],
                    'team2': new_result['team2_accuracy'] - original_result['team2_accuracy'],
                    'team4': new_result['team4_accuracy'] - original_result['team4_accuracy'],
                    'overall': new_result['average_accuracy'] - original_result['average_accuracy']
                }
            }
            
            revalidation_results.append(comparison)
        
        return revalidation_results
    
    def verify_no_regressions(self, revalidation_results, regression_threshold=-5):
        """
        재평가 후 회귀(Regression) 검증
        - 수정되지 않은 문항의 정확도가 떨어지지 않았는가?
        """
        regressions = []
        
        for result in revalidation_results:
            if result['improvement']['overall'] < regression_threshold:
                regressions.append({
                    'problem_id': result['problem_id'],
                    'regression': result['improvement']['overall'],
                    'severity': 'HIGH' if result['improvement']['overall'] < -10 else 'MEDIUM'
                })
        
        return {
            'has_regressions': len(regressions) > 0,
            'regressions': regressions,
            'recommendation': self.recommend_rollback(regressions) if regressions else None
        }
    
    def generate_revalidation_report(self, revalidation_results, corrections_log):
        """최종 재평가 보고서"""
        
        summary = {
            'total_revalidated': len(revalidation_results),
            'improved': len([r for r in revalidation_results 
                            if r['improvement']['overall'] > 0]),
            'unchanged': len([r for r in revalidation_results 
                             if r['improvement']['overall'] == 0]),
            'regressed': len([r for r in revalidation_results 
                             if r['improvement']['overall'] < 0]),
            
            'total_improvement': sum(r['improvement']['overall'] 
                                    for r in revalidation_results) / len(revalidation_results),
            
            'team_improvements': {
                'team0': sum(r['improvement']['team0'] for r in revalidation_results) / len(revalidation_results),
                'team1': sum(r['improvement']['team1'] for r in revalidation_results) / len(revalidation_results),
                'team2': sum(r['improvement']['team2'] for r in revalidation_results) / len(revalidation_results),
                'team4': sum(r['improvement']['team4'] for r in revalidation_results) / len(revalidation_results),
            }
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'details': revalidation_results,
            'corrections_applied': corrections_log,
            'status': 'SUCCESS' if not summary['regressed'] > summary['improved'] * 0.2 else 'NEEDS_REVIEW'
        }
```

---

## 📝 Part 4: 실행 계획 (Timeline)

### Phase 4.1: 설계 검증 (1주일)

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 06-07 | Snowflake 문제 분석 완료 | Claude | 문제 분석 보고서 |
| 06-08~09 | Stage 1 구현 (검증 로직) | Claude | validate_qa_consistency.py |
| 06-10 | 기존 평가 Q&A 검증 | Claude | qa_validation_report.md |
| 06-11 | Q&A 수정 완료 | User | 검증된 Q&A 셋 |
| 06-12 | 카테고리 정의 완성 | Claude | evaluation_categories.py |

### Phase 4.2: 평가 개선 구현 (2주일)

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 06-13~16 | Stage 2 구현 (검증 체크포인트) | Claude | evaluation_checkpoints.py |
| 06-17~18 | Stage 3 구현 (정답 보정) | Claude | AnswerCorrectionCLI |
| 06-19 | 정답 보정 세션 | User | corrections_20260607.json |
| 06-20~21 | 재평가 엔진 구현 | Claude | revalidation.py |
| 06-22 | 최종 보정 평가 | Claude | revalidation_report.md |

### Phase 4.3: 시스템 통합 (1주일)

| 날짜 | 작업 | 담당 | 산출물 |
|---|---|---|---|
| 06-23 | 온톨로지/RAG 업데이트 | Claude | ontology_updater.py |
| 06-24 | 통합 테스트 | Claude | integration_test_report.md |
| 06-25 | 최종 문서화 | Claude | PHASE4_eval_finalized.md |

---

## 🎓 Part 5: 학습 포인트 및 Best Practices

### 5.1 평가 설계 체크리스트

```markdown
☐ 예상답변이 제공 문서에서 답변 가능한가?
☐ 질문이 명확하고 범위가 정의되어 있는가?
☐ 카테고리와 예상답변이 일치하는가?
☐ 범위 외 질문에 대한 기본 답변이 정의되어 있는가?
☐ 평가 대상 문서가 명시적으로 나열되어 있는가?
☐ 정답이 문서 기반이 아닌 일반 지식에 의존하지 않는가?
```

### 5.2 온톨로지 기반 시스템 제약사항

```markdown
온톨로지 기반 RAG의 핵심:
1. 온톨로지에 없는 개념은 답변할 수 없다
2. 따라서 범위 외 질문을 자동으로 감지할 수 있다
3. 이는 장점 (명확한 범위)이자 단점 (유연성 부족)이다

설계 시 고려사항:
- 온톨로지 구축 전에 범위를 명확히 정의하라
- "문서에만 기반" 원칙을 명시적으로 구현하라
- LLM의 "해석"을 제약하는 메커니즘을 추가하라
- 테스트를 통해 범위 침범을 조기에 발견하라
```

### 5.3 정답 보정의 가치

```markdown
정답 보정이 중요한 이유:
1. 평가 오류 수정: 잘못된 기준을 바로잡는다
2. 시스템 개선: 평가 데이터가 시스템 개선의 신호다
3. 재사용성: 한 번의 보정이 모든 시스템을 개선한다
4. 신뢰도: 정확한 평가 기준이 신뢰도를 높인다
```

---

## 📚 Part 6: 참고 파일 및 링크

| 파일 | 경로 | 목적 |
|---|---|---|
| 원본 평가 | `validation/ont_platform_v4_eval/reports/4팀_정확도_비교.xlsx` | 기준 |
| 수정본 | `validation/ont_platform_v4_eval/reports/4팀_정확도_비교_v2_수정본.xlsx` | Snowflake 수정 후 |
| 분석 | `validation/ont_platform_v4_eval/reports/4팀_정확도_비교_v2_수정본_분석.md` | 문제 분석 |
| 본 계획 | `week_instructions/PHASE4-eval-claude.md` | 개선 계획 |

---

**문서 버전**: 1.0  
**작성일**: 2026-06-07  
**상태**: 구현 준비 완료
