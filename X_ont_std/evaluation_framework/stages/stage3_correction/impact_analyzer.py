"""
정답 보정의 영향도 분석

정답을 수정했을 때 어떤 부분의 시스템을 업데이트해야 하는지 분석합니다:

1. 온톨로지 변경점
   - 새로운 개념 추가
   - 불필요한 개념 제거
   - 관계 추가/변경

2. RAG 변경점
   - 벡터 DB 임베딩 갱신
   - 제외 규칙 추가
   - 검색 가중치 조정

3. 평가 기준 변경점
   - 예상답변 업데이트
   - 카테고리 재분류
   - 채점 기준 조정
"""

from typing import Dict, List, Set, Tuple
from datetime import datetime


class ImpactAnalyzer:
    """정답 보정의 영향도 분석"""

    def __init__(self, category_definitions: Dict):
        """
        초기화

        Args:
            category_definitions: 카테고리 정의
        """
        self.category_definitions = category_definitions

    def analyze_correction_impact(self, correction: Dict) -> Dict:
        """
        정답 보정이 어느 부분을 변경해야 하는지 분석

        Args:
            correction: {
                'problem_id': str,
                'original_expected_answer': str,
                'corrected_expected_answer': str,
                'category': str,
                'reason': str
            }

        Returns:
            {
                'ontology_updates': [],
                'rag_updates': [],
                'evaluation_updates': [],
                'estimated_impact': float,
                'risk_level': str,
                'rollback_plan': str
            }
        """
        impact = {
            'problem_id': correction['problem_id'],
            'category': correction['category'],
            'timestamp': datetime.now().isoformat(),
            'ontology_updates': [],
            'rag_updates': [],
            'evaluation_updates': [],
            'estimated_impact_score': 0.0,
            'risk_level': 'LOW',
            'rollback_plan': None
        }

        original = correction['original_expected_answer']
        corrected = correction['corrected_expected_answer']
        category = correction['category']

        # 1. 온톨로지 변경점 분석
        ontology_changes = self._analyze_ontology_changes(original, corrected)
        impact['ontology_updates'] = ontology_changes

        # 2. RAG 변경점 분석
        rag_changes = self._analyze_rag_changes(original, corrected, category)
        impact['rag_updates'] = rag_changes

        # 3. 평가 기준 변경점
        eval_changes = self._analyze_evaluation_changes(
            original, corrected, category
        )
        impact['evaluation_updates'] = eval_changes

        # 4. 영향도 점수 계산
        impact_score = self._calculate_impact_score(
            ontology_changes, rag_changes, eval_changes
        )
        impact['estimated_impact_score'] = impact_score

        # 5. 위험도 평가
        risk_level = self._assess_risk_level(
            ontology_changes, rag_changes, impact_score
        )
        impact['risk_level'] = risk_level

        # 6. 롤백 계획
        rollback = self._create_rollback_plan(correction, impact)
        impact['rollback_plan'] = rollback

        return impact

    def _analyze_ontology_changes(self, original: str,
                                  corrected: str) -> List[Dict]:
        """온톨로지 변경점 분석"""
        changes = []

        # 키워드 추출
        original_concepts = self._extract_concepts(original)
        corrected_concepts = self._extract_concepts(corrected)

        # 제거할 개념
        removed = original_concepts - corrected_concepts
        if removed:
            changes.append({
                'action': 'REMOVE_CONCEPTS',
                'concepts': list(removed),
                'reason': '정답 수정으로 더 이상 필요 없음',
                'risk': 'MEDIUM' if len(removed) > 3 else 'LOW'
            })

        # 추가할 개념
        added = corrected_concepts - original_concepts
        if added:
            changes.append({
                'action': 'ADD_CONCEPTS',
                'concepts': list(added),
                'reason': '정답 수정으로 새로 필요함',
                'risk': 'LOW'
            })

        # 관계 변경
        if original_concepts and corrected_concepts:
            relationship_changes = self._analyze_relationships(
                original_concepts, corrected_concepts
            )
            if relationship_changes:
                changes.append({
                    'action': 'UPDATE_RELATIONSHIPS',
                    'changes': relationship_changes,
                    'risk': 'MEDIUM'
                })

        return changes

    def _analyze_rag_changes(self, original: str, corrected: str,
                           category: str) -> List[Dict]:
        """RAG 변경점 분석"""
        changes = []

        # 범위 외 답변 처리
        if self._is_out_of_scope(corrected, category):
            changes.append({
                'action': 'ADD_EXCLUSION_RULE',
                'pattern': self._extract_exclusion_pattern(corrected),
                'category': category,
                'description': '정답이 범위 외이므로 이 카테고리는 자동 제외',
                'risk': 'LOW'
            })

        # 임베딩 갱신 필요
        if not self._is_out_of_scope(corrected, category):
            keywords = self._extract_keywords(corrected)
            if keywords:
                changes.append({
                    'action': 'UPDATE_EMBEDDINGS',
                    'keywords': keywords,
                    'count': len(keywords),
                    'description': '새 정답에 대한 임베딩 계산 및 저장',
                    'risk': 'LOW'
                })

        # 검색 가중치 조정
        if original and corrected and original != corrected:
            changes.append({
                'action': 'ADJUST_SEARCH_WEIGHTS',
                'original_weight': 0.5,
                'new_weight': 0.7,
                'description': '정답 수정으로 검색 가중치 상향',
                'risk': 'MEDIUM'
            })

        return changes

    def _analyze_evaluation_changes(self, original: str, corrected: str,
                                   category: str) -> List[Dict]:
        """평가 기준 변경점 분석"""
        changes = []

        # 예상답변 업데이트
        changes.append({
            'action': 'UPDATE_EXPECTED_ANSWER',
            'from_length': len(original),
            'to_length': len(corrected),
            'change_type': (
                'OUT_OF_SCOPE' if self._is_out_of_scope(corrected, category)
                else 'CONTENT_UPDATE'
            ),
            'risk': 'LOW'
        })

        # 카테고리 재검토
        inferred_category = self._infer_category(corrected)
        if inferred_category != category:
            changes.append({
                'action': 'REVIEW_CATEGORY',
                'original_category': category,
                'inferred_category': inferred_category,
                'reason': '정답 내용으로 보아 다른 카테고리일 가능성',
                'risk': 'HIGH'
            })

        # 채점 기준 영향
        if self._is_out_of_scope(corrected, category):
            changes.append({
                'action': 'UPDATE_SCORING_RULE',
                'rule': 'EXACT_MATCH',
                'description': (
                    '범위 외 답변: "관련 없음" 정확히 일치해야만 100점'
                ),
                'risk': 'MEDIUM'
            })

        return changes

    def _calculate_impact_score(self, ontology_changes: List[Dict],
                               rag_changes: List[Dict],
                               eval_changes: List[Dict]) -> float:
        """영향도 점수 계산 (0-1)"""
        scores = []

        # 온톨로지 영향도
        if ontology_changes:
            ontology_score = min(1.0, len(ontology_changes) * 0.2)
            scores.append(ontology_score * 0.3)  # 30% 가중치

        # RAG 영향도
        if rag_changes:
            rag_score = min(1.0, len(rag_changes) * 0.25)
            scores.append(rag_score * 0.4)  # 40% 가중치

        # 평가 기준 영향도
        if eval_changes:
            eval_score = min(1.0, len(eval_changes) * 0.2)
            scores.append(eval_score * 0.3)  # 30% 가중치

        return sum(scores) if scores else 0.0

    def _assess_risk_level(self, ontology_changes: List[Dict],
                          rag_changes: List[Dict],
                          impact_score: float) -> str:
        """위험도 평가"""
        high_risk = sum(
            1 for changes in [ontology_changes, rag_changes]
            for c in changes
            if c.get('risk') == 'HIGH'
        )

        if high_risk > 0:
            return 'HIGH'
        elif impact_score > 0.6:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _create_rollback_plan(self, correction: Dict,
                             impact: Dict) -> str:
        """롤백 계획 생성"""
        return f"""
롤백 계획:
1. 데이터베이스 백업 (정답 업데이트 전)
2. 온톨로지 백업 (변경 전 스냅샷 저장)
3. 벡터 DB 백업 (임베딩 갱신 전)

롤백 조건:
- 재평가 후 정확도가 5%p 이상 하락
- 회귀 테스트 실패
- 사용자 승인 취소

롤백 실행:
1. 데이터베이스 복원
2. 온톨로지 복원
3. 벡터 DB 임베딩 복원
4. 평가 기준 원상복구
5. 재평가 실행 확인
"""

    def _extract_concepts(self, text: str) -> Set[str]:
        """텍스트에서 개념 추출"""
        concept_keywords = [
            'ontology', 'concept', 'relationship', 'knowledge',
            'graph', 'entity', 'class', 'property', 'rag', 'retrieval',
            'embedding', 'vector', 'metadata', 'semantic'
        ]

        text_lower = text.lower()
        concepts = set()

        for keyword in concept_keywords:
            if keyword in text_lower:
                concepts.add(keyword)

        return concepts

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        keywords = text.lower().split()
        # 3글자 이상 필터링
        return [k for k in keywords if len(k) >= 3]

    def _extract_concepts(self, text: str) -> Set[str]:
        """개념 추출"""
        text_lower = text.lower()
        concepts = set()

        concept_patterns = {
            'ontology': ['ontology', '온톨로지'],
            'rag': ['rag', 'retrieval', '검색'],
            'semantic': ['semantic', '의미'],
            'knowledge': ['knowledge', 'graph', '지식'],
            'metadata': ['metadata', 'meta', '메타']
        }

        for concept, patterns in concept_patterns.items():
            if any(p in text_lower for p in patterns):
                concepts.add(concept)

        return concepts

    def _analyze_relationships(self, original: Set[str],
                              corrected: Set[str]) -> List[Dict]:
        """관계 변경점 분석"""
        # 간단한 분석
        if original != corrected:
            return [{
                'from': 'original_concepts',
                'to': 'corrected_concepts',
                'type': 'concept_set_changed'
            }]
        return []

    def _is_out_of_scope(self, text: str, category: str) -> bool:
        """범위 외 답변 여부 확인"""
        fallback = self.category_definitions[category].get('fallback_answer')
        if not fallback:
            return False

        return fallback.lower() in text.lower()

    def _extract_exclusion_pattern(self, text: str) -> str:
        """제외 규칙 패턴 추출"""
        if "관련이 없습니다" in text:
            return "out_of_scope"
        elif "범위 외" in text:
            return "out_of_scope"
        return "unknown"

    def _infer_category(self, text: str) -> str:
        """텍스트에서 카테고리 추론"""
        text_lower = text.lower()

        if any(w in text_lower for w in ['ontology', 'knowledge', '온톨로지']):
            return 'Ontology'
        elif any(w in text_lower for w in ['rag', 'retrieval', '검색']):
            return 'Advanced RAG'
        elif any(w in text_lower for w in ['snowflake', '관련이 없']):
            return 'Snowflake'

        return 'Unknown'


class ConsolidatedImpactAnalysis:
    """여러 정답 보정의 통합 영향도 분석"""

    def __init__(self, category_definitions: Dict):
        """초기화"""
        self.analyzer = ImpactAnalyzer(category_definitions)

    def analyze_all_corrections(self, corrections: List[Dict]) -> Dict:
        """모든 정답 보정의 통합 영향도"""
        individual_impacts = []
        consolidated_changes = {
            'ontology_changes': [],
            'rag_changes': [],
            'evaluation_changes': []
        }

        # 개별 영향도 분석
        for correction in corrections:
            impact = self.analyzer.analyze_correction_impact(correction)
            individual_impacts.append(impact)

            # 통합
            consolidated_changes['ontology_changes'].extend(
                impact['ontology_updates']
            )
            consolidated_changes['rag_changes'].extend(
                impact['rag_updates']
            )
            consolidated_changes['evaluation_changes'].extend(
                impact['evaluation_updates']
            )

        # 중복 제거
        self._deduplicate_changes(consolidated_changes)

        # 통합 위험도 평가
        overall_risk = self._assess_overall_risk(individual_impacts)

        return {
            'total_corrections': len(corrections),
            'individual_impacts': individual_impacts,
            'consolidated_changes': consolidated_changes,
            'overall_impact_score': sum(
                i['estimated_impact_score'] for i in individual_impacts
            ) / len(individual_impacts),
            'overall_risk_level': overall_risk,
            'implementation_priority': self._prioritize_changes(
                consolidated_changes
            )
        }

    def _deduplicate_changes(self, changes: Dict):
        """중복 변경점 제거"""
        for key in changes:
            unique = []
            seen = set()

            for change in changes[key]:
                # action 기반 중복 감지
                change_id = (
                    change.get('action'),
                    tuple(change.get('concepts', [])) or
                    tuple(change.get('keywords', []))
                )

                if change_id not in seen:
                    unique.append(change)
                    seen.add(change_id)

            changes[key] = unique

    def _assess_overall_risk(self, impacts: List[Dict]) -> str:
        """전체 위험도 평가"""
        high_risk_count = sum(
            1 for i in impacts if i['risk_level'] == 'HIGH'
        )

        if high_risk_count > 2:
            return 'CRITICAL'
        elif high_risk_count > 0:
            return 'HIGH'
        elif any(i['risk_level'] == 'MEDIUM' for i in impacts):
            return 'MEDIUM'
        else:
            return 'LOW'

    def _prioritize_changes(self, changes: Dict) -> List[Dict]:
        """변경사항 우선순위 정렬"""
        priority_list = []

        # 1순위: 평가 기준 변경 (즉시 영향)
        priority_list.extend([
            {**c, 'priority': 'P1', 'timeline': 'Immediate'}
            for c in changes['evaluation_changes']
            if c.get('risk') == 'HIGH'
        ])

        # 2순위: RAG 변경 (검색 영향)
        priority_list.extend([
            {**c, 'priority': 'P2', 'timeline': '1일 이내'}
            for c in changes['rag_changes']
        ])

        # 3순위: 온톨로지 변경 (배경 업데이트)
        priority_list.extend([
            {**c, 'priority': 'P3', 'timeline': '1주일 이내'}
            for c in changes['ontology_changes']
        ])

        return priority_list
