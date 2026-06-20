import json
import urllib.request
import urllib.error
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

app = FastAPI(title="Factory MCP Relay Server - Scenario 2", version="1.0.0")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOARD_BASE_URL = "http://localhost:8091/api/factory"

# Health Check Route
@app.get("/health")
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "factory_mcp"
    }

# Helper to verify target event exists on the board
def check_event_exists(event_id: str) -> Optional[JSONResponse]:
    check_url = f"{BOARD_BASE_URL}/events/{event_id}"
    try:
        req = urllib.request.Request(check_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "result": None,
                    "error": {
                        "code": "EVENT_NOT_FOUND",
                        "message": f"Target factory event '{event_id}' not found in factory board.",
                        "retryable": False
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=e.code,
                content={
                    "status": "error",
                    "result": None,
                    "error": {
                        "code": "FACTORY_BOARD_ERROR",
                        "message": f"Factory board API error during check: {e.reason}",
                        "retryable": True
                    }
                }
            )
    except urllib.error.URLError as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "result": None,
                "error": {
                    "code": "FACTORY_BOARD_ERROR",
                    "message": f"Failed to connect to factory board API: {e.reason}",
                    "retryable": True
                }
            }
        )

# Tool 1: factory_event.list
@app.post("/mcp/tools/factory_event.list")
async def execute_event_list(request: Request):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Malformed JSON request: {str(e)}",
                    "retryable": False
                }
            }
        )

    request_id = data.get("request_id") or "unknown"
    args = data.get("arguments") or data.get("args") or {}
    status = args.get("status", "open")
    limit = args.get("limit", 20)

    board_url = f"{BOARD_BASE_URL}/events/open?limit={limit}" if status == "open" else f"{BOARD_BASE_URL}/events"
    
    try:
        req = urllib.request.Request(board_url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            events = res_json.get("items") if "items" in res_json else res_json
        
        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "status": "success",
                "tool": "factory_event.list",
                "result": {
                    "items": events
                },
                "error": None
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": "factory_event.list",
                "result": None,
                "error": {
                    "code": "FACTORY_BOARD_ERROR",
                    "message": f"Failed to fetch events from factory board: {str(e)}",
                    "retryable": True
                }
            }
        )

# Tool 2: factory_response.create
@app.post("/mcp/tools/factory_response.create")
async def execute_response_create(request: Request):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Malformed JSON request: {str(e)}",
                    "retryable": False
                }
            }
        )

    request_id = data.get("request_id") or "unknown"
    tool_name = "factory_response.create"
    mode = data.get("mode", "dry_run")
    
    # Validation of tenant context
    company_id = data.get("company_id") or (data.get("tenant_context") or {}).get("company_id")
    project_id = data.get("project_id") or (data.get("tenant_context") or {}).get("project_id")
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
                    "message": "Required fields (company_id, project_id) are missing.",
                    "retryable": False
                }
            }
        )

    args = data.get("arguments") or data.get("args") or {}
    event_id = args.get("event_id")
    message = args.get("message")
    author = args.get("author") or "ontology-workflow"

    if not event_id or not message:
        return JSONResponse(
            status_code=400,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": tool_name,
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Arguments must contain event_id and message.",
                    "retryable": False
                }
            }
        )

    # 1. Check if event exists
    err_resp = check_event_exists(event_id)
    if err_resp:
        # Wrap the error response with request_id and tool name
        err_data = json.loads(err_resp.body.decode('utf-8'))
        err_data["request_id"] = request_id
        err_data["tool"] = tool_name
        return JSONResponse(status_code=err_resp.status_code, content=err_data)

    # 2. Dry-run Mode
    if mode in ("dry_run", "dry-run"):
        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "status": "dry_run",
                "tool": tool_name,
                "result": {
                    "external_response_id": None,
                    "would_create": True
                },
                "error": None
            }
        )

    # 3. Post Mode
    elif mode == "post":
        post_url = f"{BOARD_BASE_URL}/events/{event_id}/responses"
        payload = {
            "author": author,
            "content": message,
            "response_type": "comment"
        }
        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                post_url,
                data=req_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_body = response.read().decode('utf-8')
                board_res = json.loads(res_body)
                response_id = board_res.get("id")

            return JSONResponse(
                status_code=200,
                content={
                    "request_id": request_id,
                    "status": "success",
                    "tool": tool_name,
                    "result": {
                        "external_response_id": response_id,
                        "external_event_id": event_id,
                        "url": f"http://localhost:8091/events/{event_id}#response-{response_id}"
                    },
                    "error": None
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
                        "code": "FACTORY_BOARD_ERROR",
                        "message": f"Failed to post response to board API: {str(e)}",
                        "retryable": True
                    }
                }
            )
    else:
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

# Tool 3: maintenance_task.create
@app.post("/mcp/tools/maintenance_task.create")
async def execute_maintenance_task(request: Request):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Malformed JSON request: {str(e)}",
                    "retryable": False
                }
            }
        )

    request_id = data.get("request_id") or "unknown"
    tool_name = "maintenance_task.create"
    mode = data.get("mode", "dry_run")
    
    # Validation of tenant context
    company_id = data.get("company_id") or (data.get("tenant_context") or {}).get("company_id")
    project_id = data.get("project_id") or (data.get("tenant_context") or {}).get("project_id")
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
                    "message": "Required fields (company_id, project_id) are missing.",
                    "retryable": False
                }
            }
        )

    args = data.get("arguments") or data.get("args") or {}
    event_id = args.get("factory_event_id")
    equipment_name = args.get("equipment_name")
    fault_message = args.get("fault_message")
    assigned_team = args.get("assigned_team") or "정비팀"
    priority = args.get("priority") or "medium"
    message = args.get("message")

    if not event_id or not equipment_name or not message:
        return JSONResponse(
            status_code=400,
            content={
                "request_id": request_id,
                "status": "error",
                "tool": tool_name,
                "result": None,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Arguments must contain factory_event_id, equipment_name, and message.",
                    "retryable": False
                }
            }
        )

    # 1. Check if event exists
    err_resp = check_event_exists(event_id)
    if err_resp:
        err_data = json.loads(err_resp.body.decode('utf-8'))
        err_data["request_id"] = request_id
        err_data["tool"] = tool_name
        return JSONResponse(status_code=err_resp.status_code, content=err_data)

    # 2. Dry-run Mode
    if mode in ("dry_run", "dry-run"):
        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "status": "dry_run",
                "tool": tool_name,
                "result": {
                    "external_task_id": None,
                    "would_create": True
                },
                "error": None
            }
        )

    # 3. Post Mode
    elif mode == "post":
        post_url = f"{BOARD_BASE_URL}/maintenance-tasks"
        payload = {
            "factory_event_id": event_id,
            "equipment_name": equipment_name,
            "fault_message": fault_message,
            "assigned_team": assigned_team,
            "priority": priority,
            "message": message
        }
        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                post_url,
                data=req_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_body = response.read().decode('utf-8')
                board_res = json.loads(res_body)
                task_id = board_res.get("id")

            return JSONResponse(
                status_code=200,
                content={
                    "request_id": request_id,
                    "status": "success",
                    "tool": tool_name,
                    "result": {
                        "external_task_id": task_id,
                        "external_event_id": event_id,
                        "assigned_team": assigned_team
                    },
                    "error": None
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
                        "code": "FACTORY_BOARD_ERROR",
                        "message": f"Failed to create maintenance task on board API: {str(e)}",
                        "retryable": True
                    }
                }
            )
    else:
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

# Standard entry redirects for any general request mapping to tool
@app.post("/")
@app.post("/mcp")
async def execute_legacy_mcp(request: Request):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode('utf-8'))
        tool = data.get("tool")
        if tool == "factory_event.list":
            return await execute_event_list(request)
        elif tool == "factory_response.create":
            return await execute_response_create(request)
        elif tool == "maintenance_task.create":
            return await execute_maintenance_task(request)
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "request_id": data.get("request_id", "unknown"),
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
                "status": "error",
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Malformed request: {str(e)}"
                }
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)
