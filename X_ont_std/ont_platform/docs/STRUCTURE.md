# ont_platform — Project Structure

```
E:\ontology_edu\ont_platform\
│
├── archive\                         버전 스냅샷 (읽기 전용)
│   └── v1.0\                        claud_통합 Sprint 06 완료본 (2026-05-13)
│       ├── backend\
│       └── frontend\
│
├── src\                             v2.0 개발 소스 (유일한 코드 경로)
│   ├── backend\
│   │   ├── storage_config.py        ★ 물리 경로 팩토리 (V-ID 샤딩 핵심)
│   │   ├── app\
│   │   │   ├── api\                 FastAPI 라우터 (도메인별 분리)
│   │   │   ├── services\            비즈니스 로직 (OntologyService 등)
│   │   │   ├── repositories\        저장소 추상화 (JsonFileRepository 등)
│   │   │   └── config\              companies/users/projects/role_defaults
│   │   ├── tests\
│   │   └── storage_seeds\           초기 시드 데이터 (JSON)
│   └── frontend\
│       └── src\
│           ├── app\                 Next.js App Router
│           ├── components\
│           ├── context\
│           ├── hooks\
│           ├── lib\
│           └── types\
│
├── storage\                         런타임 데이터 (코드와 완전 분리)
│   ├── default\
│   │   └── proj-default\
│   │       ├── raw\                 원천 파일 (mid_cat/sub_cat/)
│   │       ├── vector_db\
│   │       │   ├── V5001\           Chroma 인스턴스 (독립 샤드)
│   │       │   └── V5002\           Chroma 인스턴스 (독립 샤드)
│   │       ├── ontology\            objects.json, relationships.json
│   │       └── uploads\             원본 PDF
│   ├── acme\
│   │   └── proj-001\  (동일 구조)
│   └── globex\
│       └── proj-002\  (동일 구조)
│
└── docs\
    ├── STRUCTURE.md                 이 파일
    ├── v2.0_requirements.md         전체 요구사항 정의 (기능/비기능/도메인 모델)
    ├── v2.0_architecture.md         시스템 아키텍처 설계 (레이어/모듈/데이터흐름)
    ├── v2.0_roadmap.md              Sprint 07~10+ 전체 로드맵
    └── sprints\
        └── sprint_07_plan.md
```

## 설계 원칙

1. **경로는 storage_config.py 한 곳에서만 계산** — 나머지 모듈은 함수 호출
2. **V-ID = Chroma 인스턴스 1개** — 용도별 분리, 필요한 샤드만 로드
3. **storage/ 는 코드 없음** — 백업/이전/마이그레이션 대상이 명확
4. **archive/ 는 건드리지 않음** — 언제든 v1.0으로 돌아올 수 있는 안전망
