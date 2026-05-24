# 3개 에이전트 병렬 개발 시작 지시서
**작성**: 2026-05-24 17:00  
**대상**: Claude (나) + Codex + Antigravity  
**시작**: 2026-06-03  
**상태**: 🚀 준비 완료

---

## 📋 각 팀이 읽어야 할 문서 (순서대로)

### 1️⃣ 먼저 읽을 것 (공통)

#### A. 프로젝트 전체 컨텍스트
**문서**: `E:\ontology_edu\X_ont_std\CLAUDE.md`
```
읽을 부분:
- 프로젝트 정체성 (ontology 기반 의사결정 시스템)
- Phase 2.5 목표 (PostgreSQL 마이그레이션)
- 현재 상태 (Week 1 완료, Week 2-4 진행 중)
```

#### B. 병렬 개발 전체 계획
**문서**: `E:\ontology_edu\X_ont_std\ont_platform\v3\PHASE2_5_PARALLEL_DEVELOPMENT_PLAN.md`
```
읽을 부분:
- 전체 목표 (3주간 병렬 개발)
- 각 팀의 역할 요약
- 협업 규칙 (git, commit, PR)
- 마일스톤 일정 (06-03 ~ 06-21)
```

---

### 2️⃣ 팀별로 읽을 것

#### 🔴 **Claude (SPARQL→SQL 번역기)**

1. **전체 미션** → `PHASE2_5_PARALLEL_DEVELOPMENT_PLAN.md`의 "CLAUDE" 섹션
   - 3주 일정 상세
   - 산출물 체크리스트
   - 마일스톤 확인

2. **기술 배경 문서들**:
   - `ont_platform/v3/docs/SPARQL_TRANSLATOR_DESIGN.md` (설계)
   - `ont_platform/v3/docs/SCHEMA_DESIGN.md` (DB 스키마)
   - `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md` (전체 로드맵)

3. **코드 상태 확인**:
   - `ont_platform/v3/src/backend/app/services/sparql_service_v2.py` (기존 rdflib 엔진)
   - `ont_platform/v3/src/backend/app/db/models.py` (ORM 모델)
   - `ont_platform/v3/src/backend/requirements.txt` (의존성)

---

#### 🟠 **Codex (Frontend UI/UX)**

1. **전체 미션** → `PHASE2_5_PARALLEL_DEVELOPMENT_PLAN.md`의 "CODEX" 섹션
   - 3주 일정 상세
   - UI 컴포넌트 목록
   - e2e 테스트 시나리오

2. **현재 Frontend 상태**:
   - `ont_platform/v3/src/frontend/` (Next.js 프로젝트)
   - `ont_platform/v3/src/frontend/package.json` (의존성 확인)

3. **성능 참고**:
   - `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md` (성능 목표)
   - Claude의 API가 Week 2 말에 완성됨을 염두에 두고 일정 조정

---

#### 🟢 **Antigravity (성능 최적화)**

1. **전체 미션** → `PHASE2_5_PARALLEL_DEVELOPMENT_PLAN.md`의 "ANTIGRAVITY" 섹션
   - 3주 일정 상세
   - 벤치마크 목표
   - 최적화 기회

2. **성능 가이드**:
   - `ont_platform/v3/docs/POSTGRES_MIGRATION_ROADMAP.md` (성능 목표)
   - `ont_platform/v3/docs/SCHEMA_DESIGN.md` (인덱스 전략)

3. **현재 DB 상태**:
   - `ont_platform/v3/scripts/init_schema.sql` (스키마 확인)
   - `ont_platform/v3/src/backend/requirements.txt` (도구 확인)

---

## 🚀 실행 명령어 (모든 팀)

### Step 1: Repository Clone (각자 자신의 branch로)

#### Claude
```bash
cd C:\dev\  # 또는 자신의 작업 폴더
git clone https://github.com/llmragdev/ont-platform-v3.git
cd ont-platform-v3
git checkout feat/claude-sparql-translator
```

#### Codex
```bash
cd C:\dev\  # 또는 자신의 작업 폴더
git clone https://github.com/llmragdev/ont-platform-v3.git
cd ont-platform-v3
git checkout feat/codex-frontend-ui
```

#### Antigravity
```bash
cd C:\dev\  # 또는 자신의 작업 폴더
git clone https://github.com/llmragdev/ont-platform-v3.git
cd ont-platform-v3
git checkout feat/antigravity-performance
```

### Step 2: 환경 설정 (팀별)

#### Claude (Backend)
```bash
cd src/backend

# 1. Python 가상환경
python -m venv venv
venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. .env 파일 생성
copy .env.example .env
# .env에 DATABASE_URL 설정 (Neon.tech 또는 로컬)

# 4. 테스트 실행 확인
pytest tests/test_priority2_sparql_v2.py -v
```

#### Codex (Frontend)
```bash
cd src/frontend

# 1. Node 패키지 설치
npm install

# 2. 개발 서버 시작 (테스트용)
npm run dev
# http://localhost:3001 접속

# 3. 테스트 실행 확인 (나중)
npm test
```

#### Antigravity (Performance)
```bash
cd src/backend

# 1. Python 가상환경
python -m venv venv
venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. PostgreSQL 시작 (로컬 또는 Neon.tech)
docker-compose -f docker-compose.dev.yml up -d

# 4. 데이터베이스 초기화
python scripts/setup_database.py
```

---

## 📅 일정 확인

### Week 2 (2026-06-03 ~ 06-07)

| 날짜 | Claude | Codex | Antigravity |
|------|--------|-------|-------------|
| 06-03 | Task 2-1 시작 | QueryResult 개선 | 벡터 최적화 |
| 06-04 | 아키텍처 설계 완료 | 실시간 UI | 임베딩 캐싱 |
| 06-05 | 구현 진행 | 시각화 기초 | 테스트 틀 |
| 06-06 | 40개 테스트 완료 | 성능 차트 | 의미 검색 테스트 |
| 06-07 | 성능 검증 완료 ✅ | UI 완성 ✅ | 인덱스 분석 ✅ |

---

## 💬 협업 규칙

### 매일 할 것
```
1. 자신의 feature branch에서 작업
2. 커밋: [Team] Task - 설명
   예: [Claude] Task 2-1 - SPARQL translator architecture design
3. push: git push origin feat/team-name

4. 문제 발생 → Slack/Email 즉시 공유
   - 다른 팀이 준비할 수 있도록
```

### 주간 (금요일 5시)
```
1. 각자 feature branch pull (최신 상태)
2. main으로 merge (conflict 확인)
3. GitHub에서 최종 확인
4. 다음 주 목표 확인
```

### PR 작성 (주말)
```
Title: [Team] Week N 완료 - 산출물 요약

Body:
## Summary
- Task N-1: 완료 (산출물 파일)
- Task N-2: 완료 (산출물 파일)
- Task N-3: 진행 중 (% 완성도)

## 테스트 결과
- Unit tests: N/N passing
- Integration tests: N/N passing
- Performance: 목표 달성 여부

## 남은 이슈
- (있으면 나열)
```

---

## 🔗 주요 URL

| 항목 | URL |
|------|-----|
| GitHub Repository | https://github.com/llmragdev/ont-platform-v3 |
| GitHub Issues | https://github.com/llmragdev/ont-platform-v3/issues |
| GitHub Projects | https://github.com/llmragdev/ont-platform-v3/projects |

---

## 📞 연락처

문제 발생 시:
1. **Slack #dev-ont-platform**: 실시간 질문 (5분 내)
2. **Email**: 정식 문서 필요 시
3. **Weekly Sync (월 9:00)**: 진행 상황 공유 (15분)

---

## ✅ 시작 전 체크리스트

```
[ ] CLAUDE.md 읽었음
[ ] PHASE2_5_PARALLEL_DEVELOPMENT_PLAN.md 읽었음
[ ] 자신의 팀 섹션 상세히 읽었음
[ ] Repository clone했음
[ ] 자신의 feature branch에서 작업 중임
[ ] 환경 설정 완료했음
[ ] 초기 테스트 실행 완료했음
[ ] 질문 없음 (있으면 Slack)
```

---

## 🎯 성공 기준

**Week 2 마지막 (2026-06-07 금요일 5시)**:
- Claude: 40개 SPARQL 패턴 테스트 통과 ✅
- Codex: QueryResult UI 완성 + 성능 차트 ✅
- Antigravity: 벡터 최적화 + 인덱스 분석 ✅

**Week 3 마지막 (2026-06-14 금요일 5시)**:
- Claude: API 엔드포인트 3개 + 동시성 지원 ✅
- Codex: 그래프 시각화 + 필터 빌더 ✅
- Antigravity: 부하 테스트 완료 + 쿼리 최적화 ✅

**Week 4 마지막 (2026-06-21 금요일 5시)**:
- Claude: 50개 통합 테스트 + 성능 튜닝 완료 ✅
- Codex: 반응형 UI + 다크모드 + e2e 테스트 ✅
- Antigravity: 캐싱 + 최종 벤치마크 + PR 병합 ✅

---

## 📝 다음 문서들

이후 필요할 때 읽을 문서들 (미리 읽지 말 것):
- `ont_platform/v3/ARCHITECTURE.md` (전체 구조)
- `ont_platform/v3/ROADMAP.md` (장기 로드맵)
- `ont_platform/v3/PHASE3_IMPLEMENTATION_PLAN.md` (Phase 3 - 액션 구현)
- `ont_platform/v3/PHASE4_ONTOLOGY_EXTENSIBILITY.md` (Phase 4 - 확장성)

---

**최종 확인**: 모든 팀 준비 완료!  
**시작 일시**: 2026-06-03 09:00 (월요일 아침)  
**최종 완료**: 2026-06-21 17:00 (금요일 저녁)
