# 온톨로지 기반 개발 가이드 (Ontology-Driven Development)

## 1. 개요
Antigravity-통합 프로젝트는 모든 비즈니스 로직의 중심에 **온톨로지(Ontology)**를 둡니다. 데이터 스키마가 먼저 정의되고, 코드는 그 스키마를 해석하여 동작하는 구조입니다.

## 2. 개발 워크플로우

### Step 1: 스키마 정의 (`backend/schema.json`)
새로운 업무 요건이 생기면 가장 먼저 `schema.json`에 객체 타입과 관계 타입을 정의합니다.
```json
{
  "id": "Warehouse",
  "display_name": "창고",
  "properties": [...]
}
```

### Step 2: 관계 매핑
객체 간의 비즈니스적 의미를 링크로 연결합니다.
- `Order` --[STORED_IN]--> `Warehouse`

### Step 3: 백엔드 엔진 연동
`OntologyEngine`은 런타임에 이 스키마를 로드하여 API 엔드포인트를 자동 구성하거나 데이터 유효성을 검증합니다.

### Step 4: 프론트엔드 그래프 탐색
프론트엔드는 `/api/ontology/graph`를 통해 전체 지식 구조를 가져와 사용자에게 그래프 캔버스로 시각화합니다.

## 3. 팔란티어 스타일의 핵심 구현 목표
- **Dynamic Entities**: DB 테이블 추가 없이 스키마 파일 수정만으로 새로운 도메인 대응.
- **Deep Traversal**: "이 창고에 있는 제품을 주문한 서울 지역 고객 리스트"와 같은 다단계 관계 쿼리 지원.
- **Semantic UI**: 객체의 타입(`icon`, `color`)에 따라 UI가 자동으로 테마를 적용.
- **Hybrid AI Integration**: 비정형 문서(PDF)의 벡터 검색과 정형 온톨로지 데이터를 결합하여 정확하고 풍부한 지능형 답변을 제공. 자세한 내용은 [Hybrid Query Guide](./HYBRID_QUERY_GUIDE.md)를 참고하세요.

---
> "코드는 변하지 않지만, 온톨로지는 진화합니다."
