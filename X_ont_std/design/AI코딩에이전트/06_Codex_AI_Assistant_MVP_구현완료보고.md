# Codex AI Assistant MVP 구현 완료 보고

**작성자**: Codex  
**작성일**: 2026-06-14  
**대상 시스템**: ont_platform v5  
**구현 범위**: 전역 AI Assistant 1차 MVP

---

## 1. 작업 요약

`ont_platform v5`에 우측 하단 전역 AI Assistant 패널을 추가하고, 백엔드에 `/api/assistant/chat` API를 구현했다.

이번 구현은 실제 코드 실행이나 앱 저장까지 자동 수행하는 단계가 아니라, 현재 화면 맥락을 받아 안전한 초안과 가이드를 생성하는 MVP 단계다.

```text
현재 화면 context
  -> AI Assistant API
  -> 의도 분류
  -> 온톨로지 질의/앱 초안/점검 가이드 생성
  -> 프론트 패널에 표시
```

---

## 2. 구현된 기능

### 2.1 전역 AI Assistant 패널

- 화면 우측 하단에 AI Assistant 버튼 추가
- 버튼 클릭 시 우측 드로어 패널 오픈
- 현재 화면, 테넌트, 프로젝트, 사용자 정보를 context로 전달
- 빠른 프롬프트 제공
  - 현재 화면 시연용 설명
  - 최근 7일 반복 고장 설비 온톨로지 질의 생성
  - 공장 반복 고장 분석 앱 초안 생성
  - 댓글이 안 달릴 때 점검 순서 안내

### 2.2 백엔드 Assistant API

- `POST /api/assistant/chat` 추가
- tenant context 자동 보강
  - company_id
  - project_id
  - user_id
  - role
- 1차 rule-based 의도 분류 구현
  - 현재 화면 설명
  - 온톨로지 질의 생성
  - 앱 초안 생성
  - 실패 원인 점검
  - 워크플로우 변경 제안
  - 일반 도움말

### 2.3 온톨로지 질의 초안

공장 자동화 시나리오 기준으로 반복 고장 설비를 찾는 SPARQL 초안을 생성한다.

참조 타입:

```text
ServiceRequest
Factory
ProductionLine
ProcessStep
Equipment
FaultEvent
MaintenanceTask
QualityIssue
```

생성 결과는 실제 실행 전 검증이 필요한 preview로 표시한다.

### 2.4 Streamlit 스타일 앱 초안

공장 반복 고장 분석 앱 초안을 `App Spec Preview` 형태로 생성한다.

포함 위젯:

- 반복 고장 설비 수 metric
- 반복 고장 목록 table
- 설비별 고장 횟수 chart
- 고장-설비-정비지시 관계 graph

현재는 저장 버튼까지 자동 연결하지 않고, 안전한 미리보기 단계로 제한했다.

### 2.5 좌측 Streamlit 앱 메뉴

설계 방향과 화면 구성을 맞추기 위해 좌측 메뉴에 `앱 빌더 > Streamlit 앱` 항목을 추가했다.

현재 화면은 실제 앱 저장소가 연결된 완성 화면은 아니지만, 다음 작업 흐름을 1차 UI로 구현했다.

- Streamlit 앱 폴더 생성
- Streamlit 파이썬 프로그램 생성
- 폴더별 프로그램 목록 조회
- 파이썬 코드 편집창 표시
- 선택된 편집창 정보를 AI Assistant context로 전달
- AI Assistant 응답의 Python 코드 블록을 선택된 편집창에 적용
- Streamlit 프로그램 코딩 실행 버튼과 보기 URL 안내
- Assistant 패널 열림 시 메인 작업 영역 자동 축소
- 좌측 메뉴 아이콘 모드 접기/펼치기

사용자는 Streamlit 파이썬 편집창을 선택한 뒤 우측 하단 챗봇에서 `코딩해줘`처럼 짧게 요청할 수 있다. 이때 챗봇은 별도의 파일명 언급이 없어도 현재 선택된 편집창을 대상으로 이해한다.

챗봇은 기존 전체 화면 모달 방식이 아니라 우측 docked panel 방식으로 동작하도록 변경했다. 따라서 챗봇이 열리면 메인 작업 영역이 자동으로 줄어들고, Streamlit 편집창과 Assistant를 나란히 사용할 수 있다.

또한 채팅창의 헤더, 대화 영역, 입력 영역에 현재 선택한 소스 편집 화면을 표시한다. Python 코드 응답은 선택된 Streamlit 편집창에 자동 적용되고, 채팅창과 Streamlit 화면 양쪽에 적용 완료 상태가 표시된다.

좌측 메뉴는 아이콘 모드로 접을 수 있다. 화면 폭이 좁은 상태에서도 Streamlit 편집기와 Assistant가 사용할 수 있는 가로 공간을 확보하기 위한 기능이다.

---

## 3. 변경 프로그램 내역

### 3.1 백엔드

| 파일 | 변경 내용 |
|---|---|
| `ont_platform/v5/backend/app/models/assistant.py` | Assistant 요청/응답, Query, App Spec 모델 추가 |
| `ont_platform/v5/backend/app/services/assistant_service.py` | 의도 분류와 응답 생성 서비스 추가 |
| `ont_platform/v5/backend/app/api/assistant.py` | `/api/assistant/chat` 라우터 추가 |
| `ont_platform/v5/backend/app/main.py` | Assistant router 등록 |

### 3.2 프론트엔드

| 파일 | 변경 내용 |
|---|---|
| `ont_platform/v5/frontend/src/components/AIAssistantPanel.tsx` | 우측 docked AI Assistant 패널, 선택 편집창 표시 강화, Python 코드 자동 적용 |
| `ont_platform/v5/frontend/src/components/StreamlitAppBuilder.tsx` | Streamlit 폴더/프로그램 생성, 파이썬 편집창, 선택 context 발행, 코드 적용 이벤트 수신, 코딩 실행 URL 안내 |
| `ont_platform/v5/frontend/src/lib/api.ts` | `api.assistant.chat()` 클라이언트 함수 추가 |
| `ont_platform/v5/frontend/src/types/api.ts` | Assistant 관련 타입과 선택된 앱/파일 context 타입 추가 |
| `ont_platform/v5/frontend/src/components/Sidebar.tsx` | 좌측 메뉴에 `앱 빌더 > Streamlit 앱` 항목 추가, 아이콘 접기/펼치기 지원 |
| `ont_platform/v5/frontend/src/app/page.tsx` | Assistant docked layout과 좌측 메뉴 접힘 상태 관리 추가 |

---

## 4. 검증 결과

### 4.1 백엔드 컴파일

다음 파일의 Python compile을 확인했다.

```text
ont_platform/v5/backend/app/models/assistant.py
ont_platform/v5/backend/app/services/assistant_service.py
ont_platform/v5/backend/app/api/assistant.py
```

결과: 통과

### 4.2 프론트 타입 검사

```powershell
npx tsc --noEmit
```

결과: 통과

### 4.3 Assistant API 호출 검증

검증 요청:

```text
공장 반복 고장 분석 앱 만들어줘
```

응답 확인:

```text
intent: create_app
summary: Streamlit 스타일 업무 앱 초안을 만들었습니다.
generated query: 최근 7일 반복 고장 설비 조회
app spec: 공장 반복 고장 분석 앱
```

결과: 통과

---

## 5. 기동 상태

구현 완료 시점에 다음 포트가 사용 중이었다.

| 포트 | 프로세스 | 용도 |
|---|---|---|
| 8001 | python | ont_platform v5 backend |
| 3002 | node | ont_platform v5 frontend |

직접 재기동할 때는 기존 프로세스가 남아 있으면 포트 충돌이 발생할 수 있다.

백엔드 종료 예:

```powershell
Stop-Process -Id <backend_pid> -Force
```

프론트 종료 예:

```powershell
Stop-Process -Id <frontend_pid> -Force
```

---

## 6. 현재 한계

이번 MVP는 안전한 초안 생성 단계다. 다음 기능은 아직 자동 실행으로 연결하지 않았다.

- 생성 쿼리 실제 실행
- 쿼리 스키마 검증 자동화
- App Spec 저장
- Streamlit 프로그램 서버 저장
- Assistant 응답 코드를 서버 파일에 저장하거나 diff로 부분 적용
- 실제 Streamlit 프로세스 실행과 포트 관리
- 외부 접속 가능한 공유 URL 발급
- `/apps/{appId}` 렌더링
- 외부 공유 URL 생성
- Streamlit 코드 export
- Live Preview 또는 Docker Sandbox 실행
- LLM 기반 고급 코드 생성

---

## 7. 다음 개발 우선순위

1. 쿼리 검증 API 추가
2. read-only 쿼리 실행 API 연결
3. 실행 결과 테이블/차트 표시
4. App Spec 저장소 설계 및 저장 API 구현
5. Assistant가 생성한 App Spec을 Streamlit 앱 화면으로 전달
6. Assistant 응답 코드를 선택된 파이썬 편집창에 적용
7. 실제 Streamlit 실행 프로세스와 포트 관리 API 구현
8. `/apps/{appId}` 내부 앱 렌더링
9. 공유 URL 발급
10. Streamlit 코드 export
11. Live Preview 실행 환경 검토
12. LLM 기반 생성으로 rule-based MVP 확장

---

## 8. 판단

이번 구현으로 `04_최종정리_플랫폼형_AI_Assistant_설계.md`의 1~4단계가 1차 구현되었다.

```text
1. 우측 하단 전역 AI Assistant 버튼/패널
2. 현재 화면 context 전달
3. 온톨로지 질의/SPARQL 초안 생성
4. 생성 쿼리 preview와 복사 기반 UI
5. 좌측 Streamlit 앱 메뉴와 준비 화면
6. Streamlit 폴더/프로그램 생성과 선택 편집창 context 전달
7. 챗봇 Python 코드 응답을 선택된 Streamlit 편집창에 적용
8. Assistant docked panel, 좌측 아이콘 메뉴, Streamlit 실행 URL 안내
```

따라서 현재 상태는 “AI 코딩 에이전트의 제품 방향을 화면과 API로 확인할 수 있는 MVP”로 볼 수 있다.

다음 단계부터는 단순 챗봇이 아니라, 실제 플랫폼 내부 자산인 쿼리, 앱, 워크플로우, 스킬로 저장되고 재사용되는 구조를 구현해야 한다.
