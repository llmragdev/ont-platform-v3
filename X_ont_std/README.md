# ont_platform v3 — 온톨로지 기반 통합 의사결정 시스템

> **팔란티어(Foundry) 경량화 특화 버전**  
> 조선·제조·건설 산업 타겟 | 데이터 → 의미 → 의사결정 → 액션 → 감사 추적

---

## 🎯 프로젝트 개요

### 핵심 가치
- **온톨로지 기반 의미 추출**: 데이터를 비즈니스 의미(개념·관계)로 변환
- **AI 기반 의사결정**: RAG + LLM으로 근거 있는 의사결정 지원
- **액션 자동화 & 감사 추적**: 의사결정에서 실행까지 추적 가능
- **경량화 & 확장성**: 팔란티어 대비 15~20% 리소스로 운영

### 대상 사용자
- 제조/조선/건설 기업의 경영진 및 실무진
- 데이터 기반 의사결정이 필요한 조직

---

## 📊 프로젝트 상태

**[→ STATUS.md에서 최신 상태 확인](./STATUS.md)**

**요약**: 조회 기능 완성 (~42%), 실행·액션 미완성  
**현재 집중**: Phase 2 마무리 — 통합 테스트 1/25 → 20/25 달성

---

## 🗂️ 폴더 구조

```
E:\ontology_edu\X_ont_std\
│
├── 📋 CLAUDE.md                  ← 프로젝트 컨텍스트 & 개발 가이드
├── 📋 README.md                  ← 이 파일
├── 📋 LOGGING_POLICY.md          ← 작업 기록 정책
│
├── 📂 requirements\              ← 요건 문서
│   ├── 분석\                     ← 기능 분석 (10개 문서)
│   ├── 추적도\                   ← 요건 추적 매트릭스
│   ├── 교육자료\
│   ├── 평가\
│   └── README.md
│
├── 📂 task_logs\                 ← 작업 기록 (모든 세션)
│   ├── claude\
│   │   ├── 20260519_1430_PROJECT_REORGANIZATION.md
│   │   ├── 20260519_1445_CLEANUP_SUMMARY.md
│   │   └── (매 작업마다 기록)
│   └── LOGGING_POLICY.md         ← 기록 규칙
│
├── 📂 cross-source-comparison\   ← 플랫폼 비교 분석
│   ├── 01_Antigravity_통합 평가.md
│   ├── 01_Claude_플랫폼통합평가.md
│   ├── 01_Codex_통합 평가.md
│   └── README.md
│
├── 📂 references\                ← 참고 자료 & 프로토타입
│   ├── old\                      ← 초기 검증 & 프로토타입 (아카이브)
│   │   ├── claud에 대한 총평\     ← 2026-05-12~14 검증
│   │   ├── src_codex\
│   │   ├── src_nextjs\
│   │   └── src_sql\
│   ├── app.js, index.html, style.css  ← 웹 예제
│   └── README.md
│
└── 📂 ont_platform\              ← 프로젝트 본체
    ├── v1_legacy\                ← v1 원본 (참조용)
    ├── v2\                       ← 구조화 버전
    └── v3\                       ← 🔴 현재 개발 버전
        ├── src\
        │   ├── backend\          ← FastAPI (포트 8001)
        │   │   ├── models\       ← 데이터 모델
        │   │   ├── routes\       ← API 엔드포인트
        │   │   ├── services\     ← 비즈니스 로직
        │   │   └── tests\
        │   ├── frontend\         ← Next.js (포트 3001)
        │   │   ├── components\
        │   │   ├── pages\
        │   │   └── styles\
        │   └── tests\
        │       └── integration\  ← 통합 테스트 (목표: 20/25)
        ├── ARCHITECTURE.md       ← 최종 아키텍처
        └── ROADMAP.md            ← 기술 로드맵
```

---

## 🚀 빠른 시작

### 1. 개발 환경 설정
```bash
# 백엔드 환경 활성화
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend

# 프론트엔드 환경 활성화  
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend
```

### 2. 서버 실행
```bash
# 터미널 1: 백엔드
uvicorn main:app --reload --port 8001

# 터미널 2: 프론트엔드
npm run dev  # http://localhost:3001
```

### 3. 테스트 실행
```bash
# 단위 테스트
pytest tests/unit/ -v

# 통합 테스트
pytest tests/integration/ -v --tb=short
```

---

## 📖 문서 가이드

| 문서 | 용도 | 대상 |
|------|------|------|
| [CLAUDE.md](./CLAUDE.md) | 프로젝트 컨텍스트 & 개발 규칙 | 모든 개발자 (필수) |
| [requirements/](./requirements/README.md) | 기능 요건 & 아키텍처 | 설계·기획팀 |
| [cross-source-comparison/](./cross-source-comparison/README.md) | 기술 선택 근거 | 아키텍처팀 |
| [ont_platform/v3/ARCHITECTURE.md](./ont_platform/v3/ARCHITECTURE.md) | 최종 구현 아키텍처 | 개발팀 |
| [ont_platform/v3/ROADMAP.md](./ont_platform/v3/ROADMAP.md) | 개발 로드맵 | PM·개발팀 |
| [task_logs/LOGGING_POLICY.md](./task_logs/LOGGING_POLICY.md) | 작업 기록 정책 | 모든 개발자 |

---

## 🔴 현재 집중 과제

### Phase 2: 통합 테스트 달성 (마감: 2026-05-19)
```
목표: 1/25 (4%) → 20/25 (80%)
```

**실패 케이스 분석 및 고속 수정**:
- 온톨로지 데이터 매칭 최적화
- 벡터 검색 성능 개선
- 엣지 케이스 처리

### Phase 3: 비즈니스 액션 구현 (2026-05-20 ~ 2026-05-31)
```
1. ActionType 추가 (ApproveProject, RejectProject, ChangeStatus)
2. 상태 전이 규칙 (10개 이상)
3. RBAC 권한 모델 구현
```

---

## 📌 개발 규칙

### 코드 작성
- 주석 최소화 (의도가 명백할 것)
- 기능 추가 시 테스트 동시 작성
- git commit: 간결한 메시지, 명확한 의도

### 문서화
- 매 작업마다 `task_logs/claude/YYYYMMDD_HHMM_작업명.md` 기록
- CLAUDE.md 업데이트 (상태 변화 시)
- 코드 변경 + 문서 동시 커밋

### 테스트
- 단위 테스트: 함수/메서드 단위
- 통합 테스트: 시나리오 기반
- 테스트 커버리지 유지

---

## 🔗 외부 링크

| 자료 | 위치 |
|------|------|
| **팔란티어 분석** | E 드라이브 (확장 제안, 회의록) |
| **RAG 표준** | 별도 워크스페이스 (X_rag_std) |

---

## 👥 팀 정보

**프로젝트 리드**: AX 전략팀  
**개발 기간**: 2026-05-12 ~ (진행 중)  
**메인 브랜치**: `master`

---

## 📚 최근 활동

- **2026-05-19**: 전체 문서화 정리 완료 ✅
  - CLAUDE.md 업데이트
  - task_logs 기록 정책 수립
  - 폴더별 README 작성
  - 구조 정리 기록 아카이빙

- **2026-05-16**: 플랫폼 비교 평가 완료
  - Antigravity, Claude, Codex 종합 평가

- **2026-05-15**: 요건 추적 대량 업데이트

---

## ❓ FAQ

**Q. 어디서부터 시작할까?**  
A. [CLAUDE.md](./CLAUDE.md)를 먼저 읽고, 현재 상태 확인 후 진행.

**Q. 기능 요건은 어디에?**  
A. [requirements/분석/](./requirements/README.md) 폴더 참고.

**Q. 과거 검증 자료는?**  
A. [references/old/](./references/old/) 아카이브 폴더 참고.

**Q. 작업을 어떻게 기록할까?**  
A. [task_logs/LOGGING_POLICY.md](./task_logs/LOGGING_POLICY.md) 참고.

---

**마지막 업데이트**: 2026-05-19  
**상태**: 진행 중 (Phase 2 마무리 단계)

