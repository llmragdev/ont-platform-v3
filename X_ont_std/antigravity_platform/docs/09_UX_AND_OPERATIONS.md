# 09. UX 및 운영 가이드 (UX & Operations)

## 1. UX/UI 디자인 원칙 (Premium Standard)

Antigravity는 사용자에게 단순한 도구를 넘어 **"신뢰할 수 있는 지능형 동반자"**의 경험을 제공합니다.

### 1.1 시각적 아이덴티티
- **Aesthetic**: 다크 모드 기반의 **Glassmorphism** (반투명 레이어, Backdrop Blur).
- **Typography**: Inter 또는 Outfit 폰트 사용, 가독성 위주의 레이아웃.
- **Interactions**: Framer Motion을 활용한 부드러운 상태 전환 (Slide, Fade).

### 1.2 핵심 UI 컴포넌트 표준
- **Tenant/Project Selector**: 헤더 우측 상단에 고정, 현재 소속을 항상 인지할 수 있도록 배지(Badge) 형태 적용.
- **Query Plan Viewer**: 질의 진행 상황을 '생각하는 과정'으로 시각화. 각 단계 완료 시 체크마크 애니메이션.
- **Evidence Panel**: 답변의 근거를 카드 형태로 제시. 클릭 시 원본 문서의 해당 페이지로 부드럽게 스크롤.
- **Permission Gate**: 권한이 없는 기능은 단순히 숨기지 않고, '잠금 아이콘'과 함께 툴팁으로 필요 권한을 안내.

---

## 2. 하이브리드 추론 시각화 (Traceability)

사용자가 AI의 답변을 검증할 수 있도록 **추론 경로(Reasoning Trace)**를 투명하게 보여줍니다.

- **Trace Graph**: 온톨로지 엔진이 탐색한 노드와 관계를 미니 그래프 형태로 출력.
- **Source Link**: 답변 내의 수치나 고유 명사에 마우스를 올리면 관련 데이터(Entity 상세 또는 문서 청크) 팝업 노출.

---

## 3. 운영 지표 및 KPI (Operations)

시스템의 건강 상태를 정량적으로 측정합니다.

| 지표명 | 측정 방법 | 목표 |
| :--- | :--- | :--- |
| **TTFT (First Token)** | LLM 응답 시작 시간 | 800ms 이내 |
| **Plan Accuracy** | 질문 의도와 실행 계획의 일치율 | 98% 이상 |
| **Token Cost / Query** | 요청당 평균 비용 추적 | $0.05 이내 (최적화) |
| **Audit Coverage** | 전체 쓰기 행위 중 로그 기록 비율 | 100% |

---

## 4. 에러 메시지 및 톤앤매너 (Error UX)

- **Tone**: 전문적이고 친절하며, 해결책을 명확히 제시함.
- **Error Display**:
    - `403 Forbidden`: "현재 계정은 이 작업을 수행할 권한이 없습니다. 관리자에게 'ontology:edit' 권한 승인을 요청하세요."
    - `Hallucination Risk`: "검색된 근거가 부족하여 정확한 답변을 드리기 어렵습니다. 대신 관련된 다음 문서들을 확인해보시겠습니까?"
