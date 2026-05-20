# Codex v3: Palantir Practical Edition

`v3` 버전은 팔란티어의 실제 현업 설계 원칙(Materialize, Write-back, Action-Driven Modeling)을 반영한 고도화 버전입니다.

## 주요 목표

1. **Materialize & Write-back**
   - 온톨로지를 논리 레이어로 취급하고, 대용량 처리를 위한 물리 데이터셋(Materialized) 생성 기능 추가.
   - Action 결과를 원천 DB(Oracle, SAP 등)에 동기화하는 Write-back 어댑터 패턴 구현.

2. **Action-Driven Modeling**
   - 기존 DB 테이블을 복사하는 방식이 아닌, "업무 행동"으로부터 역방향으로 객체와 관계를 도출하는 설계 방식 적용.

3. **Ontology Provenance**
   - 모든 업무 객체와 관계에 대해 출처(Source Document, Page), 신뢰도(Confidence), 사용자 승인 상태(Candidate/Approved) 관리.

4. **Governance**
   - 도메인별 폴더 표준화 및 네이밍 컨벤션(`[부서]_[주제]_[버전]`) 강제.

5. **Operational Evaluation**
   - `evaluate.py`를 통해 RAG 답변 품질(Faithfulness, Citation Coverage) 및 온톨로지 조회 성능 정량화.

## 개발 기준

v3는 v2의 안정적인 FastAPI/Next.js/테넌트/스토리지 골격을 유지하고, 팔란티어 실무 기능만 서비스 모듈로 분리해 확장합니다.

- `repositories.py`: 온톨로지 객체/관계 저장소. 외부 시스템 write-back을 직접 수행하지 않음.
- `action_service.py`: 업무 Action 실행. 객체 변경 이력과 write-back 요청의 시작점.
- `writeback_service.py`: Action 결과를 외부 시스템 반영 요청으로 기록하고, 현재는 ERP 어댑터를 파일로 시뮬레이션.
- `materialize_service.py`: 논리 온톨로지 객체를 물리 데이터셋 JSON으로 materialize.
- `provenance_service.py`: 출처, 신뢰도, 생성자, 생성 시각을 표준화.
- `governance_service.py`: `[도메인]_[주제]_v[버전]` 네이밍 규칙 검증.

## v3 API

```text
POST /api/v1/ontology/actions/execute
POST /api/v1/ontology/materialize
GET  /api/v1/ontology/writeback
```

Action 예시:

```json
{
  "action_name": "APPROVE_ORDER",
  "target_id": "OR001",
  "params": {
    "doc_id": "action-log-001"
  },
  "write_back": true
}
```

Materialize 예시:

```json
{
  "dataset_name": "생산_공정지연_v1",
  "object_type": "Order"
}
```

## 실행 가이드

### Backend (v3)
```powershell
cd v3/src/backend
conda activate codex_be
python -m uvicorn app.main:app --reload --port 8003
```

### Frontend (v3)
```powershell
cd v3/src/frontend
conda activate codex_fe
npm run dev -- --port 3103
```

## 참고 문서
- [13_팔란티어_실무_설계원칙.md](../../req_doc_hub/분석/13_팔란티어_실무_설계원칙.md)
