"""
평가 중 3개 검증 지점 (Checkpoints)

Checkpoint 1: 답변 생성 직후
  → 답변이 범위를 벗어나지 않았는가?
  → 필수 근거가 있는가?

Checkpoint 2: 정확도 채점 전
  → 기대값과 실제값이 비교 가능한가?
  → 채점 기준이 적절한가?

Checkpoint 3: 평가 결과 검증
  → 이 Q&A 쌍이 유효한가?
  → 점수가 타당한가?
"""

from typing import Dict, List, Optional
from datetime import datetime


class EvaluationCheckpoints:
    """평가 중 검증 지점"""

    def __init__(self, category_definitions: Dict):
        """
        초기화

        Args:
            category_definitions: 카테고리 정의
        """
        self.category_definitions = category_definitions
        self.checkpoints_log = []

    def checkpoint_1_answer_generation(self, question: str, category: str,
                                       answer: str, sources: List[str],
                                       constraint_applied: bool = False
                                       ) -> Dict:
        """
        Checkpoint 1: 답변 생성 직후

        체크 항목:
        1. 답변이 범위를 벗어나지 않았는가?
        2. 필수 근거가 있는가?
        3. 답변 길이가 적절한가?
        4. 제약이 적절히 적용되었는가?
        """
        checks = {
            'checkpoint_id': 'CP1_ANSWER_GENERATION',
            'timestamp': datetime.now().isoformat(),
            'question': question[:100],
            'category': category,
            'is_constrained': constraint_applied
        }

        issues = []
        passed_checks = 0
        total_checks = 5

        # 1. 답변 여부 검증
        has_answer = len(answer.strip()) > 0
        checks['has_answer'] = has_answer
        if has_answer:
            passed_checks += 1
        else:
            issues.append({
                'type': 'ERROR',
                'checkpoint': 'CP1',
                'message': '답변이 생성되지 않음',
                'severity': 'CRITICAL'
            })

        # 2. 근거 검증
        has_sources = len(sources) > 0
        checks['has_sources'] = has_sources
        checks['source_count'] = len(sources)
        if has_sources:
            passed_checks += 1
        else:
            issues.append({
                'type': 'WARNING',
                'checkpoint': 'CP1',
                'message': '근거 없이 답변함 (hallucination 위험)',
                'severity': 'HIGH'
            })

        # 3. 답변 길이 검증
        answer_length = len(answer)
        is_length_ok = 50 <= answer_length <= 2000
        checks['answer_length'] = answer_length
        checks['is_length_ok'] = is_length_ok
        if is_length_ok:
            passed_checks += 1
        else:
            if answer_length < 50:
                issues.append({
                    'type': 'WARNING',
                    'checkpoint': 'CP1',
                    'message': f'답변이 너무 짧음 ({answer_length}글자)',
                    'severity': 'MEDIUM'
                })
            else:
                issues.append({
                    'type': 'WARNING',
                    'checkpoint': 'CP1',
                    'message': f'답변이 너무 김 ({answer_length}글자)',
                    'severity': 'LOW'
                })

        # 4. 범위 검증 (제약 적용 여부 일관성)
        is_out_of_scope = "관련이 없습니다" in answer or "관련 없음" in answer
        fallback_answer = self.category_definitions[category].get('fallback_answer')

        if constraint_applied and not is_out_of_scope:
            issues.append({
                'type': 'WARNING',
                'checkpoint': 'CP1',
                'message': '범위 제약이 적용되었으나 답변에 반영 안 됨',
                'severity': 'MEDIUM'
            })
        elif not constraint_applied and is_out_of_scope:
            issues.append({
                'type': 'INFO',
                'checkpoint': 'CP1',
                'message': '시스템이 자체적으로 범위 외 답변을 제공',
                'severity': 'LOW'
            })
        else:
            passed_checks += 1

        # 5. 소스 관련성 (간단한 검증)
        source_quality = self._assess_source_quality(sources)
        checks['source_quality'] = source_quality
        if source_quality >= 0.5:
            passed_checks += 1
        else:
            issues.append({
                'type': 'WARNING',
                'checkpoint': 'CP1',
                'message': f'소스 품질이 낮음 (점수: {source_quality:.2f})',
                'severity': 'MEDIUM'
            })

        checks['issues'] = issues
        checks['passed_checks'] = passed_checks
        checks['total_checks'] = total_checks
        checks['status'] = (
            'PASS' if len([i for i in issues if i['severity'] in ['CRITICAL', 'ERROR']]) == 0
            else 'FAIL'
        )

        self.checkpoints_log.append(checks)
        return checks

    def checkpoint_2_accuracy_scoring(self, expected_answer: str,
                                     actual_answer: str,
                                     category: str,
                                     sources: List[str]
                                     ) -> Dict:
        """
        Checkpoint 2: 정확도 채점 전

        체크 항목:
        1. 기대값과 실제값이 비교 가능한가?
        2. 채점 기준이 적절한가?
        3. 답변 방식이 일관된가?
        """
        checks = {
            'checkpoint_id': 'CP2_ACCURACY_SCORING',
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'expected_answer_length': len(expected_answer),
            'actual_answer_length': len(actual_answer)
        }

        issues = []
        scoring_method = None

        # 1. 범위 외 답변 특별 처리
        if "관련이 없습니다" in expected_answer or "관련 없음" in expected_answer:
            # 예상답변이 범위 외
            if "관련이 없습니다" in actual_answer or "관련 없음" in actual_answer:
                scoring_method = 'EXACT_MATCH'
                accuracy_score = 100
            elif self._contains_technical_content(actual_answer):
                scoring_method = 'SCOPE_VIOLATION'
                accuracy_score = 0
                issues.append({
                    'type': 'ERROR',
                    'checkpoint': 'CP2',
                    'message': '범위 외 질문에 기술적 내용 포함',
                    'severity': 'HIGH'
                })
            else:
                scoring_method = 'PARTIAL_MATCH'
                accuracy_score = 25
        else:
            # 일반 답변 → 유사도 기반 채점
            similarity = self._calculate_semantic_similarity(
                expected_answer, actual_answer
            )
            scoring_method = 'SEMANTIC_SIMILARITY'
            accuracy_score = int(similarity * 100)

        checks['scoring_method'] = scoring_method
        checks['estimated_accuracy'] = accuracy_score
        checks['issues'] = issues
        checks['status'] = 'PASS' if accuracy_score >= 50 else 'REVIEW_NEEDED'

        self.checkpoints_log.append(checks)
        return checks

    def checkpoint_3_qa_validity(self, problem_id: str,
                                expected_answer: str,
                                actual_answer: str,
                                accuracy_score: int,
                                category: str
                                ) -> Dict:
        """
        Checkpoint 3: 평가 결과 검증

        체크 항목:
        1. 이 Q&A 쌍이 유효한가?
        2. 정답이 정말 정답인가?
        3. 점수가 타당한가?
        """
        checks = {
            'checkpoint_id': 'CP3_QA_VALIDITY',
            'timestamp': datetime.now().isoformat(),
            'problem_id': problem_id,
            'category': category,
            'accuracy_score': accuracy_score
        }

        issues = []
        red_flags = []

        # 1. 예상답변의 유효성
        expected_valid = self._is_valid_expected_answer(expected_answer, category)
        checks['expected_answer_valid'] = expected_valid
        if not expected_valid:
            red_flags.append({
                'type': 'WARNING',
                'checkpoint': 'CP3',
                'message': '예상답변이 의심스러움 (다시 검토 필요)',
                'severity': 'MEDIUM'
            })

        # 2. 실제답변의 관련성
        actual_relevant = self._is_relevant_answer(actual_answer, expected_answer)
        checks['actual_answer_relevant'] = actual_relevant
        if not actual_relevant:
            issues.append({
                'type': 'WARNING',
                'checkpoint': 'CP3',
                'message': '실제답변이 예상답변과 무관해 보임',
                'severity': 'MEDIUM'
            })

        # 3. 점수의 타당성 (의심스러운 점수 감지)
        is_score_suspicious = (
            accuracy_score > 80 and
            ("관련이 없습니다" in expected_answer or "관련 없음" in expected_answer)
        )

        checks['is_score_suspicious'] = is_score_suspicious
        if is_score_suspicious:
            red_flags.append({
                'type': 'ERROR',
                'checkpoint': 'CP3',
                'message': (
                    f'의심스러운 점수 조합: '
                    f'범위 외 질문에 {accuracy_score}% 점수 → 검토 필수'
                ),
                'severity': 'HIGH',
                'review_required': True
            })

        checks['issues'] = issues
        checks['red_flags'] = red_flags
        checks['needs_review'] = (
            len([f for f in red_flags if f['severity'] in ['ERROR', 'CRITICAL']]) > 0
        )
        checks['status'] = (
            'PASS' if not checks['needs_review'] else 'NEEDS_REVIEW'
        )

        self.checkpoints_log.append(checks)
        return checks

    def _assess_source_quality(self, sources: List[str]) -> float:
        """소스 품질 평가"""
        if not sources:
            return 0.0

        quality_score = 0.0
        for source in sources:
            # 소스 길이 (길수록 양질)
            if len(source) > 100:
                quality_score += 0.3
            elif len(source) > 50:
                quality_score += 0.2
            else:
                quality_score += 0.1

            # PDF/문서 여부
            if any(ext in source for ext in ['.pdf', '.txt', '.doc']):
                quality_score += 0.3

        # 정규화
        return min(1.0, quality_score / len(sources))

    def _contains_technical_content(self, text: str) -> bool:
        """기술적 내용 포함 여부 확인"""
        technical_keywords = [
            'rag', 'retrieval', 'embedding', 'vector', 'ontology',
            'knowledge', 'inference', 'training', 'model', 'algorithm',
            'protocol', 'architecture', 'schema', 'database'
        ]

        text_lower = text.lower()
        return any(kw in text_lower for kw in technical_keywords)

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """간단한 의미 유사도 계산"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not (words1 | words2):
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _is_valid_expected_answer(self, answer: str, category: str) -> bool:
        """예상답변의 유효성 확인"""
        # 최소 길이
        if len(answer) < 50:
            return False

        # 너무 일반적인가?
        generic_phrases = [
            '일반적으로', '보통', '일반', '다양', '여러'
        ]
        generic_count = sum(
            1 for phrase in generic_phrases if phrase in answer
        )

        if generic_count >= 2:
            return False

        return True

    def _is_relevant_answer(self, actual: str, expected: str) -> bool:
        """답변의 관련성 확인"""
        # 키워드 겹침
        actual_words = set(actual.lower().split())
        expected_words = set(expected.lower().split())

        if not expected_words:
            return True

        overlap = actual_words & expected_words
        similarity = len(overlap) / len(expected_words)

        return similarity >= 0.1  # 최소 10% 겹침

    def get_checkpoint_summary(self) -> Dict:
        """모든 체크포인트 요약"""
        if not self.checkpoints_log:
            return {
                'total_checkpoints': 0,
                'passed': 0,
                'failed': 0,
                'needs_review': 0
            }

        summary = {
            'total_checkpoints': len(self.checkpoints_log),
            'by_id': {},
            'issues': [],
            'timestamp': datetime.now().isoformat()
        }

        for checkpoint in self.checkpoints_log:
            cp_id = checkpoint['checkpoint_id']
            if cp_id not in summary['by_id']:
                summary['by_id'][cp_id] = {'passed': 0, 'failed': 0}

            if checkpoint['status'] == 'PASS':
                summary['by_id'][cp_id]['passed'] += 1
            else:
                summary['by_id'][cp_id]['failed'] += 1

            summary['issues'].extend(checkpoint.get('issues', []))

        return summary
