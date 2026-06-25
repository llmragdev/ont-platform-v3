# 21. 고객사 MCP 모의 인프라 가이드

**섹션**: 모의 인프라  
**포트**: 8080 (HTTP / MCP)  
**가상환경**: `claud_be`  
**위치**: `mock_infras/s1_customer_mcp`  
**관련 가이드**: [20_고객사_보드_모의인프라_가이드.md](./20_고객사_보드_모의인프라_가이드.md)

---

## 📋 개요

`ont_platform v5` 솔루션의 표준 MCP 도구(Tool) 호출을 수신하여 고객사 API 구조(`s1_customer_board`, Port 8090)로 매핑 및 포워딩해주는 중계 서버의 실행 및 검증 매뉴얼입니다.

> [!IMPORTANT]
> 본 서버는 HTTP 통신 상에서 MCP 표준 규격을 준수하는 프록시 레이어로 작동합니다.

---

## 🚀 구동 방법

PowerShell 혹은 CMD 터미널을 열고 다음 명령어를 실행하여 서버를 기동합니다.

```powershell
# 1. 가상환경 활성화
conda activate claud_be

# 2. 디렉토리 이동
cd E:\ontology_edu\X_ont_std\mock_infras\s1_customer_mcp

# 3. FastAPI/Uvicorn 서버 기동
python src/main.py
```

### 구동 성공 로그 예시
```text
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

---

## 🔌 연동 흐름 및 아키텍처

```
┌────────────────────┐          ┌────────────────────┐          ┌────────────────────┐
│    ont_platform    │  ──────→ │  s1_customer_mcp   │  ──────→ │  s1_customer_board │
│    (Next.js/BE)    │  (MCP)   │   (Uvicorn:8080)   │  (REST)  │   (Uvicorn:8090)   │
└────────────────────┘          └────────────────────┘          └────────────────────┘
```

1. **에이전트 노드 실행**: 워크플로우 엔진에서 `customer-comment-create` 스킬 노드가 트리거됩니다.
2. **MCP 요청 수신**: `ont_platform` 백엔드가 MCP JSON-RPC 형태로 `s1_customer_mcp`(Port 8080)에 `comment.create` 도구를 요청합니다.
3. **포워딩 및 REST 변환**: 중계 서버가 요청을 파싱하여 `s1_customer_board`(Port 8090)의 REST API로 요청을 포워딩합니다.
4. **결과 응답**: 게시판 데이터베이스 저장 성공 후 결과를 역순으로 반환합니다.

---

## 🖥️ 연동 확인 및 헬스 체크

* **Health Check API**:
  * URL: [http://localhost:8080/health](http://localhost:8080/health)
  * 정상 응답: `{"status": "ok", "service": "customer_mcp"}`

> [!CAUTION]
> 본 중계 서버는 직접 데이터를 보관하지 않습니다. 원활한 호출 동작을 위해서는 **반드시 게시판 서버(Port 8090)가 먼저 구동 중이어야 합니다.** 그렇지 않으면 503 Service Unavailable 오류가 발생합니다.

---

## 🛠️ 제공 도구 (MCP Tools)

### `comment.create`
* **설명**: 고객 문의글에 답변 댓글을 생성합니다.
* **입력 매개변수 (JSON Schema)**:
  ```json
  {
    "ticket_id": "string (필수, 대상 문의글 ID)",
    "content": "string (필수, 댓글 작성 내용)",
    "mode": "string (선택: 'dry_run' 시뮬레이션 | 'post' 실제 반영)"
  }
  ```
* **출력 스펙**:
  ```json
  {
    "comment_id": "string",
    "status": "success | failed",
    "timestamp": "string"
  }
  ```

---

## 🔗 연관 가이드 및 문서

* **대상 보드 시스템**: [20_고객사_보드_모의인프라_가이드.md](./20_고객사_보드_모의인프라_가이드.md)
* **통합 실행**: [25_통합_모의인프라_실행_가이드.md](./25_통합_모의인프라_실행_가이드.md)
