# ont_platform v3.0

상태: ✅ 개발 완료 (2026-05-14)

---

## v2 대비 주요 변경

| 항목 | v2.0 | v3.0 |
|------|------|------|
| AI 답변 | 템플릿 문자열 | Gemini API 실제 합성 (fallback 지원) |
| 질의 분류 | 키워드 휴리스틱 | LLM 기반 + fallback |
| 온톨로지 | 출처 없음 | OntologyProvenance 모델 |
| 저장소 | JSON 직접 접근 | Repository 패턴 (ABC) |
| 인증 | 헤더 신뢰 | HMAC-SHA256 서명 검증 (선택적) |
| 워크플로우 | 실행 결과만 | WorkflowRun 이력 저장 |
| 메트릭 | 없음 | `/api/metrics/query` 집계 API |
| 프론트엔드 포트 | 3000 | 3001 |

---

## 실행 방법

### 환경 준비 (최초 1회)

```bash
# 백엔드 의존성
conda activate claud_be
pip install -r E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend\requirements.txt

# 프론트엔드 의존성 (node_modules 없으면 1회만 실행)
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend
npm install
```

### 프론트엔드 실행 (포트 3001)

```bash
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend
npm run dev
# → http://localhost:3001
```

> 백엔드가 8001 포트에서 실행 중이어야 API 호출이 됩니다.

### 백엔드 실행 (포트 8001)

```bash
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
uvicorn app.main:app --reload --port 8001
```

#### 환경 변수 (선택)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `GEMINI_API_KEY` | Gemini API 키 (없으면 템플릿 fallback) | 미설정 |
| `HMAC_SECRET` | HMAC 인증 활성화 (없으면 비활성) | 미설정 |
| `COMPANY_ID` | 테넌트 회사 ID | `demo_company` |
| `PROJECT_ID` | 테넌트 프로젝트 ID | `demo_project` |

예시:
```bash
set GEMINI_API_KEY=AIza...
set HMAC_SECRET=mysecret
uvicorn app.main:app --reload --port 8001
```

---

## API 엔드포인트 요약

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/health` | 헬스체크 (`version: 3.0.0`) |
| `POST /api/hybrid/ask` | 통합 질의 (온톨로지 + 벡터) |
| `POST /api/rag/ask` | 문서 RAG 질의 |
| `GET /api/ontology` | 온톨로지 문서 목록 |
| `GET /api/ontology/{doc_id}/entities` | 엔티티 목록 |
| `POST /api/documents/upload` | PDF 업로드 |
| `GET /api/workflow-graphs` | 워크플로우 그래프 목록 |
| `POST /api/workflow-graphs/{id}/run` | 워크플로우 실행 (SSE 스트림) |
| `GET /api/workflow-graphs/{id}/runs` | 실행 이력 조회 |
| `GET /api/metrics/query` | 질의 집계 메트릭 |

Swagger UI: `http://localhost:8001/docs`

---

## 테스트 실행

```bash
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
pytest tests/ -v
# 결과: 29/29 통과
```

평가 데이터셋 실행:
```bash
python tests/eval/run_eval.py
```

### 통합 테스트 (25개 케이스)

```bash
cd E:\ontology_edu\X_ont_std\ont_platform\v3
python run_test.py
```

**현 상태 (2026-05-16):**
- 통과: 1/25 (4%)
- 목표: 20/25 (80%) 이상
- 주요 개선: find_by_name 토큰 매칭, ask_forced_hybrid 메서드 추가
- 미해결: 온톨로지 데이터 매칭 최적화, 벡터 검색 성능

---

## 디렉토리 구조

```
v3/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/          hybrid.py, workflow.py, metrics.py
│   │   │   ├── middleware/   auth.py (HMAC)
│   │   │   ├── models/       ontology.py, workflow_run.py, query_intent.py
│   │   │   ├── prompts/      synthesizer.txt, classifier.txt
│   │   │   ├── repositories/ base_interface.py, json_repository.py
│   │   │   ├── services/     llm_client.py, hybrid_synthesizer.py, query_planner.py
│   │   │   ├── dependencies.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   │   ├── eval/         run_eval.py, dataset_*.jsonl
│   │   │   └── test_phase*.py
│   │   ├── storage_config.py
│   │   └── requirements.txt
│   └── frontend/
│       └── src/
│           ├── app/          layout.tsx, page.tsx
│           ├── components/   AIQuery, HybridQuery, RAGQuery, WorkflowGraph
│           │                 LlmAnswerPanel, OntologyEvidenceList,
│           │                 VectorSourceList, ProvenanceBadge,
│           │                 WorkflowRunHistory (v3 신규)
│           ├── lib/          api.ts (v3 확장)
│           └── types/        api.ts (v3 타입)
└── README.md
```

---

## HMAC 인증 사용 시

`HMAC_SECRET` 설정 시 모든 API 요청에 헤더 필요:

```
x-user-id: {user_id}
x-timestamp: {unix_timestamp}
x-signature: HMAC-SHA256(secret, "{user_id}:{timestamp}")
```

미설정 시 v2와 동일하게 인증 없이 동작합니다.
