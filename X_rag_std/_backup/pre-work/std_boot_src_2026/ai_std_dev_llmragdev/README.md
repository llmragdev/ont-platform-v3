# User Info Streamlit App

`F:\ai_std_dev\ai_std_dev_llmragdev\doc\ai_solution_development_standard.md`의 계층 표준을 따라 만든 사용자 정보 조회 Streamlit 앱입니다.

## 실행

```powershell
conda activate ai-std-dev7
cd F:\ai_std_dev\ai_std_dev_llmragdev
streamlit run .\mainUserInfoStreamlitApp.py
```

## 필요 패키지

```powershell
pip install -r .\requirements.txt
```

## 데이터 기준

- `.env` 위치: `F:\ai_std_dev\.env`
- DB 환경변수: `DATABASE_URL`
- 조회 테이블: `temp_users`
- 조회 컬럼: `id`, `name`, `email`, `created_at`
