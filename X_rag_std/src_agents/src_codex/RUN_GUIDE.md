# src_codex 실행 가이드

이 프로젝트는 `AI_Agent_Mission_Directive.md` 지시에 따라
`E:\ontology_edu\X_rag_std\src_agents\src_codex` 내부에서만 실행되는 독립
FastAPI RAG 백엔드입니다.

## 1. 폴더 기반 conda 가상환경 생성

프로젝트 루트로 이동합니다.

```powershell
cd E:\ontology_edu\X_rag_std\src_agents\src_codex
```

`.conda` 폴더에 전용 환경을 만듭니다.

```powershell
conda env create --prefix .\.conda --file environment.yml
```

이미 환경이 있고 의존성만 갱신하려면 다음을 사용합니다.

```powershell
conda env update --prefix .\.conda --file environment.yml --prune
```

## 2. 가상환경 활성화

```powershell
conda activate .\.conda
```

Python 경로가 프로젝트 내부인지 확인합니다.

```powershell
python -c "import sys; print(sys.executable)"
```

출력 경로가 아래처럼 `.conda`를 포함해야 합니다.

```text
E:\ontology_edu\X_rag_std\src_agents\src_codex\.conda\python.exe
```

## 3. DB 설정

로컬 개발/테스트는 별도 DB 서버 없이 SQLite를 기본 사용합니다.

```powershell
$env:DATABASE_URL = "sqlite:///./storage/metadata.db"
```

운영 DB로 바꿀 때도 소스 수정 없이 환경변수만 바꿉니다.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@host:5432/ragdb"
```

또는:

```powershell
$env:DATABASE_URL = "mysql+pymysql://user:password@host:3306/ragdb"
```

현재 구현은 SQLAlchemy ORM과 Repository 계층을 사용하므로 API/Service 코드는
DB 제품을 직접 알지 않습니다.

## 4. 서버 실행

```powershell
uvicorn main:app --reload --port 8010
```

가상환경 활성화 없이 실행하려면 프로젝트 루트에서 다음을 사용해도 됩니다.

```powershell
.\.conda\python.exe -m uvicorn main:app --reload --port 8010
```

또는 제공 스크립트를 실행합니다.

```powershell
.\scripts\run_server.ps1 -Port 8010
```

브라우저 또는 API 클라이언트에서 확인합니다.

```text
http://localhost:8010/api/v1/health
http://localhost:8010/docs
```

## 5. 문서 업로드 테스트

PowerShell 예시:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$file = "E:\ontology_edu\X_rag_std\src_agents\src_codex\sample.txt"
"인사 규정 문서입니다. 휴가 규정은 연 15일입니다." | Set-Content -Encoding UTF8 $file

curl.exe -X POST "http://localhost:8010/api/v1/documents/upload" `
  -F "file=@$file" `
  -F "category_mid=규정"
```

정상 응답 예:

```json
{
  "status": "success",
  "data": {
    "doc_id": "doc_xxxxxxxx",
    "file_name": "sample.txt",
    "pipeline_status": "completed",
    "assigned_vector_db": "vdb_policy_01"
  },
  "error": null
}
```

PowerShell 또는 콘솔 코드페이지 때문에 한글 form 값이 깨지는 환경에서는
라우팅 별칭인 `policy`, `tech`, `default`를 사용할 수 있습니다.

```powershell
curl.exe -X POST "http://localhost:8010/api/v1/documents/upload" `
  -F "file=@$file" `
  -F "category_mid=policy"
```

## 6. RAG 검색 테스트

`debug_mode`가 `true`이면 후보 청크 전체가 `debug_info.candidate_chunks`에
포함됩니다.

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
curl.exe -X POST "http://localhost:8010/api/v1/rag/search" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"휴가 규정 알려줘\",\"top_k\":3,\"debug_mode\":true,\"filters\":{\"category_mid\":\"규정\"}}"
```

`debug_mode`가 `false`이면 `debug_info`는 `null`입니다.

```powershell
curl.exe -X POST "http://localhost:8010/api/v1/rag/search" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"휴가 규정 알려줘\",\"top_k\":3,\"debug_mode\":false,\"filters\":{\"category_mid\":\"규정\"}}"
```

인코딩 문제가 있으면 `filters.category_mid`도 `policy`로 보냅니다.

## 7. 빠른 자체 검증

```powershell
python -m compileall app main.py
python -c "from main import app; print(app.title)"
```

엔드포인트 자동 테스트:

```powershell
python test_endpoints.py
```

가상환경을 활성화하지 않은 경우:

```powershell
.\.conda\python.exe test_endpoints.py
```

실제 AI바우처 PDF 기준 자동 테스트:

```powershell
.\.conda\python.exe test_ai_voucher_pdf.py
```

이 테스트는 아래 파일을 업로드한 뒤 일반 검색과 디버그 검색을 검증합니다.

```text
E:\ontology_edu\ont_platform\docs\ref_data\01_raw\2025년 AI바우처 사업설명회 발표자료.pdf
```

## 8. 종료

서버는 `Ctrl+C`로 종료합니다.

가상환경 비활성화:

```powershell
conda deactivate
```
