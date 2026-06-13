# ont_platform v5 Runbook

작성일: 2026-06-12

## 기준 실행 방법

v5는 backend와 frontend를 각각 conda 가상환경에서 실행한다.

- Backend conda env: `claud_be`
- Frontend conda env: `claud_fe`
- Backend port: `8001`
- Frontend port: `3002`

## Backend 실행

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m uvicorn app.main:app --reload --port 8001
```

정상 확인:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8001/api/health
```

브라우저 또는 API 문서:

```text
http://localhost:8001/docs
```

## Frontend 실행

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run dev
```

접속 URL:

```text
http://localhost:3002
```

`frontend/package.json`의 현재 설정은 다음과 같다.

```json
{
  "dev": "next dev -p 3002"
}
```

따라서 일반 실행은 `npm run dev`만 사용하면 된다.

## 최초 준비

Backend 패키지 설치:

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m pip install -r requirements.txt
```

Frontend 패키지 설치:

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm install
```

## 스크립트 실행 방식

스크립트도 존재하지만, 혼동을 줄이기 위해 현재 기준은 직접 실행 방식이다.

Backend script:

```powershell
conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5
.\scripts\start_backend.ps1
```

Frontend script:

```powershell
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5
.\scripts\start_frontend.ps1
```

주의:

- `frontend` 폴더 안에서 `.\scripts\start_frontend.ps1`을 실행하면 파일을 찾지 못한다.
- script를 쓰려면 반드시 `E:\ontology_edu\X_ont_std\ont_platform\v5` 위치에서 실행한다.
- 가장 권장하는 방법은 위의 Backend/Frontend 직접 실행 명령이다.

## 자주 나는 오류

### Backend import string 오류

잘못된 예:

```powershell
python -m uvicorn app.main
```

정상 명령:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### Frontend 포트 충돌

오류:

```text
EADDRINUSE: address already in use :::3002
```

확인:

```powershell
Get-NetTCPConnection -LocalPort 3002 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
```

강제 종료:

```powershell
Stop-Process -Id <OwningProcess> -Force
```

### conda 환경 확인

Backend:

```powershell
conda activate claud_be
python -c "import sys; print(sys.executable)"
```

예상 경로:

```text
C:\Users\nkchoi2\anaconda3\envs\claud_be\python.exe
```

Frontend:

```powershell
conda activate claud_fe
node -v
npm -v
```

## 현재 active 개발 범위

현재 v5의 긴급 P0 범위는 다음이다.

```text
customer question
  -> LLM webhook generates reply message
  -> v5 calls customer MCP server
  -> customer MCP server calls customer API
  -> v5 stores result/audit
```

고객사 MCP 서버는 고객사 영역이다. v5는 고객사 MCP 서버를 호출하는 extn adapter까지만 책임진다.
