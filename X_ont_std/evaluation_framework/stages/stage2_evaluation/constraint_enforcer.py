"""
온톨로지 기반 제약 적용 엔진

평가 중에 온톨로지를 기반으로 범위 제약을 자동 적용합니다:
- 카테고리의 필수 개념이 온톨로지에 없으면 범위 외
- 검색 결과가 해당 카테고리가 아니면 범위 외
- 응답에 제약 자동 적용

목표: Snowflake 같은 범위 외 질문을 평가 중에 자동으로 감지 및 제약
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime


class OntologyConstraintEnforcer:
    """온톨로지 기반 범위 제약 적용"""

    def __init__(self, ontology_concepts: List[str],
                 category_definitions: Dict):
        """
        초기화

        Args:
            ontology_concepts: 온톨로지에 포함된 개념 리스트
            category_definitions: 카테고리 정의
        """
        self.ontology_concepts = set(c.lower() for c in ontology_concepts)
        self.category_definitions = category_definitions

    def validate_answer_scope(self, question: str, category: str,
                            retrieved_docs: List[str],
                            retrieved_concepts: List[str]) -> Dict:
        """
        답변 범위 검증

        Args:
            question: 질문
            category: 카테고리
            retrieved_docs: 검색된 문서
            retrieved_concepts: 검색된 개념

        Returns:
            {
                'should_answer': bool,
                'reason': str,
                'fallback_answer': str,
                'confidence': float (0-1),
                'constraints': [...]
            }
        """
        constraints = []

        # 1. 카테고리 필수 개념 검증
        required_concepts = self.category_definitions[category]['required_concepts']
        ontology_has_required = any(
            concept.lower() in self.ontology_concepts
            for concept in required_concepts
        )

        if not ontology_has_required:
            constraints.append({
                'type': 'MISSING_REQUIRED_CONCEPT',
                'severity': 'CRITICAL',
                'message': f'{category} 범주의 필수 개념이 온톨로지에 없음',
                'required_concepts': required_concepts,
                'ontology_concepts': list(self.ontology_concepts)[:10]
            })

        # 2. 검색 문서 범위 검증
        doc_categories = self._infer_doc_categories(retrieved_docs)
        has_category_docs = category in doc_categories or len(doc_categories) == 0

        if not has_category_docs:
            constraints.append({
                'type': 'MISSING_CATEGORY_DOCUMENTS',
                'severity': 'HIGH',
                'message': f'{category} 카테고리 문서 없음',
                'retrieved_categories': doc_categories,
                'needed_category': category
            })

        # 3. 범위 외 기술 감지
        out_of_scope_techs = self._detect_out_of_scope(question, category)
        if out_of_scope_techs:
            constraints.append({
                'type': 'OUT_OF_SCOPE_TECHNOLOGY',
                'severity': 'HIGH',
                'message': f'{out_of_scope_techs}는(는) {category} 범주 범위 외',
                'out_of_scope_techs': out_of_scope_techs,
                'category': category
            })

        # 4. 검색 결과 신뢰도
        retrieval_confidence = self._calculate_retrieval_confidence(
            retrieved_concepts, required_concepts
        )

        if retrieval_confidence < 0.3:
            constraints.append({
                'type': 'LOW_RETRIEVAL_CONFIDENCE',
                'severity': 'MEDIUM',
                'message': f'검색 결과의 신뢰도 낮음 ({retrieval_confidence:.1%})',
                'confidence': retrieval_confidence,
                'threshold': 0.3
            })

        # 최종 판정
        critical_constraints = [c for c in constraints
                               if c['severity'] == 'CRITICAL']
        high_constraints = [c for c in constraints
                           if c['severity'] == 'HIGH']

        should_answer = (
            len(critical_constraints) == 0 and
            len(high_constraints) <= 1  # 높음 1개는 허용
        )

        fallback = self.category_definitions[category].get(
            'fallback_answer',
            None
        )

        overall_confidence = (
            1.0 - (len(critical_constraints) * 0.5)
            - (len(high_constraints) * 0.2)
            - (len(constraints) * 0.05)
        )
        overall_confidence = max(0, overall_confidence)

        return {
            'should_answer': should_answer,
            'reason': self._explain_decision(constraints),
            'fallback_answer': fallback,
            'confidence': overall_confidence,
            'constraints': constraints,
            'constraint_count': len(constraints),
            'critical_count': len(critical_constraints),
            'high_count': len(high_constraints),
            'timestamp': datetime.now().isoformat()
        }

    def enforce_constraints_on_response(self, response: str,
                                       question: str, category: str,
                                       retrieved_docs: List[str],
                                       retrieved_concepts: List[str]) -> Dict:
        """
        생성된 응답에 제약 적용

        Args:
            response: 생성된 답변
            question: 질문
            category: 카테고리
            retrieved_docs: 검색된 문서
            retrieved_concepts: 검색된 개념

        Returns:
            {
                'original_response': str,
                'constrained_response': str,
                'was_constrained': bool,
                'constraint_reason': str,
                'confidence': float
            }
        """
        validation = self.validate_answer_scope(
            question, category, retrieved_docs, retrieved_concepts
        )

        if not validation['should_answer']:
            # 범위 외 질문 → 기본 답변 반환
            fallback = validation['fallback_answer'] or (
                "해당 질문은 평가 범위를 벗어났습니다."
            )

            return {
                'original_response': response,
                'constrained_response': fallback,
                'was_constrained': True,
                'constraint_reason': validation['reason'],
                'confidence': 0,
                'fallback_applied': True,
                'constraints': validation['constraints']
            }

        # 답변이 유효함 → 원본 반환
        return {
            'original_response': response,
            'constrained_response': response,
            'was_constrained': False,
            'constraint_reason': None,
            'confidence': validation['confidence'],
            'fallback_applied': False,
            'constraints': validation['constraints']
        }

    def _detect_out_of_scope(self, question: str, category: str) -> List[str]:
        """범위 외 기술 감지"""
        out_of_scope_list = self.category_definitions[category]['out_of_scope']
        question_lower = question.lower()

        found = [
            tech for tech in out_of_scope_list
            if tech.lower() in question_lower
        ]

        return found

    def _infer_doc_categories(self, docs: List[str]) -> List[str]:
        """문서 목록에서 카테고리 추론"""
        categories = set()

        for doc in docs:
            doc_lower = doc.lower()
            for cat, definition in self.category_definitions.items():
                for required_doc in definition['required_documents']:
                    if required_doc.lower() in doc_lower:
                        categories.add(cat)
                        break

        return list(categories)

    def _calculate_retrieval_confidence(self, retrieved_concepts: List[str],
                                       required_concepts: List[str]) -> float:
        """검색 결과 신뢰도 계산"""
        if not required_concepts:
            return 1.0

        required_lower = set(c.lower() for c in required_concepts)
        retrieved_lower = set(c.lower() for c in retrieved_concepts)

        overlap = required_lower & retrieved_lower
        confidence = len(overlap) / len(required_lower)

        return confidence

    def _explain_decision(self, constraints: List[Dict]) -> str:
        """제약 사항 설명"""
        if not constraints:
            return "범위 내 질문입니다."

        explanations = []
        for constraint in constraints:
            if constraint['severity'] == 'CRITICAL':
                explanations.append(f"[필수] {constraint['message']}")
            elif constraint['severity'] == 'HIGH':
                explanations.append(f"[높음] {constraint['message']}")
            elif constraint['severity'] == 'MEDIUM':
                explanations.append(f"[중간] {constraint['message']}")

        return " / ".join(explanations)


class ConstraintEvaluationMetrics:
    """제약 적용 평가 메트릭"""

    @staticmethod
    def calculate_constraint_impact(
        original_response: str, constrained_response: str,
        was_constrained: bool
    ) -> Dict:
        """
        제약이 응답에 미친 영향도 계산

        Returns:
            {
                'was_constrained': bool,
                'response_similarity': float,
                'fallback_applied': bool,
                'impact_score': float
            }
        """
        if not was_constrained:
            return {
                'was_constrained': False,
                'response_similarity': 1.0,
                'fallback_applied': False,
                'impact_score': 0.0
            }

        # 응답이 변경됨 → 유사도 계산
        similarity = ConstraintEvaluationMetrics._calculate_similarity(
            original_response, constrained_response
        )

        fallback_applied = len(constrained_response) < len(original_response) * 0.1

        impact_score = 1.0 if fallback_applied else (1.0 - similarity)

        return {
            'was_constrained': True,
            'response_similarity': similarity,
            'fallback_applied': fallback_applied,
            'impact_score': impact_score
        }

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """텍스트 유사도 계산 (간단한 방식)"""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
