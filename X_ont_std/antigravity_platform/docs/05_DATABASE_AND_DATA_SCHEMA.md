# 05. 데이터 및 스키마 설계서 (Data & Schema Design)

## 1. 시스템 설정 데이터 (JSON)

### 1.1 `companies.json` / `users.json` / `projects.json`
- **구조**: `claud_통합`의 성공 사례를 기반으로 테넌트-사용자-프로젝트 간 다대다(M:N) 관계 수용 가능 구조.
- **Users**: `{ "id": "uuid", "role": "admin|editor|viewer", "permissions_override": {} }`

### 1.2 `role_defaults.json`
- 역할별 기본 권한 매트릭스 정의.

---

## 2. 온톨로지 데이터 (Generic Model)

### 2.1 `ontology_objects.json`
```json
{
  "id": "uuid",
  "company_id": "tid",
  "project_id": "pid",
  "type": "EQUIPMENT",
  "values": { "serial_no": "...", "model": "..." },
  "origin": "llm-extracted",
  "status": "confirmed",
  "created_at": "timestamp",
  "created_by": "uid"
}
```

### 2.2 `ontology_relationships.json`
- `source_id`, `target_id`, `type`, `properties` 포함. `origin`, `status` 필드 필수.

### 2.3 `ontology_candidates.json`
- 승인 전 단계의 추출 데이터 저장소. `source_doc_id`와 `confidence` 점수 포함.

---

## 3. 문서 및 감사 로그 (Registry & Logs)

### 3.1 `documents_registry.json`
- `doc_id`, `company_id`, `project_id`, `filename`, `status`, `hash`.

### 3.2 `audit_log.jsonl` (Append-only)
```json
{
  "ts": "...", "uid": "...", "action": "EDIT_ENTITY",
  "resource_id": "...", "diff": { "before": {}, "after": {} }
}
```

---

## 4. 실행 계획 스키마 (Query Plan)

- **Engine**: `ONTOLOGY | VECTOR | SYSTEM`
- **Action**: `FILTER | JOIN | AGGREGATE | SEARCH | CALCULATE`
- **Params**: 각 액션별 Pydantic 기반 엄격한 스키마 정의 (06번 문서 참조).
