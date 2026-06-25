# PHASE 3 WEEK 4 에이전트 지시 배포

**배포일**: 2026-05-25  
**시작일**: 2026-06-17  
**마감일**: 2026-06-21 (5일)  
**상태**: 🟢 READY FOR DISPATCH

---

## 📢 전체 WEEK 4 개요

### 목표
Phase 3의 마지막 주: 
- **Claude**: Backend 통합 테스트 완성
- **Codex**: Frontend UI 완성  
- **Antigravity**: 성능 검증 완료

### 일정
| 날짜 | 마일스톤 | 상태 |
|------|---------|------|
| 2026-06-17 (화) | Week 4 시작 | 📌 |
| 2026-06-18 (수) | Task 1 체크포인트 | - |
| 2026-06-19 (목) | Task 2 체크포인트 | - |
| 2026-06-20 (금) | Task 3 체크포인트 | - |
| 2026-06-21 (토) | Week 4 완료 | - |

---

## 🎯 에이전트별 임무

### ① Claude (Backend Agent)
**목표**: Changelog & WriteBack API + E2E 테스트  
**시간**: 8~10 시간  
**지시**: [PHASE3_WEEK4_Claude_Instructions_20260525.md](../../week_instructions/PHASE3_WEEK4_Claude_Instructions_20260525.md)

**Task 분해**:
1. Changelog 조회 API (3~4h) → 5개 테스트
2. WriteBack 상태 API (2~3h) → 4개 테스트  
3. Backend E2E 테스트 (3~4h) → 10개+ 테스트

**완료 기준**: 모든 API 정상 작동 + E2E 85%+ 통과

---

### ② Codex (Frontend Agent)
**목표**: ActionButton + Audit 대시보드  
**시간**: 10~12 시간  
**지시**: [PHASE3_WEEK4_Codex_Instructions_20260525.md](../../week_instructions/PHASE3_WEEK4_Codex_Instructions_20260525.md)

**Task 분해**:
1. ActionButton 컴포넌트 (4~5h) → 5개 E2E 테스트
2. Audit 대시보드 (4~5h) → 5개 E2E 테스트
3. QueryResult 통합 (2~3h) → 3개 E2E 테스트

**완료 기준**: 모든 E2E 테스트 통과 (13/13)

---

### ③ Antigravity (Performance Agent)
**목표**: 성능 벤치마크 + 부하 테스트 + 리포트  
**시간**: 10~12 시간  
**지시**: [PHASE3_WEEK4_Antigravity_Instructions_20260525.md](../../week_instructions/PHASE3_WEEK4_Antigravity_Instructions_20260525.md)

**Task 분해**:
1. API 성능 벤치마크 (3~4h)
2. 부하 테스트 (4~5h)
3. 최종 성능 리포트 (2~3h)

**완료 기준**: 모든 성능 기준 충족 + 최적화 권고 제시

---

## 📋 지시 문서 위치

모든 지시서는 `week_instructions/` 폴더에 있습니다:

```
week_instructions/
├── PHASE3_WEEK4_Claude_Instructions_20260525.md
├── PHASE3_WEEK4_Codex_Instructions_20260525.md
└── PHASE3_WEEK4_Antigravity_Instructions_20260525.md
```

---

## ✅ 배포 체크리스트

- ✅ PHASE3_WEEK3 완료 및 커밋됨
- ✅ 모든 참조 링크 정합성 확보
- ✅ 에이전트별 지시문 준비 완료
- ✅ Git 상태 클린 (커밋 완료)
- ✅ 각 에이전트별 Task 분명히 정의됨
- ✅ 완료 기준 명확함

---

## 🚀 다음 단계

### Week 4 시작 시 (2026-06-17)

**Claude**:
```bash
# 지시 확인
cat week_instructions/PHASE3_WEEK4_Claude_Instructions_20260525.md

# Task 1 시작: Changelog API
# → test_changelog_api.py 작성
# → 5개 테스트 통과 확인
```

**Codex**:
```bash
# 지시 확인
cat week_instructions/PHASE3_WEEK4_Codex_Instructions_20260525.md

# Task 1 시작: ActionButton
# → ActionButton.tsx 구현
# → 5개 E2E 테스트 실행
```

**Antigravity**:
```bash
# 지시 확인
cat week_instructions/PHASE3_WEEK4_Antigravity_Instructions_20260525.md

# Task 1 시작: 벤치마크
# → locustfile.py 준비
# → 성능 측정 시작
```

---

## 📊 진행 상황 추적

### 체크포인트 (매일)
- Task 1 진행률: ____%
- Task 2 진행률: ____%
- Task 3 진행률: ____%

### 최종 점검 (2026-06-21)
- ✅ Claude: 모든 API + 테스트 통과
- ✅ Codex: 모든 컴포넌트 + E2E 테스트 통과
- ✅ Antigravity: 성능 리포트 제출

---

## 💬 커뮤니케이션

### 문제 발생 시
1. 해당 지시 문서 다시 확인
2. 작업 로그에 기록 (`task_logs/claude/`)
3. 필요시 주요 이슈를 별도 문서로 작성

### 완료 후
1. 작업 완료 로그 작성
2. 모든 테스트/검증 결과 첨부
3. 다음 단계 준비 상황 기록

---

## 📁 작업 결과 저장

각 에이전트별 최종 결과는 다음 위치에 저장:

**Claude**:
- API 구현: `ont_platform/v3/src/backend/app/`
- 테스트: `ont_platform/v3/src/backend/tests/`
- 완료 로그: `task_logs/claude/PHASE3_WEEK4_Claude_*_Complete.md`

**Codex**:
- 컴포넌트: `ont_platform/v3/src/frontend/src/components/`
- 페이지: `ont_platform/v3/src/frontend/src/pages/`
- 완료 로그: `task_logs/claude/PHASE3_WEEK4_Codex_*_Complete.md`

**Antigravity**:
- 테스트 스크립트: `ont_platform/v3/performance_tests/`
- 리포트: `ont_platform/v3/PHASE3_PERFORMANCE_REPORT.md`
- 완료 로그: `task_logs/claude/PHASE3_WEEK4_Antigravity_*_Complete.md`

---

**상태**: 🟢 READY FOR DISPATCH  
**배포자**: Claude Code  
**배포일**: 2026-05-25
