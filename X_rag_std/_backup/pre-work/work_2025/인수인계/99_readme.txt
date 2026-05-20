# 챗봇/콜봇 대화엔진 개발서버 
122.49.74.14 
 - 시스템: root / ippbx@IX
  - DB : mysql -h 122.49.74.237 -u eicn -p  
       . root  //  tofhqrpIX
       . eicn / eicnrw

# 챗봇/콜봇 대화엔진 시연용 - API   (238번 화면과 연동 ) 
122.49.74.237  root / ippbx@IX
  - DB : mysql -h 122.49.74.238 -u eicn -p  
       . root  //  tofhqrpIX
       . eicn / eicnrw

# 238번 AI 챗봇/콜봇 관리 웹 
   - 개발은 권용환 대리가 하고 대화엔진과 연동만 확인하면 됩니다. 
   - http://122.49.74.238/login
    - 회사: ubiz  아이디: master 비밀번호: orange90


# 소스 정보 
o 깃 설정 서버 정보 : 122.49.74.5 : git / roqkf@IX
git clone git@122.49.74.5:/opt/git/chat_api.git



========= 콜봇 / 챗봇 대화엔진 소스 위치 
/home/ai/src/chat_api/callbot_api/ 
  - 메인 소스:   /home/ai/src/chat_api/callbot_api/adChat
  - 관리 공통 소스: /home/ai/src/chat_api/callbot_api/mngCallbot
  - Mock API 소스: /home/ai/src/chat_api/callbot_api/adMockServer
  - 운영팀챗봇 API 소스: /home/ai/src/chat_api/callbot_api/opTeam

# 엔진 기동
cd /home/ai/src/chat_api/callbot_api/
./start_ad_adChat.sh
./start_ad_adChat_v2.sh
./start_adMockProdct1Server_app.sh
./start_adMockProdct2Server_mega_app.sh
./start_adMockServer_app.sh
./start_opTeam_app.sh

# 엔진 종료
cd /home/ai/src/chat_api/callbot_api/
./stop_ad_adChat.sh
./stop_ad_adChat_v2.sh
./stop_adMockProdct1Server_app.sh
./stop_adMockProdct2Server_mega_app.sh
./stop_adMockServer_app.sh
./stop_opTeam_app.sh

========================
Ubiz AI 클라우드 서버 IP할당내역입니다.
stt, rag는 공인아이피 부여가 되어있지 않아 다른 서버에서 ssh로 붙어야 합니다

115.178.75.58	192.168.175.12	(sohocrm_web)
115.178.75.59	192.168.175.13	(alasslst_webdb)
115.178.75.60	192.168.175.14	(ca_web)      <========
115.178.75.61	192.168.175.16	(chatbot)     <======== 
115.178.75.62	192.168.175.17	(sohocrm_pbx)
192.168.175.11	(stt)
192.168.175.15	(rag)

# ubiz AI 대화엔진 서버 정보 
 - 115.178.75.61
 - 시스템: root / ippbx@IX

  - DB : mysql -h 115.178.75.61 -u eicn -p  
       . root  //  tofhqrpIX
       . eicn / eicnrw

Ubiz AI 챗봇/콜봇 관리 웹 
https://chatbot.ubizcloud.co.kr/login
ubiz / master / orange90

===============================

# 환경 최신 서버의 라이브러리 환경 파일 생성 
cd /home/ai/src/chat_api
conda env export --no-builds > environment-core-chat.yml

# conda 환경 복제 실행 
cd /home/ai/src/chat_api
conda env create -f environment-core-chat.yml


