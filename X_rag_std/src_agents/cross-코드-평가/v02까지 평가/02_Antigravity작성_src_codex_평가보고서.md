# src_codex RAG 구현 및 표준 설계 준수 검토

## 검토 요약

`src_codex` 코드는 `RAG_표준_설계_v1.0.md`와 상세 요건을 훌륭하게 준수하고 있으며, `src_claud/v2`에서 발견되었던 치명적인 운영상의 문제점(임베딩 불일치 및 멀티테넌트 격리 오류)을 완벽히 해결한 우수한 구현입니다.

테스트 역시 정상적으로 통과되며, 전반적인 안정성이 높습니다.
```text
pytest test_endpoints.py -v
======================= 5 passed, 10 warnings ========================
```

다만, 트래픽이 많은 엔터프라이즈 환경에 배포하기 전에 **비동기 블로킹 이슈** 등 일부 성능 관련 개선이 필요합니다.

---

## 주요 장점 및 표준 준수 사항 (Good Points)

### 1. `RAG_표준_설계_v1.0.md`의 완벽한 준수
* **역매핑(Reverse Mapping) 완비**: `used_chunks`와 `candidate_chunks`를 명확히 구분하여 반환하며, 메타데이터에 `source_name`, `page_no`, `category_mid`, `vector_db_id` 등을 빠짐없이 포함하여 답변의 신뢰성(Grounding)을 추적할 수 있도록 완벽히 구현했습니다.
* **물리적 분리 라우팅**: `vector_db_id`를 기반으로 물리적 VectorDB 인스턴스를 분리하여 저장하고 검색하는 아키텍처를 정확히 따릅니다.
* **상태 전이 및 증분 업데이트**: `pending -> processing -> completed / error`로 이어지는 상태값과, `PUT` 메서드를 통한 청크 증분 업데이트 로직을 잘 구현했습니다.

### 2. `src_claud/v2`의 한계점 극복
* **Chroma + Gemini 임베딩 일관성 보장**: `src_claud`에서는 Chroma 내부 임베딩과 Gemini Query 임베딩이 혼재되는 문제가 있었으나, `src_codex`는 Chroma에 문서를 저장할 때 Gemini Gateway를 통해 생성한 `embeddings`를 명시적으로 주입하여 벡터 공간의 일관성을 확보했습니다.
* **멀티테넌트 검색 격리 보장**: `X-Company-ID`를 DB 레코드뿐만 아니라 벡터 메타데이터에 저장하고, 검색 시 Adapter 필터에 `company_id`를 강제 주입하여 A회사의 검색 결과에 B회사의 문서가 섞이는 보안 사고를 원천 차단했습니다.

---

## 주요 이슈 및 개선 필요 사항 (Issues & Recommendations)

### 1. 동기 블로킹으로 인한 FastAPI 성능 저하 (가장 치명적)
FastAPI 라우터는 `async def`로 선언되어 있으나, 내부 서비스 로직(문서 업로드 처리, RAG 검색 등)은 동기형(Synchronous) 코드로 작성되어 있습니다.
Gemini Gateway로 HTTP 요청을 보내거나 대용량 문서를 파싱하는 동안 **이벤트 루프(Event Loop)가 블로킹**되어, 다른 사용자의 요청을 전혀 처리할 수 없게 됩니다.

**수정 권장:**
* I/O 바운드 작업(파이프라인 실행, RAG 검색 등)을 라우터 레벨에서 `await asyncio.to_thread()`로 감싸 스레드 풀에서 실행하도록 변경해야 합니다. (이 부분은 최근 `src_antigravity`에서 해결한 방식과 동일합니다.)

### 2. SQLAlchemy Deprecation Warning
테스트 실행 시 `datetime.datetime.utcnow()`의 사용으로 인해 다수의 Deprecation Warning이 발생합니다. 파이썬 버전이 올라감에 따라 향후 제거될 위험이 있습니다.

**수정 권장:**
* `datetime.utcnow()`를 `datetime.now(datetime.UTC)` (또는 `timezone-aware` 객체)로 변경하여 안정성을 확보해야 합니다.

### 3. 동기 SQLAlchemy Session과 스레드 풀의 결합 시 주의 사항
1번 이슈를 해결하기 위해 `asyncio.to_thread`를 도입할 경우, `src_claud`와 마찬가지로 동기형 SQLAlchemy Session 객체가 여러 스레드를 교차하면서 스레드 세이프(Thread-Safe)하지 않은 문제가 발생할 수 있습니다.

**수정 권장:**
* 비동기 작업용 스레드로 넘어갈 때, 기존 Session을 넘기지 말고 **해당 스레드 내부에서 Session을 새로 발급**받거나, DB 상태 저장만 라우터의 메인 스레드에서 처리하고 순수 벡터 추출 로직만 스레드 풀로 넘기는 구조로 리팩토링이 필요합니다.

---

## 결론

`src_codex`는 RAG 표준 설계와 Gemini Gateway 아키텍처의 의도를 가장 정확하게 이해하고 구현한 모델입니다. 특히 데이터 보안(멀티테넌트)과 벡터 정합성을 스스로 해결한 점이 훌륭합니다.

위에서 지적한 **FastAPI 비동기 블로킹 제어(asyncio.to_thread 적용)** 최적화만 거치면 즉각적인 상용 프로덕션 운영이 가능합니다.
