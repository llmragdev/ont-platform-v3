# Server Architecture (s1_customer_mcp)

고객사 MCP 중계 서버(`s1_customer_mcp`)의 요청 처리 구조, 호환성 어댑터 설계 및 상세 통신 플로우를 정의하는 아키텍처 문서입니다.

---

## 🏗️ 시스템 아키텍처 및 처리 흐름

본 중계 서버는 `ont_platform`의 워크플로우 엔진에서 송신하는 MCP 규격의 요청을 수신받아 고객사 내부 API 포맷(`s1_customer_board`)으로 가공 및 전달하는 **프로토콜 어댑터(Protocol Adapter)** 역할을 수행합니다.

```mermaid
graph TD
    subgraph Client [ont_platform v5]
        CodexClient[Codex 표준 Client]
        ClaudeClient[Claude Code 레거시 Client]
    end

    subgraph MCP_Server [s1_customer_mcp (Port 8080)]
        Endpoint_Spec[POST /mcp/tools/comment.create]
        Endpoint_Legacy[POST / or /mcp]
        Compat_Layer[하이브리드 호환성 어댑터 레이어]
        Err_Handler[글로벌 표준 에러 핸들러]
    end

    subgraph Board [s1_customer_board (Port 8090)]
        Board_API[Board REST API]
    end

    CodexClient --> Endpoint_Spec
    ClaudeClient --> Endpoint_Legacy
    
    Endpoint_Spec --> Compat_Layer
    Endpoint_Legacy --> Compat_Layer
    
    Compat_Layer -- "1. 게시글 존재 유무 체크 (GET)" --> Board_API
    Compat_Layer -- "2. 댓글 실제 쓰기 (POST)" --> Board_API
    Compat_Layer --> Err_Handler
```

---

## ⚙️ 주요 아키텍처 설계 특징

### 1. 하이브리드 호환성 레이어 (Dual Compatibility Layer)
* **Codex 표준 규격**: `arguments` 내부에 `question_id`, `post_id`, `message` 등의 맵 구조로 값을 수집합니다.
* **Claude Code 레거시 규격**: `args` 내부에 파라미터가 들어가며 테넌트 구분 정보가 루트가 아닌 `tenant_context` 하위에 캡슐화되어 전달되는 경우가 있어, 이를 자동으로 파싱하여 호환 맵으로 정규화하는 전처리 엔진을 적용했습니다.

### 2. 무상태성 (Stateless Design)
* 서버 자체에는 별도의 데이터 상태나 데이터베이스 연결 정보를 갖지 않습니다.
* 모든 데이터 적재 및 조회는 네트워크 너머의 `s1_customer_board`(Port 8090) API에 온전히 위임(Relay)하여 중계 신뢰도를 높였습니다.

### 3. 표준 오류 정규화 (Error Normalization)
* 고객사 게시판 시스템 API의 오류(`404 Post Not Found` 등)나 네트워크 장애로 인한 예외가 발생할 경우, 이를 솔루션이 안전하게 분류할 수 있도록 규격화된 에러 JSON 패킷 및 오류 코드로 재가공하여 반환합니다.
