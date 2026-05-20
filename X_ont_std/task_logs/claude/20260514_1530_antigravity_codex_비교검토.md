# 작업 기록: src_antigravity v1 vs src_codex 비교 검토

## 작업 개요
- **작업일시**: 2026-05-14
- **요청자**: 사용자
- **작업 내용**: `src_antigravity/v1`과 `src_codex`의 코드 비교 분석, v2 요건(`v2_Development_Plan.md`) 기준 달성도 평가
- **산출물**: `X_rag_std/src_agents/클로드코드 검토.md`

## 주요 발견 사항

### v2 플랜 달성도
- ✅ Plan 2 (Repository 패턴): 완료
- ✅ Plan 3 (라우팅 우선순위): 완료
- ⚠️ Plan 1 (파이프라인): 부분 완료 — PDF, 고급 청킹 미지원
- ❌ Plan 4 (pytest): 미구현
- ❌ core/config.py, api/ 계층: 미구현

### Codex 대비 핵심 Gap
1. 설정 관리 없음 (하드코딩)
2. pytest 자동 테스트 없음
3. PDF 파싱 및 다중 인코딩 미지원
4. api/ 계층 미분리
5. 커스텀 에러 처리 없음

## 참조 파일
- `src_agents/src_antigravity/v2_Development_Plan.md`
- `src_agents/src_antigravity/v1/` (5개 파일)
- `src_agents/src_codex/app/` (17개 파일)
