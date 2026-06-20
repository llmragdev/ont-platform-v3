# 스킬 시스템 설계 문서

## 📋 개요

**스킬(Skill)** = 워크플로우에서 실행 가능한 작업/도구의 단위

### 스킬의 3가지 출처

```
┌─────────────────────────────────────────────────────┐
│ 워크플로우 빌더                                      │
├─────────────────────────────────────────────────────┤
│ ├─ Built-in Skills (갤러리에서 설치)               │
│ ├─ Custom Skills (저장된 커스텀 스킬 설치)          │
│ └─ Ad-hoc Code (빌더/실행에서 직접 작성)           │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ 아키텍처

### 스킬 화면 (Skill Marketplace)

```
┌──────────────────────────────────────────────────────────┐
│ 스킬 갤러리                                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ [검색] [카테고리 필터] [정렬]                            │
│                                                          │
│ ┌──────────────────┐  ┌──────────────────┐             │
│ │ Built-in: Web    │  │ Built-in: Email  │             │
│ │ Search           │  │ Send             │             │
│ │ ━━━━━━━━━━━━━━━ │  │ ━━━━━━━━━━━━━━━ │             │
│ │ Input: {query}   │  │ Input: {to, msg} │             │
│ │ Output: {result} │  │ Output: {status} │             │
│ │ [설치]           │  │ [설치]           │             │
│ └──────────────────┘  └──────────────────┘             │
│                                                          │
│ ┌──────────────────┐  ┌──────────────────┐             │
│ │ Custom: Extract  │  │ Custom: Transform│             │
│ │ Keywords         │  │ JSON             │             │
│ │ ━━━━━━━━━━━━━━━ │  │ ━━━━━━━━━━━━━━━ │             │
│ │ (저장됨)         │  │ (저장됨)         │             │
│ │ [편집] [설치]    │  │ [편집] [설치]    │             │
│ └──────────────────┘  └──────────────────┘             │
│                                                          │
│ [+ Create Custom Skill]                                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 커스텀 스킬 생성 모달

```
┌────────────────────────────────────────┐
│ Create Custom Skill                    │
├────────────────────────────────────────┤
│ Skill Name:                            │
│ [Extract Keywords________________]     │
│                                        │
│ Description:                           │
│ [텍스트에서 키워드 추출__________]     │
│                                        │
│ Category: [Select v]                   │
│                                        │
│ Input Schema (JSON):                   │
│ {                                      │
│   "text": {"type": "string"}           │
│ }                                      │
│                                        │
│ Output Schema (JSON):                  │
│ {                                      │
│   "keywords": {"type": "array"}        │
│ }                                      │
│                                        │
│ Python Code:                           │
│ ┌────────────────────────────────┐    │
│ │ def execute(input):            │    │
│ │   text = input['text']         │    │
│ │   ...                          │    │
│ │   return {'keywords': [...]}   │    │
│ └────────────────────────────────┘    │
│                                        │
│ [Cancel]  [Save]                       │
└────────────────────────────────────────┘
```

---

## 📊 데이터 모델

### Skill 인터페이스

```typescript
interface Skill {
  // 기본 정보
  id: string;                           // 'web-search', 'custom-extract-keywords'
  name: string;                         // 'Web Search', 'Extract Keywords'
  description: string;                  // 사용자 설명
  category: string;                     // 'search', 'text', 'data', 'notification'
  version: string;                      // '1.0'
  author: string;                       // 'Built-in' 또는 사용자명

  // 스키마
  inputSchema: Record<string, any>;     // JSON Schema
  outputSchema: Record<string, any>;    // JSON Schema

  // 구현 방식
  implementation: {
    type: 'builtin' | 'custom' | 'http' | 'mcp';
    code?: string;                      // Python 코드 (custom)
    endpoint?: string;                  // HTTP 엔드포인트 (http)
  };

  // 메타데이터
  createdAt?: string;
  updatedAt?: string;
  downloads?: number;
  rating?: number;
  tags?: string[];
}
```

### 노드에 스킬 저장

```typescript
interface WorkflowNodeData {
  label?: string;
  prompt?: string;
  skillId?: string;                     // 연결된 스킬 ID
  skillConfig?: {
    inputMapping?: Record<string, string>;  // 입력 매핑
    outputMapping?: Record<string, string>; // 출력 매핑
  };
}
```

---

## 🎯 사용 경로 (3가지)

### 경로 1️⃣: 스킬 화면에서 생성 및 설치

**흐름:**
```
스킬 갤러리
  ↓
[+ Create Custom Skill]
  ↓
폼 작성 (이름, 스키마, Python 코드)
  ↓
[Save]
  ↓
skills_catalog.json에 저장
  ↓
[설치] 클릭
  ↓
워크플로우에 노드 추가 (skillId 포함)
```

**특징:**
- ✅ 재사용 가능
- ✅ 저장됨
- ✅ 이후 워크플로우에서 빠르게 추가 가능

### 경로 2️⃣: 빌더에서 직접 코드 작성

**흐름:**
```
노드 추가 (Custom Code)
  ↓
properties 탭에서 Prompt 필드에 Python 코드 입력
  ↓
실행 시 코드 실행
```

**특징:**
- ✅ 빠른 프로토타이핑
- ❌ 재사용 불가
- ❌ 저장 안 됨

### 경로 3️⃣: 실행 중에 직접 코드 작성

**흐름:**
```
워크플로우 실행 중
  ↓
"Custom Code" 노드 실행 시 입력 요청
  ↓
코드 입력
  ↓
실행
```

**특징:**
- ✅ 즉석 수정 가능
- ❌ 재사용 불가
- ❌ 저장 안 됨

---

## 💾 스킬 저장소 구조

### 파일 구성

```
design/스킬/
├─ SKILL_SYSTEM_DESIGN.md           (이 문서)
├─ skills_catalog.json              (스킬 데이터)
└─ 01_스킬_카테고리_정의.md          (카테고리 가이드)
```

### skills_catalog.json 구조

```json
{
  "version": "1.0",
  "lastUpdated": "2026-06-14",
  "builtinSkills": [
    {
      "id": "web-search",
      "name": "Web Search",
      "type": "builtin",
      ...
    }
  ],
  "customSkills": [
    {
      "id": "custom-extract-keywords",
      "name": "Extract Keywords",
      "type": "custom",
      ...
    }
  ]
}
```

---

## 🔄 구현 흐름

### Phase 1: MVP (이번 주)

- [ ] 스킬 화면 UI 구성 (갤러리)
- [ ] 스킬 정의 파일 (skills_catalog.json)
- [ ] "설치" 기능 (노드 추가)
- [ ] Built-in Skills 5개 등록

### Phase 2: 커스텀 스킬 생성 (다음 주)

- [ ] "Create Custom Skill" 모달
- [ ] 커스텀 스킬 저장 (DB/파일)
- [ ] 커스텀 스킬 편집/삭제

### Phase 3: 실행 환경 (2주 후)

- [ ] Custom Code 노드 추가
- [ ] Python 코드 실행 (샌드박스)
- [ ] 의존성 관리

---

## 🎨 UI 탭 배치

### WorkflowGraph 우측 사이드바

```
[실행현황] [선택항목] [입출력] [온톨로지] [스킬갤러리] [이력]
```

**스킬갤러리 탭:**
- 검색 박스
- Built-in Skills (카드)
- Custom Skills (카드)
- "+ Create Custom Skill" 버튼

---

## 📝 노드 → 스킬 매핑

### 설치 후 노드 구조

```typescript
{
  id: "n-abc123",
  type: "skill",
  data: {
    label: "Web Search",
    skillId: "web-search",
    skillConfig: {
      inputMapping: {
        "query": "request_text"  // 입력 필드 매핑
      }
    }
  }
}
```

---

## 🔐 보안 고려사항

### Phase 1 (MVP): 제한사항
- 스킬 코드 검증 없음
- 샌드박싱 없음
- 신뢰할 수 있는 사용자만 사용

### Phase 3 (향후)
- 코드 검증 프로세스
- Docker 샌드박싱
- 권한 관리

---

## 📌 주요 결정사항

| 항목 | 결정 |
|------|------|
| 마켓플레이스 공유 | ❌ 없음 (이 프로젝트에만) |
| 스킬 저장소 | JSON 파일 (향후 DB) |
| 커스텀 스킬 언어 | Python (향후 JS 추가) |
| 빌더/실행 모드 | 3가지 경로 모두 지원 |
| 재사용성 | 스킬 화면에서만 가능 |

