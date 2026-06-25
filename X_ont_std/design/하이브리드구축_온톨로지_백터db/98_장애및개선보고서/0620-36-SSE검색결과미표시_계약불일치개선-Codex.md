# 0620-36 SSE 검색 결과 미표시 계약 불일치 개선 보고서

**작성일시:** 2026-06-20 19:28  
**작성자:** Codex  
**대상:** v5 하이브리드 질의 엔진  
**상태:** 1차 조치 완료, UI 재검증 필요

---

## 1. 현상

프론트엔드 화면에서 질의 실행 시 다음 문제가 발생했다.

- 답변 영역에 "관련 정보를 찾을 수 없습니다"가 표시됨
- RAG 탭이 0개로 표시됨
- Ontology 탭도 0개로 표시됨
- 사용자는 실제로 RAG와 온톨로지 검색 결과가 모두 나오지 않는 것으로 인지함

대표 질의:

```text
정형 데이터 통합에서 온톨로지와 지식그래프를 어떻게 구분해 적용해야 하는가?
```

---

## 2. 로그 기반 확인

백엔드 로그 파일:

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\logs\backend-latest.log
```

해당 질의에 대해 백엔드는 검색 자체를 수행했고, 한 시점의 로그에서는 다음과 같이 확인되었다.

```text
[AdaptiveQuery] evidence raw_rag=5 raw_ontology=4 filtered_rag=5 filtered_ontology=4
[AdaptiveQuery] complete rag=5 ontology=4
```

따라서 "백엔드 검색이 항상 0개"라는 판단은 정확하지 않다.  
직접 원인은 백엔드 검색 실패가 아니라, SSE 이벤트 계약 불일치로 인해 프론트엔드가 검색 결과 이벤트를 받지 못한 것이다.

---

## 3. 근본 원인

### 3.1 SSE 이벤트 형식 불일치

프론트엔드는 다음과 같은 표준 SSE 이벤트를 기다리고 있었다.

```ts
eventSource.addEventListener('sources', ...)
eventSource.addEventListener('answer_chunk', ...)
eventSource.addEventListener('complete', ...)
```

하지만 백엔드는 기존에 다음과 같은 JSON-in-data 형식으로만 전송했다.

```text
data: {"event":"sources","data":{...}}
```

이 방식에서는 브라우저의 `addEventListener('sources', ...)`가 호출되지 않는다.  
즉, 검색 결과가 내려와도 프론트엔드 상태 저장소에 반영되지 않았다.

### 3.2 complete 이벤트에서 sources 덮어쓰기 위험

초기 `sources` 이벤트는 상세 객체를 내려보내지만, `complete` 메타의 `sources`는 문자열 목록 형태였다.

```json
{
  "sources": {
    "rag": ["filename.pdf"],
    "ontology": ["entity-id"]
  }
}
```

프론트엔드의 완료 처리에서 `meta.sources`가 현재 sources를 덮어쓸 수 있어, 상세 출처가 손실될 위험이 있었다.

---

## 4. 조치 내용

수정 파일:

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\app\api\adaptive_query.py
```

### 4.1 표준 SSE 이벤트로 변경

기존:

```text
data: {"event":"sources","data":...}
```

개선:

```text
event: sources
data: {...}
```

이를 통해 프론트엔드의 `addEventListener('sources', ...)`와 백엔드 출력 계약을 일치시켰다.

### 4.2 complete 메타의 sources 구조 보존

`complete` 이벤트에서도 `sources_for_tab` 상세 구조를 그대로 전달하도록 수정했다.

```json
{
  "rag": [{ "filename": "...", "page": 1, "text": "...", "score": 0.75 }],
  "ontology": [{ "name": "...", "entity_id": "...", "score": 3.0 }],
  "expert_opinions": []
}
```

---

## 5. 검증 결과

### 5.1 컴파일 검증

```powershell
python -m py_compile app\api\adaptive_query.py
```

결과: 통과

### 5.2 실제 SSE 원문 검증

직접 HTTP 호출 결과, 다음 형식으로 내려오는 것을 확인했다.

```text
event: sources
data: {"rag": [...], "ontology": [...], "expert_opinions": []}
```

따라서 프론트엔드가 새로고침 또는 재빌드된 상태라면 `sources` 이벤트를 정상 수신할 수 있다.

---

## 6. 남은 이슈

### 6.1 Ontology 0개 케이스

수정 후 직접 호출에서는 RAG 5개가 내려오는 것은 확인되었으나, 일부 호출에서는 Ontology가 0개로 내려왔다.

이는 SSE 표시 문제가 아니라 온톨로지 저장소 또는 `find_by_name()` 검색 품질 문제로 분리해서 봐야 한다.

추가 확인 중 발견 사항:

- `app/services/ontology.py` 내부에 한글 키워드가 깨진 문자열로 남아 있는 흔적이 있음
- 온톨로지 저장 데이터가 프로젝트별로 충분하지 않거나, 질의 토큰과 엔티티 매칭이 안정적이지 않을 가능성이 있음

### 6.2 RAG 관련성 품질

RAG 5개가 표시되더라도 질의와 직접 관련이 낮은 문서가 포함될 수 있다.  
이는 화면 표시 장애와 별개로 검색 품질 개선 이슈다.

후속 개선 후보:

- 질문 핵심어 기반 후필터 강화
- 문서 제목/본문 필수어 매칭 정책 분리
- Chroma distance 점수 임계값 재검토
- "관련 없음" 판정 로그를 UI 메시지와 함께 연결

---

## 7. 최종 판정

| 항목 | 판정 |
|---|---|
| 백엔드 기동 | 정상 |
| SSE 이벤트 계약 | 수정 완료 |
| RAG 화면 미표시 직접 원인 | 해결 |
| Ontology 0개 | 별도 이슈 |
| RAG 관련성 품질 | 별도 개선 필요 |
| 최종 UI 재검증 | 필요 |

---

## 8. 다음 액션

1. 브라우저 새로고침 후 동일 질문 재테스트
2. RAG 탭에 5개가 표시되는지 확인
3. Ontology 탭이 계속 0개이면 온톨로지 저장소/검색 로직 별도 점검
4. RAG가 표시되지만 내용이 엉뚱하면 관련성 필터 개선 이슈로 전환

---

## 9. 결론

이번 장애의 직접 원인은 검색 엔진 자체의 중단이 아니라 **백엔드 SSE 출력 형식과 프론트엔드 EventSource 수신 방식의 계약 불일치**였다.

계약을 표준 SSE 이벤트 형식으로 맞추면서 RAG/Ontology 소스 이벤트를 프론트엔드가 수신할 수 있게 수정했다. 다만 Ontology 0개와 RAG 관련성 문제는 데이터/검색 품질 영역의 후속 과제로 남는다.
