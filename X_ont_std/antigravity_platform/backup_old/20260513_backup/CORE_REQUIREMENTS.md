# Antigravity-통합: 엔터프라이즈 온톨로지 워크벤치

> **작성자**: Antigravity (AI Coding Assistant)
> **목표**: 팔란티어(Palantir) 스타일의 유연한 온톨로지 엔진과 고도화된 UI/UX를 갖춘 지능형 업무 플랫폼 구축

## 1. 핵심 사상
1.  **Code-free Ontology**: 모든 객체 타입과 관계 정의는 코드가 아닌 **설정(Meta-data)**에 의해 결정됩니다.
2.  **Relationship-first RAG**: 단순 검색을 넘어, 객체 간의 관계를 탐색(Traversal)하여 답변의 근거를 찾아내는 지식 그래프 기반 RAG.
3.  **Visual Interaction**: 테이블 중심의 UI에서 벗어나, 그래프 캔버스를 통해 데이터를 탐색하고 조작하는 프리미엄 UX.

---

## 2. 시스템 아키텍처

### Backend (FastAPI + Async)
- **Ontology Engine**: `schema.json`을 로드하여 동적으로 엔터티와 관계 모델을 생성하는 엔진.
- **Dynamic Policy Engine**: 온톨로지 속성과 사용자의 역할을 실시간으로 대조하는 RBAC/ABAC 통합 보안.
- **Async Streaming RAG**: LLM 답변을 스트리밍으로 제공하여 사용자 체감 속도 최적화.

### Frontend (Next.js 14 + Framer Motion)
- **Graph Workspace**: 노드와 링크를 시각적으로 조작하는 인터랙티브 캔버스 (React Flow 기반).
- **Glassmorphism UI**: 다크 모드를 기본으로 하는 세련된 프리미엄 디자인 시스템.
- **Unified Command Bar**: `Ctrl+K`를 통해 모든 객체, 메뉴, 액션을 빠르게 검색하고 실행.

---

## 3. 1단계 구현 목표 (MVP+)
1.  **Meta-data 로더**: JSON 설정 파일로부터 객체/관계 정의를 읽어오는 백엔드 구조 구축.
2.  **그래프 익스플로러**: 선택한 객체와 연결된 다른 객체들을 시각적으로 '확장'하며 탐색하는 기능.
3.  **지능형 컨텍스트 패널**: 객체를 클릭할 때마다 관련 문서, 이력, 가능한 액션을 실시간으로 요약하여 노출.

---

## 4. 폴더 구조
- `backend/`: FastAPI 앱, 온톨로지 엔진, RAG 로직
- `frontend/`: Next.js 앱, 그래프 컴포넌트, 디자인 시스템
- `docs/`: 상세 요건, 아키텍처 설계, API 명세
- `data/`: 온톨로지 스키마(`schema.json`) 및 초기 데이터

---
> 이 프로젝트는 `claud_통합`의 안정성을 바탕으로 하되, **기술적으로 한 단계 높은 유연성과 심미성**을 지향합니다.
