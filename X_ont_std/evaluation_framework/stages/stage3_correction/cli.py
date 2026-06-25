"""
정답 보정 대화형 CLI

사용자로부터 정답을 입력받아 구조화된 데이터로 저장합니다:

1. 대화형 정답 입력
   - 현재 정답 표시
   - 새 정답 입력
   - 수정 이유 입력

2. 검증 및 저장
   - 입력 값 검증
   - JSON으로 저장
   - 변경 이력 기록
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class AnswerCorrectionCLI:
    """정답 보정 대화형 인터페이스"""

    def __init__(self, output_dir: Path = None):
        """
        초기화

        Args:
            output_dir: 보정 데이터 저장 디렉토리
        """
        self.output_dir = output_dir or Path(
            "E:/ontology_edu/X_ont_std/evaluation_framework/data/corrections"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.corrections = []

    def run_correction_session(self, qa_pairs: List[Dict]) -> List[Dict]:
        """
        정답 보정 세션 실행

        Args:
            qa_pairs: [
                {
                    'problem_id': str,
                    'question': str,
                    'current_expected_answer': str,
                    'category': str,
                    'team_accuracy': float
                },
                ...
            ]

        Returns:
            [
                {
                    'problem_id': str,
                    'correction_type': 'KEPT' | 'MODIFIED' | 'NEW_ANSWER' | 'SKIPPED',
                    'original_answer': str,
                    'corrected_answer': str,
                    'correction_reason': str,
                    'evidence': [...],
                    'review_status': 'APPROVED' | 'PENDING'
                },
                ...
            ]
        """
        print("\n" + "="*70)
        print("정답 보정 세션")
        print("="*70)
        print(f"세션 ID: {self.session_id}")
        print(f"총 {len(qa_pairs)}개 문항 중 필요한 것만 수정하세요")
        print("\n옵션: 1=유지, 2=수정, 3=새답변, 4=스킵, Q=종료\n")

        flagged_items = self._identify_flagged_items(qa_pairs)

        for idx, qa in enumerate(flagged_items, 1):
            print(f"\n{'='*70}")
            print(f"[{idx}/{len(flagged_items)}] {qa['problem_id']}")
            print(f"{'='*70}")

            # 현재 상태 표시
            self._display_qa_item(qa)

            # 사용자 입력
            choice = self._get_user_choice()

            if choice == '1':
                # 유지
                self.corrections.append(self._create_correction(
                    qa, 'KEPT', qa['current_expected_answer']
                ))

            elif choice == '2':
                # 수정
                new_answer = self._get_multiline_input("새 정답을 입력하세요:")
                reason = input("\n수정 사유: ").strip()

                if self._validate_answer(new_answer, qa['category']):
                    self.corrections.append(self._create_correction(
                        qa, 'MODIFIED', new_answer, reason
                    ))
                else:
                    print("❌ 검증 실패. 유지로 처리합니다.")
                    self.corrections.append(self._create_correction(
                        qa, 'KEPT', qa['current_expected_answer']
                    ))

            elif choice == '3':
                # 새 정답
                new_answer = input("새로운 정답을 제시하세요: ").strip()
                reason = input("새 정답 근거: ").strip()

                if new_answer and reason:
                    self.corrections.append(self._create_correction(
                        qa, 'NEW_ANSWER', new_answer, reason
                    ))

            elif choice == '4':
                # 스킵
                self.corrections.append(self._create_correction(
                    qa, 'SKIPPED', qa['current_expected_answer']
                ))

            elif choice.upper() == 'Q':
                # 종료
                print("\n세션 종료됨")
                break

        return self.corrections

    def save_corrections(self) -> Path:
        """보정 데이터 저장"""
        output_file = (
            self.output_dir / f"{self.session_id}_corrections.json"
        )

        data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'total_processed': len(self.corrections),
            'corrections': self.corrections
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 보정 데이터 저장: {output_file}")
        return output_file

    def _identify_flagged_items(self, qa_pairs: List[Dict]) -> List[Dict]:
        """검토 필요 항목 식별"""
        flagged = []

        for qa in qa_pairs:
            # Stage 2에서 제약이 적용되거나 점수가 의심스러운 항목
            if qa.get('needs_review') or qa.get('accuracy_score', 0) > 80:
                flagged.append(qa)

        return flagged

    def _display_qa_item(self, qa: Dict):
        """Q&A 항목 표시"""
        print(f"\n📝 질문: {qa['question'][:100]}...")
        print(f"📂 카테고리: {qa['category']}")
        print(f"📊 현재 팀 정확도: {qa.get('team_accuracy', 'N/A')}%")

        current_answer = qa['current_expected_answer']
        print(f"\n✓ 현재 정답:")
        if len(current_answer) > 200:
            print(f"  {current_answer[:200]}...")
        else:
            print(f"  {current_answer}")

    def _get_user_choice(self) -> str:
        """사용자 선택 입력"""
        while True:
            choice = input("\n선택 (1-4, Q): ").strip().upper()
            if choice in ['1', '2', '3', '4', 'Q']:
                return choice
            print("❌ 잘못된 입력. 1-4 또는 Q를 입력하세요.")

    def _get_multiline_input(self, prompt: str) -> str:
        """여러 줄 입력 받기"""
        print(prompt)
        print("(여러 줄 입력 가능, 끝나면 'END' 입력)")

        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)

        return '\n'.join(lines)

    def _create_correction(self, qa: Dict, correction_type: str,
                          answer: str, reason: str = None) -> Dict:
        """보정 객체 생성"""
        return {
            'problem_id': qa['problem_id'],
            'category': qa['category'],
            'question': qa['question'][:100],

            'original_expected_answer': qa['current_expected_answer'],
            'corrected_expected_answer': answer,

            'correction_type': correction_type,
            'correction_reason': reason or '',

            'evidence': qa.get('evidence', []),
            'team_accuracy_before': qa.get('team_accuracy', 0),

            'review_status': 'PENDING' if correction_type != 'SKIPPED' else 'SKIPPED',
            'timestamp': datetime.now().isoformat()
        }

    def _validate_answer(self, answer: str, category: str) -> bool:
        """정답 검증"""
        # 최소 길이
        if len(answer) < 20:
            print("❌ 정답이 너무 짧습니다 (최소 20글자)")
            return False

        # 너무 길지 않은가?
        if len(answer) > 5000:
            print("❌ 정답이 너무 길습니다 (최대 5000글자)")
            return False

        # 범위 외 답변 확인
        if category == "Snowflake":
            if "관련이 없습니다" not in answer:
                print(f"⚠️  경고: {category} 카테고리의 정답은 '관련이 없습니다'를 포함해야 합니다")
                confirm = input("계속하시겠습니까? (Y/N): ").strip().upper()
                if confirm != 'Y':
                    return False

        return True


class CorrectionValidator:
    """정답 보정 검증"""

    @staticmethod
    def validate_corrections(corrections: List[Dict]) -> Dict:
        """정답 보정 검증"""
        issues = []
        warnings = []

        for correction in corrections:
            # 1. 수정된 항목만 검증
            if correction['correction_type'] == 'SKIPPED':
                continue

            # 2. 정답 길이 검증
            answer = correction.get('corrected_expected_answer', '')
            if len(answer) < 20:
                issues.append({
                    'problem_id': correction['problem_id'],
                    'type': 'INVALID_LENGTH',
                    'message': '정답이 너무 짧음'
                })

            # 3. 범위 외 답변 검증
            if correction['category'] == 'Snowflake':
                if "관련이 없습니다" not in answer:
                    warnings.append({
                        'problem_id': correction['problem_id'],
                        'type': 'MISSING_OUT_OF_SCOPE_MARKER',
                        'message': 'Snowflake 정답에 "관련이 없습니다" 없음'
                    })

            # 4. 수정 이유 검증
            if not correction.get('correction_reason'):
                warnings.append({
                    'problem_id': correction['problem_id'],
                    'type': 'MISSING_REASON',
                    'message': '수정 이유가 없음'
                })

        return {
            'total_corrections': len(corrections),
            'issues': issues,
            'warnings': warnings,
            'is_valid': len(issues) == 0,
            'validation_status': (
                'PASS' if len(issues) == 0 else 'FAIL'
            )
        }


def interactive_correction_session(qa_pairs: List[Dict]) -> Dict:
    """대화형 정답 보정 세션 실행"""
    cli = AnswerCorrectionCLI()

    # 1. 정답 입력
    print("\n[Step 1] 정답 입력 중...")
    corrections = cli.run_correction_session(qa_pairs)

    # 2. 검증
    print("\n[Step 2] 입력 검증 중...")
    validation = CorrectionValidator.validate_corrections(corrections)

    if not validation['is_valid']:
        print(f"\n❌ 검증 실패: {len(validation['issues'])}개 문제")
        for issue in validation['issues']:
            print(f"  - {issue['problem_id']}: {issue['message']}")
        return None

    if validation['warnings']:
        print(f"\n⚠️  경고: {len(validation['warnings'])}개")
        for warning in validation['warnings']:
            print(f"  - {warning['problem_id']}: {warning['message']}")

    # 3. 저장
    print("\n[Step 3] 보정 데이터 저장 중...")
    output_file = cli.save_corrections()

    return {
        'corrections': corrections,
        'validation': validation,
        'output_file': str(output_file)
    }
