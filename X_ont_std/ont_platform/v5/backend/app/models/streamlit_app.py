from __future__ import annotations

from pydantic import BaseModel
from typing import Literal


class StreamlitRunRequest(BaseModel):
    """Streamlit 앱 실행 요청"""
    app_id: str
    folder_name: str
    file_name: str
    code: str


class StreamlitSaveRequest(BaseModel):
    """Streamlit 앱 소스 저장 요청"""
    app_id: str
    folder_name: str
    file_name: str
    code: str


class StreamlitSaveResponse(BaseModel):
    """Streamlit 앱 소스 저장 응답"""
    app_id: str
    status: Literal["saved"]
    file_path: str
    message: str


class StreamlitRunResponse(BaseModel):
    """Streamlit 앱 실행 응답"""
    app_id: str
    status: Literal["running", "fallback", "error"]
    mode: Literal["streamlit", "fallback"]
    url: str
    file_path: str
    port: int
    message: str


class StreamlitAppStatus(BaseModel):
    """Streamlit 앱 상태"""
    app_id: str
    folder_name: str
    file_name: str
    status: Literal["ready", "running", "stopped", "error"]
    port: int | None = None
    url: str | None = None
    created_at: str
    last_modified: str
