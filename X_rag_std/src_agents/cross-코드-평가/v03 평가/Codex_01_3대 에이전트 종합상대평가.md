# Codex 작성: v03 3대 에이전트 종합상대평가

작성일: 2026-05-15

## 1. 평가 대상

본 문서는 `RAG_표준_설계_v1.3.md` 기준으로 세 구현체의 v3 산출물을 상대평가한다.

| 구분 | 평가 대상 | 상태 |
|------|-----------|------|
| Codex | `src_agents/src_codex/v3` | 실제 FastAPI 코드, 서비스, 테스트, 실행 가이드 존재 |
| Claude | `src_agents/src_claud/v3` | 실제 FastAPI 코드, 서비스, 테스트 존재 |
| Antigravity | `src_agents/src_antigravity/v3` | 실제 FastAPI 코드, 서비스, 테스트 존재 |

주의: 본 문서는 최초 작성 후 `src_codex/v3` 구현 완료 결과를 반영해 갱신했다. 점수는 현재 코드와 테스트 결과 기준이다.

## 2. 검증 방법

확인한 기준은 다음과 같다.

- `RAG_표준_설계_v1.3.md`의 필수 요구사항
- `src_agents/cross-코드-평가/v02까지 평가`의 기존 지적사항
- 각 구현체 v3 README/설계/코드
- 가능한 범위의 pytest 실행 결과

실행 검증 결과:

```text
src_codex/v3
python -m pytest -q
결과: 17 passed

python test_endpoints.py
결과: ALL TESTS PASSED
```

```text
src_claud/v3
python -m pytest -q
결과: 14 passed, 29 warnings
```

```text
src_antigravity/v3
python -m pytest -q test_v3_standard.py
결과: 2 passed, 1 failed
주요 실패: Gateway /api/v1/embed 호출 404로 upload/search hierarchy 테스트 실패
```

## 3. 종합 순위

| 순위 | 구현체 | 점수 | 판정 |
|------|--------|------|------|
| 1 | `src_codex/v3` | 8.7 / 10 | v1.3 핵심 요구사항을 구현하고 테스트로 고정 |
| 2 | `src_claud/v3` | 8.2 / 10 | 구현 완성도 높음. 일부 표준 표현/운영 보강 필요 |
| 3 | `src_antigravity/v3` | 6.1 / 10 | v1.3 핵심 개념을 구현했으나 테스트/운영 안정성 미흡 |

점수는 현재 산출물 기준이다. `src_codex/v3`는 구현 전 평가에서는 낮았으나, 구현 완료 후 테스트 통과 결과를 반영해 1위로 재평가했다.

## 4. 항목별 비교

| 평가 항목 | src_codex/v3 | src_claud/v3 | src_antigravity/v3 |
|-----------|--------------|--------------|--------------------|
| v1.3 표준 반영 | 코드에 반영 | 코드에 상당 부분 반영 | 코드에 일부 반영 |
| 실제 구현 코드 | 있음 | 있음 | 있음 |
| 테스트 결과 | 17/17 통과 + smoke 통과 | 14/14 통과 | 2/3 통과 |
| `X-Tenant-ID` 필수화 | 구현됨 | 구현됨 | 구현됨 |
| `company_id` 제거 | RAG 운영 경로 제거 | 대체로 제거됨 | 대체로 제거됨 |
| `org_id`/`dept_code` | 구현됨 | 구현됨 | 구현됨 |
| 전사 공유 문서 포함 | 구현 및 테스트 있음 | 구현됨 | 구현됨 |
| Chroma `embeddings=` | 구현 및 테스트 있음 | 구현됨 | Chroma 미구현 |
| Gateway `tenant_id` 전달 | RAG/Gateway 호환 구현 | 구현됨 | 구현됨, 단 테스트 실패 |
| PDF 실제 `page_no` | page 단위 추출 구조 구현 | 구현 여부 추가 검증 필요 | pypdf 기반 구현 흔적 있음 |
| Session thread safety | 동기 pipeline 구조로 공유 문제 회피 | 개선된 구조로 보임 | 여전히 점검 필요 |
| Alembic migration | 초기 revision 추가 | 확인 안 됨 | 확인 안 됨 |
| 실행 가이드 | 매우 상세 | 간결함 | 있으나 일부 명령 부정확 |

## 5. src_claud/v3 평가

### 강점

`src_claud/v3`는 세 v3 산출물 중 현재 가장 완성도가 높다. 실제 코드와 테스트가 있고, `pytest` 기준 14개 테스트가 모두 통과했다.

주요 개선점도 v2 평가에서 지적된 핵심을 잘 겨냥하고 있다.

- `X-Tenant-ID` 필수화
- `tenant_id` 기반 검색 필터 강제
- Gateway embed/generate 호출에 `tenant_id` 전달
- Chroma adapter에서 `embeddings=` 명시
- Chroma metadata에서 `tags`와 `None` 값 제외
- Local JSON/Chroma 양쪽에 조직 범위 OR 조건 구현
- 팀/부서 검색 시 전사 공유 문서 포함

특히 v2에서 가장 큰 문제였던 Chroma embedding 불일치와 tenant 격리 누락을 실제 코드로 보완한 점이 크다.

### 남은 리스크

1. `org_id IS NULL` 표준을 Chroma/Local JSON에서 빈 문자열 `""`로 표현한다. Chroma metadata 제약 때문에 실용적 선택일 수 있으나, 표준 문서와 구현 표현이 다르므로 README나 adapter 주석에 “Vector DB 저장 시 전사 공유 문서는 `org_id=""`로 정규화”라고 명시해야 한다.
2. `datetime.utcnow()` 경고가 남아 있다. v1.3의 timezone-aware ISO 8601 원칙에 맞게 `datetime.now(datetime.UTC)` 계열로 바꾸는 것이 좋다.
3. Claude/Voyage provider 경로가 남아 있다면 Gemini Gateway 운영 기본값과 legacy provider를 명확히 분리해야 한다.
4. Alembic migration 도입 여부가 명확하지 않다. 운영 후보라면 migration 체계가 필요하다.

### 판정

현재 v03 기준 가장 앞선 구현체다. 운영 후보로 올리려면 시간대 처리, migration, Gateway 실제 연동 테스트, Chroma 실서버 테스트를 보강하면 된다.

## 6. src_antigravity/v3 평가

### 강점

`src_antigravity/v3`는 v2 대비 확실히 개선되었다.

- `X-Tenant-ID` 누락 시 400 테스트 존재
- `tenant_id`, `org_id`, `dept_code` metadata 생성
- 팀/부서 검색 시 전사 공유 문서 포함 로직 구현
- Gateway 호출 시 `tenant_id` 전달
- 임베딩 실패 시 `[0.1, 0.2]` fallback을 제거하고 예외 전파
- PDF 파싱에 `pypdf` 사용 흔적 있음
- 프로젝트/카테고리 메타 API 테스트 존재

v2에서 가장 위험했던 “fallback vector로 장애를 숨기는 문제”를 제거한 것은 좋은 방향이다.

### 주요 문제

1. 테스트가 실패한다. `test_upload_and_search_hierarchy`에서 Gateway `/api/v1/embed` 호출이 404로 실패했다.
2. 테스트가 외부 Gateway 상태에 의존한다. 표준 단위 테스트라면 Gateway를 mock/stub 처리해야 한다.
3. README의 Gateway 실행 명령이 `python main.py`로 되어 있는데, 실제 Gateway 구조는 `uvicorn app.main:app --port 8010 --reload` 쪽이 맞다.
4. Chroma adapter가 없다. v1.3의 운영형 Vector DB 기준에서는 Local JSON만으로 부족하다.
5. Vector adapter 내부에서 직접 Gateway embedding을 호출한다. 문서 pipeline에서 embedding을 생성해 `embeddings=`처럼 명시 전달하는 구조가 더 표준에 가깝다.
6. `datetime.utcnow()`와 FastAPI `on_event` deprecation warning이 남아 있다.
7. Session thread safety는 코드상 더 확인이 필요하다. `asyncio.to_thread`와 DB Session 사용 흐름이 안전하게 분리되었는지 테스트로 고정되어야 한다.

### 판정

v1.3을 의식한 구현은 되었지만 아직 운영 후보는 아니다. 먼저 테스트가 외부 Gateway 없이 통과하도록 고치고, Gateway 실행 계약과 Chroma/embedding boundary를 정리해야 한다.

## 7. src_codex/v3 평가

### 강점

`src_codex/v3`는 계획/설계 단계에서 실제 실행 가능한 FastAPI 구현체로 전환되었다. v1.3 핵심 요구사항을 코드와 테스트로 고정했고, `pytest` 17개와 endpoint smoke test가 통과했다.

작성된 문서:

- `V3_DEVELOPMENT_PLAN.md`
- `V3_ARCHITECTURE_DESIGN.md`
- `V3_RUN_GUIDE.md`

구현에는 v1.3 핵심이 다음처럼 반영되어 있다.

- `company_id`/`X-Company-ID` 운영 경로 제거
- `tenant_id`/`X-Tenant-ID` 중심 API 계약
- `X-Tenant-ID` 필수화와 default fallback 제거
- `X-Org-ID` 기반 팀/부서 검색 범위 처리
- 팀 검색: `tenant_id == T AND (org_id == X OR org_id IS NULL)`
- 부서 검색: `tenant_id == T AND (dept_code == D OR org_id IS NULL)`
- `(tenant_id, org_id)` 복합키 기반 조직 모델
- `tags` Vector metadata 제외
- Gateway 요청의 `tenant_id` 전달
- Gateway도 `tenant_id`를 정식 필드로 수용하도록 호환 수정
- Chroma `embeddings=` 유지 및 테스트
- PDF page 단위 추출 구조와 실제 `page_no` metadata 저장
- 동기 pipeline 구조로 `asyncio.to_thread` Session 공유 문제 회피
- Alembic 초기 migration 추가
- 폴더 기준 conda 가상환경 실행 가이드

특히 v2 평가에서 지적된 Codex의 보완점 중 `tenant_id` 전환, page_no, Gateway 계약, Chroma embedding 일관성, 조직 범위 검색은 이번 구현에서 실제 코드와 테스트로 보완되었다.

### 약점

1. 실제 Chroma 서버와 실제 Gemini Gateway를 붙인 통합 테스트는 아직 별도다.
2. 인증/권한 기반의 “관리자만 전사 검색 허용” 정책은 구조상 확장 포인트로 남아 있다. 현재는 `X-Org-ID`가 없으면 tenant scope 검색으로 동작한다.
3. SQLite에서는 timezone-aware datetime이 저장 후 naive로 돌아오는 제약이 있어 응답 직렬화에서 UTC를 보정한다. PostgreSQL 운영 검증이 필요하다.

### 판정

현재 v03 기준으로는 가장 균형이 좋다. v1.3 표준의 핵심 보안/검색 계약을 구현했고, 테스트도 가장 넓다. 남은 운영 과제는 migration과 실서버 통합 테스트다.

## 8. v03 기준 최우선 개선 권고

### src_claud/v3

1. `org_id IS NULL` 표준과 `org_id=""` 저장 구현의 차이를 문서화한다.
2. timezone-aware timestamp로 전환한다.
3. Alembic migration을 도입한다.
4. 실제 Chroma 서버 + Gemini Gateway 통합 테스트를 추가한다.
5. legacy Claude/Voyage provider를 운영 기본 경로와 분리한다.

### src_antigravity/v3

1. 테스트에서 외부 Gateway 의존성을 제거하고 mock Gateway를 사용한다.
2. README의 Gateway 실행 명령을 실제 구조에 맞게 수정한다.
3. Chroma adapter를 추가한다.
4. Vector adapter가 직접 embedding을 만들지 않도록 pipeline/service boundary를 정리한다.
5. Session thread safety 테스트를 추가한다.
6. timezone-aware timestamp와 FastAPI lifespan으로 전환한다.

### src_codex/v3

1. 실제 Chroma 서버 + 실제 Gemini Gateway 통합 테스트를 추가한다.
2. 인증/권한 모델을 붙여 `X-Org-ID` 부재 시 관리자/일반 사용자 정책을 완성한다.
3. PostgreSQL 기준 timezone-aware datetime 저장/조회 검증을 수행한다.
4. README를 v3 기준으로 추가하거나 루트 README에서 v3 실행 가이드로 연결한다.

## 9. 최종 결론

현재 v03 시점에서는 `src_codex/v3`가 가장 앞서 있다. 실제 구현과 테스트가 추가되었고, v1.3의 핵심 격리/metadata/Gateway/Chroma 계약을 가장 균형 있게 반영했다.

`src_antigravity/v3`는 v2보다 좋아졌지만 테스트 실패와 Gateway 계약 불일치, Chroma 부재 때문에 아직 중간 단계다.

`src_claud/v3`는 여전히 좋은 구현체이며, 테스트도 통과한다. 다만 Codex v3가 구현 완료되면서 Chroma/Gateway/tenant-org 정책 테스트 범위에서 다시 앞섰다.

권장 개발 순서는 다음과 같다.

1. `src_codex/v3`는 실서버 통합 테스트를 추가해 운영 후보로 안정화한다.
2. `src_claud/v3`는 운영 후보 안정화 작업으로 진행한다.
3. `src_antigravity/v3`는 테스트 격리와 Gateway 계약 수정부터 처리한다.
