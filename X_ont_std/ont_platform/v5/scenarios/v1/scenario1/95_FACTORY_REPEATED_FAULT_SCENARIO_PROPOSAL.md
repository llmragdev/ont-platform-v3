# 확장 예시: 공장 반복 고장 시나리오

작성일: 2026-06-13  
위치: `ont_platform/v5/scenarios/v1/scenario1`  
성격: Scenario 1 고객 문의 자동댓글 이후 확장 데모 후보

현재 상태:

- Workflow Builder 시스템 템플릿 생성 완료
- Workflow-Ontology 매핑 템플릿 생성 완료
- `demo-co / proj-01` 프로젝트 온톨로지 스키마에 공장 도메인 타입 설치 완료

구현 파일:

```text
ont_platform/v5/backend/app/config/workflow_templates/factory_repeated_fault_response.json
ont_platform/v5/backend/app/config/workflow_ontology_mappings/factory_repeated_fault_response.json
```

## 1. 왜 이 예시가 필요한가

비밀번호 초기화나 댓글 자동화는 구현 흐름을 검증하기 좋다.

하지만 사람들이 이런 의문을 가질 수 있다.

```text
댓글 하나 다는 것을 꼭 워크플로우와 온톨로지로 해야 하나?
그냥 DB에 저장하면 되는 것 아닌가?
```

이 의문을 설득하려면, 단순 댓글보다 "여러 문의가 같은 업무 상황으로 연결되는 예시"가 필요하다.

공장 반복 고장 시나리오는 이 점을 보여주기 좋다.

```text
게시판에서는 글 3개로 보이지만,
온톨로지에서는 같은 공장, 같은 라인, 같은 장비, 같은 문제로 묶인다.
```

## 2. 쉬운 예시 배경

```text
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
공정 단계: 용접
장비: 배터리 탭 용접기
문제: 압력이 낮다는 오류
```

어려운 전문용어 대신 화면에는 아래처럼 표시한다.

| 표시명 | 내부 모델 후보 |
| --- | --- |
| 세종 배터리팩 공장 | Factory |
| 3번 조립 라인 | ProductionLine |
| 용접 단계 | ProcessStep |
| 배터리 탭 용접기 | Equipment |
| 반복 고장 | FaultEvent |
| 정비팀 확인 건 | MaintenanceTask |
| 품질 문제 | QualityIssue |

## 3. 게시글 예시

### 게시글 1

```text
카테고리: 장비 고장
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
단계: 용접
장비: 배터리 탭 용접기
시간: 오전 10시

내용:
오전 10시에 배터리 탭 용접기가 멈췄습니다.
화면에 "압력이 낮습니다"라는 오류가 떴습니다.
다시 켜니 일단 움직입니다.
```

자동 댓글:

```text
배터리 탭 용접기 고장 문의를 접수했습니다.
같은 장비에서 같은 문제가 반복되는지 확인하겠습니다.
```

온톨로지 변화:

```text
ServiceRequest 생성
FaultEvent 생성
Equipment = 배터리 탭 용접기 연결
ProcessStep = 용접 단계 연결
ProductionLine = 3번 조립 라인 연결
Factory = 세종 배터리팩 공장 연결
```

### 게시글 2

```text
카테고리: 장비 고장
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
단계: 용접
장비: 배터리 탭 용접기
시간: 오전 11시

내용:
오전 11시에 배터리 탭 용접기가 또 멈췄습니다.
아까와 같은 "압력이 낮습니다" 오류입니다.
작업이 15분 정도 멈췄습니다.
```

자동 댓글:

```text
같은 장비에서 같은 문제가 반복 접수되었습니다.
단순 문의가 아니라 반복 고장으로 보고 정비팀 확인 건으로 올리겠습니다.
```

온톨로지 변화:

```text
두 번째 ServiceRequest 생성
기존 FaultEvent와 연결
FaultEvent.status = repeated
MaintenanceTask 생성
MaintenanceTask.assigned_team = 정비팀
```

### 게시글 3

```text
카테고리: 품질 문제
공장: 세종 배터리팩 공장
라인: 3번 조립 라인
단계: 검사
장비: 검사 카메라
시간: 오전 11시 40분

내용:
배터리 탭 용접기를 다시 켠 뒤부터 검사 카메라에서 불량이 많이 잡힙니다.
평소보다 불량이 늘었습니다.
```

자동 댓글:

```text
장비 고장 이후 품질 문제가 함께 접수되었습니다.
이 품질 문제를 앞서 발생한 배터리 탭 용접기 반복 고장과 연결해서 확인하겠습니다.
정비팀과 품질팀이 함께 확인해야 할 건으로 올리겠습니다.
```

온톨로지 변화:

```text
QualityIssue 생성
QualityIssue --possibly_caused_by--> FaultEvent 연결
QualityIssue --detected_by--> 검사 카메라 연결
QualityIssue --affects--> 3번 조립 라인 연결
```

## 4. 온톨로지로 보이는 쉬운 그림

```text
세종 배터리팩 공장
  └─ 3번 조립 라인
      └─ 용접 단계
          └─ 배터리 탭 용접기
              └─ 반복 고장
                  ├─ 오전 10시 문의
                  ├─ 오전 11시 문의
                  ├─ 정비팀 확인 건
                  └─ 이후 발생한 품질 문제
```

핵심 설명:

```text
DB는 글 3개를 저장한다.
온톨로지는 이 세 글이 같은 장비 문제에서 나온 것임을 알게 해준다.
```

## 5. 온톨로지 객체 후보

### ServiceRequest

게시판 글 1건.

```text
속성:
- external_id
- category
- title
- content
- requester
- occurred_at
- status
```

### Factory

공장.

```text
예: 세종 배터리팩 공장
```

### ProductionLine

생산 라인.

```text
예: 3번 조립 라인
```

### ProcessStep

작업 단계.

```text
예: 용접, 검사, 포장
```

### Equipment

장비.

```text
예: 배터리 탭 용접기, 검사 카메라
```

### FaultEvent

고장 상황.

```text
예: 배터리 탭 용접기 압력 낮음 반복 고장
```

### MaintenanceTask

정비팀 확인 건.

```text
예: 배터리 탭 용접기 점검 요청
```

### QualityIssue

품질 문제.

```text
예: 검사 카메라에서 불량 증가
```

## 6. 관계 후보

```text
Factory --has_line--> ProductionLine
ProductionLine --has_step--> ProcessStep
ProcessStep --uses--> Equipment
ServiceRequest --reports--> FaultEvent
FaultEvent --affects--> Equipment
FaultEvent --creates--> MaintenanceTask
QualityIssue --possibly_caused_by--> FaultEvent
QualityIssue --detected_by--> Equipment
QualityIssue --affects--> ProductionLine
```

## 7. 워크플로우 판단 규칙 예시

### 규칙 1. 첫 고장

```text
같은 장비/같은 문제의 최근 접수가 없으면
  -> FaultEvent 신규 생성
  -> 자동 댓글
  -> 상태: observed
```

### 규칙 2. 반복 고장

```text
2시간 안에 같은 장비/같은 문제가 2회 이상 접수되면
  -> FaultEvent.status = repeated
  -> MaintenanceTask 생성
  -> 정비팀 확인 건으로 승격
```

### 규칙 3. 품질 문제 연결

```text
장비 고장 이후 같은 라인에서 품질 문제가 접수되면
  -> QualityIssue 생성
  -> 기존 FaultEvent와 연결
  -> 정비팀 + 품질팀 공동 확인 건으로 승격
```

## 8. 화면에서 보여줄 것

### 게시판

기존 게시판 글은 그대로 둔다.

추가 필드 후보:

```text
카테고리
공장
라인
단계
장비
발생 시각
심각도
```

### Workflow Builder

시나리오 그래프:

```text
문의 입력
  -> 카테고리 분류
  -> 공장/라인/장비 매핑
  -> 반복 여부 확인
  -> 자동 댓글
  -> 정비팀/품질팀 이관
  -> 온톨로지 저장
```

### Ontology Trace

아래 흐름을 쉽게 보여준다.

```text
게시글 3개
  -> 같은 반복 고장 1건
  -> 정비팀 확인 건
  -> 품질 문제 연결
```

## 9. 현재 시나리오와의 관계

이 문서는 확장 예시이며, 1차 템플릿 구현은 완료했다.

우선순위:

```text
1. 현재 비밀번호/댓글 시나리오를 온톨로지에 저장
2. Workflow-Ontology Trace 화면 구현
3. 공장 반복 고장 시나리오로 확장
```

현재는 3단계의 첫 작업으로 템플릿과 온톨로지 매핑을 추가했다.

남은 작업:

- 공장 현장 요청 샘플 데이터 생성
- 공장 도메인 전용 온톨로지 writer 구현
- 반복 판단 규칙 실행 구현
- Workflow Trace에서 공장 흐름 전용 표시
- customer_board 또는 별도 factory_board 입력폼 확장

## 10. 데모 설명 문구

```text
게시판에서는 글이 3개로 보입니다.

하지만 온톨로지에서는
같은 공장, 같은 라인, 같은 장비, 같은 문제로 묶입니다.

그래서 시스템은
그냥 댓글만 다는 것이 아니라
반복 고장인지 알아보고,
정비팀으로 올리고,
나중에 생긴 품질 문제까지 연결해서 보여줍니다.
```
