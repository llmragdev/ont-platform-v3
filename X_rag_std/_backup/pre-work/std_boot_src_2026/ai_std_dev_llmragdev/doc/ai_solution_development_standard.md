# AI Solution 개발 표준

기준 파일: `F:\ai_std_dev\ai_std_dev5\src\mainSolnApp.py`

이 문서는 `mainSolnApp.py`의 FastAPI 실행 구조를 기준으로 AI Solution/RAG API 개발 시 따라야 할 기본 표준을 정의한다.

## 1. 애플리케이션 구조 표준

Solution 애플리케이션은 다음 계층을 기준으로 구성한다.

```text
src/
  mainSolnApp.py                  # Solution API 서버 진입점
  soln/
    qabot/
      app/
        qaApp.py                  # FastAPI Router, Endpoint 정의
      biz/
        qaBiz.py                  # 업무 로직, RAG 응답 생성
      repository/
        qaRpo.py                  # Vector DB, 문서 로딩, 저장소 접근
      schemas/
        qaSch.py                  # Request/Response/Settings 스키마
```

계층별 책임은 다음과 같다.

| 계층 | 역할 | 주요 규칙 |
|---|---|---|
| `mainSolnApp.py` | FastAPI 앱 생성, 환경 로드, 라우터 등록, 서버 실행 | 비즈니스 로직을 직접 작성하지 않는다. |
| `app` | API endpoint와 router 정의 | 요청을 받고 `biz` 계층으로 위임한다. |
| `biz` | 업무 흐름 제어, 프롬프트 구성, LLM 호출 | 저장소 세부 구현은 `repository`에 위임한다. |
| `repository` | 파일, Vector DB, 외부 저장소 접근 | API 요청/응답 모델을 직접 다루지 않는다. |
| `schemas` | Pydantic 모델, 설정 모델 정의 | 입출력 계약을 명확히 관리한다. |

## 2. FastAPI 진입점 표준

`mainSolnApp.py`는 다음 형태를 기본으로 한다.

```python
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from soln.qabot.app import qaApp

app = FastAPI(
    title="AI Standard Solution",
    description="AI Standard Solution RAG API",
    version="1.0.0",
)

app.include_router(qaApp.router, prefix="/soln/qabot")

if __name__ == "__main__":
    uvicorn.run("mainSolnApp:app", host="0.0.0.0", port=8002, reload=True)
```

개발 기준:

- `.env`는 다른 모듈 import 전에 `load_dotenv()`로 먼저 로드한다.
- `mainSolnApp.py`에는 앱 생성, 라우터 등록, 실행 설정만 둔다.
- 라우터 prefix는 기능 도메인을 표현하도록 `/soln/{module}` 형식으로 작성한다.
- Solution API 기본 포트는 `8002`를 사용한다.
- 운영 배포에서는 `reload=True`를 사용하지 않는다.

## 3. API 라우터 표준

라우터 파일은 `soln/qabot/app/qaApp.py`처럼 작성한다.

```python
from fastapi import APIRouter
from soln.qabot.biz.qaBiz import QaBizService
from soln.qabot.schemas.qaSch import QaRequest

router = APIRouter()
biz = QaBizService()

@router.post("/admin/ingest")
async def ingest_assets():
    return await biz.ingest_assets()

@router.post("/ask")
async def direct_qa(req: QaRequest):
    return await biz.ask_with_rag(req)
```

개발 기준:

- endpoint 함수는 얇게 유지하고, 실제 처리는 `biz` 서비스로 위임한다.
- 요청 본문은 Pydantic request schema로 받는다.
- 응답은 `biz` 계층에서 response schema 형태로 반환한다.
- 관리성 API는 `/admin/...` 하위 경로로 분리한다.

현재 기준 API:

| Method | Path | 설명 |
|---|---|---|
| `POST` | `/soln/qabot/admin/ingest` | 문서 ingest 및 vector DB 생성 |
| `POST` | `/soln/qabot/ask` | RAG 기반 질의응답 |

## 4. Biz 서비스 표준

`biz` 계층은 업무 흐름을 조립한다.

주요 책임:

- repository 초기화
- RAG 검색 결과 정렬
- LLM 프롬프트 구성
- LLM 호출
- response schema 생성

개발 기준:

- 외부 저장소나 vector DB 접근은 `repository`를 통해 수행한다.
- LLM 모델명, API Key 등은 환경변수에서 읽는다.
- 프롬프트는 context와 question이 명확히 분리되도록 작성한다.
- async endpoint에서 호출되는 함수는 `async def`로 작성한다.
- 검색 결과는 사용자가 확인할 수 있도록 source 정보와 함께 반환한다.

## 5. Repository 표준

`repository` 계층은 저장소 접근을 담당한다.

현재 기준 구현:

- `Chroma` vector DB 사용
- `GoogleGenerativeAIEmbeddings` embedding 사용
- `PyPDFLoader`로 PDF 문서 로드
- `RecursiveCharacterTextSplitter`로 chunk 분할

개발 기준:

- 저장 경로는 코드에 고정하지 말고 환경변수로 제어한다.
- vector DB 인스턴스는 lazy loading 방식으로 초기화할 수 있다.
- ingest 시 기존 DB 삭제, 문서 로딩, chunk 생성, DB 저장 단계를 분리한다.
- Windows 콘솔 호환을 위해 로그에는 이모지보다 `[OK]`, `[ERROR]` 같은 ASCII prefix를 사용한다.
- 예외 발생 시 최소한의 원인 로그를 출력하고 실패 상태를 반환한다.

## 6. Schema 및 설정 표준

Pydantic 모델은 `schemas` 계층에 둔다.

기준 모델:

```python
class QaRequest(BaseModel):
    question: str
    user_id: str = "guest"

class QaResponse(BaseModel):
    answer: str
    source_documents: Optional[List[str]] = []
    status: str = "success"

class IngestResponse(BaseModel):
    status: str
    message: str
```

설정 모델은 `pydantic-settings`의 `BaseSettings`를 사용한다.

개발 기준:

- request/response 필드는 API 계약이므로 이름 변경 시 호출부 영향도를 확인한다.
- 환경변수 alias는 명시적으로 지정한다.
- `.env` 경로는 프로젝트 공통 위치를 기준으로 관리한다.
- 민감정보는 코드에 직접 작성하지 않는다.

필수 패키지:

```powershell
pip install pydantic-settings
```

## 7. 환경변수 표준

`F:\ai_std_dev\.env`를 기준으로 환경변수를 관리한다.

주요 환경변수:

| 변수 | 설명 |
|---|---|
| `GEMINI_API_KEY` | Gemini API Key |
| `LLM_MODEL_NAME` | LLM 모델명 |
| `SOURCE_DOC_DIR5` | RAG 원천 문서 경로 |
| `VECTOR_DB_BASE_PATH5` | Vector DB base 경로 |
| `VECTOR_DB_NAME5` | Vector DB 이름 |
| `CORE_INFERENCE_URL5` | Core LLM API URL |
| `STATIC_DB_PATH` | Chroma DB 저장 경로 |
| `SOURCE_RAW_DIR` | 원천 PDF 문서 경로 |

개발 기준:

- 로컬 경로는 `.env`로 분리한다.
- 환경별 값은 `.env`, `.env.dev`, `.env.prod`처럼 분리할 수 있다.
- API Key는 Git에 커밋하지 않는다.

## 8. 실행 표준

개발 환경 활성화:

```powershell
conda activate ai-std-dev7
```

Solution API 실행:

```powershell
cd F:\ai_std_dev\ai_std_dev5\src
python .\mainSolnApp.py
```

API 문서 확인:

```text
http://127.0.0.1:8002/docs
```

RAG ingest 호출 예시:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8002/soln/qabot/admin/ingest"
```

RAG 질문 호출 예시:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8002/soln/qabot/ask" `
  -ContentType "application/json" `
  -Body '{"question":"AI 바우처 사업의 지원 대상은?","user_id":"guest"}'
```

## 9. 포트 표준

현재 프로젝트 기준 포트는 다음처럼 분리한다.

| 앱 | 파일 | 포트 |
|---|---|---|
| Core LLM API | `mainCoreApp.py` | `8001` |
| Solution RAG API | `mainSolnApp.py` | `8002` |
| Extension API | `mainExtnApp.py` | `8050` |

새 API 서버를 추가할 때는 기존 포트와 충돌하지 않도록 별도 포트를 지정한다.

## 10. 네이밍 표준

파일 네이밍:

| 유형 | 규칙 | 예시 |
|---|---|---|
| App Router | `{domain}App.py` | `qaApp.py` |
| Business Service | `{domain}Biz.py` | `qaBiz.py` |
| Repository | `{domain}Rpo.py` | `qaRpo.py` |
| Schema | `{domain}Sch.py` | `qaSch.py` |

클래스 네이밍:

| 유형 | 규칙 | 예시 |
|---|---|---|
| Service | `{Domain}BizService` | `QaBizService` |
| Repository | `{Domain}Repository` | `QaRepository` |
| Request | `{Domain}Request` | `QaRequest` |
| Response | `{Domain}Response` | `QaResponse` |

## 11. 로그 표준

Windows PowerShell 기본 인코딩에서도 깨지지 않도록 로그 prefix는 ASCII를 사용한다.

권장:

```python
print("[OK] Repository initialized")
print("[ERROR] RPO Save Error: ...")
print("[INFO] Starting Solution API")
```

비권장:

```python
print("✅ 초기화 완료")
print("❌ 에러")
```

## 12. 개발 체크리스트

새 기능을 추가할 때 다음 순서로 작업한다.

1. `schemas`에 request/response 모델을 정의한다.
2. `repository`에 저장소 또는 외부 시스템 접근 로직을 작성한다.
3. `biz`에 업무 흐름과 응답 생성 로직을 작성한다.
4. `app`에 endpoint를 추가한다.
5. `mainSolnApp.py`에 필요한 router prefix를 등록한다.
6. `.env`에 필요한 설정값을 추가한다.
7. `/docs`에서 API 스펙을 확인한다.
8. PowerShell 또는 API client로 ingest/ask 흐름을 검증한다.

## 13. 오류 대응 기준

자주 발생하는 오류와 대응:

| 오류 | 원인 | 대응 |
|---|---|---|
| `ModuleNotFoundError: pydantic_settings` | `pydantic-settings` 미설치 | `pip install pydantic-settings` |
| `UnicodeEncodeError: cp949` | 콘솔이 이모지 출력 불가 | 로그를 ASCII로 변경 |
| `GEMINI_API_KEY` 오류 | `.env` 누락 또는 키 오류 | `F:\ai_std_dev\.env` 확인 |
| Vector DB 경로 오류 | 저장 경로 미존재 또는 권한 문제 | `STATIC_DB_PATH`, `VECTOR_DB_BASE_PATH5` 확인 |
| API 404 | router prefix 또는 endpoint 경로 불일치 | `/docs`에서 실제 경로 확인 |

## 14. 향후 개선 권장사항

- `QaBizService()`를 전역 인스턴스로 만들기보다 FastAPI dependency로 관리한다.
- `class Config` 대신 Pydantic v2의 `model_config` 사용을 검토한다.
- source document 파일명을 환경변수 또는 설정 파일로 분리한다.
- `print()` 대신 `logging` 모듈을 적용한다.
- 깨진 한글 주석과 문자열은 UTF-8 기준으로 복구한다.
- ingest, ask API에 최소 단위 테스트를 추가한다.

## 15. Streamlit 앱 개발 표준

Streamlit 기반 내부 도구도 API 프로젝트와 같은 계층 기준을 따른다.

기준 구조:

```text
ai_std_dev_llmragdev/
  mainUserInfoStreamlitApp.py
  userinfo/
    app/
      userInfoApp.py
    biz/
      userInfoBiz.py
    repository/
      userInfoRpo.py
    schemas/
      userInfoSch.py
```

계층별 책임:

| 계층 | 역할 | 규칙 |
|---|---|---|
| `main...StreamlitApp.py` | Streamlit 진입점 | `st.set_page_config()`와 화면 렌더 함수 호출만 둔다. |
| `app` | 화면 구성 | Streamlit widget, dataframe, button, error 표시를 담당한다. |
| `biz` | 업무 흐름 | 화면 입력을 schema로 정리하고 repository를 호출한다. |
| `repository` | DB 접근 | SQLAlchemy engine/session/query를 담당한다. |
| `schemas` | 설정/입출력 모델 | `BaseSettings`, `BaseModel`로 계약을 정의한다. |

Streamlit 개발 규칙:

- DB 연결 서비스는 `st.cache_resource`로 캐시한다.
- 화면 코드는 SQLAlchemy 세부 구현을 직접 알지 않게 한다.
- 조회 결과는 `pandas.DataFrame`으로 변환한 뒤 `st.dataframe`에 표시한다.
- 사용자에게 보여줄 오류는 `st.error()`로 처리한다.
- 조회 결과가 없을 때는 `st.info()`로 안내한다.
- 파일 다운로드가 필요한 경우 `st.download_button()`을 사용한다.

## 16. DB 개발 표준

DB 접속 정보는 반드시 `.env`에서 읽는다.

기준 파일:

```text
F:\ai_std_dev\.env
```

필수 환경변수:

```text
DATABASE_URL=postgresql://...
```

DB 접근 표준:

- DB URL, 비밀번호, API Key는 코드에 직접 작성하지 않는다.
- SQLAlchemy `create_engine()` 사용 시 `pool_pre_ping=True`를 권장한다.
- session은 `try/finally`로 반드시 닫는다.
- query 조건은 repository에서 처리한다.
- app 계층에서 SQLAlchemy model이나 session을 직접 사용하지 않는다.
- 테이블 컬럼은 schema 모델로 변환해서 biz/app 계층에 전달한다.

사용자 정보 조회 기준 테이블:

```text
temp_users
```

기준 컬럼:

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | Integer | 사용자 ID |
| `name` | String | 사용자 이름 |
| `email` | String | 이메일 |
| `created_at` | DateTime | 생성일시 |

Pydantic schema 기준:

```python
class UserInfoRead(BaseModel):
    user_id: int = Field(validation_alias="id")
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
```

## 17. 사용자 정보 조회 프로그램 표준

현재 사용자 정보 조회 프로그램은 다음 요구사항을 기본으로 한다.

- Streamlit으로 실행한다.
- PostgreSQL의 `temp_users` 테이블을 조회한다.
- 이름 또는 이메일 검색을 지원한다.
- 최대 조회 건수를 제한한다.
- 조회 건수, 검색어, 표시 제한을 metric으로 보여준다.
- 결과를 표 형태로 보여준다.
- CSV 다운로드를 지원한다.

실행 명령:

```powershell
conda activate ai-std-dev7
cd F:\ai_std_dev\ai_std_dev_llmragdev
streamlit run .\mainUserInfoStreamlitApp.py
```

검증 명령:

```powershell
python -m py_compile `
  .\mainUserInfoStreamlitApp.py `
  .\userinfo\app\userInfoApp.py `
  .\userinfo\biz\userInfoBiz.py `
  .\userinfo\repository\userInfoRpo.py `
  .\userinfo\schemas\userInfoSch.py
```

DB 조회 검증:

```powershell
python -c "from userinfo.biz.userInfoBiz import UserInfoBizService; svc=UserInfoBizService(); print(svc.get_summary(None).total_count); print(len(svc.search_users(None, 5)))"
```

관련 문서:

```text
F:\ai_std_dev\ai_std_dev_llmragdev\doc\바이브코딩가이드.md
F:\ai_std_dev\ai_std_dev_llmragdev\doc\실행 가이드.md
```
