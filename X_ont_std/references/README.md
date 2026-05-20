# Ontology Workbench (src_anti)

이 프로그램은 `06_온톨로지_AI_업무화면_기획.md` 분석 파일을 바탕으로 구현된 **온톨로지 AI 업무 의사결정 플랫폼**입니다.

## 문서 (Documentation)

이 프로젝트의 상세 분석 및 설계 문서는 다음 경로에서 확인할 수 있습니다.
- **[전체 오버뷰 (00_전체_오버뷰.md)](../req_doc_hub/%EB%B6%84%EC%84%9D/00_%EC%A0%84%EC%B2%B4_%EC%98%A4%EB%B2%84%EB%B7%B0.md)**
- **[추적도 마스터 매트릭스](../req_doc_hub/%EC%B6%94%EC%A0%81%EB%8F%84/00_%EC%B6%94%EC%A0%81%EB%8F%84_%EB%A7%88%EC%8A%A4%ED%84%B0_%EB%A7%A4%ED%8A%B8%EB%A6%AD%EC%8A%A4.md)**

## 기술 스택

- **Frontend**: Semantic HTML5, Vanilla JavaScript (ES6+), Vanilla CSS
- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **API**: REST API (CORS enabled)

## 실행 방법

### 1. 백엔드 (Python FastAPI) 실행

```bash
cd src_anti/backend

# 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 필수 패키지 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```
서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 실행

1. 브라우저에서 `src_anti/index.html` 파일을 엽니다. (또는 Live Server 확장 프로그램 사용 권장)
2. 백엔드 서버가 실행 중이면 데이터를 실시간으로 가져옵니다.

## 자동 테스트 (Testing)

백엔드 API의 신뢰성을 검증하기 위해 자동화된 테스트 코드가 포함되어 있습니다.

### 테스트 실행 방법

```bash
cd src_anti/backend

# 테스트 실행
pytest test_main.py
```

### 테스트 항목
- **객체 조회**: Customer 및 Order 목록 조회 검증.
- **상세 컨텍스트**: 주문에 연결된 고객 및 제품 정보 조회 검증.
- **AI 질의 엔진**: 질문 내용 및 주문 조건(금액, 리스크)에 따른 답변 정확도 검증.
- **워크플로우**: 승인/반려 액션에 따른 주문 상태 변경 프로세스 검증.

## 주요 기능


1. **대시보드**: 백엔드 API를 통한 실시간 주문 통계 및 리스트 조회.
2. **객체 탐색**: 온톨로지 컨텍스트(Order-Customer-Product) 관계형 데이터 조회.
3. **AI 질의**: 백엔드의 분석 로직을 통한 지능형 답변 및 근거 제공.
4. **워크플로우**: API 호출을 통한 주문 상태 변경 및 즉각적인 UI 갱신.
5. **실시간 컨텍스트 패널**: 선택된 객체의 상세 정보와 관련 제품 정보를 우측 패널에서 즉시 확인.
