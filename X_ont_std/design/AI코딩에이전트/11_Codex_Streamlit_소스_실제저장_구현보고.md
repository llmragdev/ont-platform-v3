# 11. Codex Streamlit 소스 실제 저장 구현 보고

## 작성자

Codex

## 목적

Streamlit 앱 빌더의 Python 편집창에 표시된 소스가 화면 상태에만 머물지 않고, 백엔드 저장소의 실제 `.py` 파일로 작성되도록 구현했다.

## 변경 전 문제

- `코딩 실행`은 실행 과정에서 파일 저장을 수행했지만, 일반 `로컬 저장` 버튼은 실제 API 호출이 없었다.
- AI Assistant가 생성한 Python 코드가 편집창에 반영되어도 브라우저 상태만 변경되고 실제 파일로 즉시 저장되지는 않았다.
- 사용자는 편집창에 코드가 보여도 이 코드가 실제 파일에 작성되었는지 확인하기 어려웠다.

## 구현 내용

### 백엔드

- `app/models/streamlit_app.py`
  - `StreamlitSaveRequest` 추가
  - `StreamlitSaveResponse` 추가

- `app/services/streamlit_app_service.py`
  - `save_app()` 추가
  - 기존 `save_app_code()`를 재사용하여 실행 없이 소스만 저장

- `app/api/streamlit_apps.py`
  - `POST /api/streamlit-apps/save` 추가
  - 현재 tenant context의 `company_id`, `project_id` 기준으로 저장

### 프론트엔드

- `src/lib/api.ts`
  - `api.streamlitApps.save()` 추가

- `src/components/StreamlitAppBuilder.tsx`
  - `로컬 저장` 버튼에 실제 저장 API 연결
  - 저장 중/저장 완료/저장 실패 상태 표시
  - 저장된 실제 파일 경로 표시
  - AI Assistant 코드 적용 이벤트 발생 시 편집창 반영 후 실제 파일 저장까지 자동 수행

## 저장 경로

현재 구현은 아래 구조에 저장한다.

```text
ont_platform/v5/backend/storage/{company_id}/{project_id}/streamlit_apps/{app_id}/{file_name}
```

예:

```text
ont_platform/v5/backend/storage/default/proj-default/streamlit_apps/codex-save-smoke/codex_save_smoke.py
```

## 검증

### Python 문법 검사

```powershell
python -m py_compile app\models\streamlit_app.py app\services\streamlit_app_service.py app\api\streamlit_apps.py
```

결과: 통과

### TypeScript 검사

```powershell
npx tsc --noEmit
```

결과: 통과

### 저장 API Smoke Test

```http
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

## 남은 개선 후보

- 편집창 입력 후 자동 저장 debounce 적용
- 저장된 파일 목록을 백엔드에서 다시 조회하는 API 추가
- 신규 폴더/프로그램 생성 정보도 백엔드 저장소에 영속화
- Streamlit 앱 실행/중지 상태를 화면에서 주기적으로 조회
