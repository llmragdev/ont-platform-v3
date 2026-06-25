from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class MCPHttpConfig(BaseModel):
    """MCP HTTP 설정"""
    transport: Optional[Literal["stdio", "sse"]] = None
    callStyle: Optional[Literal["tool_endpoint", "jsonrpc_proxy"]] = "tool_endpoint"
    server: Optional[str] = None
    tool: Optional[str] = None
    endpoint: str
    method: Optional[str] = "POST"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    cwd: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 10000


class SkillAuth(BaseModel):
    """HTTP 인증 정보"""
    type: Optional[Literal["basic", "bearer", "custom"]] = None
    username: Optional[str] = None
    password: Optional[str] = None


class SkillImplementation(BaseModel):
    """스킬 구현 방식"""
    type: Literal["builtin", "http", "mcp_http", "custom"]
    endpoint: Optional[str] = None
    code: Optional[str] = None
    mcpConfig: Optional[MCPHttpConfig] = None
    credentialMapping: Optional[Dict[str, str]] = None
    auth: Optional[SkillAuth] = None


class Skill(BaseModel):
    """워크플로우 스킬 정의"""
    id: str = Field(..., description="스킬 고유 ID")
    name: str = Field(..., description="스킬 이름")
    description: str = Field(..., description="스킬 설명")
    category: str = Field(..., description="스킬 카테고리")
    version: str = Field(default="1.0", description="스킬 버전")
    author: str = Field(default="", description="스킬 작성자")
    tags: Optional[list[str]] = None

    inputSchema: Dict[str, Any] = Field(..., description="입력 스키마 (JSON Schema)")
    outputSchema: Dict[str, Any] = Field(..., description="출력 스키마 (JSON Schema)")

    requiredCredentials: Optional[list[str]] = None
    implementation: SkillImplementation = Field(..., description="구현 방식")

    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "factory-comment-create",
                "name": "공장 게시판 댓글 등록",
                "description": "공장 시나리오에서 게시판에 댓글을 등록합니다",
                "category": "integration",
                "version": "1.0",
                "author": "Built-in",
                "tags": ["mcp", "factory"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["event_id", "content"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "comment_id": {"type": "string"},
                        "status": {"type": "string"}
                    }
                },
                "implementation": {
                    "type": "mcp_http",
                    "callStyle": "tool_endpoint",
                    "endpoint": "http://127.0.0.1:8081/mcp/tools/comment.create",
                    "method": "POST",
                    "timeout": 10000
                }
            }
        }


class SkillConfig(BaseModel):
    """워크플로우 노드에서의 스킬 설정"""
    inputMapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="입력 필드 매핑 (표현식 지원: {{nodes.x.output.y}})"
    )
    outputMapping: Optional[Dict[str, str]] = None
    parameters: Optional[Dict[str, Any]] = None


class SkillCatalog(BaseModel):
    """스킬 카탈로그 (Built-in + Custom)"""
    version: str = "1.0"
    lastUpdated: str
    builtinSkills: list[Skill]
    customSkills: Optional[list[Skill]] = None
