# 고객사 모의 게시판 시스템 구동 매뉴얼 (s1_customer_board)

시나리오 1 연동 테스트 및 시연을 위한 SQLite 기반 고객사 모의 게시판 시스템의 서버 구동 방법 안내서입니다.

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
cd E:\ontology_edu\X_ont_std\mock_infras\s1_customer_board

# 3. FastAPI/Uvicorn 서버 기동
python src/main.py
```

* **구동 확인**: 콘솔창에 다음과 같은 로그가 출력되면 성공적으로 시작된 것입니다.
  ```text
  INFO:     Started server process [12345]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8090 (Press CTRL+C to quit)
  ```

---

## 🖥️ 3. 접속 및 구동 확인 방법
* **웹 브라우저 접속 (사용자 UI)**:
  * URL: [http://localhost:8090](http://localhost:8090)
  * 설명: 브라우저로 접속 시 3단 프리미엄 대시보드 화면이 표시되어 문의글 확인, 댓글 목록 조회, 실시간 웹훅 연동 온/오프 및 배치 시뮬레이션을 제어할 수 있습니다.
* **로컬 DB 파일 자동 생성**:
  * 서버 구동 시 프로젝트 루트 폴더에 `s1_customer_board.db` SQLite 파일이 자동으로 빌드되고 초기 테스트 데이터(시드 문의글 2건, 기본 댓글 1건)가 인입됩니다.

---

## 🗂️ 4. 관련 상세 문서 리스트
* [doc/schema.md](file:///E:/ontology_edu/X_ont_std/s1_customer_board/doc/schema.md): 데이터베이스 테이블 명세
* [doc/api_spec.md](file:///E:/ontology_edu/X_ont_std/s1_customer_board/doc/api_spec.md): 제공되는 REST API 규격서
* [doc/architecture.md](file:///E:/ontology_edu/X_ont_std/s1_customer_board/doc/architecture.md): 시스템 컴포넌트 아키텍처 및 통신 플로우 설명
