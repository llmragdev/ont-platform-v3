# Backend

온톨로지 중심 FastAPI 백엔드를 개발할 위치입니다.

`claud_통합/backend`를 참조하되, 첫 구현부터 다음 차이를 둡니다.

- 객체 타입/관계 타입은 코드가 아니라 `config/*.json`에서 로드
- `get_order_context`보다 범용 `get_object_context` 우선
- Action Type을 워크플로우와 그래프 노드의 공통 정의로 사용
- 관계 인스턴스 추가/삭제 API 제공

## 현재 구현

- `config/ontology.default.json`: 객체 타입, 관계 타입, 액션 타입
- `config/data.default.json`: 객체 인스턴스, 관계 인스턴스, 문서
- `app/ontology.py`: 설정 기반 온톨로지 저장소와 범용 context API
- `app/main.py`: FastAPI 엔드포인트
- `tests/test_ontology.py`: 7개 백엔드 테스트

## 실행

```powershell
cd E:\ontology_edu\Codex-통합\backend
$env:PYTHONIOENCODING="utf-8"
python -m uvicorn app.main:app --reload --port 8001
```

## 테스트

```powershell
pytest
```
