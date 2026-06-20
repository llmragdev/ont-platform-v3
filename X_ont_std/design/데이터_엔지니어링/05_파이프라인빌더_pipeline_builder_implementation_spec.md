# 🛠️ 파이프라인 빌더(Pipeline Builder) 상세 구현 명세서

본 문서는 `01_파이프라인빌더_화면_및_기능_설계서.md`에 기재된 시각적 데이터 흐름 저작 도구를 실제 ont_platform v5 시스템의 프론트엔드와 백엔드 API 간 연동 및 변환 규칙에 맞추어 통합하기 위한 **상세 구현 명세**를 기술합니다.

---

## 1. 🌐 아키텍처 및 데이터 흐름 컴파일 메커니즘

파이프라인 빌더는 프론트엔드의 React Flow 컴포넌트 상태(State)로 구성된 노드/엣지 데이터를 백엔드가 직접 실행하고 인식할 수 있는 범용 워크플로우 그래프 포맷(`WorkflowGraph`)으로 **컴파일 및 변환(Compilation & Transformation)**하여 저장합니다.

```text
┌──────────────────────────────┐
│  [Front] React Flow Canvas   │  - UI 상의 드래그앤드롭 좌표 정보 보유
│  - nodes: [Node, Node, ...]  │  - 노드별 세부 config 설정값 입력
│  - edges: [Edge, Edge, ...]  │
└──────────────┬───────────────┘
               │
               ▼  [ handleDeploy() 컴파일 ]
┌──────────────────────────────┐
│  [Backend] API Payload JSON  │  - React Flow nodes/edges -> backend 호환 스키마 변환
│  - id: "wfg-builder-xxxxxx"  │  - graph_kind: "template_copy" 로 설정
│  - runtime: { executor: ... }│  - nodes.data.config 에 속성값 패킹
└──────────────┬───────────────┘
               │
               ▼  [ POST /api/workflow-graphs ]
┌──────────────────────────────┐
│  [File] workflow_graphs.json │  - 테넌트/프로젝트 스코프의 JSON 영구 적재
│  - graphs: { "wfg-...": {} } │  - 배포 즉시 '워크플로우 실행기'에서 감지
└──────────────────────────────┘
```

---

## 2. 🔌 프론트엔드 컴포넌트 설계 (`PipelineBuilderView.tsx`)

### 2.1 핵심 컴포넌트 상태(State) 설계

- **`pipelineName`**: 파이프라인의 표시 이름 (기본값: `"신규 데이터 파이프라인"`)
- **`scenarioId`**: 대상 시나리오 스코프 선택값 (`"scenario1"` | `"scenario2"`)
- **`nodes` / `setNodes`**: React Flow에서 관리하는 캔버스 노드 상태 배열
- **`edges` / `setEdges`**: React Flow에서 관리하는 연결선 상태 배열
- **`selectedNode`**: 사용자가 현재 선택하여 우측 속성 패널에 편집창이 열린 노드 객체
- **`saving` / `message`**: 저장/배포 진행 상태 및 API 성공/실패 토스트 메시지

### 2.2 드래그 앤 드롭 (Drag & Drop) 메커니즘

사용자가 좌측 팔레트에서 노드를 드래그하여 중앙 캔버스로 드롭할 때 실행되는 포지션 및 데이터 주입 모델입니다.
1. **드래그 시작 (`onDragStart`)**:
   - 드래그 중인 HTML 엘리먼트에 `application/reactflow/type`, `label`, `category` 메타데이터를 바인딩하여 전달.
2. **드롭 위치 연산 (`onDrop`)**:
   - `getBoundingClientRect()`를 통해 캔버스의 상대 좌표를 측정하고 드롭된 마우스 좌표 (`clientX`, `clientY`)를 대입하여 노드의 초기 생성 좌표 (`position: { x, y }`)를 계산.
3. **노드 스펙 생성 (`newNode`)**:
   - 고유 ID 생성 (`node-{type}-{timestamp}`)
   - 팔레트에 정의된 `defaultConfig` 복제 적용하여 `data.config`에 바인딩.

---

## 3. 📑 노드 유형별 속성 및 매핑 명세 (Palette Schema)

각 카테고리별 정의된 노드 스펙과 우측 속성 패널에서 편집 가능한 Configuration 매핑 규칙입니다.

### 3.1 Sources (수집 노드)

1. **웹훅 이벤트 수신 (`request_input`)**
   - **목적**: 실시간 HTTP Webhook POST 수집
   - **기본 속성 스펙**:
     ```json
     { "mode": "post", "auth_required": false, "endpoint": "/api/extn/events" }
     ```
2. **배치 폴링 수집 (`batch_polling`)**
   - **목적**: 특정 스케줄에 따른 배치 수집
   - **기본 속성 스펙**:
     ```json
     { "mode": "batch", "interval_cron": "*/5 * * * *", "limit": 10 }
     ```

### 3.2 Transforms (가공 노드)

1. **LLM 의도/유형 분류 (`intent_classify`)**
   - **목적**: 텍스트 분류를 위한 프롬프트 가이드
   - **기본 속성 스펙**:
     ```json
     {
       "model": "gpt-4o",
       "categories": "password, billing, refund, general",
       "system_prompt": "고객 문의의 핵심 의도를 분류하시오."
     }
     ```
2. **설비/자산 매핑 (`equipment_map`)**
   - **목적**: 원문에서 온톨로지 인스턴스 ID 매칭
   - **기본 속성 스펙**:
     ```json
     { "ontology_class": "Equipment", "match_threshold": 0.8 }
     ```
3. **반복/재발 여부 판단 (`recurrence_check`)**
   - **목적**: 온톨로지 쿼리를 활용한 최근 장애 중복 조회
   - **기본 속성 스펙**:
     ```json
     { "lookback_days": 7, "count_threshold": 2 }
     ```

### 3.3 Executes (실행 노드)

1. **지식/RAG 조회 (`knowledge_lookup`)**
   - **목적**: 지식 베이스 또는 온톨로지 매뉴얼 문서 RAG 쿼리
   - **기본 속성 스펙**:
     ```json
     { "kb_source": "ontology_manuals", "search_top_k": 3 }
     ```
2. **조치/답변 초안 생성 (`draft_response`)**
   - **목적**: LLM 기반 조치 지침 드래프트 생성
   - **기본 속성 스펙**:
     ```json
     { "temperature": 0.5, "max_tokens": 500 }
     ```

### 3.4 Sinks (적재 및 외부 등록 노드)

1. **고객사 MCP 댓글 등록 (`customer_mcp_comment_create`)**
   - **목적**: 외부 MCP API 호출 및 Writeback
   - **기본 속성 스펙**:
     ```json
     { "mcp_server": "customer_mcp", "tool": "comment.create", "port": 8080 }
     ```
2. **온톨로지 저장 (Sink) (`ontology_write`)**
   - **목적**: 신규 데이터 및 관계 링크를 RDF 온톨로지 DB에 적재
   - **기본 속성 스펙**:
     ```json
     { "target_class": "FaultEvent", "relationship_link": "has_task" }
     ```
3. **감사 로그 및 알림 (`notify_user`)**
   - **목적**: 감사(Audit) 저장 및 Teams/Email 알림 발송
   - **기본 속성 스펙**:
     ```json
     { "alert_channel": "Teams", "log_format": "jsonl" }
     ```

---

## 4. 🔀 백엔드 그래프 호환 컴파일 변환 스펙

### 4.1 변환 데이터 구조 매핑

사용자가 상단 우측 `[배포 (Deploy)]`를 누를 시, 프론트엔드는 다음 구조로 JSON 페이로드를 조립하여 백엔드 `POST /api/workflow-graphs`에 전달합니다.

| 프론트엔드 ReactFlow 노드 필드 | 백엔드 저장 JSON 매핑 대상 | 설명 |
| :--- | :--- | :--- |
| `n.id` | `nodes[i].id` | 노드 고유 ID 문자열 유지 |
| `n.data.type` | `nodes[i].type` | 내부 실행 시 지칭될 노드 실행 타입명 |
| `n.position` | `nodes[i].position` | 캔버스 상의 x, y 드로잉 좌표 정보 유지 |
| `n.data.label` | `nodes[i].data.label` | 사용자 화면용 표시 라벨명 |
| `n.data.category` | `nodes[i].data.category` | 노드 카탈로그 대분류군 |
| `n.data.config` | `nodes[i].data.config` | 속성 패널에서 편집된 상세 파라미터 셋 |

### 4.2 생성된 WorkflowGraph 메타데이터 변환 예시

```json
{
  "id": "wfg-builder-123456",
  "name": "공장 반복 고장 대응 파이프라인 (자동 빌드)",
  "scenario_id": "scenario2",
  "scenario_version": "v1",
  "graph_kind": "template_copy",
  "execution_mode": "batch",
  "runtime": {
    "executor": "factory.repeated_fault_response",
    "default_mode": "post",
    "allow_post": true,
    "batch_status": "open",
    "batch_limit": 10
  },
  "nodes": [
    {
      "id": "node-batch_polling-9988",
      "type": "batch_polling",
      "position": { "x": 100, "y": 250 },
      "data": {
        "label": "배치 폴링 수집",
        "category": "source",
        "config": {
          "mode": "batch",
          "interval_cron": "*/5 * * * *",
          "limit": 10
        }
      }
    },
    {
      "id": "node-ontology_write-4422",
      "type": "ontology_write",
      "position": { "x": 400, "y": 250 },
      "data": {
        "label": "온톨로지 저장 (Sink)",
        "category": "sink",
        "config": {
          "target_class": "FaultEvent",
          "relationship_link": "has_task"
        }
      }
    }
  ],
  "edges": [
    {
      "id": "edge-node-batch_polling-9988-node-ontology_write-4422",
      "source": "node-batch_polling-9988",
      "target": "node-ontology_write-4422"
    }
  ]
}
```

---

## 5. 🛠️ 백엔드 저장 API 사양 (`POST /api/workflow-graphs`)

- **URI**: `/api/workflow-graphs`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
  - `x-company-id: default` (테넌트 식별용)
  - `x-project-id: proj-default` (프로젝트 식별용)
- **백엔드 로직 처리 순서**:
  1. `TenantContext`를 통해 현재 테넌트의 프로젝트 경로 확인 (`get_project_root`).
  2. 요청 페이로드에서 `nodes` 정보가 올바른 배열 구조이고 position이 입력되었는지 `_validate_graph_nodes`로 유효성 검사.
  3. `workflow_graphs.json`에 신규 `graph_id` 키값으로 병합 저장.
  4. 컴파일 완료된 템플릿 그래프가 `workflow_graphs.json`에 성공적으로 파일 쓰기 완료되면 200 OK 응답 반환.
