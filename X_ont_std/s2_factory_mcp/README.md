# 공장 MCP 중계 서버 구동 매뉴얼 (s2_factory_mcp)

`ont_platform v5` 솔루션의 표준 MCP 도구(Tool) 호출을 수신하여 공장 API 구조로 포워딩해주는 중계 서버의 실행 및 검증 매뉴얼입니다.

---

## ⚙️ 1. 사전 요구사항 및 환경 구성
* **Python 버전**: Python 3.10 이상 권장
* **가상환경**: Anaconda/Conda `claud_be` 환경을 활성화하여 사용합니다.
* **주요 종속성**:
  * `fastapi`
  * `uvicorn`
  * `pydantic`
  * `urllib.request` (내장 모듈)

---

## 🚀 2. 서버 구동 방법 (Run Server)

### 2.1 콘솔/터미널 실행
PowerShell 혹은 CMD 터미널을 열고 다음 명령어를 순서대로 실행합니다.

```powershell
# 1. 가상환경 활성화
conda activate claud_be

# 2. 프로젝트 디렉토리로 이동
cd E:\ontology_edu\X_ont_std\s2_factory_mcp

# 3. FastAPI/Uvicorn 서버 기동
python src/main.py
```

* **구동 확인**: 콘솔창에 다음과 같이 Port 8081로 실행되었다는 로그가 정상 출력되면 성공입니다.
  ```text
  INFO:     Started server process [67891]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8081 (Press CTRL+C to quit)
  ```

---

## 🖥️ 3. 연동 확인 및 헬스 체크
* **Health Check API**:
  * URL: [http://localhost:8081/health](http://localhost:8081/health)
  * 정상 응답: `{"status": "ok", "service": "factory_mcp"}`
* **종속성 주의 사항**:
  * 본 중계 서버는 데이터를 직접 보관하지 않고 `s2_factory_board`(Port 8091)로 데이터 처리를 전송합니다. 따라서 원활한 작동을 위해서는 **반드시 게시판 서버가 포트 8091에서 먼저 구동 중이어야 합니다.** 그렇지 않으면 헬스 체크 시 503 오류가 발생할 수 있습니다.
