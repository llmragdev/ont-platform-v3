# 스킬 시스템 (Skill System)

## 📌 개요

**스킬(Skill)** = 워크플로우 노드가 실행할 수 있는 재사용 가능한 작업/도구의 단위

- 내장 스킬 (Built-in): 웹 검색, 이메일 발송, 데이터베이스 조회 등
- 커스텀 스킬 (Custom): 프로젝트별로 정의한 Python 코드 스킬
- MCP 스킬 (Integration): 외부 MCP 서버를 통한 통합 (고객사/공장 댓글 등록)

---

## 📚 문서 구조

### 1. **SKILL_SYSTEM_DESIGN.md** (개념 설계)
- 스킬/액션/온톨로지 구분
- 3가지 사용 경로 (갤러리 설치, 빌더 직접, 실행 중)
- 데이터 모델 정의
- 저장 구조

**대상:** 설계 리뷰, 아키텍처 이해

---

### 2. **06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md** (구현 가이드) ⭐ **필수**
- 8가지 Critical/High 이슈 및 해결책
- 변수 바인딩 엔진 ({{nodes.xxx.output.yyy}})
- MCP HTTP 호출 방식 (tool_endpoint vs jsonrpc_proxy)
- Windows 호환성, 타입 보존, Phase별 범위
- 최종 구현 체크리스트
- 권장 Built-in Skill 목록
- 백엔드/프론트엔드 구조

**대상:** 개발 팀 (구현 시작 전 필독)

---

### 3. **skills_catalog.json** (스킬 정의 샘플)
- Built-in Skill 5개 예시
- Custom Skill 1개 예시 (Extract Keywords)
- 카테고리 정의

**대상:** 스킬 정의 참고, JSON 구조 확인

---

### 4. **archive/** (과정 기록)
- `01_Codex_스킬_시스템_검토보고서.md` - 초기 검토
- `02_antigravity_skill_design_review.md` - 기술 검토
- `03_SKILL_IMPLEMENTATION_SPEC.md` - 초기 구현 명세
- `04_antigravity_spec_review.md` - 기술 이슈 분석
- `05_Codex_SKILL_IMPLEMENTATION_SPEC_검토보고서.md` - v5 정합성 검토

**참고:** 06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md 에 통합됨

---

## 🚀 구현 시작하기

### Step 1: 문서 읽기
1. **이 README.md** (현재 파일)
2. **06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md** ⭐ 필수
3. **SKILL_SYSTEM_DESIGN.md** (개념 이해)

### Step 2: 구현 체크리스트 확인
- 07_IMPLEMENTATION_CHECKLIST.md 참고

### Step 3: 백엔드/프론트엔드 작업
06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md의 다음 섹션 참고:
- "최종 구현 체크리스트" (A/B/C/D)
- "권장 백엔드 구조"
- "권장 프론트엔드 구조"

---

## 🎯 Phase별 범위

| Phase | 포함 | 제외 |
|-------|------|------|
| **Phase 1** | Built-in/HTTP/MCP_HTTP 스킬, 변수 바인딩, 갤러리 UI | Custom Code 실행, MCP stdio, Docker |
| **Phase 2** | Custom Skill 저장/편집 | Custom Code 실행 |
| **Phase 3** | Custom Code 실행 (Docker 샌드박스) | - |

---

## 📋 주요 개념

### 스킬 vs 액션 vs 온톨로지

```
워크플로우 노드
  ↓ (실행)
스킬 (Skill)
  ↓ (결과)
액션 (Action) - 사용자 승인 가능
  ↓ (저장)
온톨로지 (Ontology) - 업무 객체/관계
```

### 변수 바인딩 표현식

```
{{nodes.n-asset-map.output.equipmentName}}
 ↑     ↑              ↑      ↑
 |     노드 ID         출력   필드명
 표현식 시작
```

- **단일 표현식:** `{{nodes.xxx.output.field}}` → 원본 타입 유지 (배열, 객체, 숫자)
- **복합 보간:** `"Equipment: {{nodes.xxx}}"` → 문자열로 변환

### MCP HTTP 호출 방식

| 방식 | 현재 v5 | 엔드포인트 | Phase |
|------|--------|----------|-------|
| **tool_endpoint** | ✅ | `/mcp/tools/comment.create` | Phase 1 |
| **jsonrpc_proxy** | - | `/mcp` + JSON-RPC wrapper | Phase 2+ |

---

## 💾 저장 위치

```
시스템 기본 스킬:
  ont_platform/v5/backend/app/config/skills/builtin_skills.json

프로젝트별 커스텀 스킬:
  ont_platform/storage/{company_id}/{project_id}/skills/custom_skills.json

⚠️ 반드시 get_project_root() helper 사용!
```

---

## ❓ FAQ

**Q: Phase 1에서 Custom Code를 실행할 수 있나?**
A: 아니오. Phase 1에서는 저장만 가능합니다. 실행은 Phase 3에서 Docker 샌드박스로 지원합니다.

**Q: 표현식에서 배열 타입이 문자열로 변환되는데?**
A: `"{{nodes.xxx.output.array}}"` 형태만 사용하세요. 복합 보간 (문자열 중간에 포함)이면 문자열로 변환됩니다.

**Q: 현재 mock MCP (s2_factory_mcp) 와 호환되나?**
A: 네. `callStyle: "tool_endpoint"`를 사용하면 현재 `/mcp/tools/{tool}` 방식과 호환됩니다. (06 문서 참고)

**Q: Windows 환경에서 작동하나?**
A: 네. 06 문서의 multiprocessing 방식으로 Windows/Linux 모두 지원합니다.

---

## 📞 다음 단계

1. **06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md 정독** (필수)
2. **07_IMPLEMENTATION_CHECKLIST.md 확인** (체계적 진행)
3. **백엔드 작업 시작** (`backend/app/services/skill_*.py`)
4. **프론트엔드 작업 시작** (`frontend/src/components/SkillGallery.tsx`)

---

**최종 확인:**
- ✅ 개념 이해: SKILL_SYSTEM_DESIGN.md
- ✅ 구현 가이드: 06_SKILL_SPEC_FINAL_CONSOLIDATED_REPORT.md
- ✅ 샘플 코드: skills_catalog.json

**준비 완료! 구현을 시작하세요.** 🚀

