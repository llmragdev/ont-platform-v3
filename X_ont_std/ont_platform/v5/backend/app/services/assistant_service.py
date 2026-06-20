from __future__ import annotations

import re

from app.models.assistant import (
    AppSpecPreview,
    AppWidgetSpec,
    AssistantAction,
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantIntent,
    GeneratedQuery,
)


FACTORY_TYPES = [
    "ServiceRequest",
    "Factory",
    "ProductionLine",
    "ProcessStep",
    "Equipment",
    "FaultEvent",
    "MaintenanceTask",
    "QualityIssue",
]


class AssistantService:
    """Rule-based MVP for the platform-wide AI Assistant.

    The first version intentionally avoids executing generated code. It produces
    safe previews that can later be backed by an LLM and query executor.
    """

    def chat(self, request: AssistantChatRequest) -> AssistantChatResponse:
        message = request.message.strip()
        intent = self._detect_intent(message, request.context.current_view)
        trace = [
            "assistant.mvp.rule_based",
            f"intent={intent}",
            f"view={request.context.current_view or 'unknown'}",
        ]

        if intent == "create_app":
            query = self._factory_repeated_fault_query(message)
            app = AppSpecPreview(
                title="공장 반복 고장 분석 앱",
                description="최근 반복 고장 설비, 정비지시 상태, 고장-설비 관계를 한 화면에서 확인합니다.",
                layout=[
                    AppWidgetSpec(type="metric", title="반복 고장 설비 수", query_id=query.query_id),
                    AppWidgetSpec(type="table", title="반복 고장 목록", query_id=query.query_id),
                    AppWidgetSpec(type="chart", title="설비별 고장 횟수", query_id=query.query_id),
                    AppWidgetSpec(type="graph", title="고장-설비-정비지시 관계"),
                ],
            )
            return AssistantChatResponse(
                intent=intent,
                summary="Streamlit 스타일 업무 앱 초안을 만들었습니다.",
                answer=(
                    "요청을 공장 반복 고장 분석 앱 생성으로 이해했습니다. "
                    "아래 SPARQL 초안을 검증한 뒤 테이블, 차트, 관계 그래프가 포함된 App Spec으로 저장할 수 있습니다."
                ),
                generated_queries=[query],
                app_spec_preview=app,
                suggested_actions=self._actions(include_save_app=True),
                trace=trace,
                context_used=request.context,
            )

        if intent == "edit_streamlit_program":
            file_name = request.context.selected_file_name or "streamlit_app.py"
            file_path = request.context.selected_file_path or file_name
            folder_name = request.context.selected_folder_name or "선택된 폴더"
            display_path = file_path if "/" in file_path or "\\" in file_path else f"{folder_name}/{file_path}"
            streamlit_code = self._streamlit_program_code(message)
            return AssistantChatResponse(
                intent=intent,
                summary=f"{file_name} 편집 초안을 만들었습니다.",
                answer=(
                    f"현재 선택된 편집 대상은 `{display_path}`입니다. "
                    "아래 코드를 해당 Streamlit 파이썬 편집창에 반영합니다.\n\n"
                    "```python\n"
                    f"{streamlit_code}"
                    "```\n\n"
                    "선택된 편집창에 자동 적용되며, 필요하면 코딩 실행 버튼으로 바로 확인할 수 있습니다."
                ),
                suggested_actions=[
                    AssistantAction(
                        id="code-applied",
                        label="편집창 적용",
                        description="응답 코드가 선택된 편집기에 자동 반영됩니다.",
                    )
                ],
                trace=trace + [f"selected_file={file_path}"],
                context_used=request.context,
            )

        if intent == "generate_ontology_query":
            query = self._factory_repeated_fault_query(message)
            return AssistantChatResponse(
                intent=intent,
                summary="온톨로지 질의 초안을 생성했습니다.",
                answer=(
                    "현재는 안전한 미리보기 단계입니다. 생성된 SPARQL은 읽기 전용 질의로 설계했으며 "
                    "실행 전 스키마 매핑과 권한 검증을 거치는 것이 좋습니다."
                ),
                generated_queries=[query],
                suggested_actions=self._actions(),
                trace=trace,
                context_used=request.context,
            )

        if intent == "analyze_failure":
            return AssistantChatResponse(
                intent=intent,
                summary="실패 원인 점검 순서를 제안합니다.",
                answer=(
                    "먼저 워크플로우 상태가 completed인지 확인하고, 실행 모드가 post인지 확인하세요. "
                    "그 다음 MCP 서버 기동 여부, 게시판 target URL, Workflow Trace의 마지막 실패 노드, "
                    "Writeback DLQ와 감사 로그 순서로 확인하면 됩니다."
                ),
                suggested_actions=[
                    AssistantAction(
                        id="open-trace",
                        label="실행 추적 확인",
                        description="Workflow Trace에서 마지막 실행 노드를 봅니다.",
                    ),
                    AssistantAction(
                        id="open-dlq",
                        label="DLQ 확인",
                        description="외부 등록 실패 여부를 확인합니다.",
                    ),
                ],
                trace=trace,
                context_used=request.context,
            )

        if intent == "suggest_workflow_change":
            return AssistantChatResponse(
                intent=intent,
                summary="워크플로우 변경 제안을 만들었습니다.",
                answer=(
                    "현재 워크플로우에서는 입력, 분류, 자산 매핑, 반복 확인, 조치 생성, 외부 등록, 온톨로지 저장 단계가 "
                    "분리되어야 합니다. 현장 영향이 있는 고장 시나리오는 정비지시 생성 전에 Evidence Gate 또는 "
                    "승인 확인 단계를 추가하는 구성이 좋습니다."
                ),
                suggested_actions=[
                    AssistantAction(id="copy-plan", label="제안 복사", description="워크플로우 변경 제안을 복사합니다."),
                    AssistantAction(
                        id="add-node-later",
                        label="노드 추가 준비",
                        description="다음 단계에서 빌더 노드 추가와 연결을 지원합니다.",
                        enabled=False,
                    ),
                ],
                trace=trace,
                context_used=request.context,
            )

        if intent == "explain_current_view":
            return AssistantChatResponse(
                intent=intent,
                summary="현재 화면 설명을 준비했습니다.",
                answer=self._explain_view(request.context.current_view, request.context.view_title),
                suggested_actions=[
                    AssistantAction(
                        id="suggest-query",
                        label="질의 만들기",
                        description="현재 화면 맥락으로 온톨로지 질의를 제안합니다.",
                    ),
                    AssistantAction(
                        id="explain-value",
                        label="가치 설명",
                        description="외부 시연용 설명 문장을 만듭니다.",
                    ),
                ],
                trace=trace,
                context_used=request.context,
            )

        return AssistantChatResponse(
            intent="general_help",
            summary="AI Assistant가 지원할 수 있는 작업입니다.",
            answer=(
                "현재 화면을 기준으로 온톨로지 질의 생성, 공장 반복 고장 분석 앱 초안, "
                "워크플로우 실패 원인 점검, 워크플로우 변경 제안, 시연용 설명 문장 생성을 지원할 수 있습니다."
            ),
            suggested_actions=self._actions(),
            trace=trace,
            context_used=request.context,
        )

    def _detect_intent(self, message: str, current_view: str | None) -> AssistantIntent:
        normalized = message.lower()
        
        # 1. Streamlit 앱 빌더 화면(app-builder) 맥락에서는 앱/차트 생성 요청도 파이썬 코딩 지시로 매핑
        if current_view == "app-builder":
            if any(
                word in normalized
                for word in ["code", "coding", "python", "streamlit", "app", "chart", "dashboard", "graph", "plot"]
            ):
                return "edit_streamlit_program"
            if any(
                word in message
                for word in ["코딩", "코드", "파이썬", "프로그램", "앱", "화면", "차트", "그래프", "그려", "그리", "대시보드", "스트림릿"]
            ):
                return "edit_streamlit_program"

        # 2. 일반 화면 맥락의 감지 규칙
        if any(word in normalized for word in ["code", "coding", "python", "streamlit"]):
            return "edit_streamlit_program"
        if any(word in message for word in ["코딩", "코드", "파이썬", "프로그램"]):
            return "edit_streamlit_program"
        if any(word in normalized for word in ["app", "chart", "dashboard", "streamlit"]):
            return "create_app"
        if any(word in message for word in ["앱", "화면", "차트", "그래프", "대시보드", "스트림릿"]):
            return "create_app"
        if any(word in normalized for word in ["query", "sparql", "sql", "select"]):
            return "generate_ontology_query"
        if any(word in message for word in ["쿼리", "질의", "조회", "보여줘"]):
            return "generate_ontology_query"
        if any(word in normalized for word in ["fail", "error", "running", "dlq"]):
            return "analyze_failure"
        if any(word in message for word in ["실패", "안달", "안 달", "오류", "에러"]):
            return "analyze_failure"
        if any(word in normalized for word in ["add", "modify", "change", "node", "step"]):
            return "suggest_workflow_change"
        if any(word in message for word in ["추가", "수정", "바꿔", "변경", "노드", "단계"]):
            return "suggest_workflow_change"
        if any(word in normalized for word in ["explain", "what", "how"]):
            return "explain_current_view"
        if any(word in message for word in ["설명", "뭐야", "무엇", "어떻게"]):
            return "explain_current_view"
        if current_view:
            return "explain_current_view"
        return "general_help"

    def _factory_repeated_fault_query(self, message: str) -> GeneratedQuery:
        days = self._extract_days(message) or 7
        query = f"""PREFIX ont: <http://ontology.local/v5#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?equipment ?equipmentName (COUNT(?fault) AS ?faultCount) ?line ?taskStatus
WHERE {{
  ?request a ont:ServiceRequest ;
           ont:reports ?fault .
  ?fault a ont:FaultEvent ;
         ont:affects ?equipment ;
         ont:occurredAt ?occurredAt .
  ?equipment a ont:Equipment ;
             ont:name ?equipmentName .
  OPTIONAL {{ ?line ont:uses ?equipment . }}
  OPTIONAL {{
    ?fault ont:creates ?task .
    ?task a ont:MaintenanceTask ;
          ont:status ?taskStatus .
  }}
  FILTER (?occurredAt >= NOW() - "P{days}D"^^xsd:duration)
}}
GROUP BY ?equipment ?equipmentName ?line ?taskStatus
HAVING (COUNT(?fault) >= 2)
ORDER BY DESC(?faultCount)
LIMIT 20"""
        return GeneratedQuery(
            language="SPARQL",
            title=f"최근 {days}일 반복 고장 설비 조회",
            description="ServiceRequest, FaultEvent, Equipment, MaintenanceTask 관계를 따라 반복 고장 설비를 찾습니다.",
            query=query,
            safe_to_execute=True,
            warnings=[
                "MVP query preview입니다. 실제 실행 전 날짜 함수 지원 여부와 실제 스키마 매핑을 검증해야 합니다.",
                f"참조 온톨로지 타입: {', '.join(FACTORY_TYPES)}",
            ],
        )

    def _extract_days(self, message: str) -> int | None:
        match = re.search(r"(\d+)\s*(?:일|days?|d)", message, flags=re.IGNORECASE)
        if not match:
            return None
        days = int(match.group(1))
        return max(1, min(days, 365))

    def _streamlit_program_code(self, message: str) -> str:
        wants_graph = "그래프" in message or "그려" in message or "graph" in message.lower() or "chart" in message.lower()
        chart_block = ""
        if wants_graph:
            chart_block = (
                "\nst.subheader(\"설비별 반복 고장 그래프\")\n"
                "chart_data = data.set_index(\"설비\")[\"고장횟수\"]\n"
                "st.bar_chart(chart_data)\n\n"
                "st.subheader(\"일자별 고장 추이\")\n"
                "trend = pd.DataFrame({\n"
                "    \"일자\": [\"D-6\", \"D-5\", \"D-4\", \"D-3\", \"D-2\", \"D-1\", \"오늘\"],\n"
                "    \"검사 카메라\": [0, 1, 0, 1, 0, 0, 1],\n"
                "    \"배터리 탭 용접기\": [1, 0, 0, 0, 1, 0, 0],\n"
                "})\n"
                "st.line_chart(trend.set_index(\"일자\"))\n"
            )
        return (
            "import pandas as pd\n"
            "import streamlit as st\n\n"
            "st.set_page_config(page_title=\"공장 반복 고장 분석\", layout=\"wide\")\n"
            "st.title(\"공장 반복 고장 분석\")\n\n"
            "data = pd.DataFrame([\n"
            "    {\"설비\": \"검사 카메라\", \"고장횟수\": 3, \"상태\": \"정비 필요\"},\n"
            "    {\"설비\": \"배터리 탭 용접기\", \"고장횟수\": 2, \"상태\": \"관찰\"},\n"
            "    {\"설비\": \"압력 센서\", \"고장횟수\": 1, \"상태\": \"정상 확인\"},\n"
            "])\n\n"
            "metric_cols = st.columns(3)\n"
            "metric_cols[0].metric(\"반복 고장 설비\", len(data[data[\"고장횟수\"] >= 2]))\n"
            "metric_cols[1].metric(\"총 고장 횟수\", int(data[\"고장횟수\"].sum()))\n"
            "metric_cols[2].metric(\"정비 필요\", int((data[\"상태\"] == \"정비 필요\").sum()))\n"
            f"{chart_block}\n"
            "st.subheader(\"상세 목록\")\n"
            "st.dataframe(data, use_container_width=True)\n"
        )

    def _actions(self, include_save_app: bool = False) -> list[AssistantAction]:
        actions = [
            AssistantAction(id="copy-query", label="쿼리 복사", description="생성된 쿼리를 클립보드로 복사합니다."),
            AssistantAction(
                id="validate-query",
                label="검증",
                description="스키마, 권한, 읽기 전용 여부를 검증합니다.",
                enabled=False,
            ),
            AssistantAction(id="execute-query", label="실행", description="검증 후 쿼리를 실행합니다.", enabled=False),
        ]
        if include_save_app:
            actions.append(
                AssistantAction(id="save-app", label="앱 저장", description="App Spec으로 저장합니다.", enabled=False)
            )
        return actions

    def _explain_view(self, current_view: str | None, view_title: str | None) -> str:
        title = view_title or current_view or "현재 화면"
        explanations = {
            "workflow-graph": (
                "빌더와 실행 화면은 업무 흐름을 편집하고 실행하며, 블록별 입출력과 온톨로지 매핑을 확인하는 통합 화면입니다."
            ),
            "ontology-graph": (
                "관계 탐색 화면은 요청, 설비, 공정, 정비지시 같은 업무 객체가 어떤 관계로 연결되는지 보여줍니다."
            ),
            "hybrid-query": "통합 질의 화면은 온톨로지 관계와 문서 RAG 근거를 결합해 업무 질문에 답합니다.",
            "rag-query": "문서 RAG 질의 화면은 정책, 매뉴얼, 지침 문서에서 근거를 찾아 답변을 생성합니다.",
            "skills": "스킬 관리 화면은 워크플로우 노드가 재사용할 실행 기능과 외부 연동 기능을 관리합니다.",
        }
        return explanations.get(
            current_view or "",
            f"{title} 화면에서는 현재 업무 맥락을 기준으로 질의 생성, 앱 초안, 워크플로우 설명을 요청할 수 있습니다.",
        )
