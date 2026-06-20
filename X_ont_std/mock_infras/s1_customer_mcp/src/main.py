import json
import urllib.request
import urllib.error
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

app = FastAPI(title="Customer MCP Relay Server - Scenario 1 (Robust Version)", version="1.0.0")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOARD_API_URL = "http://localhost:8090/api/posts"

# Pydantic Schemas matching CUSTOMER_MCP_CALL_SPEC.md (Spec Version)
class MCPArguments(BaseModel):
    question_id: Optional[str] = None
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    message: str
    author: Optional[str] = "ontology-workflow"

class MCPRequest(BaseModel):
    request_id: str
    company_id: str
    project_id: str
    mode: Optional[str] = "dry_run"
    tool: str
    arguments: MCPArguments
    metadata: Optional[dict] = None

# Health Check Route (supports both spec and root health check)
@app.get("/health")
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "customer_mcp"
    }

async def process_comment_create(data: dict) -> JSONResponse:
    """
    Common business logic for comment.create.
    Supports both Codex spec format and Claude Code's format.
    """
    request_id = data.get("request_id") or data.get("audit_id") or "unknown"
    tool_name = data.get("tool", "comment.create")
    mode = data.get("mode", "dry_run")
    
    # Extract tenant context (supports root level or nested under tenant_context)
    tenant_ctx = data.get("tenant_context") or {}
    company_id = data.get("company_id") or tenant_ctx.get("company_id")
    project_id = data.get("project_id") or tenant_ctx.get("project_id")
    
    # 1. Validation of main parameters
    if not company_id or not project_id:
        return JSONResponse(
            status_code=400,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": tool_name,
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Required fields (company_id/tenant_context, project_id) are missing.",
                    "retryable": False
                }
            }
        )

    # Extract arguments (supports both Codex 'arguments' and Claude Code 'args')
    args = data.get("arguments") or data.get("args") or {}
    message = args.get("message") or args.get("text")
    question_id = args.get("question_id") or args.get("post_id") or args.get("thread_id")
    author = args.get("author") or "ontology-workflow"

    if not message or not question_id:
        return JSONResponse(
            status_code=400,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": tool_name,
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Arguments must contain message/text and a valid target ID (question_id/post_id).",
                    "retryable": False
                }
            }
        )

    thread_id = args.get("thread_id") or question_id
    print(f"[Customer MCP S1] Robust Handler | Mode: {mode} | Post ID: {question_id} | Author: {author}")

    # Check if the board post exists (required for both dry_run and post verification)
    check_url = f"{BOARD_API_URL}/{question_id}"
    try:
        req = urllib.request.Request(check_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "request_id": request_id,
                    "status": "error",
                    "tool": tool_name,
                    "result": None,
                    "error": {
                        "code": "BOARD_API_ERROR",
                        "message": f"Target post/question '{question_id}' not found in customer board.",
                        "retryable": False
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=e.code,
                content={
                    "request_id": request_id,
                    "status": "error",
                    "tool": tool_name,
                    "result": None,
                    "error": {
                        "code": "BOARD_API_ERROR",
                        "message": f"Customer board API error during check: {e.reason}",
                        "retryable": True
                    }
                }
            )
    except urllib.error.URLError as e:
        return JSONResponse(
            status_code=503,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": tool_name,
                "result": None,
                "error": {
                    "code": "BOARD_TIMEOUT",
                    "message": f"Failed to connect to customer board API: {e.reason}",
                    "retryable": True
                }
            }
        )

    # 2. Dry-run logic
    if mode in ("dry_run", "dry-run"):
        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "status": "dry_run",
                "tool": tool_name,
                "result": {
                    "external_comment_id": None,
                    "external_thread_id": thread_id,
                    "message": message
                },
                "error": None
            }
        )

    # 3. Post (Write) logic
    elif mode == "post":
        comment_url = f"{BOARD_API_URL}/{question_id}/comments"
        payload = {
            "author": author,
            "content": message
        }
        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                comment_url,
                data=req_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_body = response.read().decode('utf-8')
                board_res = json.loads(res_body)
                comment_id = board_res.get("id")

            return JSONResponse(
                status_code=200,
                content={
                    "request_id": request_id,
                    "status": "success",
                    "tool": tool_name,
                    "result": {
                        "external_comment_id": comment_id,
                        "external_thread_id": thread_id,
                        "url": f"http://localhost:8090/posts/{question_id}#comment-{comment_id}"
                    },
                    "error": None
                }
            )
        except urllib.error.HTTPError as e:
            return JSONResponse(
                status_code=e.code,
                content={
                    "request_id": request_id,
                    "status": "error",
                    "tool": tool_name,
                    "result": None,
                    "error": {
                        "code": "BOARD_API_ERROR",
                        "message": f"Failed to post comment to customer board API: {e.reason}",
                        "retryable": True
                    }
                }
            )
        except urllib.error.URLError as e:
            return JSONResponse(
                status_code=503,
                content={
                    "request_id": request_id,
                    "status": "error",
                    "tool": tool_name,
                    "result": None,
                    "error": {
                        "code": "BOARD_TIMEOUT",
                        "message": f"Connection lost during write to customer board API: {e.reason}",
                        "retryable": True
                    }
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "request_id": request_id,
                    "status": "error",
                    "tool": tool_name,
                    "result": None,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": f"Unexpected error during comment register: {str(e)}",
                        "retryable": True
                    }
                }
            )
    else:
        # Invalid mode
        return JSONResponse(
            status_code=400,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": tool_name,
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Invalid mode '{mode}'. Supported modes are 'dry_run' and 'post'.",
                    "retryable": False
                }
            }
        )

# Endpoint A: Codex Spec Endpoint
@app.post("/mcp/tools/comment.create")
async def execute_comment_create_spec(request: Request):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode('utf-8'))
        return await process_comment_create(data)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "request_id": "unknown",
                "status": "error",
                "tool": "comment.create",
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Malformed JSON request: {str(e)}",
                    "retryable": False
                }
            }
        )

# Endpoint B: Base URL POST endpoint (For Claude Code's customer_mcp_client.py fallback)
@app.post("/")
@app.post("/mcp")
async def execute_comment_create_legacy(request: Request):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode('utf-8'))
        # If calling legacy, map fields like audit_id -> request_id, and check tool
        tool = data.get("tool")
        if tool == "comment.create":
            # Map legacy mode parameter (dry_run is inside config, but client allows it)
            # Check client's dry_run state (if client config has dry_run, it doesn't even make POST)
            # If it makes POST, let's look at mode inside request payload.
            # In customer_mcp_client.py, it sends payload:
            # {"tool": "comment.create", "args": {...}, "audit_id": "...", "tenant_context": {...}}
            # We map this data to standard processing.
            return await process_comment_create(data)
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "request_id": data.get("audit_id", "unknown"),
                    "status": "error",
                    "tool": tool or "unknown",
                    "result": None,
                    "error": {
                        "code": "TOOL_NOT_FOUND",
                        "message": f"Unsupported tool: {tool}",
                        "retryable": False
                    }
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "request_id": "unknown",
                "status": "error",
                "tool": "unknown",
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Malformed JSON request: {str(e)}",
                    "retryable": False
                }
            }
        )

# Endpoint C: Batch Polling list tool
@app.get("/mcp/tools/question.list")
async def list_questions(status: Optional[str] = None):
    """
    Candidate endpoint for batch polling.
    Lists questions from the customer board, optionally filtering by status (e.g. status=open).
    """
    board_url = f"{BOARD_API_URL}?status={status}" if status else BOARD_API_URL
    try:
        req = urllib.request.Request(board_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            posts = json.loads(res_body)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "tool": "question.list",
                "result": {
                    "questions": [
                        {
                            "question_id": p["id"],
                            "title": p["title"],
                            "author": p["author"],
                            "content": p["content"],
                            "created_at": p["created_at"]
                        }
                        for p in posts
                    ]
                },
                "error": None
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "tool": "question.list",
                "result": None,
                "error": {
                    "code": "BOARD_API_ERROR",
                    "message": f"Failed to fetch posts from board: {str(e)}",
                    "retryable": True
                }
            }
        )

# Endpoint D: Batch Polling get tool
@app.get("/mcp/tools/question.get")
async def get_question(question_id: str):
    """
    Candidate endpoint for batch polling.
    Retrieves detail of a specific question from the customer board.
    """
    board_url = f"{BOARD_API_URL}/{question_id}"
    try:
        req = urllib.request.Request(board_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            post = json.loads(res_body)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "tool": "question.get",
                "result": {
                    "question_id": post["id"],
                    "title": post["title"],
                    "author": post["author"],
                    "content": post["content"],
                    "created_at": post["created_at"],
                    "comments_count": len(post.get("comments", []))
                },
                "error": None
            }
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "tool": "question.get",
                    "result": None,
                    "error": {
                        "code": "BOARD_API_ERROR",
                        "message": f"Question '{question_id}' not found.",
                        "retryable": False
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=e.code,
                content={
                    "status": "error",
                    "tool": "question.get",
                    "result": None,
                    "error": {
                        "code": "BOARD_API_ERROR",
                        "message": f"Board error: {e.reason}",
                        "retryable": True
                    }
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "tool": "question.get",
                "result": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Unexpected error: {str(e)}",
                    "retryable": True
                }
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
