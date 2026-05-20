# Click Test Checklist (Antigravity-통합)

> **용도**: Antigravity 온톨로지 워크벤치의 핵심 기능을 사람 눈으로 직접 클릭하며 검증하는 체크리스트입니다.

---

## 1. 사전 준비

### 1.1 서버 구동
- [ ] **Backend**
cd E:\ontology_edu\Antigravity-통합\backend
conda activate anti_be
uvicorn app.main:app --reload --port 8000

- [ ] **Frontend**
cd E:\ontology_edu\Antigravity-통합\frontend
conda activate anti_fe
npm run dev

### 1.2 헬스체크 확인
- [ ] http://localhost:8000/api/health
접속 시 engine: "Antigravity-Flex" 확인

---

## 2. 온톨로지 그래프 탐색 (Graph Workspace)

- [ ] **초기 로딩**: 접속 시 중앙 캔버스에 고객(Alpha), 주문(O001), 제품(P001) 노드가 연결된 형태로 표시되는가?
- [ ] **노드 드래그**: 노드를 마우스로 드래그했을 때 부드럽게 이동하며 연결선(Edge)이 따라오는가?
- [ ] **노드 선택**: 노드를 클릭했을 때 우측 패널에 해당 객체의 상세 정보(Properties)가 즉시 로드되는가?

---

## 3. 다이나믹 정책 엔진 (Role-based Security)

- [ ] **Analyst 모드**: 왼쪽 사이드바에서 `Analyst` 선택 -> O001 주문 클릭 -> `risk_tier` 값이 `Low`로 정상 표시되는가?
- [ ] **Viewer 모드**: 사이드바에서 `Viewer` 선택 -> 다시 O001 클릭 -> `risk_tier` 값이 **●●●●● (Restricted)**로 마스킹되는가?
- [ ] **실시간 반영**: 역할을 바꿀 때마다 그래프 내 노드의 라벨이나 패널 정보가 즉시 업데이트되는가?

---

## 4. 지능형 RAG 분석 (Streaming AI)

- [ ] **질문 입력**: 우측 패널 하단에 "O001 승인 근거 요약해줘" 입력 후 'Analyze' 클릭.
- [ ] **스트리밍 응답**: 답변이 한 번에 나오지 않고 단어 단위로 실시간으로 타이핑되듯(Streaming) 출력되는가?
- [ ] **근거(Evidence) 노출**: 답변 완료 후 하단에 `주문 승인 가이드라인` 등의 근거 문서 카드가 표시되는가?

---

## 5. 유연한 스키마 확장 (Code-free Test) ⭐

- [ ] **스키마 수정**: `backend/schema.json` 파일에서 `Product` 객체의 `icon`을 `"Package"`에서 `"Gift"`로 변경하고 저장.
- [ ] **즉시 반영**: 프론트엔드 새로고침 시 제품 노드의 아이콘이 자동으로 변경되어 표시되는가? (코드 수정 없이 반영 확인)

---

## 6. 에러 핸들링

- [ ] **서버 다운**: 백엔드 종료 후 프론트엔드 조작 시 적절한 에러 메시지 또는 로딩 상태가 유지되는가?
- [ ] **잘못된 ID**: API를 통해 존재하지 않는 객체 요청 시 404 응답 및 UI 경고가 발생하는가?

---
> 모든 항목이 통과되면 **Antigravity-통합 버전**의 배포 준비가 완료된 것으로 간주합니다.
