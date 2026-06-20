# 12. Codex Streamlit 소스 저장 구현 리포트

## 1. 개요

본 구현은 AI Assistant가 생성한 Streamlit Python 코드와 사용자가 편집창에서 수정한 코드를 실제 서버 파일로 저장할 수 있도록 개선한 작업이다.

기존에는 화면의 텍스트 상자에 코드가 보이더라도, 해당 내용이 실제 `.py` 파일로 저장되었는지 명확하지 않았다. 이번 개선으로 `로컬 저장` 버튼과 AI Assistant 코드 적용 흐름이 백엔드 저장 API와 연결되어, 화면 편집 상태와 실제 파일 상태가 일치하도록 했다.

## 2. 구현 목표

- Streamlit 앱 빌더의 텍스트 편집창 내용을 실제 Python 파일로 저장한다.
- AI Assistant가 생성한 코드를 선택된 편집창에 반영한 뒤 실제 파일에도 저장한다.
- 저장 성공/실패 상태와 실제 저장 경로를 화면에 표시한다.
- 기존 `코딩 실행` 기능과 충돌하지 않고, 실행 전 저장만 따로 수행할 수 있게 한다.

## 3. 주요 변경 프로그램

### Backend

| 파일 | 변경 내용 |
|---|---|
| `ont_platform/v5/backend/app/models/streamlit_app.py` | 저장 요청/응답 모델 추가 |
| `ont_platform/v5/backend/app/services/streamlit_app_service.py` | 실행 없이 소스만 저장하는 `save_app()` 추가 |
| `ont_platform/v5/backend/app/api/streamlit_apps.py` | `POST /api/streamlit-apps/save` 엔드포인트 추가 |

### Frontend

| 파일 | 변경 내용 |
|---|---|
| `ont_platform/v5/frontend/src/lib/api.ts` | `api.streamlitApps.save()` 추가 |
| `ont_platform/v5/frontend/src/components/StreamlitAppBuilder.tsx` | 로컬 저장 버튼 API 연결, AI Assistant 코드 적용 후 자동 저장, 저장 상태/경로 표시 |

### Documentation

| 파일 | 변경 내용 |
|---|---|
| `design/AI코딩에이전트/11_Codex_Streamlit_소스_실제저장_구현보고.md` | 작업 상세 보고서 작성 |
| `design/AI코딩에이전트/12_Codex_Streamlit_소스저장_구현리포트.md` | 구현 결과 요약 리포트 작성 |

## 4. 기능 흐름

### 4.1 사용자가 직접 저장하는 경우

1. 사용자가 Streamlit 앱 화면에서 프로그램을 선택한다.
2. Python 편집창에서 코드를 작성하거나 수정한다.
3. `로컬 저장` 버튼을 클릭한다.
4. 프론트엔드는 `POST /api/streamlit-apps/save`를 호출한다.
5. 백엔드는 현재 tenant context 기준으로 실제 `.py` 파일을 저장한다.
6. 화면에는 저장된 실제 파일 경로가 표시된다.

### 4.2 AI Assistant가 코드를 생성하는 경우

1. 사용자가 Streamlit 앱 화면에서 Python 편집창을 선택한다.
2. AI Assistant에 “그래프 그려줘”, “표와 차트 추가해줘” 같은 지시를 입력한다.
3. Assistant가 Python 코드 블록을 포함한 응답을 생성한다.
4. 프론트엔드는 응답 코드 블록을 추출해 선택된 편집창에 반영한다.
5. 동시에 `POST /api/streamlit-apps/save`를 호출해 실제 파일로 저장한다.
6. 화면에는 “AI Assistant 코드가 실제 파일로 저장되었습니다.” 메시지가 표시된다.

## 5. 저장 위치

저장 파일은 tenant와 project 단위로 분리된다.

```text
ont_platform/v5/backend/storage/{company_id}/{project_id}/streamlit_apps/{app_id}/{file_name}
```

예시:

```text
ont_platform/v5/backend/storage/default/proj-default/streamlit_apps/codex-save-smoke/codex_save_smoke.py
```

이 구조는 향후 회사별, 프로젝트별 Streamlit 앱 자산을 분리 관리하기 위한 기본 구조다.

## 6. API 명세

### POST `/api/streamlit-apps/save`

Streamlit 앱 소스를 실행하지 않고 파일로 저장한다.

Request:

```json
{
  "app_id": "factory-repeat-fault-app",
  "folder_name": "공장 자동화",
  "file_name": "factory_repeated_fault_app.py",
  "code": "import streamlit as st\n\nst.title(\"공장 반복 고장 분석\")\n"
}
```

Response:

```json
{
  "app_id": "factory-repeat-fault-app",
  "status": "saved",
  "file_path": "E:\\ontology_edu\\X_ont_std\\ont_platform\\v5\\backend\\storage\\default\\proj-default\\streamlit_apps\\factory-repeat-fault-app\\factory_repeated_fault_app.py",
  "message": "Streamlit app source saved."
}
```

## 7. 검증 결과

### Python 문법 검사

```powershell
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m py_compile app\models\streamlit_app.py app\services\streamlit_app_service.py app\api\streamlit_apps.py
```

결과: 정상 통과

### TypeScript 검사

```powershell
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npx tsc --noEmit
```

결과: 정상 통과

### 저장 API Smoke Test

```powershell
POST http://127.0.0.1:8001/api/streamlit-apps/save
```

결과:

```json
{
  "app_id": "codex-save-smoke",
  "status": "saved",
  "file_path": "E:\\ontology_edu\\X_ont_std\\ont_platform\\v5\\backend\\storage\\default\\proj-default\\streamlit_apps\\codex-save-smoke\\codex_save_smoke.py",
  "message": "Streamlit app source saved."
}
```

## 8. 사용자 관점 개선 효과

- 편집창에 작성한 코드가 실제 파일로 저장되는지 명확해졌다.
- AI Assistant가 생성한 코드가 단순 답변에 머물지 않고 실제 앱 소스로 반영된다.
- `코딩 실행` 전에도 소스를 저장할 수 있어 작업 흐름이 자연스러워졌다.
- 저장된 실제 경로를 화면에서 확인할 수 있어 디버깅과 인수인계가 쉬워졌다.

## 9. 남은 개선 과제

- 텍스트 편집 후 일정 시간 뒤 자동 저장하는 debounce 저장 기능
- 저장된 앱/폴더 목록을 백엔드에서 다시 불러오는 영속 목록 API
- 신규 폴더와 신규 프로그램 메타데이터의 서버 저장
- Streamlit 실행 상태 조회 및 중지 UI 강화
- 저장 파일을 기반으로 외부 공유 URL을 안정적으로 발급하는 기능

## 10. 결론

이번 구현으로 AI 코딩 에이전트의 Streamlit 앱 작성 기능은 “코드 제안” 단계에서 “실제 파일 작성” 단계로 진입했다.

즉, 사용자는 Streamlit 앱 화면에서 편집창을 선택하고 AI Assistant에게 코딩을 요청한 뒤, 생성된 코드를 실제 Python 파일로 저장하고 실행할 수 있다. 이는 향후 온톨로지 질의, 데이터 테이블, Streamlit 앱, 워크플로우를 하나의 플랫폼 안에서 생성하고 운영하는 기반 기능이다.
