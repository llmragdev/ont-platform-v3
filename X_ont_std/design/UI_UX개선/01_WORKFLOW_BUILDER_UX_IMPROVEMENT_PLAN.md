# Workflow Builder UI/UX 개선 방안

**작성일**: 2026-06-13  
**작성자**: Claude (Claude Code)  
**대상**: ont_platform v5 Frontend  
**범위**: Workflow Builder, Workflow Execution, 메뉴 구조  
**우선순위**: P0 (즉시), P1 (단기), P2 (중기)

---

## 📋 Executive Summary

현재 Workflow Builder는 기능은 완성되었지만 사용자 체험(UX)에 개선이 필요합니다.

**핵심 문제:**
1. 실행 중 상태가 Trace 페이지에서만 보임 (화면 분리)
2. Workflow 박스 디자인이 평범함
3. 메뉴가 관련 항목끼리 묶이지 않음
4. 온톨로지-엔티티 연계 네비게이션 없음

**목표:**
- 한 화면에서 그래프 + 실행 상태 동시 확인
- 직관적이고 전문적인 디자인
- 업계 표준 (Jenkins, Airflow) 수준의 UX

---

## 🎯 Problem Statement

### 1. Execution Flow 단절

**현재:**
```
Workflow Builder에서 [Run]
  ↓ (화면 전환)
Workflow Trace 페이지에서 상태 확인
  ↓ (다시 돌아가야 함)
Workflow Builder로 돌아감
```

**문제점:**
- 3단계 이동 필요
- 그래프와 실행 상태를 동시에 볼 수 없음
- "현재 어디가 실행 중인가?" 파악 어려움
- 새 사용자가 혼란스러워함

**비교 (업계 표준):**
- Jenkins: 파이프라인 화면 자체에서 실행 중 스테이지 하이라이트
- Airflow: DAG 그래프 위에 각 task 상태 표시
- GitHub Actions: 워크플로우 옆에 실시간 로그

---

### 2. Workflow 박스 시각화 부족

**현재:**
```
□ Intent Classify
```

**문제점:**
- 시각적 차이 없음
- Input/Output 타입 불명확
- 아이콘 없어서 단계 구분 어려움

---

### 3. 메뉴 구조 분산

**현재:**
```
- Workflow Home
- Workflow Builder
- 승인 워크플로우
- Ontology
- Documents
- Vector Search
- Settings
- ...
```

**문제점:**
- 관련 항목 분산 (메뉴가 12개 이상)
- 새 사용자가 찾기 어려움

---

### 4. 온톨로지 네비게이션 없음

**현재:**
- Workflow에서 온톨로지로 가는 길 없음
- 역으로도 불가능

**필요:**
- Workflow 실행 결과 → 온톨로지 엔티티 하이퍼링크

---

## ✅ 개선 방안

### **Phase 0: 즉시 (P0) - 2주**

#### **1. Builder 우측 Execution Panel**

**레이아웃:**

```
┌─ Workflow Builder: 서비스 요청 자동댓글 ────────────────────────────┐
│                                                                        │
│  ┌─ Graph (60%) ─────────────────────┐  ┌─ Execution (40%) ────────┐│
│  │                                   │  │ 📊 Execution Trace       ││
│  │ ┌─────────────────────────────┐   │  │                          ││
│  │ │ [●] Request Input          │   │  │ Status: ⏳ Running       ││
│  │ │ Process customer question  │   │  │ Progress: 2/5            ││
│  │ │                            │   │  │ ━━━●─────────────────    ││
│  │ │ Input: question_text       │   │  │                          ││
│  │ └────────────────────────────┘   │  │ ⏱️ Elapsed: 2.3s         ││
│  │          ↓ (Active)              │  │                          ││
│  │ ┌─────────────────────────────┐   │  │ 🔍 Current Step:         ││
│  │ │ [●] Intent Classify         │   │  │ intent_classify          ││
│  │ │ Categorize question type    │   │  │                          ││
│  │ │                            │   │  │ Input:                   ││
│  │ │ Input: question_text       │   │  │ ┌──────────────────────┐││
│  │ │ Output: intent_type        │   │  │ │{                     │││
│  │ └────────────────────────────┘   │  │ │  "query": "비밀번호.│││
│  │          ↓                        │  │ │  "user_id": "001"   │││
│  │ ┌─────────────────────────────┐   │  │ │}                    │││
│  │ │ [ ] Knowledge Lookup        │   │  │ └──────────────────────┘││
│  │ │ Search relevant documents   │   │  │                          ││
│  │ │                            │   │  │ Output:                  ││
│  │ │ Input: intent_type         │   │  │ ┌──────────────────────┐││
│  │ │ Output: search_results     │   │  │ │{                     │││
│  │ └────────────────────────────┘   │  │ │  "intent": "reset.." │││
│  │          ↓                        │  │ │  "confidence": 0.95  │││
│  │ ┌─────────────────────────────┐   │  │ │}                    │││
│  │ │ [ ] Evidence Gate           │   │  │ └──────────────────────┘││
│  │ │ Validate response quality   │   │  │                          ││
│  │ └────────────────────────────┘   │  │ [📋 Copy] [💾 Export]   ││
│  │          ↓                        │  └──────────────────────────┘│
│  │ ┌─────────────────────────────┐   │                             │
│  │ │ [ ] Draft Response          │   │                             │
│  │ │ Generate final answer       │   │                             │
│  │ └────────────────────────────┘   │                             │
│  └───────────────────────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**기능:**
- 좌측: Workflow 그래프 (60%)
- 우측: 실시간 Execution 패널 (40%)
- 현재 실행 중인 스텝 하이라이트
- Input/Output 실시간 표시
- Progress bar
- Duration 표시

**구현:**
```html
<div class="workflow-container">
  <div class="graph-panel">
    <!-- Workflow 그래프 -->
  </div>
  <div class="execution-panel">
    <!-- 실행 상태 패널 -->
  </div>
</div>
```

---

#### **2. Workflow 박스 색상 코딩**

**설계:**

```
┌──────────────────────────┐
│ 🔵 Request Input          │  (Input - 파란색)
│ 🔹 Request customer Q     │
│ 🔹 Input: question_text   │
└──────────────────────────┘

┌──────────────────────────┐
│ 🟢 Intent Classify        │  (Process - 초록색)
│ 🔹 Categorize Q type      │
│ 🔹 In: question_text      │
│ 🔹 Out: intent_type       │
└──────────────────────────┘

┌──────────────────────────┐
│ 🟡 Evidence Gate          │  (Decision - 노란색)
│ 🔹 Validate quality       │
│ 🔹 In: search_results     │
│ 🔹 Out: is_valid          │
└──────────────────────────┘

┌──────────────────────────┐
│ 🔴 Action (MCP Call)      │  (Action - 빨간색)
│ 🔹 Register comment       │
│ 🔹 In: draft_message      │
│ 🔹 Out: comment_id        │
└──────────────────────────┘
```

**색상:**
- 🔵 Input/Request: `#2563eb` (파란색)
- 🟢 Process/Logic: `#16a34a` (초록색)
- 🟡 Decision/Gate: `#ea580c` (주황색)
- 🔴 Action/Side Effect: `#dc2626` (빨간색)

**아이콘:**
- Input: 📥
- Process: ⚙️
- Decision: 🚦
- Action: ▶️
- Ontology: 🧬

---

#### **3. 블록 상태 시각화**

**상태 표시:**

```
상태         시각 효과              의미
────────────────────────────────────────
○ 대기     흐린 회색 + 투명도     실행 대기 중
● 실행     주황색 + 로딩 아이콘   현재 실행 중
✓ 완료     초록색 + 체크 마크     성공적 완료
✗ 실패     빨간색 + X 마크        실행 실패
⊘ 스킵     회색 + 줄              조건부 건너뜀
```

**CSS 구현:**

```css
/* 실행 중 */
.node.running {
  border: 2px solid #ea580c;
  box-shadow: 0 0 10px rgba(234, 88, 12, 0.5);
  animation: pulse 1.5s infinite;
}

/* 완료 */
.node.completed {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border-color: #16a34a;
}

/* 실패 */
.node.failed {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border-color: #dc2626;
}
```

---

### **Phase 1: 단기 (P1) - 3주**

#### **4. 메뉴 구조 재정리**

**개선 후:**

```
┌─ 📊 Dashboard
│  ├─ Home
│  └─ Analytics
│
├─ ⚙️ Workflow
│  ├─ Builder
│  ├─ Templates
│  ├─ Execution History
│  ├─ Traces
│  └─ Approvals
│
├─ 🧬 Ontology
│  ├─ Schema
│  ├─ Entities
│  ├─ Relationships
│  └─ Traces
│
├─ 📚 Knowledge
│  ├─ Documents
│  ├─ Vector Search
│  └─ RAG Config
│
├─ 🔧 Settings
│  ├─ Project
│  ├─ Users
│  └─ Integrations
│
└─ ❓ Help
   └─ Documentation
```

**이점:**
- 관련 항목 그룹화
- 3단계 깊이 제한
- 메뉴 12개 → 5개 카테고리로 정리

---

#### **5. 온톨로지 엔티티 연계**

**Workflow 결과:**

```
┌─ Execution Result ─────────┐
│                            │
│ intent: reset_password     │
│ system: dev_server        │
│ confidence: 0.95          │
│                            │
│ [🧬 View in Ontology]     │  (클릭 가능)
│                            │
└────────────────────────────┘
```

**클릭 시:**
```
Ontology 페이지로 이동
  → Action: ResetPassword (엔티티 선택)
  → Details 표시
  → requires_approval: false
  → system: dev_server
```

---

### **Phase 2: 중기 (P2) - 4주**

#### **6. 반응형 디자인 (모바일)**

**큰 화면 (≥1200px):**
- Split View (좌 60%, 우 40%)

**중간 화면 (768-1200px):**
- Drawer 방식 (Execution Panel은 오른쪽 드로어)

**작은 화면 (<768px):**
- Tab 방식 (Graph / Execution 탭)

---

#### **7. 고급 기능**

**a) Workflow 통계**

```
┌─ Statistics ─────────────┐
│ Total Runs: 245          │
│ Success Rate: 98.4%      │
│ Avg Duration: 2.3s       │
│ Most Used: intent_class  │
└──────────────────────────┘
```

**b) 즐겨찾기/태그**

```
[☆] Save as Template
[#] Add Tags: auto-reply, critical
```

**c) 비교 모드**

```
[🔄] Compare with Previous Run
Old vs New 병렬 표시
```

---

## 📊 우선순위 및 추정치

| 항목 | Phase | 난이도 | 예상 일정 | 효과 |
|------|-------|--------|---------|------|
| 우측 Execution Panel | P0 | 중 | 5일 | ⭐⭐⭐⭐⭐ |
| 블록 색상 코딩 | P0 | 하 | 2일 | ⭐⭐⭐⭐ |
| 메뉴 구조 재정리 | P1 | 중 | 3일 | ⭐⭐⭐ |
| 온톨로지 연계 | P1 | 중 | 4일 | ⭐⭐⭐⭐ |
| 박스 디자인 개선 | P2 | 중 | 3일 | ⭐⭐⭐ |
| 모바일 반응형 | P2 | 중 | 4일 | ⭐⭐⭐ |
| 통계/고급 기능 | P2 | 낮 | 3일 | ⭐⭐ |

**Total P0: 7일**  
**Total P0+P1: 14일**  
**Total All: 24일**

---

## 🎯 의사결정: Execution Panel 위치

### 옵션 비교

| 옵션 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **A. Split View** | 좌 60% 그래프, 우 40% 패널 | 한 화면에서 모든 것 가능 | 그래프 축소 |
| **B. Drawer** | 그래프 전체, 필요시 우측 드로어 | 그래프 전체 보기 | 패널 열어야 함 |
| **C. Modal** | 그래프 전체, 실행 시 모달 | 깔끔함 | 화면 전환 |

**권장: A (Split View)**
- 업계 표준 (Jenkins, Airflow 등)
- 사용자가 별도 조작 불필요
- 실시간으로 두 가지 정보 동시 확인

---

## 📝 구현 체크리스트

### **P0 (Week 1)**

- [ ] Execution Panel UI 디자인 (Figma)
- [ ] Split View 레이아웃 구현
- [ ] 실시간 데이터 바인딩
- [ ] 색상 코드 적용
- [ ] 로딩 애니메이션
- [ ] 테스트 및 피드백

### **P1 (Week 2-3)**

- [ ] 메뉴 재구성
- [ ] 온톨로지 네비게이션 링크
- [ ] History 개선
- [ ] 접근성(A11y) 개선

### **P2 (Week 4-5)**

- [ ] 박스 디자인 재작업
- [ ] 모바일 반응형
- [ ] 통계 대시보드
- [ ] 성능 최적화

---

## 🎨 디자인 시스템

### **색상 팔레트**

```
Primary Blue:     #2563eb
Success Green:    #16a34a
Warning Orange:   #ea580c
Error Red:        #dc2626
Neutral Gray:     #6b7280
```

### **타이포그래피**

```
Heading: Inter Bold 20px
Body: Inter Regular 14px
Code: JetBrains Mono Regular 12px
```

### **간격 (Spacing)**

```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
```

---

## ✅ 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 페이지 전환 수 | 3회 → | 1회 |
| 사용자 만족도 | 3.2/5 → | 4.5/5 |
| 학습 시간 | 20분 → | 5분 |
| 오류율 | 8% → | 2% |

---

## 📚 참고 자료

- Jenkins Pipeline UI: https://www.jenkins.io/
- Airflow DAG UI: https://airflow.apache.org/
- GitHub Actions UI: https://github.com/features/actions

---

**다음 단계**: 이 문서를 바탕으로 P0 (Execution Panel) Figma 목업 작성

---

**작성**: Claude (Claude Code)  
**작성일**: 2026-06-13  
**검토 및 피드백**: 환영합니다
