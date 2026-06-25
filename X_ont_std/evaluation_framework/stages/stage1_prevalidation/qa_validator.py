"""
Q&A 일관성 검증

평가 시작 전에 모든 Q&A 쌍이 유효한지 검증합니다:
- 예상 답변이 제공 문서에 있는가?
- 질문과 답변의 관련성이 있는가?
- 카테고리와 일치하는가?
"""

from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime


class QAConsistencyValidator:
    """Q&A 쌍의 일관성 검증"""

    def __init__(self):
        """초기화"""
        # 한글/영문 불용어
        self.stopwords_ko = {
            '의', '이', '그', '저', '것', '수', '등', '들', '및', '또는',
            '그리고', '하지만', '따라서', '그러므로', '이를', '그를', '있다',
            '없다', '아니다', '이다', '더'
        }
        self.stopwords_en = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must'
        }

    def validate_pair(self, question: str, expected_answer: str,
                     category: str, documents: List[str]) -> Dict:
        """
        Q&A 쌍 검증

        Args:
            question: 질문 텍스트
            expected_answer: 예상 답변
            category: 카테고리
            documents: 제공 문서 텍스트 리스트

        Returns:
            검증 결과 딕셔너리
        """
        issues = []

        # 1. 길이 검증
        if len(question.strip()) < 20:
            issues.append({
                'type': 'WARNING',
                'message': f'질문이 너무 짧음 ({len(question)}글자, 최소 20글자)',
                'severity': 'LOW'
            })

        if len(expected_answer.strip()) < 50:
            issues.append({
                'type': 'ERROR',
                'message': f'예상답변이 너무 짧음 ({len(expected_answer)}글자, 최소 50글자)',
                'severity': 'HIGH'
            })

        # 2. 키워드 추출
        question_keywords = self._extract_keywords(question)
        answer_keywords = self._extract_keywords(expected_answer)
        doc_keywords = self._extract_doc_keywords(documents)

        # 3. 질문-답변 관련성 검증
        keyword_overlap = set(question_keywords) & set(answer_keywords)
        overlap_ratio = len(keyword_overlap) / max(len(question_keywords), 1)

        if overlap_ratio < 0.2:  # 20% 미만이면 경고
            issues.append({
                'type': 'WARNING',
                'message': f'질문과 예상답변의 키워드 겹침이 낮음 ({overlap_ratio:.1%})',
                'severity': 'MEDIUM',
                'overlap_ratio': overlap_ratio
            })

        # 4. 문서 기반 검증
        answer_concepts = [kw for kw in answer_keywords if len(kw) > 2]
        answer_in_docs = self._check_answer_in_documents(
            expected_answer, answer_concepts, documents
        )

        if not answer_in_docs:
            issues.append({
                'type': 'ERROR',
                'message': '예상답변의 핵심 개념이 제공 문서에 없음 (일반 지식?)',
                'severity': 'HIGH',
                'answer_concepts': answer_concepts
            })

        # 5. 문체 검증
        if self._is_too_generic(expected_answer):
            issues.append({
                'type': 'WARNING',
                'message': '예상답변이 너무 일반적임 (구체성 낮음)',
                'severity': 'MEDIUM'
            })

        # 6. 범위 외 답변 검증 ("관련 없습니다" 패턴)
        if "관련이 없습니다" in expected_answer or "관련 없음" in expected_answer:
            # 범위 외 답변의 경우 문서 기반 검증 불필요
            issues = [i for i in issues if i['type'] != 'ERROR']

        # 점수 계산
        score = 100
        for issue in issues:
            if issue['severity'] == 'HIGH':
                score -= 30
            elif issue['severity'] == 'MEDIUM':
                score -= 15
            elif issue['severity'] == 'LOW':
                score -= 5

        score = max(0, score)

        return {
            'is_valid': len([i for i in issues if i['severity'] == 'HIGH']) == 0,
            'issues': issues,
            'score': score,
            'errors': len([i for i in issues if i['type'] == 'ERROR']),
            'warnings': len([i for i in issues if i['type'] == 'WARNING']),
            'recommendation': self._recommend(issues),
            'question_keywords': question_keywords,
            'answer_keywords': answer_keywords,
            'timestamp': datetime.now().isoformat()
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        # 단어 분리
        words = text.split()
        # 불용어 제거 및 길이 필터링
        keywords = [
            w.lower() for w in words
            if len(w) > 2
            and w.lower() not in self.stopwords_ko
            and w.lower() not in self.stopwords_en
        ]
        return list(set(keywords))  # 중복 제거

    def _extract_doc_keywords(self, documents: List[str]) -> List[str]:
        """문서들에서 키워드 추출"""
        all_keywords = []
        for doc in documents:
            keywords = self._extract_keywords(doc)
            all_keywords.extend(keywords)
        return list(set(all_keywords))

    def _check_answer_in_documents(self, answer: str, concepts: List[str],
                                   documents: List[str]) -> bool:
        """
        답변이 문서에 기반하는지 확인

        - 답변의 핵심 개념들이 문서에 있는가?
        - 최소 2개 이상의 개념이 있어야 함
        """
        if not concepts:
            return False

        doc_text = ' '.join(documents).lower()
        found_concepts = [
            c for c in concepts
            if c.lower() in doc_text
        ]

        # 최소 2개 이상의 개념이 문서에 있어야 함
        return len(found_concepts) >= 2

    def _is_too_generic(self, answer: str) -> bool:
        """답변이 너무 일반적인지 확인"""
        generic_patterns = [
            r'[를|을|이|가] (있|수|것|사항)으로 (알려져|생각되|판단)됩니다',
            r'(일반적으로|보통|전통적으로) (생각|언급)된',
            r'(매우|많이|여러|다양한) (관점|방법|형태)' ,
            r'^(것이다|이다|있다|것이므로)',
        ]

        count = 0
        for pattern in generic_patterns:
            if re.search(pattern, answer):
                count += 1

        return count >= 2  # 2개 이상이면 너무 일반적

    def _recommend(self, issues: List[Dict]) -> str:
        """권장사항 생성"""
        if not issues:
            return "✓ 검증 통과"

        high_severity = [i for i in issues if i['severity'] == 'HIGH']
        if high_severity:
            return f"❌ {len(high_severity)}개 심각한 문제 수정 필요"

        warnings = [i for i in issues if i['type'] == 'WARNING']
        if warnings:
            return f"⚠️ {len(warnings)}개 경고 항목 검토 권장"

        return "✓ 검증 통과 (경고 있음)"


class BatchQAValidator:
    """여러 Q&A 쌍을 일괄 검증"""

    def __init__(self, documents: List[str]):
        """
        초기화

        Args:
            documents: 평가 대상 문서 리스트
        """
        self.validator = QAConsistencyValidator()
        self.documents = documents

    def validate_all(self, qa_pairs: List[Dict]) -> Dict:
        """
        모든 Q&A 쌍 검증

        Args:
            qa_pairs: [{'problem_id': str, 'question': str,
                        'expected_answer': str, 'category': str}, ...]

        Returns:
            전체 검증 결과
        """
        results = []

        for pair in qa_pairs:
            result = self.validator.validate_pair(
                question=pair['question'],
                expected_answer=pair['expected_answer'],
                category=pair['category'],
                documents=self.documents
            )

            results.append({
                'problem_id': pair['problem_id'],
                'category': pair['category'],
                **result
            })

        # 요약 통계
        passed = len([r for r in results if r['is_valid']])
        failed = len([r for r in results if not r['is_valid']])
        total_score = sum(r['score'] for r in results) / len(results)

        summary = {
            'total_validated': len(results),
            'passed': passed,
            'failed': failed,
            'pass_rate': f"{passed / len(results) * 100:.1f}%",
            'average_score': f"{total_score:.1f}",
            'critical_issues': [
                r['problem_id'] for r in results
                if not r['is_valid'] and r['errors'] > 0
            ]
        }

        return {
            'results': results,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
