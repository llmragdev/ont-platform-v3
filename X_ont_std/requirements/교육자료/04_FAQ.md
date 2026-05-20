# 04. FAQ — 자주 막히는 지점

## 환경 셋업

**Q1. `conda env create -f environment.yml`에서 멈춤**
- 인터넷 연결 / 사내 프록시 확인 (`HTTP_PROXY`, `HTTPS_PROXY`)
- 또는 conda 채널 충돌 — `conda config --set channel_priority flexible`

**Q2. `pip install`에서 SSL 인증서 오류**
- 사내망 SSL inspection 인증서를 추가하거나, 사외망에서 환경 만든 뒤 가져오기.

**Q3. `npm install`이 unrs-resolver postinstall에서 죽음**
- `npm install --ignore-scripts` 사용 (README와 동일).
- 또는 conda env의 node를 PATH에 명시적으로 추가:
  ```powershell
  $env:Path = "C:\Users\<you>\anaconda3\envs\claud_fe;" + $env:Path
  ```

**Q4. 한글 폴더(`claud_통합`)에서 npm 캐시 오류**
- 임시로 `claud_unified`로 리네임 후 진행.

## 백엔드

**Q5. `pytest`에서 `from app.main import app` ImportError**
- 반드시 `backend/` 디렉토리 안에서 실행.

**Q5-1. PowerShell에서 `curl -X POST ...` 가 "매개 변수 'X'를 찾을 수 없습니다" 에러**
- PowerShell의 `curl`은 `Invoke-WebRequest` 별칭이라 진짜 curl 플래그(`-X`, `-d` 등)를 못 받습니다.
- 둘 중 하나로 해결:
  ```powershell
  # 옵션 A — PowerShell 네이티브 (응답이 자동 JSON 파싱됨)
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/system/reset

  # 옵션 B — 진짜 curl 강제 호출 (Windows 10/11 기본 설치)
  curl.exe -X POST http://localhost:8000/api/system/reset
  ```

**Q6. `python -m uvicorn app.main:app` 띄웠는데 `/api/health` 응답 없음**
- 다른 프로세스가 8000 점유 중일 수 있음:
  ```powershell
  netstat -ano | findstr :8000
  ```
- 다른 포트로:
  ```powershell
  python -m uvicorn app.main:app --reload --port 8001
  ```

**Q7. `/api/health.llm.provider`가 `rule-based`인데 키는 있음**
- dotenv가 키를 못 읽음. 점검:
  ```powershell
  python -c "import os; from dotenv import load_dotenv; load_dotenv('F:/ai_std_dev/.env'); print(os.environ.get('GEMINI_API_KEY'))"
  ```
- 파일이 UTF-8 (BOM 없이)인지 확인.

**Q8. Gemini 호출 시 `429 RESOURCE_EXHAUSTED`**
- 무료 티어 일일 한도 초과.
- 응답 자체는 룰베이스로 자동 폴백되니 데모는 진행 가능.
- 즉시 정상 답변이 필요하면 `GEMINI_API_KEY2/3/4` 중 다른 키 환경변수에 직접 주거나, 1분~24시간 후 재시도.
- `/api/health.llm.stats`로 어느 키가 한도 도달했는지 확인.

## 프론트엔드

**Q9. `/`에 접속했더니 "데이터 가져오기 실패" 메시지**
- 백엔드(8000)가 떠 있는지 먼저 확인.
- `.env.local`의 `NEXT_PUBLIC_API_BASE`가 정확히 `http://localhost:8000`인지 (마지막 슬래시 없음).

**Q10. 사용자 셀렉터를 바꿔도 표가 그대로**
- React state 갱신 누락 가능. `npm run dev` 콘솔에 에러 있는지 확인.
- 가장 빠른 해결: 페이지 새로고침 (F5).

**Q11. Playwright `npm run test:e2e` 첫 실행 실패**
- Chromium 바이너리 없음. 1회만:
  ```powershell
  npx playwright install chromium
  ```
- 백엔드(8000)가 떠 있는지 확인. 프론트(3100)는 Playwright가 자동 기동.

## 코드/디자인

**Q12. 시나리오 추가하려는데 어디서부터 시작?**
- 백엔드 시나리오: [backend/eval/scenarios.py](../../claud_통합/backend/eval/scenarios.py) 의 함수를 복제.
- 프론트엔드 E2E: [frontend/e2e/scenarios.spec.ts](../../claud_통합/frontend/e2e/scenarios.spec.ts) 의 test() 블록 복제.

**Q13. `pytest` 통과하는데 evaluate가 실패**
- pytest는 단위/API 테스트, evaluate는 통합 검증. evaluate의 `notes` 필드를 보면 어느 단계에서 깨졌는지 표시됨.
- `python evaluate.py --json` 후 `eval/evaluate-*.json` 열어서 실패한 케이스의 `notes`/`actual` 확인.

**Q14. 인메모리 상태가 자꾸 초기화돼서 데모 어려움**
- `/api/system/reset` POST를 호출하지 않으면 서버가 떠 있는 동안 상태 유지됨.
- 영구 저장이 필요하면 `ONTOLOGY_DATA_PATH=./data/ontology.json` 환경변수 설정 (JsonFileDataRepository 사용).

## 학습 흐름

**Q15. 8단계 trace 중 어디서 막혔는지 모르겠음**
- `/api/ask` 응답의 `steps` 배열을 보면 마지막 success step + 그 다음에 실패. 응답에 `error_code`가 있으면 `errors.py`의 코드 상수로 위치 추정.

**Q16. 강의 끝나고 운영형으로 넘어가려면?**
- [NEXT_STEPS.md](../../claud_통합/NEXT_STEPS.md) #6 (Postgres) → #7 (JWT) → #8 (OTel) → #9 (Docker) 순서.
