# 07 Next.js 온톨로지 AI 업무화면 구현 추적도

## 1. 원문 문서

- `req_doc_hub/분석/07_Nextjs_온톨로지_AI_업무화면_구현.md`

## 2. 핵심 요구/설계

- Next.js 프로젝트 구조
- 타입 정의
- 목 데이터
- 온톨로지 조회 함수
- 검색 함수
- 워크플로우 함수
- 단일 페이지 MVP
- API Route

## 3. 구현 추적

### 3.1 Next.js 프로젝트 구조

`src_codex`:
- Next.js 미사용
- Vanilla JS + Python HTTP server 구조

`src_anti`:
- Next.js 미사용
- Vanilla JS + FastAPI 구조

판단:
- 두 소스 모두 **미구현**

### 3.2 타입 정의와 데이터 모델

`src_codex`:
- `src_codex/backend/models.py`
- `src_codex/backend/data.py`

`src_anti`:
- `src_anti/backend/models.py`
- `src_anti/backend/data.py`

판단:
- Next.js TypeScript 타입은 미구현
- 백엔드 모델로 대체 구현

### 3.3 조회/검색/워크플로우 함수

`src_codex`:
- 조회: `OntologyService.get_order_context()`
- 검색: `SearchService.search()`
- 워크플로우: `WorkflowService.execute()`

`src_anti`:
- 조회: `OntologyService.get_order_context()`
- 검색: `SearchService.search()`
- 워크플로우: `WorkflowService.validate_and_execute()`

판단:
- 두 소스 모두 대체 구현

### 3.4 단일 페이지 MVP

`src_codex`:
- `index.html`, `app.js`, `style.css`

`src_anti`:
- `index.html`, `app.js`, `style.css`
- 대시보드/객체탐색/AI질의/워크플로우/감사 메뉴

판단:
- `src_anti`: 부분 구현 이상
- `src_codex`: 부분 구현

### 3.5 API Route

`src_codex`:
- `src_codex/server.py`

`src_anti`:
- `src_anti/backend/main.py`

판단:
- Next.js API Route는 미구현
- HTTP API로 대체 구현

## 4. 요약

`07` 문서의 Next.js 자체 구현은 두 소스 모두 하지 않았습니다. 대신 `src_anti`는 Vanilla JS와 FastAPI로 화면 MVP를 구현했고, `src_codex`는 Vanilla JS와 Python HTTP API로 운영형 백엔드 흐름을 보여줍니다.
