# Antigravity Platform 실행 가이드

본 프로젝트는 온톨로지 중심의 유연한 아키텍처를 시연하기 위해 백엔드(FastAPI)와 프론트엔드(Next.js)로 구성되어 있습니다.

## 1. 백엔드 실행
환경 활성화 단계 없이 아래 명령어를 터미널에 복사하여 붙여넣으세요.
```powershell
cd E:\ontology_edu\antigravity_platform\project\src\backend

# 전용 가상환경 생성 (최초 1회)
# conda create -n anti_be python=3.10 -y

# 패키지 설치 (최초 1회 또는 업데이트 시)
conda run -n anti_be pip install -r requirements.txt

# 백엔드 서버 시작
conda run -n anti_be python -m uvicorn app.main:app --reload --port 8000
```

## 2. 프론트엔드 실행
환경 활성화 단계 없이 아래 명령어를 터미널에 복사하여 붙여넣으세요.
```powershell
cd E:\ontology_edu\antigravity_platform\project\src\frontend

# 전용 가상환경 생성 (최초 1회)
# conda create -n anti_fe nodejs=20 -y

# 패키지 설치 (최초 1회)
conda run -n anti_fe npm install

# 프론트엔드 서버 시작
conda run -n anti_fe npm run dev
```

## 3. 확인 방법
- 브라우저에서 `http://localhost:3000` 접속
- 중앙의 **하이브리드 질의 콘솔**을 통한 온톨로지 탐색 및 RAG 질의
- 사이드바 메뉴를 통해 **온톨로지 설정** 및 **Q&A 문서 업로드** 관리

---
### 🛠️ 주요 특징
- **Premium Mesh Gradient**: 은은하게 움직이는 배경으로 엔터프라이즈급 감성 유지
- **Hybrid Query Console**: 자연어 질의와 온톨로지 계획을 시각적으로 결합
- **Framer Motion UX**: 모든 인터페이스 요소에 부드러운 애니메이션 적용
- **Multi-Tenant Ready**: 테넌트 간 물리적 격리 및 보안 정책 반영 (준비 중)

### 💡 문제 해결 (Troubleshooting)
- **CondaError**: `conda run` 사용 시 활성화 오류가 발생하지 않습니다.
- **npm Not Found**: `conda create -n anti_fe nodejs=20` 명령어로 Node.js가 포함된 가상환경을 먼저 생성해 주세요.
