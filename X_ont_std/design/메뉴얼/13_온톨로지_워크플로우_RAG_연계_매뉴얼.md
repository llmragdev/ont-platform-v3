# 온톨로지, 워크플로우, RAG 연계 매뉴얼

**문서 번호**: 13  
**대상 화면**: Builder and Run, Ontology Explorer, Schema Manager, Instance Editor, Integrated Query  
**목적**: 워크플로우 실행 결과가 온톨로지와 RAG에 어떻게 연결되는지 설명한다.

---

## 1. 세 가지 구성요소의 역할

| 구성요소 | 쉬운 설명 | 시스템 역할 |
|---|---|---|
| 워크플로우 | 일을 처리하는 절차 | 입력, 판단, 조회, 실행, 기록 단계를 순서대로 수행 |
| RAG | 문서와 지식을 찾아 답변에 활용 | 정책, 매뉴얼, 지식 문서에서 근거 검색 |
| 온톨로지 | 업무 객체와 관계 지도 | 요청, 설비, 사람, 답변, 정비지시의 연결 저장 |

간단히 말하면 다음과 같다.

```text
워크플로우는 일을 처리하고,
RAG는 근거를 찾고,
온톨로지는 처리한 일의 맥락을 관계로 남긴다.
```

---

## 2. 왜 DB만으로 부족한가

일반 DB는 데이터를 표 형태로 잘 저장한다.  
하지만 업무 자동화에서는 “이 데이터가 어떤 업무 의미를 갖는지”가 중요하다.

예:

```text
문의글 1건
댓글 1건
정비지시 1건
설비 1개
품질 이슈 1건
```

DB에서는 각각 별도 테이블의 행일 수 있다.  
온톨로지에서는 다음처럼 업무 의미가 연결된다.

```text
현장 요청이 특정 설비의 고장을 보고했다.
그 고장은 특정 생산 라인에 영향을 줬다.
그 고장 때문에 정비 지시가 생성됐다.
정비 결과는 품질 이슈와 연결됐다.
```

이 관계가 있어야 반복 고장, 영향 분석, 원인 추적, 자동 조치 추천을 하기 쉬워진다.

---

## 3. 워크플로우와 온톨로지 매핑

워크플로우의 각 노드는 실행 결과를 만들 수 있다.  
이 결과 중 일부는 온톨로지 객체나 관계로 저장된다.

예:

| 워크플로우 노드 | 생성/갱신되는 온톨로지 |
|---|---|
| Request Input | ServiceRequest |
| Asset Map | Factory, ProductionLine, Equipment |
| Repeat Check | FaultEvent, occurrence count |
| Draft Response | AutoReply |
| Maintenance | MaintenanceTask |
| MCP Comment | ExternalComment |

---

## 4. 매핑 설정 시 고려 사항

### 4.1 객체 타입을 먼저 정한다

예:

```text
ServiceRequest
Equipment
FaultEvent
MaintenanceTask
AutoReply
ExternalComment
```

### 4.2 어떤 속성을 저장할지 정한다

예:

| 객체 | 주요 속성 |
|---|---|
| ServiceRequest | title, category, status, created_at |
| Equipment | name, line, process_step |
| FaultEvent | severity, occurred_at, repeated |
| MaintenanceTask | task_type, assignee, due_at, status |
| AutoReply | body, confidence, generated_by |

### 4.3 관계를 정한다

예:

```text
ServiceRequest -> reports -> FaultEvent
FaultEvent -> affects -> Equipment
FaultEvent -> creates -> MaintenanceTask
AutoReply -> posted_as -> ExternalComment
WorkflowExecution -> generated -> AutoReply
```

---

## 5. RAG와 온톨로지의 차이

| 구분 | RAG | 온톨로지 |
|---|---|---|
| 주 대상 | 문서, 매뉴얼, 정책 | 업무 객체와 관계 |
| 질문 예 | “비밀번호 초기화 정책 알려줘” | “이 고장이 어떤 설비와 연결돼?” |
| 장점 | 문서 기반 답변 생성 | 구조화된 관계 추적 |
| 결과 | 근거 문서와 답변 | 객체, 속성, 관계 |

둘 중 하나를 고르는 것이 아니라 함께 쓰는 구조가 좋다.

```text
RAG가 답변 근거를 찾고,
온톨로지가 답변의 업무 맥락을 남긴다.
```

---

## 6. 화면에서 확인하는 방법

### 6.1 Builder and Run

확인할 것:

- 선택한 워크플로우의 온톨로지 매핑
- 노드별 실행 상태
- 선택 노드의 입출력
- 스킬 노드의 입력 매핑

### 6.2 Ontology Explorer

확인할 것:

- 실행으로 생성된 객체
- 객체 간 관계
- 선택 객체 상세 속성
- 외부 댓글 또는 정비지시와의 연결

### 6.3 Integrated Query

확인할 것:

- 온톨로지와 RAG를 함께 활용한 질의 결과
- 검색 근거와 객체 관계가 함께 나오는지

---

## 7. 데모 설명 문장

```text
일반 RAG는 문서를 찾아 답변하는 데 강합니다.
하지만 업무 자동화에서는 답변 이후의 실행과 추적이 더 중요합니다.
이 솔루션은 워크플로우가 업무를 실행하고,
RAG가 근거를 찾고,
온톨로지가 처리 결과의 관계를 남기기 때문에
나중에 왜 이런 조치가 나왔는지 추적할 수 있습니다.
```

---

## 8. 설계 원칙

- 온톨로지는 모든 로그를 무조건 저장하는 곳이 아니다.
- 업무적으로 의미 있는 객체와 관계만 저장한다.
- 워크플로우 노드는 실행 절차이고, 온톨로지 객체는 업무 의미이다.
- 액션 타입과 온톨로지 타입은 분리해서 관리한다.
- 외부 시스템 호출 결과는 감사 로그와 온톨로지 관계 양쪽에서 추적할 수 있어야 한다.

