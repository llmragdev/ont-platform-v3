# ont_platform CHANGELOG

## v3.0 (개발 중)

상태: 🚧 Phase 1 진행 예정  
경로: `v3/`  
설계서: `docs/v3.0_upgrade_plan.md`, `docs/v3.0_architecture_design.md`

### 주요 변경 예정
- Gemini API 연동으로 실제 AI 답변 합성
- LLM 기반 질의 의도 분류
- 온톨로지 엔티티 Provenance 모델 (출처·신뢰도·버전)
- Repository 패턴 도입 (JSON → SQLite 교체 준비)
- HMAC 인증 미들웨어

---

## v2.0 (2026-05-14, 운영 중)

상태: ✅ 운영 중  
경로: `v2/`

### 주요 내용
- 12개 메뉴 프론트엔드 (React Flow 포함)
- FastAPI 백엔드 + 멀티테넌트 헤더 인증
- 온톨로지 CRUD (스키마·인스턴스·그래프)
- 하이브리드 질의 (`/api/hybrid/ask`) — 템플릿 합성
- 워크플로우 그래프 + SSE 실행 시뮬레이션
- 감사 로그 (JSONL append-only)
- PDF 업로드 + Chroma 벡터 저장 (Gemini embeddings 선택)

---

## v1.0 (legacy)

상태: 🗄️ 보관  
경로: `E:\ontology_edu\claud_v1_legacy\`

### 주요 내용
- 초기 온톨로지 탐색 + 하이브리드 질의 MVP
- JWT 인증 + 단일 테넌트
