래처럼 실행하세요.

conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\backend
python -m uvicorn app.main:app --reload --port 8001
프론트는 별도 창에서:

conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v3\src\frontend
npm run dev


# 접속 
http://localhost:3001

--------------------------- 

conda activate claud_be
cd E:\ontology_edu\X_ont_std\ont_platform\v5\backend
python -m uvicorn app.main:app --reload --port 8001

 
# 방법 1: 현재 frontend 폴더에서 직접 실행
 
conda activate claud_fe
cd E:\ontology_edu\X_ont_std\ont_platform\v5\frontend
npm run dev

프론트엔드 URL: 
http://localhost:3002