# 03. 프로젝트 관리 및 운영 표준 (Project Governance & SOP)

## 1. 개발 및 코드 품질 표준

### 1.1 완료 정의 (Definition of Done: DoD)
모든 Task는 다음의 5가지 체크리스트를 통과해야 'Done'으로 표시됩니다.
1. **코드 품질**: 린트(`black`, `flake8`) 및 정적 분석 통과.
2. **자동화된 DoD 테스트**: `tests/automated_dod_check.py`를 통해 명시된 시나리오가 100% 통과됨 (수동 확인 불가).
3. **보안 검증**: 신규 API가 `IdentityContext`를 사용하며 타 테넌트 침범 불가능함이 코드로 증명됨.
4. **문서화**: 관련 설계서 및 스프린트 결과 보고서 업데이트 (상대 경로 링크 정확성 확인).
5. **UI 일관성**: 디자인 시스템 가이드에 따른 프리미엄 UI 적용 여부.

### 1.2 테스트 전략
- **Unit Test**: 개별 모듈 로직 검증.
- **Integration Test**: 테넌트 간 데이터 침범 여부 집중 검증 (Cross-tenant access test).
- **QA Test**: 시나리오 기반의 E2E 테스트 (Playwright 활용).
- **LLM Eval**: 답변의 정확성, 무결성, 신뢰성 자동 평가.

---

## 2. 스프린트 및 버전 관리

### 2.1 스프린트 프로세스
1. **Planning**: 백로그에서 Task 추출 및 수용 기준(Acceptance Criteria) 정의.
2. **Implementation**: TDD(Test Driven Development) 방식으로 개발.
3. **Review**: 설계서 및 요구사항과의 일관성 검토.
4. **Retrospective**: KPT(Keep, Problem, Try) 방식의 회고.

### 2.2 문서화 규칙
- 모든 스프린트 이력은 `docs/sprints/sprint_NN.md`로 관리.
- 기술적 난제 해결 과정은 `docs/tech_notes/`에 별도 기록.
- 주요 결정 사항은 `ADR(Architecture Decision Record)` 형식으로 README에 요약.

---

## 3. 운영 환경 (SOP)

### 3.1 환경 변수 관리
- `.env.example`을 철저히 관리하여 신규 참여자의 설정 편의성 제공.
- API Key 등 보안 민감 정보는 절대로 Git에 노출하지 않음.

### 3.2 배포 전 검증 (Staging)
- 실제 데이터와 유사한 시드 데이터를 활용하여 하이브리드 질의의 정확도 측정.
- 대용량 문서 업로드 시 시스템 리소스(CPU/RAM) 사용량 체크.

---

## 4. 최종 품질 목표 (KPIS)
- **보안성**: 권한 위반 접근 차단율 100%.
- **정확성**: 구조형 질의 정답률 95% 이상.
- **성능**: 평균 응답 시간 3초 이내 (LLM 포함).
- **관리성**: 코드 수정 없이 신규 도메인 확장 가능성 100%.
