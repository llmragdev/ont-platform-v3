# Codex 작성: v03-2 3개 코드 평가 및 개선 제안

작성일: 2026-05-15

## 1. 평가 대상

본 문서는 `RAG_표준_설계_v1.3.md`를 기준으로 v03-2 시점의 3개 구현체를 다시 평가한다.

| 구분 | 평가 경로 | 확인 결과 |
|------|-----------|-----------|
| Codex | `src_agents/src_codex/v3` | FastAPI 구현, Chroma/Local JSON adapter, Streaming RAG, Alembic, 테스트 17개 통과 |
| Claude | `src_agents/src_claud/v3` | FastAPI 구현, Chroma/Local JSON adapter, Streaming RAG, 독립 테스트 17개 통과 |
| Antigravity | `src_agents/src_antigravity/v3` | FastAPI 구현, Streaming RAG, Index Swap API 추가, 독립 테스트 1개 실패 |

## 2. 검증 결과

실행한 명령과 결과는 다음과 같다.

```text
src_codex/v3
python -m pytest -q
결과: 17 passed
```

```text
src_claud/v3
python -m pytest -q
결과: 17 passed
```

```text
src_antigravity/v3
python -m pytest -q test_v3_standard.py
결과: 2 passed, 1 failed
주요 실패 원인: 테스트가 실제 LLM Gateway /api/v1/embed 연결을 요구하며, Gateway 미기동 시 EmbeddingError 발생
```

Antigravity의 실패는 단순 문법 오류가 아니라 테스트 격리성 문제다. v1.3의 "fallback 금지" 원칙 자체는 맞게 적용했지만, 단위/통합 테스트에서 외부 Gateway를 mock 또는 fixture로 대체하지 않아 재현성이 떨어진다.

## 3. 종합 순위

| 순위 | 구현체 | 점수 | 판단 |
|------|--------|------|------|
| 1 | `src_codex/v3` | 9.1 / 10 | 표준 반영 범위, 테스트 안정성, 문서화, Alembic까지 가장 균형적 |
| 2 | `src_claud/v3` | 8.8 / 10 | 구현 완성도와 테스트 독립성이 좋고 Chroma 경계가 명확함 |
| 3 | `src_antigravity/v3` | 8.3 / 10 | Index Swap과 Streaming 추가는 강점이나, 테스트 격리와 Vector DB 확장성이 약함 |

Antigravity가 v03-2에서 Index Swap과 SSE Streaming을 추가한 점은 분명한 장점이다. 다만 운영 가능성을 평가할 때는 "기능 존재"뿐 아니라 "독립 검증 가능성", "실제 Vector DB adapter 구조", "운영 migration/테스트 체계"까지 함께 보아야 한다. 그 기준에서는 Codex와 Claude가 더 안정적이다.

## 4. 항목별 비교

| 평가 항목 | Codex | Claude | Antigravity |
|-----------|-------|--------|-------------|
| `X-Tenant-ID` 필수화 | 구현 및 테스트 통과 | 구현 및 테스트 통과 | 구현 및 테스트 통과 |
| tenant 격리 | 저장/검색/삭제 경로 반영 | 저장/검색 경로 반영 | 주요 경로 반영 |
| org/dept 계층 검색 | 팀/부서/전사 공유 테스트 있음 | 팀/부서 정책 구현 | 구현되어 있으나 Gateway 의존 테스트 실패 |
| Streaming RAG | `/api/v1/rag/search/stream` 구현 | `/api/v1/rag/search/stream` 구현 | `/api/v1/search/stream` 구현 |
| Index Swap | 설계 문서 중심, 실행 API는 부족 | 미구현 | `/api/v1/admin/projects/{project_code}/swap` 구현 |
| Chroma `embeddings=` | 구현 및 테스트 있음 | 구현 | Chroma adapter 없음 |
| Gateway `tenant_id` 전달 | embed/generate/stream 반영 | embed/generate/stream 반영 | embed/generate/stream 반영 |
| PDF `page_no` | 실제 페이지 단위 구조 반영 | extractor 구조 존재 | pypdf 기반 추출 흔적 존재 |
| 테스트 독립성 | 좋음 | 좋음 | 외부 Gateway 미기동 시 실패 |
| 운영 migration | Alembic 초기 revision 있음 | 별도 migration 체계 약함 | 별도 migration 체계 약함 |

## 5. Codex 소스 개선 제안

`src_codex/v3`는 현재 가장 균형이 좋지만, v03-2의 Antigravity가 추가한 운영 기능을 흡수해야 한다.

1. **Index Swap 실행 API 추가**
   - 현재 문서에는 Index Swap 설계가 있지만, Antigravity처럼 운영자가 호출할 수 있는 admin endpoint가 부족하다.
   - `POST /api/v1/admin/projects/{project_code}/swap` 형태의 API를 추가하고, 신규 collection 생성 후 routing registry를 원자적으로 교체하는 테스트를 붙인다.

2. **실제 Chroma + Gemini Gateway 통합 테스트 추가**
   - 현재 단위 테스트는 안정적이지만 실제 외부 Chroma 서버와 Gateway를 붙인 smoke/integration 테스트는 별도 체계로 분리하는 것이 좋다.
   - `pytest -m integration`처럼 기본 테스트와 분리하면 CI 재현성과 운영 검증을 동시에 가져갈 수 있다.

3. **권한 모델 보강**
   - `X-Org-ID`가 없을 때 전사 검색을 허용하는 경로는 관리자/시스템 사용자와 일반 사용자를 구분해야 한다.
   - 임시 헤더 또는 token context라도 도입해 "전사 검색은 관리자만"이라는 v1.3 정책을 코드로 고정해야 한다.

4. **Index Swap 이후 rollback/검증 절차**
   - swap 전후 chunk count, doc_id coverage, routing registry 백업, 실패 시 rollback을 표준화해야 한다.
   - 이 부분이 들어가면 Antigravity의 운영 강점을 Codex가 흡수할 수 있다.

## 6. Claude 소스 개선 제안

`src_claud/v3`는 테스트 독립성과 adapter boundary가 좋다. 다만 운영 패키징과 migration 쪽이 약하다.

1. **Alembic migration 도입**
   - v1.3은 RDBMS 복합키와 FK 정합성이 중요하므로 `create_all()` 중심 운영은 한계가 있다.
   - 초기 migration을 추가하고, tenant/org/project/doc/dialog 테이블의 복합키와 FK를 migration으로 고정해야 한다.

2. **Index Swap API 추가**
   - Chroma/Local JSON adapter 구조가 이미 있으므로 swap 구현을 붙이기 좋은 상태다.
   - routing registry를 업데이트하는 admin service와 테스트를 추가하면 운영 점수가 크게 오른다.

3. **전사 공유 sentinel 정책 추가 검증**
   - README는 Chroma metadata에서 `org_id=""` sentinel을 쓴다고 명확히 설명한다.
   - 이 정책이 Local JSON, Chroma where 변환, RDBMS `NULL` 저장 사이에서 항상 같은 의미를 유지하는지 회귀 테스트를 더 촘촘히 추가해야 한다.

4. **legacy provider 정리**
   - Claude/Voyage 계열 provider와 Gemini Gateway provider가 함께 남아 있다.
   - 운영 기본 경로는 Gemini Gateway로 고정하고, legacy provider는 선택 확장으로 명확히 분리하는 편이 좋다.

## 7. Antigravity 소스 개선 제안

`src_antigravity/v3`는 v03-2에서 가장 공격적으로 기능을 추가했다. 특히 Streaming RAG와 Index Swap은 좋은 방향이다. 하지만 지금 상태로는 독립 검증성이 부족하다.

1. **테스트에서 실제 Gateway 의존 제거**
   - 현재 `test_upload_and_search_hierarchy`는 Gateway가 떠 있지 않으면 실패한다.
   - `LlmGatewayClient.embed_text`, `generate_answer`, `stream_answer`를 fixture/mock으로 대체해 기본 테스트는 항상 독립 실행되게 해야 한다.

2. **Chroma adapter 추가**
   - v1.3 표준은 Vector DB adapter에서 `embeddings=`를 명시해 저장하는 구조를 요구한다.
   - 현재는 Local JSON 중심이라 운영 Vector DB 확장성이 Codex/Claude보다 약하다.

3. **embedding 생성 책임 분리**
   - 현재 vector adapter 내부에서 Gateway embedding을 직접 호출한다.
   - 문서 pipeline 또는 embedding service가 embedding을 생성하고, vector adapter는 전달받은 embedding을 저장하는 구조가 표준에 더 가깝다.

4. **Index Swap 안정성 보강**
   - swap API는 강점이지만, 현재는 local 파일 삭제/생성 후 project routing을 바꾸는 수준이다.
   - swap 전 검증, 실패 시 rollback, swap 결과 count 검증, 이전 index 보관 정책이 필요하다.

5. **FastAPI lifespan 및 timezone-aware timestamp 전환**
   - `@app.on_event("startup")` deprecation warning과 `datetime.utcnow()` warning이 남아 있다.
   - `lifespan`과 `datetime.now(datetime.UTC)` 계열로 바꾸면 운영 경고를 줄일 수 있다.

6. **README 실행 명령 보정**
   - Gateway 실행 명령은 실제 Gateway 구조에 맞춰 `python -m uvicorn app.main:app --port 8010 --reload` 형태로 맞추는 것이 좋다.

## 8. 최종 결론

v03-2 기준으로 가장 안정적인 기준 구현은 `src_codex/v3`다. 테스트가 모두 통과하고, v1.3 표준의 tenant/org 격리, Gateway tenant 전달, Chroma embedding 저장, Alembic migration, 실행 가이드가 균형 있게 갖춰져 있다.

`src_claud/v3`는 근소한 2위다. 구현과 테스트는 매우 좋고, migration과 Index Swap이 추가되면 Codex와 거의 같은 수준까지 올라온다.

`src_antigravity/v3`는 기능 아이디어가 가장 진취적이다. Streaming과 Index Swap을 실제 API로 넣은 점은 칭찬할 만하다. 다만 기본 테스트가 외부 Gateway에 묶여 실패하고, Chroma adapter와 embedding boundary가 약해 현재는 운영 안정성에서 감점한다.

권장 개발 순서는 다음과 같다.

1. Codex: Antigravity의 Index Swap 실행 API를 흡수하고 통합 테스트를 보강한다.
2. Claude: Alembic migration과 Index Swap을 추가해 운영 완성도를 끌어올린다.
3. Antigravity: Gateway mock 기반 테스트 독립성, Chroma adapter, embedding boundary 정리를 먼저 처리한다.
