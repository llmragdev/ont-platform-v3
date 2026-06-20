# System Integration Guide (s1_customer_mcp)

`s1_customer_mcp` 중계 서버를 활용하여 `ont_platform` 백엔드 시스템과 통합 연동을 설정하고, 정상 구동 상태를 직접 확인 및 검증하는 통합 연동 가이드 문서입니다.

---

## 🛠️ 1. 환경 변수 및 설정 파일

고객사 MCP 서버는 시스템 기동 시 및 런타임에 다음의 설정 요소를 검토합니다.

| 설정 키 (Config Key) | 기본값 (Default) | 설명 |
| :--- | :--- | :--- |
| `CUSTOMER_MCP_BASE_URL` | `http://localhost:8080` | `ont_platform` 측에서 바라볼 본 중계 서버의 물리 진입 주소 |
| `BOARD_API_URL` | `http://localhost:8090/api/posts` | 실제 고객사 게시판 시스템 API의 기동 경로 (로컬 8090 포트) |
| `CUSTOMER_MCP_TIMEOUT_SECONDS` | `30` | 통신 제한 오버헤드 시간 (초 단위) |

---

## 🧪 2. 연동 스모크 테스트 (PowerShell Command)

정상 설치 및 실행 완료 후 아래의 PowerShell 명령어를 기동하여 연동 규격 호환 여부를 원격으로 즉시 테스트할 수 있습니다.

### 2.1 헬스 체크 테스트
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get
```
* **기대 결과**: `{"status": "ok", "service": "customer_mcp"}`

### 2.2 Dry-run 검증 테스트
실제 저장소 쓰기를 생략하고 데이터 유효성만 체크하는 모드 테스트입니다.
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/mcp/tools/comment.create" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"request_id":"test-dryrun-001","company_id":"demo-company","project_id":"demo-project","mode":"dry_run","tool":"comment.create","arguments":{"question_id":"q-001","post_id":"q-001","message":"Dry-run 통합 테스트 댓글","author":"ontology-workflow"}}'
```
* **기대 결과**: `status: "dry_run"` 반환 및 `external_comment_id: null` 검증 완료.

### 2.3 Post 실제 등록 테스트
데이터베이스에 실제 댓글 데이터를 적재하는 동작을 수행합니다.
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/mcp/tools/comment.create" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"request_id":"test-post-001","company_id":"demo-company","project_id":"demo-project","mode":"post","tool":"comment.create","arguments":{"question_id":"q-001","post_id":"q-001","message":"Post 통합 테스트 댓글","author":"ontology-workflow"}}'
```
* **기대 결과**: `status: "success"` 반환 및 생성된 댓글 고유 ID와 웹 게시판 상세 조회 URL 수령.

---

## 🚦 3. 단계별 장애 진단 체크리스트 (Troubleshooting)

1. **상태**: 헬스 체크 시 503 Service Unavailable 오류 발생
   * **원인**: 본 중계 서버는 켜져 있으나, 중계 대상인 `s1_customer_board` API(Port 8090)가 죽어 있는 경우입니다.
   * **해결**: `s1_customer_board` 서비스가 켜져 있는지 확인하고 DB 생성이 완료되었는지 확인하십시오.
2. **상태**: `POST /mcp/tools/comment.create` 호출 시 404 오류 발생
   * **원인**: `arguments.question_id` 값에 해당되는 문의 원본 게시글이 고객사 SQLite DB에 물리적으로 존재하지 않는 경우입니다.
   * **해결**: 게시판 시스템 UI(`http://localhost:8090`)에 접속하여 대상 ID로 글이 올라와 있는지 확인한 뒤 테스트를 기동하십시오.
