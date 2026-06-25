from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


AssistantIntent = Literal[
    "explain_current_view",
    "generate_ontology_query",
    "create_app",
    "edit_streamlit_program",
    "analyze_failure",
    "suggest_workflow_change",
    "general_help",
]


class AssistantContext(BaseModel):
    current_view: str | None = None
    view_title: str | None = None
    company_id: str | None = None
    project_id: str | None = None
    user_id: str | None = None
    role: str | None = None
    selected_object_id: str | None = None
    selected_workflow_id: str | None = None
    selected_workflow_name: str | None = None
    selected_node_id: str | None = None
    selected_node_label: str | None = None
    selected_app_id: str | None = None
    selected_app_name: str | None = None
    selected_folder_id: str | None = None
    selected_folder_name: str | None = None
    selected_file_path: str | None = None
    selected_file_name: str | None = None
    selected_language: str | None = None


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: AssistantContext = Field(default_factory=AssistantContext)


class GeneratedQuery(BaseModel):
    query_id: str = Field(default_factory=lambda: f"q-{uuid4().hex[:10]}")
    language: Literal["SPARQL", "SQL", "ONTOLOGY"] = "SPARQL"
    title: str
    description: str
    query: str
    safe_to_execute: bool = True
    warnings: list[str] = Field(default_factory=list)


class AppWidgetSpec(BaseModel):
    type: Literal["metric", "table", "chart", "graph", "text"]
    title: str
    query_id: str | None = None
    description: str | None = None


class AppSpecPreview(BaseModel):
    app_id: str = Field(default_factory=lambda: f"app-{uuid4().hex[:10]}")
    title: str
    description: str
    layout: list[AppWidgetSpec] = Field(default_factory=list)


class AssistantAction(BaseModel):
    id: str
    label: str
    description: str
    enabled: bool = True


class AssistantChatResponse(BaseModel):
    conversation_id: str = Field(default_factory=lambda: f"asst-{uuid4().hex[:12]}")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    intent: AssistantIntent
    summary: str
    answer: str
    generated_queries: list[GeneratedQuery] = Field(default_factory=list)
    app_spec_preview: AppSpecPreview | None = None
    suggested_actions: list[AssistantAction] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)
    context_used: AssistantContext
