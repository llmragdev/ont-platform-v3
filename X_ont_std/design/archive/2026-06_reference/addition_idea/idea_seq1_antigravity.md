# Addition Idea for PHASE8/v5: idea_seq1_antigravity

이 문서는 Antigravity AI 코딩 어시스턴트가 제안한 `ont_platform` v5 설계 및 구현(P0/P1) 단계에서의 보완 설계 및 구현 아이디어를 기록합니다.

---

## 💡 주요 추가 아이디어

### 1. `answer_policies.jsonl`의 단일 소스(SSOT) 아키텍처 구체화
*   **배경**: `answer_policies.jsonl` 파일은 정답표 보정(평가)과 실제 API의 검증(EvidenceGate) 모두에 동일하게 적용되어야 하는 계약 파일입니다.
*   **아이디어**: 
    *   API 서버가 구동될 때 `answer_policies.jsonl`을 로드하여 메모리에 `PolicyRule` 객체 리스트로 빌드합니다.
    *   `EvidenceGate` 내부에 **PolicyFilter** 또는 **RegexMatcher** 모듈을 장착하여, LLM을 호출하기 전에 들어오는 질문이 정의된 룰 패턴 중 하나에 매칭되는지 선제 검사합니다.
    *   **효과**: 코드 변경 없이 JSONL 정책 파일 업데이트만으로 실시간 서빙 차단 및 평가 정답 보정을 즉각 동형 적용(Isomorphic Policy Enforcement)할 수 있습니다.
*   **구현 방향 (예시)**:
    ```python
    import re
    from pathlib import Path
    from pydantic import BaseModel

    class PolicyRule(BaseModel):
        question_id: str | None = None
        question_pattern: str  # Regex 패턴
        category: str
        target_response: str
        applies_to: list[str]

    class PolicyEngine:
        def __init__(self, policy_file_path: Path):
            self.rules = self.load_rules(policy_file_path)

        def load_rules(self, path: Path) -> list[PolicyRule]:
            # JSONL 파싱 후 rules 로드
            ...

        def match_explicit_policy(self, question: str) -> PolicyRule | None:
            for rule in self.rules:
                if "evidence_gate" in rule.applies_to:
                    if re.search(rule.question_pattern, question, re.IGNORECASE):
                        return rule
            return None
    ```

---

### 2. `Question Analyzer`의 카테고리 판정과 `EvidenceGate` 임계치의 연계 및 우선순위
*   **배경**: RAG 검색 스코어가 매우 높은 문서가 존재하더라도, 질문 카테고리와 검색 문서 카테고리가 다른 경우가 발생할 수 있습니다.
*   **아이디어**:
    *   `Question Analyzer`가 분류한 `question_category`와 검색된 문서/온톨로지 노드의 카테고리(메타데이터)가 불일치(`category_mismatch`)할 경우, 검색 스코어의 높고 낮음에 상관없이 즉시 `EvidenceGate`에서 차단합니다.
    *   **우선순위 강화**: 
        1. Explicit Policy Match (명시적 룰 차단)
        2. Category Mismatch (카테고리 불일치 차단 - 검색 스코어 무시)
        3. Threshold Check (검색 관련성 스코어 미달 차단)
    *   **효과**: RAG 모델이나 온톨로지 탐색기가 무관한 카테고리 질문에 대해 우연히 높은 유사도 스코어를 내더라도, 카테고리 수준에서 강제 차단하여 Snowflake(STD-S)와 같은 범위 외 질문 오답을 완벽히 방어합니다.

---

### 3. "no-answer 시 LLM 호출 0회"를 검증하기 위한 모킹(Mocking) 테스트 기준 수립
*   **배경**: 수용 기준(Acceptance Criteria) 중 "no-answer 시 LLM 호출 0회"는 비용 절감 및 환각 차단을 위해 매우 중요합니다.
*   **아이디어**:
    *   회귀 테스트 러너(Regression Test Runner)를 구현할 때, 실제 LLM 클라이언트(OpenAI, Gemini SDK 등)의 API 호출부에 래퍼(Wrapper)나 카운터를 탑재합니다.
    *   `STD-S-01 ~ STD-S-08`과 같이 답변 차단이 예상되는 쿼리를 수행할 때, LLM 클라이언트 모킹 객체의 호출 횟수가 `0`인지 확인하는 Assert문을 테스트 프레임워크에 강제합니다.
    *   **효과**: 개발자 실수로 `EvidenceGate`가 우회되거나 예외 상황에서 LLM 호출이 새나가는 것을 빌드/테스트 타임에 완전히 차단할 수 있습니다.

---

## 📌 향후 v5 로드맵 반영 계획
*   **P0 (MVP)**: `PolicyEngine` 클래스 설계 및 JSONL 로드 로직 구현, LLM 호출 모킹 테스트 케이스 1개 이상 추가
*   **P1 (정책 통합)**: `answer_policies.jsonl` 단일 소스 연동 완료 및 회귀 러너에 LLM Call Counter 검증 결합
