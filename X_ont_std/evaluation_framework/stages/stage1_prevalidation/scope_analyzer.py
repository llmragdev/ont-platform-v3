"""
범위 명시성 검증

질문에서 특정 기술을 언급하면:
- 예상 답변도 그 기술을 포함해야 함
- 또는 "관련 없음"으로 명시해야 함

Snowflake 같은 범위 외 기술 감지
"""

from typing import Dict, List, Tuple
import re


class ScopeAnalyzer:
    """질문과 답변의 범위 일관성 검증"""

    def __init__(self):
        """초기화"""
        # 특정 기술/도메인 목록
        self.specific_technologies = {
            'snowflake': '데이터 웨어하우스',
            'elasticsearch': '검색 엔진',
            'mongodb': 'NoSQL 데이터베이스',
            'postgresql': 'SQL 데이터베이스',
            'kafka': '메시지 브로커',
            'spark': '분산 처리',
            'hadoop': '분산 저장',
            'cuda': 'GPU 프로그래밍',
            'tensorflow': 'ML 프레임워크',
            'pytorch': 'ML 프레임워크',
            'kubernetes': '컨테이너 오케스트레이션',
            'docker': '컨테이너화'
        }

        # 범위 외 답변 패턴
        self.out_of_scope_patterns = [
            '관련이 없습니다',
            '해당 카테고리',
            '관련 없음',
            '포함되지 않음',
            '다루지 않음',
            '없습니다'
        ]

    def analyze_scope(self, question: str, expected_answer: str,
                      category: str) -> Dict:
        """
        범위 분석

        Args:
            question: 질문 텍스트
            expected_answer: 예상 답변
            category: 카테고리

        Returns:
            범위 분석 결과
        """
        issues = []

        # 1. 질문에서 특정 기술 언급 감지
        specific_mentions = self._detect_specific_mentions(question)

        for tech, description in specific_mentions:
            # 예상 답변에 같은 기술이 있는가?
            if tech.lower() not in expected_answer.lower():
                # 범위 외 답변인가?
                if not self._is_out_of_scope_answer(expected_answer):
                    issues.append({
                        'type': 'ERROR',
                        'message': (
                            f'질문에 "{tech}" ({description})이 있으나 답변에 없음. '
                            f'"{tech}"에 대한 답변이거나 "관련 없음"으로 명시해야 함'
                        ),
                        'severity': 'HIGH',
                        'detected_tech': tech,
                        'tech_description': description
                    })

        # 2. 질문 범위 분석
        question_scope = self._analyze_question_scope(question)

        return {
            'has_scope_issues': len([i for i in issues if i['severity'] == 'HIGH']) > 0,
            'issues': issues,
            'specific_mentions': specific_mentions,
            'question_scope': question_scope,
            'is_out_of_scope_answer': self._is_out_of_scope_answer(expected_answer),
            'recommendation': self._recommend(issues, specific_mentions)
        }

    def _detect_specific_mentions(self, text: str) -> List[Tuple[str, str]]:
        """
        텍스트에서 특정 기술 언급 감지

        Returns:
            [(기술명, 설명), ...]
        """
        found = []
        text_lower = text.lower()

        for tech, description in self.specific_technologies.items():
            if tech in text_lower:
                found.append((tech, description))

        return found

    def _is_out_of_scope_answer(self, answer: str) -> bool:
        """
        답변이 "관련 없음"을 명시하는가?
        """
        answer_lower = answer.lower()
        return any(
            pattern.lower() in answer_lower
            for pattern in self.out_of_scope_patterns
        )

    def _analyze_question_scope(self, question: str) -> Dict:
        """
        질문의 범위 분석

        Returns:
            {
                'is_specific': bool,      # 특정 기술을 언급하는가?
                'is_general': bool,       # 일반적인 개념인가?
                'scope_type': str         # 'specific' | 'general' | 'mixed'
            }
        """
        specific_mentions = self._detect_specific_mentions(question)
        is_specific = len(specific_mentions) > 0

        # 일반적인 개념 체크
        general_patterns = [
            r'(개념|기법|방법|원리|정의|역할|특징)',
            r'(무엇|어떻게|왜|언제|어디)',
            r'기반|지원|활용|포함'
        ]

        is_general = any(
            re.search(pattern, question, re.IGNORECASE)
            for pattern in general_patterns
        )

        if is_specific and is_general:
            scope_type = 'mixed'
        elif is_specific:
            scope_type = 'specific'
        else:
            scope_type = 'general'

        return {
            'is_specific': is_specific,
            'is_general': is_general,
            'scope_type': scope_type,
            'specific_mentions': specific_mentions
        }

    def _recommend(self, issues: List[Dict],
                   specific_mentions: List[Tuple[str, str]]) -> str:
        """권장사항 생성"""
        if not issues and not specific_mentions:
            return "✓ 범위 검증 통과"

        high_severity = [i for i in issues if i['severity'] == 'HIGH']
        if high_severity:
            return (
                f"❌ {len(high_severity)}개 범위 관련 문제 발견\n"
                f"   - 예상답변에 {[i['detected_tech'] for i in high_severity]}에 대한 "
                f"내용이 없거나 '관련 없음'으로 명시해야 함"
            )

        if specific_mentions:
            techs = [t[0] for t in specific_mentions]
            return (
                f"⚠️ 특정 기술 언급 감지: {techs}\n"
                f"   예상답변이 이를 포함하는지 확인하세요"
            )

        return "✓ 범위 검증 통과"


def validate_snowflake_specific(question: str, expected_answer: str,
                                 category: str) -> Dict:
    """
    Snowflake 관련 특별 검증

    Snowflake는 평가 대상 문서에 없으므로
    특별히 처리해야 함
    """
    analyzer = ScopeAnalyzer()
    result = analyzer.analyze_scope(question, expected_answer, category)

    # Snowflake 카테고리에서는 반드시 "관련 없음"이어야 함
    if category == 'Snowflake':
        if not analyzer._is_out_of_scope_answer(expected_answer):
            result['issues'].append({
                'type': 'ERROR',
                'message': (
                    'Snowflake 카테고리의 질문은 반드시 '
                    '"해당 카테고리 문서와 관련이 없습니다"로 답변해야 함'
                ),
                'severity': 'CRITICAL',
                'required_answer': '해당 카테고리 문서와 관련이 없습니다'
            })
            result['has_scope_issues'] = True

    return result
