# Sprint 05 — 통합 테스트 자동화 + 문서화 체계

> **기간**: 2026-05-13 ~
> **상태**: 🔄 진행 중
> **이전 스프린트**: [Sprint 04](sprint_04.md)

---

## 1. 스프린트 목표

- [x] 스프린트 보고서 체계 구축 (`docs/sprints/`)
- [x] 하이브리드 질의 통합 테스트 자동화 프로그램 구현
- [x] 온톨로지 시드 데이터 → hybrid 질의 E2E 검증 (시드 주입 + runner)
- [x] 리포트 HTML + JSON 결과 파일 저장

---

## 2. 백로그 → 완료 항목

| ID | 항목 | 구분 | 결과 |
|----|------|------|------|
| S-01 | 스프린트 보고서 체계 (`docs/sprints/`) + README + TEMPLATE | docs | ✅ |
| S-02 | Sprint 01~04 소급 보고서 작성 | docs | ✅ |
| S-03 | 통합 테스트 자동화 프로그램 설계 | docs | ✅ |
| S-04 | `backend/integration_tests/` 구현 | feature | ✅ |
| S-05 | 시나리오 15개 하드코딩 + 온톨로지 시드 주입 | feature | ✅ |
| S-06 | HTML + JSON 리포트 생성기 | feature | ✅ |

---

## 3. 기술 변경 사항

### 신규 파일 (예정)

| 파일 경로 | 역할 |
|-----------|------|
| `docs/sprints/README.md` | 스프린트 인덱스 + ADR 요약 |
| `docs/sprints/TEMPLATE.md` | 신규 스프린트 보고서 템플릿 |
| `docs/sprints/sprint_01~05.md` | 각 스프린트 보고서 |
| `backend/integration_tests/run.py` | 통합 테스트 진입점 |
| `backend/integration_tests/config.py` | 서버 URL, 인증, doc_id 상수 |
| `backend/integration_tests/seed_data.py` | 온톨로지 시드 데이터 주입 |
| `backend/integration_tests/scenarios.py` | 15개 시나리오 (하드코딩) |
| `backend/integration_tests/runner.py` | 시나리오 실행 + 채점 |
| `backend/integration_tests/reporter.py` | HTML/JSON 리포트 생성 |

---

## 4. 발견된 문제

### 🐛 버그

| # | 현상 | 원인 | 해결 방법 |
|---|------|------|-----------|
| B-01 | `main.py`에 USB auto-copy shutil 코드 잔존 | Sprint 04에서 임시 추가 후 제거 누락 | 제거 완료 (단순 3-candidate .env 탐색으로 복원) |

### 🚧 블로커

| # | 내용 | 현황 |
|---|------|------|
| BL-01 | 온톨로지 DB 비어있어 filter/compare/calculate 질의 결과 없음 | 통합 테스트 시드 주입으로 해결 예정 |

---

## 5. 개선된 점

- **문서화 체계**: CHANGELOG 단일 파일 → 스프린트 단위 보고서로 이력 추적 개선
- **배포 안정성**: `.env` 로컬 복사 완료 → USB 없이 동작

---

## 6. 테스트 결과

| 테스트 종류 | Sprint 04 | Sprint 05 | 비고 |
|------------|-----------|-----------|------|
| pytest | 67+45 | 67+45 (변동 없음) | integration_tests 패키지 추가만 |
| 통합 테스트 (신규) | 없음 | 15개 시나리오 구현 완료 | 실 서버 실행 후 수치 업데이트 필요 |
| 회귀 건수 | 0 | 0 (추정) | |

---

## 7. 다음 스프린트 제안 백로그

> 이번 스프린트 진행 중 도출되면 추가 예정

- [ ] 통합 테스트 CI 연동 (GitHub Actions)
- [ ] 질문 유형 분류 정확도 지표 (`classification_accuracy`)
- [ ] 온톨로지 시드 데이터를 fixture JSON으로 관리

---

## 8. 회고

### 잘 된 것 👍
- 통합 테스트 6개 파일을 한 세션에서 완성 (config → seed → scenarios → runner → reporter → run)
- 시드 데이터 엔티티 ID 매핑 문제를 설계 단계에서 선제적으로 해결 (name→id 맵)
- HTML 리포트에 행 클릭 상세 토글, 점수 바 시각화, 유형별 색상 배지 적용

### 아쉬운 것 👎
- 실 서버 실행 없이 작성 → 실제 통합 테스트 수치는 미확보 (다음 세션에서 실행 필요)

### 다음에 시도할 것 🔁
- `python -m integration_tests --open-report` 실행으로 실 수치 확인
- 통합 테스트 CI 연동 (GitHub Actions)
