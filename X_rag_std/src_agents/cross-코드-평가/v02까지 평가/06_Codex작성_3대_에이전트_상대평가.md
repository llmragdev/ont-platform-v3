# 세 RAG 구현 상대평가: Codex vs Claude v2 vs Antigravity v2

검토일: 2026-05-14

대상:

- `src_agents/src_codex`
- `src_agents/src_claud/v2`
- `src_agents/src_antigravity/v2`

평가 기준:

- `RAG_표준_설계_v1.0.md`
- `details/01_Document_Embedding_Pipeline.md`
- `details/02_VectorDB_Management_Routing.md`
- `details/03_RAG_Search_API.md`
- `details/04_RDBMS_Schema_Design.md`
- 실제 테스트 통과 여부
- Gemini Gateway 키 관리/연동 방식
- 운영 확장성 및 위험도

## 테스트 결과

```text
src_codex
pytest -q
14 passed

src_claud/v2
pytest -q tests
14 passed

src_antigravity/v2
pytest -q test_endpoints_v2.py
1 passed
```

테스트는 모두 green이지만, 테스트 범위는 다르다. `src_codex`와 `src_claud/v2`는 상대적으로 넓은 pytest suite가 있고, `src_antigravity/v2`는 단일 통합 테스트 중심이다.

## 종합 순위

| 순위 | 구현 | 점수 | 요약 |
|---:|---|---:|---|
| 1 | `src_codex` | 8.6 / 10 | 표준 metadata, tenant 격리, Gemini Gateway, Chroma embedding 일관성, 삭제/stream/project/category까지 가장 균형 좋음 |
| 2 | `src_claud/v2` | 7.3 / 10 | API 범위와 구조는 좋지만 metadata, tenant 격리, Chroma embedding 저장, Session thread safety가 미완성 |
| 3 | `src_antigravity/v2` | 5.0 / 10 | v1보다 발전했지만 PDF 파싱, routing registry, RDBMS schema, metadata, update/delete, tenant 격리가 부족 |

## 항목별 비교

| 항목 | src_codex | src_claud/v2 | src_antigravity/v2 |
|---|---|---|---|
| FastAPI/Pydantic 구조 | 양호 | 양호 | 보통 |
| 계층 분리 | 양호 | 양호 | 보통 |
| 문서 파이프라인 | 양호 | 양호 | 미흡 |
| 실제 PDF 파싱 | 지원 | 지원 | 미흡/mock fallback |
| raw/processed 분리 | 지원 | 지원 | 미흡 |
| 상태 전이 | 지원 | 지원 | 지원 |
| 증분 업데이트 | 문서 단위 재삽입 | 문서 단위 재삽입 | 없음 |
| VectorDB 라우팅 registry | 지원 | 지원 | 없음 |
| Local JSON VectorDB | 지원 | 지원 | 지원 |
| Chroma adapter | 지원 | 지원하나 embedding 저장 미흡 | 없음 |
| Chroma embedding 일관성 | 양호 | 미흡 | 해당 없음 |
| Gemini Gateway LLM | 지원 | 지원 | 지원 |
| Gemini Gateway embedding | 지원 | 지원 | 지원 |
| Gateway API key 분리 | 양호 | 양호 | 부분 준수 |
| Gateway company_id 전달 | 지원 | 미흡 | 미흡 |
| tenant 검색 격리 | 지원 | 미흡 | 없음 |
| 표준 metadata | 양호 | 미흡 | 미흡 |
| RAG search layout | 양호 | 보통 | 보통 |
| debug mode 후보 노출 제어 | 양호 | 양호 | 양호 |
| RDBMS 상세설계 준수 | 양호 | 양호 | 미흡 |
| Projects/Categories API | 지원 | 지원 | 없음 |
| 문서 삭제 API | 지원 | 지원 | 없음 |
| Streaming search | 지원 | 지원 | 없음 |
| 테스트 범위 | 양호 | 보통 | 미흡 |

## 구현별 평가

### 1. src_codex

강점:

- Gemini API key를 직접 보유하지 않고 `LLM_GATEWAY_URL`만 사용
- `company_id`를 RDBMS, vector metadata, dialog history에 저장
- RAG 검색 시 `company_id`를 adapter filter에 강제 주입
- 표준 metadata가 가장 잘 유지됨
- Chroma adapter가 document embedding도 같은 provider로 생성해 `embeddings=`를 명시 저장
- 문서 삭제, streaming search, projects/categories API까지 구현
- pytest와 smoke test가 모두 통과

약점:

- Alembic migration은 아직 없음
- timezone-aware timestamp는 아직 미적용
- 실제 Chroma/Gemini Gateway 실서버 통합 테스트는 별도 필요

평가:

```text
8.6 / 10
```

현재 세 구현 중 표준 준수와 실행 안정성의 균형이 가장 좋다.

### 2. src_claud/v2

강점:

- 구조와 API 범위가 넓음
- projects/categories/document delete/streaming/audit log 제공
- Gemini Gateway 연동 방향이 맞음
- local_json/chroma 선택 구조 있음
- 테스트 14개 통과

약점:

- Chroma 문서 저장 시 `embeddings=`를 명시하지 않아 query embedding과 불일치 가능
- chunk metadata에 `vector_db_id`, `created_at`, `company_id`가 없음
- `X-Company-ID`를 받지만 vector search filter에 강제하지 않음
- `asyncio.to_thread()`에서 동일 SQLAlchemy Session 사용
- Gateway 호출에 실제 company_id 미전달

평가:

```text
7.3 / 10
```

확장성은 좋지만 운영 신뢰성을 위해 High 항목 보완이 필요하다.

### 3. src_antigravity/v2

강점:

- v1보다 계층 구조가 개선됨
- Local JSON VectorDB와 Gateway embedding/LLM 호출을 사용
- RDBMS에 문서 상태와 검색 이력 저장
- RAG search layout과 debug mode 구조는 구현
- 단일 통합 테스트 통과

약점:

- 실제 PDF parser가 아니라 UTF-8 decode/mock fallback
- routing registry 없이 `vdb_{category_mid}_01` 하드코딩
- RDBMS 스키마가 상세설계 04에 미달
- 표준 metadata 부족
- update/delete/stream/projects/categories API 없음
- tenant 격리 없음
- Gateway 실패 시 `[0.1, 0.2]` mock fallback
- 동일 Session을 thread로 넘기는 구조

평가:

```text
5.0 / 10
```

v1 대비 개선은 분명하지만, 운영형 표준 구현과는 아직 거리가 있다.

## 최종 결론

현재 기준으로는 `src_codex`가 가장 표준 준수도가 높고 안정적이다. `src_claud/v2`는 기능 범위와 구조적 야심은 좋지만, 핵심 운영 리스크가 남아 있다. `src_antigravity/v2`는 RAG 흐름 데모로는 의미가 있으나 상세 설계 준수도와 운영 준비도는 가장 낮다.

추천 방향:

1. 기준 구현은 `src_codex`로 둔다.
2. `src_claud/v2`는 High 항목을 보완하면 운영 후보로 재평가한다.
3. `src_antigravity/v2`는 PDF parser, routing registry, RDBMS schema, metadata, update/delete부터 보강한다.
