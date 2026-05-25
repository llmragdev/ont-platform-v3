# Phase 4 Week 1: v4 환경 구성 & 준비 (2026-06-01 ~ 2026-06-07)

**목표**: v4 폴더 생성, 개발 환경 구성, 3에이전트 병렬 개발 시작 준비  
**기간**: 1주 (5일)  
**팀**: Claude + Antigravity + Codex  

---

## 🎯 Week 1 목표 (공통)

```
Day 1-2: v4 폴더 및 기초 구조 설정
Day 3-4: 개발 환경 및 테스트 환경 구성
Day 5: 최종 확인 및 Week 2 준비
```

---

## 📋 공통 작업 (모든 에이전트 협력)

### Task 1: v4 폴더 생성 & 복제 (Day 1)

#### 실행 명령어
```bash
# 현재 위치: E:\ontology_edu\X_rag_std\src_agents\src_claud\

# 1. v3 → v4 복제
cp -r v3 v4

# 2. 폴더 구조 확인
ls -la v4/

# 3. v4로 이동
cd v4
```

#### 확인 사항
```
✅ 폴더 생성 완료
✅ 모든 파일 복제 확인
✅ __pycache__ 제거 (선택)
✅ .git 상태 확인
```

---

### Task 2: v4 README.md 업데이트 (Day 1-2)

#### 변경 내용
```markdown
# src_claud v4

**버전**: v4 (프로덕션 고도화 단계)  
**상태**: 개발 중 (2026-06-01 ~ 2026-06-30)  
**개발 방식**: 3에이전트 병렬 개발  

## v3 → v4 변경사항

### 신규 기능
- ✨ 검색 결과 재순위화
- ✨ 쿼리 확장
- ✨ 다중 필터 조건
- ✨ 배치 API
- ✨ 비동기 검색

### 성능 개선
- ⚡ 청킹 품질: 500자+ 보장
- ⚡ 응답시간: p99 < 200ms
- ⚡ 처리량: 1000 QPS
- ⚡ 캐시 hit rate: 70%+

### 문서 추가
- 📖 마이그레이션 가이드
- 📖 배포 자동화
- 📖 성능 리포트
- 📖 사용자 가이드
```

#### 파일
```
src_claud/v4/README.md (수정)
```

---

### Task 3: CLAUDE.md 업데이트 (Day 2)

#### 변경 내용
```markdown
## 🚦 지금 당장 해야 할 것

### Phase 4: v4 고도화 (우선순위: 높음) 🔨 진행 중 (2026-06-01~)

**목표**: 프로덕션 레벨 RAG v4 완성 (3에이전트 병렬 개발)

**개발 방식**:
- Claude: API 고도화 (재순위화, 쿼리 확장 등)
- Antigravity: 성능 최적화 (청킹, 캐싱, 부하 테스트)
- Codex: 통합 & QA (E2E 테스트, 배포)

**예상 시간**: 4주  
**담당**: 3에이전트 병렬

**상세**: `PHASE4_v4_UPGRADE_PLAN.md` 참고
```

#### 파일
```
CLAUDE.md (수정)
```

---

### Task 4: v4 폴더 구조 검증 (Day 2-3)

#### 폴더 구조
```
src_claud/v4/
├── app/
│   ├── api/
│   │   ├── search.py
│   │   ├── documents.py
│   │   ├── projects.py
│   │   ├── categories.py
│   │   ├── health.py
│   │   └── reranking.py (신규, Week 3)
│   ├── services/
│   │   ├── pipeline/
│   │   │   ├── extractor.py
│   │   │   ├── chunker.py
│   │   │   └── __init__.py
│   │   ├── rag_service.py
│   │   ├── document_service.py
│   │   ├── project_service.py
│   │   ├── router.py
│   │   ├── providers.py
│   │   └── query_expansion.py (신규, Week 3)
│   ├── models/
│   ├── db/
│   ├── repositories/
│   ├── core/
│   ├── main.py
│   └── __init__.py
├── tests/
│   ├── test_*.py (기존)
│   ├── load/ (신규, Antigravity)
│   ├── e2e/ (신규, Codex)
│   └── __init__.py
├── storage/
│   ├── raw_documents/
│   ├── processed/
│   ├── vector_store/
│   └── metadata.db
├── requirements.txt
├── README.md (수정)
└── v2_Development_Plan.md (유지)
```

#### 검증 체크리스트
```
✅ app/ 폴더 구조 확인
✅ tests/ 폴더 구조 확인
✅ storage/ 폴더 구조 확인
✅ requirements.txt 존재 확인
✅ 불필요한 캐시 파일 제거 (__pycache__, .pytest_cache)
```

---

### Task 5: 개발 환경 구성 (Day 3-4)

#### conda 환경 설정
```bash
# v4 폴더에서
cd E:\ontology_edu\X_rag_std\src_agents\src_claud\v4

# 1. 새로운 conda 환경 생성 (선택)
# 또는 기존 v3 환경 재사용
conda activate E:\ontology_edu\X_rag_std\src_agents\src_claud\v3\env

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 테스트 실행 (v3 기존 테스트)
pytest tests/ -v
```

#### 환경변수 설정 (.env)
```bash
# v3와 동일한 .env 사용 (또는 복제)
cp ../v3/.env .env

# 필요시 수정 (Vector DB 경로 등)
```

#### 데이터베이스 준비
```bash
# v3 metadata.db를 v4에 복제 (선택)
cp ../v3/storage/metadata.db ./storage/metadata.db
```

---

### Task 6: 테스트 환경 검증 (Day 4-5)

#### 기존 테스트 실행
```bash
# v3의 모든 테스트가 v4에서도 통과하는지 확인
pytest tests/ -v --tb=short

# 예상 결과: 28개 테스트 모두 통과 (v3 기준)
```

#### 헬스 체크
```bash
# v4 서버 시작
set VECTOR_DB_ENGINE=local_json
uvicorn app.main:app --port 8000 --reload

# 다른 터미널에서 health check
curl -H "X-Tenant-ID: company_abc" http://localhost:8000/api/v1/health
```

#### 문제 해결
```
만약 테스트 실패 시:
1. requirements.txt 의존성 확인
2. Python 버전 확인 (3.11+)
3. v3와의 차이점 비교
4. 의존성 재설치: pip install -r requirements.txt --force-reinstall
```

---

## 👥 에이전트별 Week 1 추가 작업

### Claude 에이전트

#### 추가 작업
```
□ v4 API 설계 문서 작성
  - 신규 엔드포인트: /reranking, /query-expand, /batch-search 등
  - OpenAPI 3.0 스펙 초안
  
□ 코드 리뷰 준비
  - v3 API 코드 분석
  - Week 3 구현 계획 수립
```

#### 담당 파일
```
docs/API_v4_DESIGN.md (신규)
```

---

### Antigravity 에이전트

#### 추가 작업
```
□ 성능 측정 기준선 수립
  - v3 현재 응답시간 측정
  - v3 현재 처리량 측정
  - v4 목표 설정
  
□ 부하 테스트 환경 준비
  - locust 또는 k6 설치
  - 부하 테스트 시나리오 설계
```

#### 담당 파일
```
tests/load/baseline_v3.py (신규)
docs/PERFORMANCE_BASELINE.md (신규)
```

---

### Codex 에이전트

#### 추가 작업
```
□ E2E 테스트 계획 수립
  - 멀티테넌트 시나리오 설계
  - org_id 계층 테스트 케이스
  
□ CI/CD 파이프라인 초안
  - GitHub Actions 워크플로우 설계
  - 테스트 자동화 계획
```

#### 담당 파일
```
tests/e2e/test_plan.md (신규)
.github/workflows/ci.yml (초안)
```

---

## ✅ Week 1 체크리스트

### Day 1
- [ ] v4 폴더 생성 (v3 복제)
- [ ] 폴더 구조 검증
- [ ] README.md 업데이트 시작

### Day 2
- [ ] README.md 업데이트 완료
- [ ] CLAUDE.md 업데이트
- [ ] 폴더 구조 최종 확인

### Day 3
- [ ] 개발 환경 구성 (conda, pip)
- [ ] .env 파일 준비
- [ ] 데이터베이스 준비

### Day 4
- [ ] 기존 테스트 실행
- [ ] 모든 테스트 통과 확인
- [ ] 헬스 체크 통과

### Day 5
- [ ] 최종 검증
- [ ] 3에이전트 준비 완료 확인
- [ ] Week 2 준비 (에이전트별 지시서)

---

## 🎯 Week 1 완료 기준

```
✅ v4 폴더 생성 및 구조 확정
✅ 모든 기존 테스트 통과
✅ 개발 환경 정상 작동
✅ 3에이전트 병렬 개발 준비 완료
✅ Week 2 에이전트별 작업 지시서 준비
```

---

## 📚 참고 문서

- `PHASE4_v4_UPGRADE_PLAN.md` (전체 계획)
- `README.md` (개발 환경 설정)
- `CLAUDE.md` (프로젝트 컨텍스트)

---

## 🚀 다음 주 (Week 2)

```
Claude: API 설계 상세화 + Week 3 구현 준비
Antigravity: 성능 측정 기준선 수립 + 부하 테스트 환경
Codex: E2E 테스트 설계 + CI/CD 파이프라인 구축
```
