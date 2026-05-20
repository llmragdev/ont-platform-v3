# Click Test Checklist

작성일: 2026-05-12  
대상 프로젝트: `E:\ontology_edu\Codex-통합`  
목적: 온톨로지 중심 MVP가 실제 화면과 API에서 정상 동작하는지 사람이 직접 클릭해서 확인하는 체크리스트

## 0. 사전 준비

### 0.1 conda 환경 최초 생성

`codex_be`, `codex_fe` 환경이 아직 없다면 최초 1회만 생성한다.

백엔드:

```powershell
cd E:\ontology_edu\Codex-통합\backend
conda env create -f environment.yml
```

프론트엔드:

```powershell
cd E:\ontology_edu\Codex-통합\frontend
conda env create -f environment.yml
conda activate codex_fe
npm install
```

확인:

- [ ] `conda info --envs`에서 `codex_be` 표시
- [ ] `conda info --envs`에서 `codex_fe` 표시
- [ ] `codex_be`에서 `python --version` 실행 가능
- [ ] `codex_fe`에서 `node --version`, `npm --version` 실행 가능

이미 환경이 있으면 이 단계는 건너뛴다.

### 0.2 백엔드 실행

```powershell
cd E:\ontology_edu\Codex-통합\backend
conda activate codex_be
$env:PYTHONIOENCODING="utf-8"
uvicorn app.main:app --reload --port 8001
```

확인:

- [ ] **Backend**: `conda activate codex_be` 후 `uvicorn app.main:app --reload --port 8001` 실행
- [ ] `http://localhost:8001/api/health` 접속
- [ ] `status`가 `ok`
- [ ] `object_type_count`가 `3`
- [ ] `relationship_type_count`가 `2`
- [ ] `action_type_count`가 `2`
- [ ] `object_count`가 `9`
- [ ] `relationship_count`가 `9`

포트 오류가 날 때:

```powershell
# 8001을 점유한 프로세스 확인
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess

# 프로세스 상세 확인
Get-Process -Id <OwningProcess>

# 이전 테스트 서버라면 종료
Stop-Process -Id <OwningProcess>
```

또는 임시로 다른 포트를 사용한다.

```powershell
uvicorn app.main:app --reload --port 8011
```

이 경우 프론트엔드 API 주소도 맞춰야 한다.

```powershell
cd E:\ontology_edu\Codex-통합\frontend
@"
NEXT_PUBLIC_API_BASE=http://localhost:8011
"@ | Set-Content -Encoding UTF8 .env.local
```

### 0.3 프론트엔드 실행

```powershell
cd E:\ontology_edu\Codex-통합\frontend
conda activate codex_fe
npm run dev
```

확인:

- [ ] **Frontend**: `conda activate codex_fe` 후 `npm run dev` 실행
- [ ] `http://localhost:3100` 접속
- [ ] 좌측 메뉴가 표시됨
- [ ] 상단에 `Codex Ontology` 제목이 표시됨
- [ ] 기본 화면이 `온톨로지 관리`

프론트 포트 오류가 날 때:

```powershell
# 3100을 점유한 프로세스 확인
Get-NetTCPConnection -LocalPort 3100 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess

# 프로세스 상세 확인
Get-Process -Id <OwningProcess>

# 이전 테스트 서버라면 종료
Stop-Process -Id <OwningProcess>
```

또는 임시로 다른 포트를 사용한다.

```powershell
npx next dev -p 3101
```

## 1. 온톨로지 관리 화면

목적: JSON 설정에서 로드된 객체 타입, 관계 타입, 액션 타입이 화면에 표시되는지 확인한다.

### 1.1 개요 배지

화면 상단 확인:

- [ ] `Types 3`
- [ ] `Links 2`
- [ ] `Objects 9`
- [ ] `Relations 9`

### 1.2 객체 타입

`온톨로지 관리` 화면의 객체 타입 카드 확인:

- [ ] `고객 / Customer` 카드 표시
- [ ] `상품 / Product` 카드 표시
- [ ] `주문 / Order` 카드 표시
- [ ] Customer 속성에 `name`, `segment`, `region`, `risk_tier` 표시
- [ ] Order 속성에 `order_date`, `status`, `amount` 표시

### 1.3 관계 타입

관계 타입 카드 확인:

- [ ] `Customer --PLACED_ORDER--> Order` 표시
- [ ] `Order --ORDER_CONTAINS_PRODUCT--> Product` 표시
- [ ] `one_to_many` 배지 표시
- [ ] `many_to_many` 배지 표시

### 1.4 액션 타입

액션 타입 영역 확인:

- [ ] `주문 승인 / Order`
- [ ] `리스크 평가 / Customer`

## 2. 객체 탐색 화면

목적: 객체 타입별 목록과 범용 객체 컨텍스트가 동작하는지 확인한다.

### 2.1 Customer 목록

- [ ] 좌측 메뉴에서 `객체 탐색` 클릭
- [ ] 타입 선택이 `Customer`
- [ ] `C001`, `C002`, `C003` 표시
- [ ] `Alpha Manufacturing`, `Beta Retail`, `Gamma Logistics` 표시

### 2.2 Order 목록

- [ ] 타입 선택을 `Order`로 변경
- [ ] `O001`, `O002`, `O003` 표시
- [ ] 상태 값 `Submitted`, `Review` 등이 표시

### 2.3 Product 목록

- [ ] 타입 선택을 `Product`로 변경
- [ ] `P001`, `P002`, `P003` 표시
- [ ] 상품명 `Industrial Sensor`, `Analytics License`, `Support Package` 표시

### 2.4 객체 컨텍스트

Order 타입에서:

- [ ] `O001` 행의 `Context` 버튼 클릭
- [ ] 우측 `객체 컨텍스트` 패널 표시
- [ ] Selected에 `O001 (Order)` 표시
- [ ] Incoming에 `C001 --PLACED_ORDER--> O001` 표시
- [ ] Outgoing에 `O001 --ORDER_CONTAINS_PRODUCT--> P001` 또는 `P003` 표시
- [ ] Documents에 `Order Approval Policy` 표시
- [ ] Actions에 `주문 승인` 표시

Customer 타입에서:

- [ ] 타입 선택을 `Customer`로 변경
- [ ] `C001` 행의 `Context` 버튼 클릭
- [ ] Outgoing에 `C001 --PLACED_ORDER--> O001` 표시
- [ ] Documents에 고객 관련 문서 표시
- [ ] Actions에 `리스크 평가` 표시

## 3. 관계 관리 화면

목적: 관계 인스턴스 조회와 추가 API가 화면에서 동작하는지 확인한다.

### 3.1 전체 관계 목록

- [ ] 좌측 메뉴에서 `관계 관리` 클릭
- [ ] 관계 목록 테이블 표시
- [ ] `R001`, `R002`, `R003` 표시
- [ ] `PLACED_ORDER` 관계 표시
- [ ] `ORDER_CONTAINS_PRODUCT` 관계 표시
- [ ] Source와 Target ID가 표시

### 3.2 관계 타입 필터

- [ ] 관계 타입 선택 박스에서 `PLACED_ORDER` 선택
- [ ] `PLACED_ORDER` 관계만 표시
- [ ] 관계 타입 선택 박스에서 `ORDER_CONTAINS_PRODUCT` 선택
- [ ] 상품 포함 관계만 표시

### 3.3 샘플 관계 추가

- [ ] `샘플 관계 추가` 버튼 클릭
- [ ] 오류 없이 관계가 추가됨
- [ ] 새 관계 ID가 `REL-...` 형식으로 표시
- [ ] 새 관계가 `C001 -> O003` 형태로 추가됨

주의:
- 현재 MVP는 메모리 상태에 추가된다.
- 서버를 재시작하면 `data.default.json`의 기본 데이터로 돌아간다.

## 4. AI 질의 화면

목적: 질문에서 객체 ID를 추출하고, 범용 객체 컨텍스트와 문서 근거를 사용해 응답하는지 확인한다.

### 4.1 기본 질의

- [ ] 좌측 메뉴에서 `AI 질의` 클릭
- [ ] 기본 질문 `O001의 관계와 승인 근거를 알려줘` 표시
- [ ] `질의 실행` 클릭
- [ ] 응답 영역 표시
- [ ] 배지에 `O001` 표시
- [ ] 답변에 `incoming`, `outgoing`, `Available actions` 관련 내용 표시

### 4.2 Trace 확인

Trace 영역 확인:

- [ ] `extract_object_id`
- [ ] `load_object_context`
- [ ] `collect_relationships`
- [ ] `search_documents`
- [ ] `compose_answer`

### 4.3 Evidence 확인

Evidence 영역 확인:

- [ ] `Order Approval Policy` 표시
- [ ] `Risk Review Guideline` 또는 관련 문서 표시
- [ ] score 배지 표시

### 4.4 다른 객체 질의

질문을 다음처럼 변경:

```text
C001과 연결된 주문과 리스크 정보를 알려줘
```

확인:

- [ ] 감지 객체가 `C001`
- [ ] 객체 타입이 `Customer`
- [ ] 관계 컨텍스트에 연결 주문 표시
- [ ] 액션에 `RiskAssess` 또는 `리스크 평가` 표시

## 5. OpenAPI 빠른 확인

브라우저에서 `http://localhost:8001/docs` 접속.

확인:

- [ ] `GET /api/ontology/schema`
- [ ] `GET /api/ontology/object-types`
- [ ] `GET /api/ontology/relationship-types`
- [ ] `GET /api/ontology/objects`
- [ ] `GET /api/ontology/objects/{object_id}/context`
- [ ] `GET /api/ontology/relationships`
- [ ] `POST /api/ontology/relationships`
- [ ] `POST /api/ask`

Try it out:

- [ ] `GET /api/ontology/objects/O001/context` 실행
- [ ] incoming/outgoing 관계가 JSON으로 표시
- [ ] `POST /api/ask`에 `{"question":"O001의 관계를 알려줘"}` 실행
- [ ] `detected_object_id`가 `O001`

## 6. 자동 검증

### 6.1 백엔드 테스트

```powershell
cd E:\ontology_edu\Codex-통합\backend
conda activate codex_be
$env:PYTHONIOENCODING="utf-8"
pytest
```

기대 결과:

- [ ] `7 passed`

### 6.2 프론트엔드 빌드

```powershell
cd E:\ontology_edu\Codex-통합\frontend
conda activate codex_fe
npm run build
```

기대 결과:

- [ ] `Compiled successfully`
- [ ] `/` route 생성 성공

## 7. 현재 MVP 한계

아래 항목은 아직 미구현 또는 후속 작업이다.

- [ ] 객체 타입 생성/수정 UI
- [ ] 관계 타입 생성/수정 UI
- [ ] 객체 인스턴스 생성/수정 UI
- [ ] 관계 인스턴스 삭제 UI
- [ ] 온톨로지 validate/publish/rollback
- [ ] 정책/권한 설정화
- [ ] Action Type 기반 워크플로우 그래프 자동 팔레트
- [ ] 실제 LLM 연동
- [ ] Playwright E2E 자동화

## 8. 발견 이슈 기록

테스트 중 발견한 문제는 아래 형식으로 기록한다.

```text
[ ] 날짜 / 화면 / 증상 / 재현 절차 / 임시 조치
```

기록:

- [ ] 
