# LLM Gateway — Gemini 임베딩/생성 API 게이트웨이

멀티테넌트 RAG 시스템에서 LLM 레이어를 분리하는 중앙 게이트웨이.

## 아키텍처

```
[RAG 서비스 - src_claud v2]
        ↓ HTTP POST /api/v1/embed
        ↓ HTTP POST /api/v1/generate
[LLM Gateway :8010]           ← API 키 중앙 관리, 임베딩 캐싱
        ↓
[Google Gemini API]           ← gemini-embedding-001 / gemini-2.5-flash-lite
```

## 실행

```bash
cd E:\ontology_edu\X_rag_std\src_agents\llm_gateway
conda activate .\.conda
pip install -r requirements.txt
uvicorn app.main:app --port 8010 --reload
```

**주의**: `.env` 파일은 이미 설정되어 있습니다. (Gemini API 키 포함)

## 환경변수 (.env)

현재 `.env`에 설정된 Gemini API 키 (우선순위: 3K → 20K → 무료):

| 키 | 한도 | 상태 | 설명 |
|----|------|------|------|
| `GEMINI_API_KEY1` | 3,000원 | 유료 [PRIMARY] | Gemini Project namkyu 2026 |
| `GEMINI_API_KEY2` | 20,000원 | 유료 [SECONDARY] | my Project - paid |
| `GEMINI_API_KEY3` | 무료 | [FALLBACK] | Gemini Project - new1 |
| `GEMINI_API_KEY4` | 무료 | [FALLBACK] | Gemini Project-2026 |
| `GEMINI_API_KEY` | 기본값 | - | KEY1 (3,000원) |

**라운드 로빈 순환**: KEY1(3K) → KEY2(20K) → KEY3 → KEY4 → KEY1...

## 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/embed` | 텍스트 임베딩 (캐싱) |
| POST | `/api/v1/generate` | LLM 응답 생성 |
| POST | `/api/v1/generate/stream` | LLM 스트리밍 (SSE) |
| GET | `/api/v1/health` | Gemini 연결 상태 |

## src_claud v2 연동

```bash
set EMBEDDING_PROVIDER=gemini_http
set LLM_PROVIDER=gemini_http
set LLM_GATEWAY_URL=http://localhost:8010
```

## 임베딩 캐시

- SHA256(model::text) → 벡터 인메모리 캐시
- TTL 3600초 (1시간), 최대 10,000건
- 동일 문서 재업로드 시 Gemini API 호출 없음
