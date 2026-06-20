# 공장 모의 게시판 시스템 구동 매뉴얼 (s2_factory_board)

시나리오 2 (공장 반복 고장 흐름) 연동 테스트 및 시연을 위한 SQLite 기반 공장 모의 게시판 시스템의 서버 구동 방법 안내서입니다.

---

## ⚙️ 1. 사전 요구사항 및 환경 구성
* **Python 버전**: Python 3.10 이상 권장
* **가상환경**: Anaconda/Conda 사용을 권장하며, 사전에 구축된 `claud_be` 환경을 활성화하여 사용합니다.
* **주요 종속성**:
  * `fastapi`
  * `uvicorn`
  * `pydantic`
  * `sqlite3` (Python 내장 라이브러리)

---

## 🚀 2. 서버 구동 방법 (Run Server)

### 2.1 콘솔/터미널 실행
PowerShell 혹은 CMD 터미널을 열고 다음 명령어를 순서대로 실행합니다.

```powershell
# 1. 가상환경 활성화
conda activate claud_be

# 2. 프로젝트 디렉토리로 이동
cd E:\ontology_edu\X_ont_std\mock_infras\s2_factory_board

# 3. FastAPI/Uvicorn 서버 기동
python src/main.py
```

* **구동 확인**: 콘솔창에 다음과 같은 로그가 출력되면 성공적으로 시작된 것입니다.
  ```text
  INFO:     Started server process [54321]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8091 (Press CTRL+C to quit)
  ```

---

## 🖥️ 3. 접속 및 구동 확인 방법
* **웹 브라우저 접속 (사용자 UI)**:
  * URL: [http://localhost:8091](http://localhost:8091)
  * 설명: 브라우저로 접속 시 오렌지/앰버 색상의 다크모드 공장 모의 대시보드 화면이 표시됩니다.
  * 기능: 현장 고장 요청 목록 조회, 상세 설명 및 정비 지시서 모니터링, 실시간 웹훅 설정 변경 및 수동 데모 고장 주입 버튼을 통한 시연이 가능합니다.
* **로컬 DB 파일 자동 생성**:
  * 서버 구동 시 프로젝트 루트 폴더에 `s2_factory_board.db` SQLite 파일이 자동으로 빌드되고 초기 테스트 데이터(시드 고장 1건, 기본 피드백 댓글 1건)가 인입됩니다.
