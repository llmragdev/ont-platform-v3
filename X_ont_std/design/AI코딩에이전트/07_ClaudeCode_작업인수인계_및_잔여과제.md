# Claude Code 작업 인수인계 및 잔여 과제

**작성자**: Codex  
**작성일**: 2026-06-14  
**대상 시스템**: `ont_platform/v5`  
**목적**: AI 코딩 에이전트 + Streamlit 앱 빌더 MVP 구현 현황과 Claude Code 후속 작업 지시

---

## 1. 현재 결론

현재까지 구현된 것은 “AI Assistant와 Streamlit 앱 빌더의 화면/상태 연동 MVP”이다.

다음은 구현 완료되었다.

- 우측 AI Assistant 패널
- 좌측 메뉴 `앱 빌더 > Streamlit 앱`
- Streamlit 앱 폴더 생성 UI
- Streamlit 파이썬 프로그램 생성 UI
- 파이썬 코드 편집창
- 선택된 편집창 정보를 AI Assistant context로 전달
- 챗봇에서 `코딩해줘` 요청 시 선택된 편집창 기준으로 Python 코드 초안 생성
- 생성된 Python 코드 블록을 선택된 편집창에 자동 적용
- 채팅창에 현재 선택한 소스 편집 화면 표시
- Streamlit 화면에 적용 완료 상태 표시
- Assistant 패널 docked layout
- 좌측 메뉴 아이콘 접기/펼치기
- Streamlit 화면의 `코딩 실행` 버튼과 URL 안내

하지만 실제 Streamlit 서버 실행은 아직 구현되지 않았다.

---

## 2. 가장 중요한 미해결 문제

### 문제

Streamlit 화면에서 `코딩 실행`을 누르면 다음 형태의 URL이 표시된다.

```text
http://127.0.0.1:8501/?app=test3
```

브라우저에서 URL 자체는 열려고 하지만, 실제 `8501` 포트에 Streamlit 서버가 떠 있지 않기 때문에 다음 오류가 발생한다.

```text
페이지에 연결할 수 없습니다
```

### 원인

현재 프론트는 URL 문자열만 생성한다.

```text
프론트 상태의 코드
  -> URL 문자열 생성
  -> 브라우저 open
```

하지만 아래 과정은 없다.

```text
프론트 코드
  -> 백엔드 저장 API 호출
  -> .py 파일 저장
  -> streamlit run 실행
  -> 포트 할당
  -> 실제 접속 가능한 URL 반환
```

또한 현재 확인 결과 `claud_be` Python 환경에는 `streamlit` 패키지가 설치되어 있지 않다.

```text
streamlit False
```

---

## 3. 변경된 주요 파일

### 3.1 백엔드

| 파일 | 상태 | 내용 |
|---|---|---|
| `ont_platform/v5/backend/app/models/assistant.py` | 신규 | Assistant 요청/응답 모델, 선택된 앱/파일 context 모델 |
| `ont_platform/v5/backend/app/services/assistant_service.py` | 신규 | rule-based Assistant MVP, Streamlit 코드 초안 생성 |
| `ont_platform/v5/backend/app/api/assistant.py` | 신규 | `POST /api/assistant/chat` API |
| `ont_platform/v5/backend/app/main.py` | 수정 | Assistant router 등록 |

### 3.2 프론트엔드

| 파일 | 상태 | 내용 |
|---|---|---|
| `ont_platform/v5/frontend/src/components/AIAssistantPanel.tsx` | 신규 | 우측 AI Assistant 패널, 선택 편집창 표시, 코드 자동 적용 |
| `ont_platform/v5/frontend/src/components/StreamlitAppBuilder.tsx` | 신규 | Streamlit 폴더/프로그램/편집기/실행 URL UI |
| `ont_platform/v5/frontend/src/components/Sidebar.tsx` | 수정 | `앱 빌더 > Streamlit 앱` 메뉴, 좌측 메뉴 접기/펼치기 |
| `ont_platform/v5/frontend/src/app/page.tsx` | 수정 | Assistant docked layout, Streamlit 화면 라우팅 |
| `ont_platform/v5/frontend/src/lib/api.ts` | 수정 | `api.assistant.chat()` 추가 |
| `ont_platform/v5/frontend/src/types/api.ts` | 수정 | Assistant 관련 타입, 선택된 앱/파일 context 타입 |

### 3.3 문서

| 파일 | 상태 | 내용 |
|---|---|---|
| `design/AI코딩에이전트/06_Codex_AI_Assistant_MVP_구현완료보고.md` | 수정 | MVP 구현내역 갱신 |
| `design/AI코딩에이전트/07_ClaudeCode_작업인수인계_및_잔여과제.md` | 신규 | 본 인수인계 문서 |

---

## 4. 현재 동작 흐름

### 4.1 Streamlit 편집

1. 좌측 메뉴에서 `앱 빌더 > Streamlit 앱` 선택
2. 폴더 생성
3. Streamlit 프로그램 생성
4. 파이썬 편집창 선택
5. 선택된 파일 정보가 AI Assistant context에 저장됨

저장되는 context 예:

```json
{
  "selected_app_id": "stapp-xxxx",
  "selected_app_name": "test3",
  "selected_folder_id": "folder-xxxx",
  "selected_folder_name": "공장 자동화",
  "selected_file_path": "test3.py",
  "selected_file_name": "test3.py",
  "selected_language": "python"
}
```

### 4.2 챗봇 코딩

1. Streamlit 편집창이 선택된 상태에서 AI Assistant 열기
2. 채팅창에 현재 선택한 소스 편집 화면 표시
3. 사용자가 `코딩해줘` 입력
4. 백엔드 `POST /api/assistant/chat` 호출
5. `edit_streamlit_program` intent로 분류
6. Python 코드 블록 생성
7. 프론트가 코드 블록을 추출
8. `assistant-apply-code` 이벤트 발생
9. `StreamlitAppBuilder`가 이벤트를 수신해 선택된 프로그램 코드 교체

### 4.3 현재 실행 URL

현재 `코딩 실행` 버튼은 실제 서버 실행이 아니라 URL 문자열만 만든다.

```text
http://127.0.0.1:8501/?app={slug}
```

이 URL은 현재 반드시 실패한다. `8501` 서버가 없기 때문이다.

---

## 5. Claude Code에게 요청할 작업

## 작업 1. Streamlit 앱 저장/실행 백엔드 API 구현

### 목표

`코딩 실행` 버튼 클릭 시 실제로 접속 가능한 URL을 반환해야 한다.

### 권장 API

```http
POST /api/streamlit-apps/run
```

요청:

```json
{
  "app_id": "stapp-xxxx",
  "folder_name": "공장 자동화",
  "file_name": "test3.py",
  "code": "import streamlit as st\n..."
}
```

응답:

```json
{
  "app_id": "stapp-xxxx",
  "status": "running",
  "mode": "streamlit",
  "url": "http://127.0.0.1:8501/?app=test3",
  "file_path": "E:/ontology_edu/X_ont_std/ont_platform/v5/backend/storage/demo-co/proj-01/streamlit_apps/stapp-xxxx/test3.py",
  "message": "Streamlit app is running."
}
```

### 저장 위치

테넌트와 프로젝트별로 분리한다.

```text
ont_platform/v5/backend/storage/{company_id}/{project_id}/streamlit_apps/{app_id}/{file_name}
```

예:

```text
ont_platform/v5/backend/storage/demo-co/proj-01/streamlit_apps/stapp-test3/test3.py
```

---

## 작업 2. Streamlit 패키지 처리

현재 `claud_be`에는 Streamlit이 없다.

선택지는 두 가지다.

### 옵션 A. 실제 Streamlit 설치

```powershell
conda activate claud_be
pip install streamlit
```

그 후 백엔드에서 다음 방식으로 실행한다.

```powershell
python -m streamlit run <file_path> --server.port 8501 --server.address 127.0.0.1
```

### 옵션 B. 패키지 없을 때 fallback preview server

Streamlit이 없으면 `8501` 포트에 간단한 HTML preview server를 띄워서 최소한 URL 연결 실패는 막는다.

권장 동작:

```text
streamlit installed
  -> real streamlit run

streamlit not installed
  -> fallback preview page
  -> code preview, 실행 불가 안내, 설치 명령 표시
```

현재 사용자 입장에서는 “URL이 열렸는데 연결 실패”가 가장 나쁜 UX다.  
따라서 실제 Streamlit 실행 전이라도 fallback page는 필요하다.

---

## 작업 3. 프론트 `코딩 실행` 버튼을 API 호출로 변경

현재 위치:

```text
ont_platform/v5/frontend/src/components/StreamlitAppBuilder.tsx
```

현재 동작:

```ts
setRunUrl(`http://127.0.0.1:8501/?app=${encodeURIComponent(slug)}`);
```

변경 후:

```text
api.streamlitApps.run(...)
  -> 백엔드가 file 저장
  -> 서버 실행
  -> 실제 url 반환
  -> runUrl에 반영
```

필요 타입:

```ts
export interface StreamlitRunRequest {
  app_id: string;
  folder_name: string;
  file_name: string;
  code: string;
}

export interface StreamlitRunResponse {
  app_id: string;
  status: "running" | "fallback" | "error";
  mode: "streamlit" | "fallback";
  url: string;
  file_path: string;
  message: string;
}
```

---

## 작업 4. 포트 관리

단일 MVP에서는 `8501` 고정 포트를 사용해도 된다.

하지만 기존 실행 프로세스가 있으면 다음 중 하나를 해야 한다.

1. 기존 Streamlit 프로세스 종료 후 재실행
2. 기존 프로세스 재사용
3. 다음 포트 사용

권장 MVP:

```text
8501 포트 사용 가능 -> 8501 사용
8501 사용 중이고 같은 app -> 재사용
8501 사용 중이고 다른 app -> 8502, 8503 순차 탐색
```

응답에는 실제 사용 포트를 포함한다.

```json
{
  "url": "http://127.0.0.1:8502/?app=test3",
  "port": 8502
}
```

---

## 작업 5. 실행 상태 UI 보완

`StreamlitAppBuilder.tsx`에서 다음 상태를 보여준다.

- 저장 중
- 실행 중
- 실행 완료
- fallback preview
- 실행 실패

예:

```text
실행 완료
http://127.0.0.1:8501/?app=test3
```

실패 예:

```text
Streamlit 패키지가 설치되어 있지 않아 fallback preview로 열었습니다.
pip install streamlit 후 다시 실행하면 실제 앱으로 실행됩니다.
```

---

## 6. 주의할 점

### 6.1 고객사/공장 모의 서버는 건드리지 말 것

이 작업은 AI 코딩 에이전트와 Streamlit 앱 빌더 작업이다.

다음 외부 모의 서버는 수정하지 않는다.

```text
mock_infras/
s1_customer_board
s1_customer_mcp
s2_factory_board
s2_factory_mcp
```

### 6.2 기존 워크플로우/온톨로지 기능 회귀 금지

다음 기능은 이미 시나리오 데모에서 사용 중이다.

- 워크플로우 빌더/실행
- 온톨로지 매핑
- 공장 자동화 댓글 등록
- 고객사 댓글 등록
- 스킬 관리

Streamlit 앱 빌더 작업 중 위 기능을 변경하지 않는다.

### 6.3 저장 경로는 반드시 tenant/project 분리

잘못된 예:

```text
backend/storage/streamlit_apps/test3.py
```

올바른 예:

```text
backend/storage/demo-co/proj-01/streamlit_apps/stapp-test3/test3.py
```

---

## 7. 검증 방법

### 7.1 프론트 타입 검사

```powershell
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npx tsc --noEmit
```

### 7.2 백엔드 컴파일

```powershell
cd E:\ontology_edu\X_ont_std
python -m py_compile ont_platform\v5\backend\app\api\assistant.py `
  ont_platform\v5\backend\app\models\assistant.py `
  ont_platform\v5\backend\app\services\assistant_service.py
```

Streamlit API를 새로 만들면 해당 파일도 추가한다.

### 7.3 시나리오 검증

1. `ont_platform v5 backend` 기동
2. `ont_platform v5 frontend` 기동
3. 좌측 메뉴에서 `앱 빌더 > Streamlit 앱`
4. 폴더 생성
5. 프로그램 생성
6. 편집창 선택
7. Assistant에 `코딩해줘` 입력
8. 편집창에 코드 자동 반영 확인
9. `코딩 실행` 클릭
10. 반환된 URL 클릭
11. `페이지에 연결할 수 없습니다`가 나오지 않아야 함

---

## 8. 현재 가장 먼저 할 일

Claude Code는 다음 순서로 작업하면 된다.

1. `POST /api/streamlit-apps/run` 백엔드 API 추가
2. 코드 저장 위치 구현
3. `streamlit` 설치 여부 감지
4. 설치되어 있으면 실제 `streamlit run`
5. 없으면 fallback preview server라도 실행
6. 프론트 `StreamlitAppBuilder.tsx`의 `runSelectedProgram()`을 API 호출로 변경
7. URL 클릭 시 연결 실패가 사라지는지 확인

---

## 9. 한 줄 요약

현재 MVP는 “챗봇이 선택된 Streamlit 편집창에 코드를 작성하는 화면 경험”까지 구현되었다.  
남은 핵심은 “그 코드를 실제 파일로 저장하고 Streamlit 서버로 실행해서 URL이 열리게 만드는 백엔드 실행 계층”이다.
