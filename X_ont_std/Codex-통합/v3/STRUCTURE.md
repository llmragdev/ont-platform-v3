# Codex Platform Project Structure

작성일: 2026-05-13

## 구조 원칙

실제 개발 소스는 `project/src` 아래에 둔다. 루트의 `Codex-통합`은 저장소 구분용 이름이며, 코드 모듈명이나 런타임 저장 경로로 사용하지 않는다.

```text
project/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   ├── config/
│   │   └── tests/
│   └── frontend/
│       ├── src/
│       ├── package.json
│       └── tsconfig.json
└── storage/
    ├── default/proj-default/
    │   ├── raw/
    │   ├── vector_db/
    │   ├── ontology/
    │   └── uploads/
    ├── acme/proj-001/
    │   ├── raw/
    │   ├── vector_db/
    │   ├── ontology/
    │   └── uploads/
    └── globex/proj-002/
        ├── raw/
        ├── vector_db/
        ├── ontology/
        └── uploads/
```

## 디렉터리 역할

| 경로 | 역할 |
| --- | --- |
| `src/backend` | FastAPI 백엔드 소스 |
| `src/frontend` | Next.js 프론트엔드 소스 |
| `storage/{company}/{project}/raw` | 원천 데이터와 시드 |
| `storage/{company}/{project}/vector_db` | 벡터 인덱스 |
| `storage/{company}/{project}/ontology` | 온톨로지 객체/관계/후보 |
| `storage/{company}/{project}/uploads` | 업로드 파일 |

## 금지 사항

- `src` 아래에 `node_modules`, `.next`, `__pycache__`, `.pytest_cache`를 커밋하지 않는다.
- 코드 안에서 `Codex-통합` 경로를 하드코딩하지 않는다.
- 테넌트 데이터는 코드 디렉터리에 저장하지 않는다.

## 향후 권장

완전히 ASCII인 최종 개발 경로가 필요하면 다음처럼 `project` 폴더만 별도 위치로 승격한다.

```text
E:\ontology_edu\codex_platform\
├── src\
├── storage\
└── docs\
```

이때 `Codex-통합/docs`의 최종 설계 문서를 함께 복사하면 된다.
