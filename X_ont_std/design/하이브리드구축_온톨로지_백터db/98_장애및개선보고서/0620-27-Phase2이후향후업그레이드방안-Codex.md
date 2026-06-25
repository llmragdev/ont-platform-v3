# 0620-27 Phase 2 이후 향후 업그레이드 방안

**작성일:** 2026-06-20  
**작성자:** Codex  
**상태:** 향후 작업 인수인계용  
**범위:** v5 질의응답 정책, RAG 근거 판정, 온톨로지 검색, 평가 자동화, UI 동기화

---

## 1. 현재 결론

현재 v5는 RAG 검색 자체는 동작하지만, 평가 시스템으로 쓰기에는 아직 다음 문제가 남아 있다.

1. 질문 주제와 무관한 검색 결과가 RAG 근거로 노출될 수 있다.
2. Snowflake처럼 문서 근거가 없는 질문에도 일반적인 설명이 섞여 정상 답변처럼 보일 수 있다.
3. "문서만", "한계 포함", "전문가" 모드의 정책 차이가 UI와 백엔드에서 완전히 동기화되어야 한다.
4. 프론트엔드 `AdaptiveQueryInterface.tsx`가 현재 파일시스템에서 확인되지 않는다.
5. 백엔드는 옵션 파라미터를 받을 준비가 되어 있으나, 프론트 API 호출은 아직 옵션 4개를 전달하지 않는 상태다.

따라서 다음 작업의 핵심은 **답변을 더 그럴듯하게 만드는 것**이 아니라, 먼저 **근거의 관련성, 답변 범위, 일반 설명 여부를 명확히 통제하는 것**이다.

---

## 2. 현재 시스템 상태

### 2.1 백엔드

대상 파일:

`E:\ontology_edu\X_ont_std\ont_platform\v5\backend\app\api\adaptive_query.py`

확인 상태:

- 파일 존재 확인됨
- `GET /api/v1/projects/{project_id}/query/stream` 구조 사용
- `mode` 파라미터 지원
- 옵션 파라미터 수신 구조 있음
  - `hide_irrelevant`
  - `allow_partial`
  - `separate_sources`
  - `allow_general`
- 모드별 기본값 설계 반영 가능

주의 사항:

- 현재 백엔드 정책은 프론트가 옵션을 보내지 않아도 모드별 기본값으로 동작해야 한다.
- 단, 프론트 UI에서 사용자가 체크박스를 바꿔도 API로 전달되지 않으면 사용자 선택이 반영되지 않는다.

### 2.2 프론트엔드

확인 상태:

- `frontend/src/components/project/QueryTab.tsx`는 `AdaptiveQueryInterface`를 import한다.
- `frontend/src/app/(dashboard)/hybrid-query/page.tsx`도 `AdaptiveQueryInterface`를 import한다.
- 하지만 `frontend/src/components/query/AdaptiveQueryInterface.tsx` 파일은 현재 확인되지 않는다.
- `frontend/src/lib/api.ts`의 `queryStream()`은 현재 `project_id`, `session_id`, `query`, `mode`만 전달한다.
- 옵션 4개는 아직 URLSearchParams에 포함되지 않는다.

판정:

**프론트와 백엔드 동기화는 아직 완료 상태가 아니다.**

---

## 3. 즉시 해야 할 작업

### 3.1 프론트 질의 UI 복구 또는 신규 작성

대상:

`frontend/src/components/query/AdaptiveQueryInterface.tsx`

필수 기능:

1. 질문 입력 textarea
2. 모드 라디오 버튼 3개
   - 문서만 (엄격)
   - 한계 포함 (부분)
   - 전문가 (유연)
3. 체크박스 4개
   - 무관한 검색 결과 숨기기
   - 부분 답변 허용
   - 출처 분리
   - 일반 설명 허용
4. 모드 변경 시 기본 체크박스 값 자동 적용
5. 질의 실행 시 `api.queryStream()` 호출
6. 스트리밍 답변, 출처, 한계점, 완료 메타데이터를 store에 반영

### 3.2 프론트 API 계약 확장

대상:

`frontend/src/lib/api.ts`

현재:

```ts
queryStream(projectId, sessionId, query, mode, callbacks)
```

개선:

```ts
queryStream(projectId, sessionId, query, mode, options, callbacks)
```

추가 옵션:

```ts
{
  hideIrrelevant: boolean;
  allowPartial: boolean;
  separateSources: boolean;
  allowGeneral: boolean;
}
```

URL 파라미터 매핑:

| 프론트 옵션 | 백엔드 Query 파라미터 |
|---|---|
| `hideIrrelevant` | `hide_irrelevant` |
| `allowPartial` | `allow_partial` |
| `separateSources` | `separate_sources` |
| `allowGeneral` | `allow_general` |

### 3.3 Zustand Store 확장

대상:

`frontend/src/store/useQueryStore.ts`

추가 권장 상태:

```ts
interface EvaluationOptions {
  hideIrrelevant: boolean;
  allowPartial: boolean;
  separateSources: boolean;
  allowGeneral: boolean;
}
```

추가 액션:

- `setEvaluationOptions(options)`
- `resetOptionsForMode(mode)`

권장 기본값:

| 모드 | hideIrrelevant | allowPartial | separateSources | allowGeneral |
|---|---:|---:|---:|---:|
| 문서만 | true | false | true | false |
| 한계 포함 | true | true | true | false |
| 전문가 | true | true | true | true |

---

## 4. 답변 정책 업그레이드

### 4.1 관련성 게이트

질문과 검색 결과의 토픽 일치 여부를 먼저 판단해야 한다.

예:

질문:

`Snowflake 기반 QA 테스트에서 응답 시간과 운영 제약을 함께 봐야 하는 이유는 무엇인가?`

검색 결과:

- NLP 온톨로지 논문
- 국방 온톨로지 문서
- 지식그래프 설명 문서

판정:

Snowflake 관련 직접 근거 없음.

기대 동작:

- 문서만 모드: RAG 0개, 관련 없음 응답
- 한계 포함 모드: 문서 근거 없음 + 범위 제한 응답
- 전문가 모드: 문서 근거 없음 명시 후 일반 설명 분리

### 4.2 도메인 키워드 기반 1차 게이트

초기에는 규칙 기반으로 충분하다.

Snowflake 질문 감지 키워드:

- `snowflake`
- `스노우플레이크`
- `cortex`
- `warehouse`
- `웨어하우스`
- `medallion`
- `메달리온`
- `bronze`
- `silver`
- `gold`

질문에 위 키워드가 포함되면, 검색 결과의 파일명/본문/메타데이터에도 최소 1개 이상 포함되어야 관련 근거로 인정한다.

### 4.3 일반 토픽 게이트

Snowflake처럼 명확한 도메인이 아닌 경우에는 다음 기준을 적용한다.

1. 질문 핵심 토큰 추출
2. 파일명, chunk text, entity name, ontology property에서 토큰 검색
3. 핵심 토큰 2개 이상 일치하면 관련 근거로 인정
4. 1개 이하이면 낮은 관련성으로 판정

향후에는 BM25, reranker, cross-encoder 기반 relevance gate로 업그레이드한다.

---

## 5. 모드별 응답 정책

### 5.1 문서만 (엄격)

목적:

평가, 검증, 감사 로그용.

정책:

- 문서에 없으면 답하지 않는다.
- 일반 지식, 추정, 전문가 설명을 포함하지 않는다.
- 관련 근거가 없으면 신뢰도를 낮게 표시한다.

예상 응답:

`현재 업로드되었거나 검색된 문서 근거에서 Snowflake 관련 내용을 확인하지 못했습니다. 문서만 모드에서는 근거가 없는 내용을 답변하지 않습니다.`

UI 기대값:

- Level 1
- 신뢰도 25~35%
- RAG 0
- Ontology 0 또는 관련 entity만 표시

### 5.2 한계 포함 (부분)

목적:

문서 기반 운영 QA.

정책:

- 문서에 있는 부분은 답한다.
- 문서에 없는 부분은 "확인되지 않음"으로 분리한다.
- 일반 설명은 기본적으로 하지 않는다.

예상 응답:

`문서에서 확인되는 범위에서는 A만 확인됩니다. B에 대한 직접 근거는 현재 문서에서 확인되지 않습니다.`

UI 기대값:

- Level 2 또는 Level 3
- 한계점 섹션 표시
- 신뢰도 45~70%

### 5.3 전문가 (유연)

목적:

컨설팅, 탐색, 설명 보완.

정책:

- 문서 근거와 일반 설명을 반드시 분리한다.
- 문서 근거가 없으면 그 사실을 먼저 말한다.
- 일반 설명을 하더라도 출처 있는 답변처럼 보이면 안 된다.

예상 응답:

`문서 근거 판단: 현재 검색된 문서에는 Snowflake 관련 직접 근거가 없습니다.`

`일반 설명: 일반적인 엔터프라이즈 RAG/QA 관점에서는 응답 시간은 SLA와 사용자 경험을, 운영 제약은 비용, 보안, 권한, 장애 대응을 좌우하므로 함께 검토해야 합니다.`

UI 기대값:

- Level 2 또는 Level 3
- "문서 근거"와 "일반 설명" 영역 분리
- 신뢰도 45~65%
- RAG 0이면 90%대 신뢰도 금지

---

## 6. 평가 시스템 업그레이드

### 6.1 24문항 평가를 모드별로 분리

현재 24문항 평가는 한 가지 모드만 보면 안 된다.

필수 평가 세트:

1. `document_only`
2. `document_with_limits`
3. `expert_mode`

각 모드별로 다음을 기록한다.

| 항목 | 설명 |
|---|---|
| answer | 최종 답변 |
| source_counts | RAG/Ontology/Expert 개수 |
| confidence | 신뢰도 |
| level | 답변 레벨 |
| evidence.status | 관련 근거 상태 |
| filtered_counts | 무관 근거 제거 개수 |
| limitations | 한계점 |

### 6.2 채점 기준 보정

기존 채점은 "답변이 그럴듯한가"에 치우칠 수 있다.

개선 채점 기준:

| 기준 | 배점 |
|---|---:|
| 질문 주제 관련성 판정 | 25 |
| 문서 근거 사용 정확성 | 25 |
| 없는 근거를 없다고 말하는 정직성 | 20 |
| 일반 설명 분리 | 15 |
| 출처/페이지/점수 렌더링 | 15 |

중요:

문서에 없는 질문에서 "관련 없음"이라고 정확히 말하면 실패가 아니라 정답으로 봐야 한다.

### 6.3 Snowflake 문항 별도 평가

Snowflake 관련 문서가 실제로 업로드되어 있지 않다면, Snowflake 8문항의 목표는 "정답 생성"이 아니라 "근거 없음 판정"이다.

평가 예:

| 모드 | 기대 평가 |
|---|---|
| 문서만 | 관련 없음 판정이면 합격 |
| 한계 포함 | 문서 근거 없음 + 범위 제한이면 부분 합격 |
| 전문가 | 문서 근거 없음 + 일반 설명 분리이면 부분 합격 |

---

## 7. 온톨로지 업그레이드

### 7.1 단기: 데이터 존재 확인 자동화

온톨로지 검색 성능을 보기 전에 데이터가 있는지 먼저 확인해야 한다.

체크 대상:

```text
storage/{company_id}/{project_id}/ontology/*.json
```

자동 체크:

- ontology json 개수
- entity 총 개수
- relationship 총 개수
- `온톨로지` entity 존재 여부
- 최근 벡터화 문서와 ontology json 매핑 여부

### 7.2 중기: 관계 검색 연결

현재 UI는 entity 중심으로 보이기 쉽다.

업그레이드:

- entity 검색 후 관계 확장
- `from_id`, `to_id` 기반 인접 entity 조회
- 질문에 `역할`, `관계`, `차이`, `연계`가 포함되면 relationship 우선 검색

### 7.3 장기: Rules 계층 도입

현재 v5 온톨로지는 기본적으로 entity/relationship 중심이다.

Rules 도입 시 추가할 것:

1. `generate_ontology_from_pdf.py`에서 rules 추출
2. `OntologyService.add_rule()`
3. `OntologyRepository` rules 저장 구조
4. UI Rules 탭 또는 Ontology 탭 내 Rules 섹션
5. 규칙 기반 추론 결과와 원문 근거 분리

주의:

Rules는 바로 넣기보다 기획 결정 후 별도 이슈로 분리하는 것이 안전하다.

---

## 8. RAG 업그레이드

### 8.1 단기: 근거 텍스트 필드 정렬

현재 백엔드 RAG 결과는 `text`를 내려줄 수 있고, 프론트 `SourcePanel`은 `content` 또는 `excerpt`를 우선 표시한다.

동기화 필요:

백엔드에서 다음 중 하나를 보장한다.

```json
{
  "text": "...",
  "content": "...",
  "excerpt": "..."
}
```

또는 프론트가 `item.text`도 표시하도록 수정한다.

권장:

프론트 `SourcePanel`에서 다음 순서로 표시한다.

```ts
item.content || item.excerpt || item.text || '내용 없음'
```

### 8.2 중기: Score 의미 통일

Chroma는 distance 성격의 score를 반환한다.

필요한 정리:

- 내부 원점수: `distance`
- UI 표시 점수: `similarity`
- 변환: `similarity = 1 - distance`
- 단, distance 범위가 0~1을 넘을 수 있으므로 clamp 필요

권장 응답:

```json
{
  "score": 0.74,
  "distance": 0.26
}
```

UI는 `score`만 백분율로 표시한다.

### 8.3 장기: Reranker 도입

현재 로그에 `sentence_transformers not installed` 경고가 있었다.

업그레이드 선택지:

1. 경량 cross-encoder reranker
2. Gemini/Claude 기반 relevance judge
3. BM25 + vector hybrid reranking

초기에는 비용과 속도 때문에 BM25 + vector score fusion을 권장한다.

---

## 9. UI 업그레이드

### 9.1 필수 UI

질의 입력 영역 구성:

1. 질문 textarea
2. 모드 라디오
3. 고급 옵션 체크박스
4. 질의 실행 버튼

권장 배치:

```text
[질문 입력]

응답 모드:
( ) 문서만 (엄격)
( ) 한계 포함 (부분)
( ) 전문가 (유연)

세부 옵션:
[x] 무관한 검색 결과 숨기기
[ ] 부분 답변 허용
[x] 출처 분리
[ ] 일반 설명 허용
```

### 9.2 모드별 옵션 자동화

사용자가 모드를 바꾸면 체크박스가 자동으로 바뀌어야 한다.

하지만 사용자가 체크박스를 직접 바꾼 뒤에는 해당 수동 선택을 존중한다.

간단한 구현:

- 모드 변경 시 항상 기본값 적용
- 고급 사용자가 원하면 체크박스 다시 수정

### 9.3 결과 UI

현재 Level 1에서도 SourcePanel이 표시될 수 있다.

개선:

- 관련 없음 상태에서 `RAG 0`, `Ontology 0`이면 SourcePanel을 접거나 "관련 근거 없음"으로 표시
- `evidence.status = no_relevant_evidence`이면 빨간/노란 안내 표시
- 전문가 모드의 일반 설명은 출처 탭과 분리

---

## 10. 자동화 업그레이드

### 10.1 evaluate_24qa.py 확장

필요 옵션:

```bash
python scripts/evaluate_24qa.py --mode document_only
python scripts/evaluate_24qa.py --mode document_with_limits
python scripts/evaluate_24qa.py --mode expert_mode
```

추가 옵션:

```bash
--hide-irrelevant true
--allow-partial true
--separate-sources true
--allow-general false
```

출력 파일 예:

```text
eval_results_24qa_document_only.json
eval_results_24qa_document_with_limits.json
eval_results_24qa_expert_mode.json
```

### 10.2 비교 리포트 자동 생성

추가 스크립트:

`scripts/summarize_eval_modes.py`

역할:

- 모드별 평균 confidence
- 평균 source count
- no_relevant_evidence 비율
- Snowflake 문항의 무관 근거 차단률
- Ontology 문항의 ontology hit count

---

## 11. 단계별 로드맵

### Phase 2A: 화면-백엔드 계약 동기화

목표:

옵션 시스템이 실제 UI에서 백엔드로 전달되도록 한다.

작업:

1. `AdaptiveQueryInterface.tsx` 생성
2. `api.queryStream()` 옵션 인자 추가
3. store에 evaluation options 추가
4. `npm run build` 또는 `npx tsc --noEmit` 검증
5. Snowflake 질문으로 수동 UI 테스트

완료 기준:

- 문서만 모드에서 Snowflake 질문 입력 시 RAG 0
- "관련 근거 없음" 답변 표시
- 신뢰도 90%대 표시 금지

### Phase 2B: 평가 스크립트 확장

목표:

모드별 24문항 평가를 자동화한다.

작업:

1. `evaluate_24qa.py` 옵션 파라미터 추가
2. 모드별 JSON 저장
3. 결과 요약 스크립트 작성

완료 기준:

- 3개 모드 각각 24문항 실행
- 에러 0
- JSON 파일 3개 생성

### Phase 2C: 온톨로지 데이터 품질 보강

목표:

Ontology 0 상태가 데이터 부재인지 검색 실패인지 자동 판정한다.

작업:

1. ontology storage health check
2. entity/relationship count 리포트
3. 관계 기반 검색 추가

완료 기준:

- 온톨로지 데이터 없음이면 "검색 실패"가 아니라 "데이터 없음"으로 표시
- 온톨로지 질문에서 entity 1개 이상 반환

### Phase 3: 고급 평가와 100점 전략

목표:

단순 RAG를 넘어 평가 가능한 하이브리드 QA로 고도화한다.

작업:

1. RAG relevance gate 정교화
2. reranker 도입
3. ontology relationship expansion
4. rules 도입 여부 결정
5. 자동 채점 기준 확정

완료 기준:

- 관련 없는 질문에 관련 없음 판정 정확도 95% 이상
- 문서 있는 질문의 근거 회수율 90% 이상
- 일반 설명과 문서 근거 혼동 0건

---

## 12. 역할별 인수인계

### Codex

담당:

- 백엔드 정책 분기
- RAG/Ontology 관련성 게이트
- 평가 스크립트 확장
- 백엔드 컴파일/스모크 검증

우선순위:

1. `adaptive_query.py` 현재 상태 유지 및 테스트
2. `evaluate_24qa.py` 옵션 확장
3. Snowflake 질문 mock test 추가

### Antigravity

담당:

- 프론트 UI 라디오/체크박스 구현
- API 파라미터 전달
- 화면 QA

우선순위:

1. 누락된 `AdaptiveQueryInterface.tsx` 복구 또는 작성
2. 체크박스 옵션을 `api.queryStream()`에 연결
3. Level 1 관련 없음 화면 검증

### Claude Code

담당:

- 모드별 24문항 평가 실행
- 결과 취합
- 최종 평가 보고서 작성

우선순위:

1. 백엔드/프론트 재기동 후 UI smoke test
2. 3개 모드별 24문항 실행
3. Snowflake 문항의 관련 없음 판정 검증

---

## 13. 최종 권장 순서

오후 이후 이어서 작업할 때는 다음 순서가 가장 안전하다.

1. 프론트 `AdaptiveQueryInterface.tsx` 존재 여부 재확인
2. 없으면 UI 컴포넌트 먼저 작성
3. `api.queryStream()` 옵션 전달 추가
4. 프론트 타입 체크
5. 백엔드 재시작
6. 프론트 재시작
7. Snowflake 질문 1개 수동 테스트
8. 문서만/한계포함/전문가 3개 모드 결과 캡처
9. 24문항 자동 평가 실행
10. 평가 결과 보고서 작성

---

## 14. 최종 판단

현재 설계 방향은 타당하다.

다만 "구현 완료"로 판단하려면 아직 부족하다.

현재 완료로 볼 수 있는 것:

- 백엔드가 옵션 파라미터를 받을 수 있는 구조
- 향후 정책 방향과 모드별 기본값 설계
- 관련 없음과 일반 설명 분리 원칙

아직 해야 할 것:

- 프론트 UI 복구/구현
- 체크박스 옵션 API 전달
- 모드별 수동 UI 검증
- 모드별 24문항 자동 평가

따라서 최종 상태는 다음과 같이 기록한다.

**상태:** 설계 승인, 백엔드 일부 준비, 프론트 동기화 필요  
**다음 액션:** `AdaptiveQueryInterface.tsx` 구현 및 옵션 전달 연결  
**품질 게이트:** Snowflake 질문에서 무관 RAG 5개가 사라지고, 문서만 모드에서 관련 없음으로 표시되어야 함

