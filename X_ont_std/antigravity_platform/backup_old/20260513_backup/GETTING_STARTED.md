# Getting Started (Antigravity-통합)

## 1. 환경 설정
Claude용 환경과 충돌하지 않도록 Antigravity 전용 환경을 생성합니다.

### 백엔드 (Python)
```powershell
cd E:\ontology_edu\Antigravity-통합\backend
conda deactivate
conda create -n anti_be python=3.10 -y
conda activate anti_be
pip install -r requirements.txt
```

### 프론트엔드 (Node.js) - 별도 터미널 
```powershell
cd E:\ontology_edu\Antigravity-통합\frontend
conda deactivate
conda create -n anti_fe nodejs=20 -y
conda activate anti_fe
npm install
```

## 2. 서버 실행
상세 내용은 [LAUNCH_GUIDE.md](../LAUNCH_GUIDE.md)를 참조하세요.

### 서버 1: 백엔드
```powershell
cd backend
conda activate anti_be
python -m uvicorn app.main:app --reload --port 8000
```

### 서버 2: 프론트엔드
```powershell
cd frontend
conda activate anti_fe
npm run dev
```
