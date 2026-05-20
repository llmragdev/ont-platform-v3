# Claude 통합 — 추가 작업 (Next Steps)

> 미완료 백로그입니다.
> 완료된 항목의 상세 결과는 [CHANGELOG.md](CHANGELOG.md), 전체 진행 상태 요약은 [PROGRESS.md](PROGRESS.md) 참조.

## 우선순위 한눈에

| # | 항목 | 분류 | 난이도 | 사람 기준 예상시간 | 의존성 | 상태 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 브라우저 학습 시나리오 5종 클릭 검증 | 검증 | 낮음 | 30분 | 없음 | ✅ API/E2E 자동화로 대체 ([CHANGELOG](CHANGELOG.md)) |
| 2 | Gemini 실제 답변 품질 확인 | 검증 | 낮음 | 30분 | API 키 한도 회복 | ✅ ([CHANGELOG](CHANGELOG.md), [LLM_EVAL](기타_분석/LLM_EVAL.md)) — 모델 gemini-2.5-flash로 갱신 |
| 3 | LLM Gateway 키 로테이션 | 보강 | 낮음 | 1시간 | #2 결과 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 4 | `evaluate.py` RAG 자동 평가 | 보강 | 중간 | 3시간 | #2 결과 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 5 | Playwright 프론트 E2E | 보강 | 중간 | 4시간 | 없음 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 6 | PostgreSQL Repository | 운영 | 중간 | 4시간 | 없음 | ✅ ([CHANGELOG](CHANGELOG.md)) — 실제 DB 연결은 사용자 환경에서 검증 |
| 7 | 실제 인증 (JWT) — 백엔드 | 운영 | 높음 | 1일 | 없음 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 7b | JWT 프론트 통합 (로그인 페이지) | 운영 | 중간 | 4시간 | #7 | ✅ ([CHANGELOG](CHANGELOG.md)) — 하위호환 유지, E2E 6/6 |
| 8 | OpenTelemetry 관측성 | 운영 | 높음 | 1일 | 없음 | ✅ ([CHANGELOG](CHANGELOG.md)) — Jaeger 실연결은 사용자 환경에서 |
| 9 | Docker compose 패키징 | 운영 | 낮음 | 2시간 | #6 권장 | ✅ ([CHANGELOG](CHANGELOG.md)) — 빌드 실행은 사용자 환경에서 확인 |
| 10 | 교육 가이드 슬라이드/스크립트 | 교육 | 중간 | 반나절 | #1 후 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| WG-1 | WorkflowGraph Phase 1 (React Flow + CRUD) | 시각화 | 중간 | 1일 | 없음 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| WG-2 | WorkflowGraph Phase 2 (서버 실행 + SSE) | 시각화 | 높음 | 1일 | WG-1 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| WG-3 | WorkflowGraph Phase 3 (거버넌스 통합) | 시각화 | 중간 | 반나절 | WG-2 | ✅ ([CHANGELOG](CHANGELOG.md)) — 노드 타입별 권한 + 도메인 노드 2종 |
| **온톨로지 재설계 Phase 1** | 스키마 외부화 (ontology.default.json) | 재설계 | 중간 | 1일 | 없음 | ✅ ([CHANGELOG](CHANGELOG.md)) — pytest 67/67 |
| 온톨로지 재설계 Phase 2 | Generic graph traversal + object_context 일반화 | 재설계 | 중간 | 4시간 | Phase 1 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 온톨로지 재설계 Phase 3 | 관계 CRUD API + 액션 스키마 통합 | 재설계 | 높음 | 1일 | Phase 2 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 온톨로지 재설계 Phase 4 | 온톨로지 그래프 캔버스 UI | 재설계 | 중간 | 1일 | Phase 3 | ✅ ([CHANGELOG](CHANGELOG.md)) |
| 온톨로지 재설계 Phase 5 | sensitive 자동 마스킹 | 재설계 | 낮음 | 4시간 | Phase 1 | ✅ ([CHANGELOG](CHANGELOG.md)) |

상세 설계서: [docs/note/온톨로지_재설계_보고서.md](note/온톨로지_재설계_보고서.md)

> **시작 한 줄**: `"NEXT_STEPS.md의 #N 작업 시작해줘"`.
> 사람 기준 예상시간은 사람이 직접 작업한다고 가정한 추정치. 제가 코드 작성만 하면 보통 1/8~1/4 수준입니다.

---

| RAG | PDF 업로드 + Chroma 벡터 검색 + 하이브리드 BM25+Vector 질의 + 프론트엔드 PDF 관리 UI | 구현 | 중간 | 반나절 | 없음 | ✅ (2026-05-12) — 67/67 pytest |

> **모든 백로그 항목 완료**. 본 문서는 추가 백로그가 생길 때까지 유지됩니다.

## 향후 후보 (필요 시 사용자가 추가)

- [ ] **노드 타입 외부화** — 관리자가 코드 수정 없이 새 노드 타입(JSON 정의) 추가
- [ ] **evaluate.py에 LLM 품질 룰 추가** — 답변 형식 준수율 / 한국어 비율 / 환각 검출
- [ ] **그래프 실행 캐시** — 같은 워크플로우 + 같은 입력 시 결과 캐시
- [ ] **CI 통합** — GitHub Actions에서 backend pytest + scenarios + evaluate + Playwright 자동 실행
- [ ] **BPMN 2.0 지원** — 엔터프라이즈 고객 요구 시 bpmn-js 전환 검토
- [ ] **다국어 LLM 프롬프트** — 영어/한국어 외 일본어/중국어 등
