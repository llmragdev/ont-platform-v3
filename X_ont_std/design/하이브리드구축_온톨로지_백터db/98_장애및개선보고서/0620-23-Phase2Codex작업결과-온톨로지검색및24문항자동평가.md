# 0620-23 Phase 2 Codex 작업 결과 보고서

**작성일:** 2026-06-20  
**작성자:** Codex  
**범위:** Phase 2 Codex 담당 작업  
**상태:** Task 2-1 코드 완료, Task 2-2 완료

---

## 1. 작업 요약

Phase 2 전체팀 작업지시서에 따라 Codex 담당 작업 2개를 수행했다.

- Task 2-1: 온톨로지 검색 토큰화 개선
- Task 2-2: 24문항 자동 평가 스크립트 작성

---

## 2. Task 2-1 온톨로지 검색 개선

### 적용 파일

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\app\services\ontology.py
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\app\api\adaptive_query.py
```

### 적용 내용

`OntologyService.find_by_name()` 검색 품질을 개선했다.

개선 사항:

- 한글 완성형 코드포인트 기반 판별 추가
- 초성 분해 함수 추가
- 공백 제거 토큰, 2~4글자 n-gram 토큰 생성
- entity name/type/description/properties 전체를 검색 대상으로 확장
- 토큰 겹침, 이름 포함, 초성 포함, 온톨로지/지식그래프 키워드 포함 여부를 점수화
- 낮은 점수 잡음 결과 제거
- SSE API 온톨로지 반환 상한을 3개에서 5개로 조정

### 검증 결과

문법 검증:

```powershell
python -m py_compile app\services\ontology.py app\api\adaptive_query.py scripts\evaluate_24qa.py
```

결과:

```text
PASS
```

현재 프로젝트 데이터 상태:

```text
E:\ontology_edu\X_ont_std\ont_platform\storage\demo-co\proj-deafe1fe\ontology
json_count 0
```

즉, 현재 선택 프로젝트에는 온톨로지 엔티티 JSON 파일이 없다. 따라서 검색 토큰화 코드는 개선되었지만, 실제 UI/API에서 `Ontology (0)`이 유지되는 것은 코드 실패가 아니라 검색할 엔티티 데이터 부재 때문이다.

### 판정

```text
Task 2-1 코드 구현: 완료
Task 2-1 목표값 0→3~5개: 데이터 부재로 현 시점 미달
필요 후속 조치: 온톨로지 엔티티 재생성 또는 저장 경로 점검
```

---

## 3. Task 2-2 24문항 자동 평가 스크립트

### 적용 파일

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\scripts\evaluate_24qa.py
```

### 기능

24문항 자동 호출 스크립트를 신규 작성했다.

지원 기능:

- 기본 24문항 템플릿 내장
- 외부 JSON/CSV/TSV 질문 파일 입력 지원
- v5 SSE API 자동 호출
- `answer_chunk`, `sources`, `complete` 이벤트 파싱
- 답변 본문, RAG/Ontology/Expert 근거 수, coverage check, confidence 저장
- 결과 JSON 저장
- 실패 문항도 error 필드로 저장

실행 예:

```powershell
python scripts\evaluate_24qa.py --output eval_results_24qa.json
```

외부 질문 파일 사용 예:

```powershell
python scripts\evaluate_24qa.py --questions questions_24qa.json --output eval_results_24qa.json
```

### 실행 검증

명령:

```powershell
python scripts\evaluate_24qa.py --output eval_results_24qa_smoke.json --timeout 20
```

결과:

```text
Completed: 24/24
errors: 0
categories: Ontology 8, Advanced RAG 8, Snowflake 8
RAG min/max/avg: 5 / 5 / 5.0
Ontology min/max/avg: 0 / 0 / 0.0
Expert min/max/avg: 0 / 0 / 0.0
first coverage_percent: 100.0
```

생성 파일:

```text
E:\ontology_edu\X_ont_std\ont_platform\v5\backend\eval_results_24qa_smoke.json
```

### 판정

```text
Task 2-2: 완료
24문항 자동 호출: PASS
응답 수집 JSON 저장: PASS
```

---

## 4. 현재 리스크

### 리스크 1. Ontology 0개 유지

현재 프로젝트의 온톨로지 저장소가 비어 있다.

```text
proj-deafe1fe/ontology/*.json = 0개
```

따라서 검색 토큰화 개선만으로는 Ontology 탭에 3~5개 결과가 나올 수 없다.

필요 조치:

- `generate_ontology_from_pdf.py` 실행 결과가 현재 storage root에 저장되는지 확인
- 엔티티 JSON 재생성
- 생성 후 `find_by_name()` 재검증

### 리스크 2. 24문항 expected answer 원본 필요

자동평가 스크립트는 24개 기본 템플릿을 포함하지만, 최종 채점용 expected answer는 PM/QA가 확정한 원본 파일을 연결하는 것이 좋다.

필요 조치:

- `--questions` 옵션으로 최종 24문항 JSON/CSV 연결
- 이후 Antigravity/Claude Code의 자동 채점 단계로 전달

---

## 5. 최종 판단

Codex 담당 Phase 2 작업은 다음 상태다.

```text
Task 2-1 온톨로지 토큰화: 코드 완료
Task 2-1 3~5개 반환 목표: 현재 프로젝트 엔티티 데이터 부재로 미달
Task 2-2 24문항 자동 평가 스크립트: 완료 및 24/24 호출 성공
```

다음 순서는 온톨로지 엔티티 데이터 재생성/저장 경로 점검 후, 동일 스크립트로 재평가하는 것이다.
