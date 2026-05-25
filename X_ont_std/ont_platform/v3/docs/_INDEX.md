# ont_platform v3 문서 색인
## Documentation Index & Navigation Guide

**최종 업데이트**: 2026-05-25  
**구조 개선**: 문서를 논리적 카테고리별로 정리

---

## 📂 문서 구조

```
docs/
├── _INDEX.md                    ← 이 파일 (네비게이션 가이드)
├── phases/                      ← Phase별 개발 문서
│   ├── phase3/                  ← Phase 3 (완료)
│   │   ├── ACTION_DEFINITION.md
│   │   ├── STATE_MACHINE.md
│   │   ├── IMPLEMENTATION_PLAN.md
│   │   ├── STARTUP_INSTRUCTIONS.md
│   │   ├── COMPLETION_CHECKLIST.md
│   │   ├── WEEK4_CLAUDE_REPORT.md
│   │   ├── WEEK4_FINAL_INTEGRATION_v2.md
│   │   └── PERFORMANCE_REPORT.md
│   │
│   └── phase4/                  ← Phase 4 (개발 예정)
│       ├── ONTOLOGY_EXTENSIBILITY.md
│       ├── WEEK_BY_WEEK_PLAN.md
│       ├── TECHNICAL_PREP.md
│       ├── AGENT_INSTRUCTIONS.md
│       └── PROGRESS.md          (자동 생성)
│
├── guides/                      ← 설계 및 가이드
│   ├── ARCHITECTURE.md          ← 시스템 아키텍처
│   ├── PROJECT_ROADMAP_2026.md  ← 전체 프로젝트 로드맵
│   ├── API_DESIGN.md            (향후 추가)
│   └── DATABASE_DESIGN.md       (향후 추가)
│
├── specifications/              ← 명세서 및 요구사항
│   ├── NAMING.md                ← 이름 지정 규칙
│   ├── REQUIREMENTS.md          ← 요구사항 정렬
│   ├── SCHEMA_DESIGN.md         ← 데이터 스키마
│   └── SPARQL_API.md            ← SPARQL API 계약
│
├── setup/                       ← 환경 설정
│   ├── NEON.md                  ← Neon PostgreSQL 설정
│   └── ENVIRONMENT.md           (향후 추가)
│
├── performance/                 ← 성능 관련 문서
│   ├── BASELINE.md
│   ├── LOAD_TESTING.md
│   ├── QUERY_OPTIMIZATION.md
│   ├── MIGRATION.md
│   ├── FINAL_REPORT.md
│   └── VECTOR_SEARCH.md
│
├── DOCUMENT_NAMING_CONVENTION.md ← 문서 작성 규칙
├── IMPLEMENTATION_GUARDRAILS.md ← 구현 가이드
├── MIGRATION_SCRIPTS.md
├── MONITORING_SETUP.md
├── INDEX_ANALYSIS.md
└── 기타...
```

---

## 🎯 사용 시나리오별 문서 읽기 순서

### 🆕 신규 개발자 온보딩
1. **[../README.md](../README.md)** - 프로젝트 개요
2. **[../ROADMAP.md](../ROADMAP.md)** - 고수준 로드맵
3. **[guides/ARCHITECTURE.md](guides/ARCHITECTURE.md)** - 시스템 아키텍처
4. **[specifications/NAMING.md](specifications/NAMING.md)** - 명명 규칙
5. **[phases/phase4/AGENT_INSTRUCTIONS.md](phases/phase4/AGENT_INSTRUCTIONS.md)** - 현재 진행 중인 작업

### 📖 Phase 3 이해하기
1. **[phases/phase3/ACTION_DEFINITION.md](phases/phase3/ACTION_DEFINITION.md)** - 액션 정의
2. **[phases/phase3/STATE_MACHINE.md](phases/phase3/STATE_MACHINE.md)** - 상태 관리
3. **[phases/phase3/COMPLETION_CHECKLIST.md](phases/phase3/COMPLETION_CHECKLIST.md)** - 완료 현황
4. **[phases/phase3/PERFORMANCE_REPORT.md](phases/phase3/PERFORMANCE_REPORT.md)** - 성능 분석

### 🚀 Phase 4 개발 시작
1. **[phases/phase4/ONTOLOGY_EXTENSIBILITY.md](phases/phase4/ONTOLOGY_EXTENSIBILITY.md)** - Phase 4 개요
2. **[phases/phase4/TECHNICAL_PREP.md](phases/phase4/TECHNICAL_PREP.md)** - 기술 준비
3. **[phases/phase4/WEEK_BY_WEEK_PLAN.md](phases/phase4/WEEK_BY_WEEK_PLAN.md)** - 주간 계획
4. **[phases/phase4/AGENT_INSTRUCTIONS.md](phases/phase4/AGENT_INSTRUCTIONS.md)** - 역할별 지시서

### 📊 성능 분석하기
1. **[performance/BASELINE.md](performance/BASELINE.md)** - 성능 기준선
2. **[phases/phase3/PERFORMANCE_REPORT.md](phases/phase3/PERFORMANCE_REPORT.md)** - Phase 3 성능 분석
3. **[performance/QUERY_OPTIMIZATION.md](performance/QUERY_OPTIMIZATION.md)** - 쿼리 최적화
4. **[performance/MIGRATION.md](performance/MIGRATION.md)** - PostgreSQL 마이그레이션

### 🔧 API 설계하기
1. **[specifications/SPARQL_API.md](specifications/SPARQL_API.md)** - SPARQL API 명세
2. **[guides/ARCHITECTURE.md](guides/ARCHITECTURE.md)** - 시스템 아키텍처
3. **[specifications/SCHEMA_DESIGN.md](specifications/SCHEMA_DESIGN.md)** - 스키마 설계

### 📈 데이터베이스 설정
1. **[setup/NEON.md](setup/NEON.md)** - Neon 클라우드 설정
2. **[specifications/SCHEMA_DESIGN.md](specifications/SCHEMA_DESIGN.md)** - 테이블 설계
3. **[performance/MIGRATION.md](performance/MIGRATION.md)** - 마이그레이션 스크립트

---

## 📁 주간 지시서 위치

개별 에이전트의 **주간 작업 지시서**는 별도 관리됩니다:

```
week_instructions/
└── PHASE4/
    └── Week_1-2_Schema/
        ├── Claude.md         ← Claude의 Week 1-2 지시서
        ├── Codex.md          ← Codex의 Week 1-2 지시서
        └── Antigravity.md    ← Antigravity의 Week 1-2 지시서

Week 3, 4, 5-8은 추가될 예정입니다.
```

---

## 🏗️ 문서 카테고리 설명

### phases/
**목적**: 각 Phase별 계획, 구현, 완료 문서 관리  
**구조**: phase1/, phase2/, phase3/, phase4/ ...  
**대상자**: 전체 팀

### guides/
**목적**: 시스템 설계, 아키텍처, 로드맵 등 참고 자료  
**내용**: 
- ARCHITECTURE.md - 시스템 전체 구조
- PROJECT_ROADMAP_2026.md - 연간 계획
- API_DESIGN.md - API 설계 원칙 (향후)
- DATABASE_DESIGN.md - DB 설계 원칙 (향후)

**대상자**: 신규 개발자, 아키텍트

### specifications/
**목적**: 정식 명세서, 요구사항, 계약  
**내용**:
- NAMING.md - 파일, 함수, 변수 명명 규칙
- REQUIREMENTS.md - 비즈니스 요구사항
- SCHEMA_DESIGN.md - 데이터 스키마
- SPARQL_API.md - RDF API 계약

**대상자**: 개발자, QA, 아키텍트

### setup/
**목적**: 환경 설정 및 배포 가이드  
**내용**:
- NEON.md - 클라우드 PostgreSQL 설정
- ENVIRONMENT.md - 개발/스테이징/프로덕션 환경

**대상자**: DevOps, 시스템 관리자

### performance/
**목적**: 성능 분석, 최적화, 벤치마크 결과  
**내용**:
- BASELINE.md - 기준선 메트릭
- LOAD_TESTING.md - 부하 테스트 결과
- QUERY_OPTIMIZATION.md - SQL 쿼리 최적화
- MIGRATION.md - 마이그레이션 로드맵
- FINAL_REPORT.md - 최종 성능 분석

**대상자**: 성능 담당자, DevOps

---

## 🔗 관련 리소스

| 리소스 | 위치 | 용도 |
|--------|------|------|
| 주간 작업 지시서 | `week_instructions/` | 에이전트별 주간 태스크 |
| 개발 로그 | `task_logs/claude/` | 개별 작업 기록 |
| 소스 코드 | `src/` | 구현 |
| 테스트 | `tests/` | 검증 |
| 프로젝트 README | `../README.md` | 최상단 개요 |

---

## 📝 문서 작성 가이드

### 새로운 문서 추가 시
1. **카테고리 결정**: phases/, guides/, specifications/, setup/, performance/ 중 선택
2. **파일명**: `UPPERCASE_WITH_UNDERSCORES.md`
3. **템플릿**: 상단에 메타데이터 포함
   ```markdown
   # 문서 제목
   
   **작성**: YYYY-MM-DD  
   **마지막 수정**: YYYY-MM-DD  
   **관련 문서**: [문서명](경로), [문서명](경로)
   ```

### 문서 이동 시
- `git mv old-path new-path` 사용 (히스토리 유지)
- 이 인덱스 업데이트
- 다른 문서의 참조 링크 업데이트

---

## 🔄 자동 생성 문서

다음 문서들은 자동으로 생성되거나 업데이트됩니다:

- `phases/phase4/PROGRESS.md` - Phase 4 주간 진행 상황 (매주 업데이트)

---

**최종 목표**: 신규 개발자가 `docs/_INDEX.md`를 읽고 필요한 모든 문서를 쉽게 찾을 수 있도록 구성
