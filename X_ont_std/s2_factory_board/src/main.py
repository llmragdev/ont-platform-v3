import os
import sqlite3
import uuid
import threading
import json
import urllib.request
import urllib.error
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

app = FastAPI(title="Factory Mock Board API - Scenario 2", version="1.0.0")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "s2_factory_board.db")

# In-memory webhook event logs for UI visualization
webhook_logs = []

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create factory_events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factory_events (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        factory_name TEXT NOT NULL,
        line_name TEXT NOT NULL,
        process_step TEXT NOT NULL,
        equipment_name TEXT NOT NULL,
        fault_message TEXT,
        severity TEXT NOT NULL DEFAULT 'medium',
        occurred_at TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        reporter TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        created_at TEXT NOT NULL
    )
    """)
    
    # 2. Create factory_responses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factory_responses (
        id TEXT PRIMARY KEY,
        event_id TEXT NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        response_type TEXT NOT NULL DEFAULT 'comment',
        created_at TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES factory_events (id) ON DELETE CASCADE
    )
    """)
    
    # 3. Create maintenance_tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maintenance_tasks (
        id TEXT PRIMARY KEY,
        factory_event_id TEXT NOT NULL,
        equipment_name TEXT NOT NULL,
        fault_message TEXT,
        assigned_team TEXT NOT NULL,
        priority TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (factory_event_id) REFERENCES factory_events (id) ON DELETE CASCADE
    )
    """)
    
    # 4. Create settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    # Pre-populate default settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("webhook_enabled", "true"))
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("webhook_mode", "post"))
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("webhook_target", "http://localhost:8001/api/extn/factory-events/events"))
    
    # Insert initial seed event if empty
    cursor.execute("SELECT COUNT(*) FROM factory_events")
    if cursor.fetchone()[0] == 0:
        event_id = "fe-001"
        created_time = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO factory_events (
            id, category, factory_name, line_name, process_step, equipment_name, 
            fault_message, severity, occurred_at, title, content, reporter, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            "equipment_fault",
            "세종 배터리팩 공장",
            "3번 조립 라인",
            "용접 단계",
            "배터리 탭 용접기",
            "압력이 낮습니다",
            "high",
            "2026-06-13T10:00:00+09:00",
            "[공장] 배터리 탭 용접기 압력 낮음 오류",
            "오전 10시에 배터리 탭 용접기가 멈췄습니다. 화면에 압력이 낮습니다라는 오류가 떴습니다. 다시 켜니 일단 움직입니다.",
            "라인 작업자",
            "open",
            created_time
        ))
        
        # Add a seed response to represent initial observation
        cursor.execute("""
        INSERT INTO factory_responses (id, event_id, author, content, response_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "fr-seed",
            event_id,
            "system-bot",
            "배터리 탭 용접기 압력 오류 접수되었습니다. 추가 알림이나 고장이 반복되는지 확인하겠습니다.",
            "comment",
            created_time
        ))
        
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

# DB Helpers
def load_settings() -> Dict[str, Any]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    rows = c.fetchall()
    conn.close()
    
    cfg = {
        "webhook_enabled": True,
        "webhook_mode": "post",
        "webhook_target": "http://localhost:8001/api/extn/factory-events/events"
    }
    for r in rows:
        key, val = r["key"], r["value"]
        if key == "webhook_enabled":
            cfg["webhook_enabled"] = val.lower() == "true"
        elif key == "webhook_mode":
            cfg["webhook_mode"] = val
        elif key == "webhook_target":
            cfg["webhook_target"] = val
    return cfg

def save_db_settings(cfg: Dict[str, Any]):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("webhook_enabled", str(cfg["webhook_enabled"]).lower()))
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("webhook_mode", cfg["webhook_mode"]))
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("webhook_target", cfg["webhook_target"]))
    conn.commit()
    conn.close()

# Models
class EventCreate(BaseModel):
    category: str
    factory_name: str
    line_name: str
    process_step: str
    equipment_name: str
    fault_message: Optional[str] = None
    severity: str = "medium"
    occurred_at: str
    title: str
    content: str
    reporter: str

class ResponseCreate(BaseModel):
    author: str
    content: str
    response_type: str = "comment"

class MaintenanceTaskCreate(BaseModel):
    factory_event_id: str
    equipment_name: str
    fault_message: Optional[str] = None
    assigned_team: str
    priority: str = "medium"
    message: str

class SettingsUpdate(BaseModel):
    webhook_enabled: bool
    webhook_mode: str
    webhook_target: str

# Webhook Dispatcher
def trigger_webhook_background(event_data: Dict[str, Any]):
    cfg = load_settings()
    if not cfg["webhook_enabled"]:
        return
        
    event_id = f"evt-{uuid.uuid4()}"
    payload = {
        "event_id": event_id,
        "event_type": "factory_event.created",
        "factory_event_id": event_data["id"],
        "category": event_data["category"],
        "factory_name": event_data["factory_name"],
        "line_name": event_data["line_name"],
        "process_step": event_data["process_step"],
        "equipment_name": event_data["equipment_name"],
        "fault_message": event_data["fault_message"],
        "severity": event_data["severity"],
        "occurred_at": event_data["occurred_at"],
        "title": event_data["title"],
        "content": event_data["content"],
        "reporter": event_data["reporter"],
        "mode": cfg["webhook_mode"],
        "metadata": {
            "source": "factory_board"
        }
    }
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "event_id": event_id,
        "factory_event_id": event_data["id"],
        "title": event_data["title"],
        "status": "pending",
        "mode": cfg["webhook_mode"],
        "response": None,
        "error": None
    }
    webhook_logs.insert(0, log_entry)
    if len(webhook_logs) > 20:
        webhook_logs.pop()
        
    def run():
        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                cfg["webhook_target"],
                data=req_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-Company-Id': 'demo-co',
                    'X-Project-Id': 'proj-01',
                    'X-User-Id': 'factory-board'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_body = resp.read().decode('utf-8')
                res_json = json.loads(res_body)
                log_entry["status"] = "success"
                log_entry["response"] = res_json
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode('utf-8')
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message") or err_json.get("detail") or err_body
            except Exception:
                err_msg = str(e)
            log_entry["status"] = "failed"
            log_entry["error"] = f"HTTP {e.code}: {err_msg[:100]}"
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = f"Connection failed: {str(e)[:100]}"
            
    threading.Thread(target=run).start()

# API Endpoints
@app.get("/health")
@app.get("/api/health")
def get_health():
    return {"status": "ok", "service": "factory_board"}

@app.get("/api/settings")
def get_settings():
    return load_settings()

@app.post("/api/settings")
def update_settings(update: SettingsUpdate):
    if update.webhook_mode not in ("dry_run", "post"):
        raise HTTPException(status_code=400, detail="Invalid webhook_mode. Must be 'dry_run' or 'post'.")
    cfg = {
        "webhook_enabled": update.webhook_enabled,
        "webhook_mode": update.webhook_mode,
        "webhook_target": update.webhook_target
    }
    save_db_settings(cfg)
    return cfg

@app.get("/api/webhook-logs")
def get_webhook_logs():
    return {"logs": webhook_logs}

@app.post("/api/webhook-logs/clear")
def clear_webhook_logs():
    webhook_logs.clear()
    return {"status": "cleared"}

@app.get("/api/factory/events")
def get_events():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM factory_events ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/factory/events/open")
def get_open_events(limit: int = 20):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM factory_events WHERE status = 'open' ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.get("/api/factory/events/{event_id}")
def get_event(event_id: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM factory_events WHERE id = ?", (event_id,))
    event_row = c.fetchone()
    if not event_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
    
    event = dict(event_row)
    
    c.execute("SELECT * FROM factory_responses WHERE event_id = ? ORDER BY created_at ASC", (event_id,))
    responses = [dict(r) for r in c.fetchall()]
    event["responses"] = responses
    
    c.execute("SELECT * FROM maintenance_tasks WHERE factory_event_id = ? ORDER BY created_at ASC", (event_id,))
    tasks = [dict(t) for t in c.fetchall()]
    event["maintenance_tasks"] = tasks
    
    conn.close()
    return event

@app.post("/api/factory/events")
def create_event(event: EventCreate, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    c = conn.cursor()
    
    event_id = "fe-" + str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()
    
    c.execute("""
    INSERT INTO factory_events (
        id, category, factory_name, line_name, process_step, equipment_name, 
        fault_message, severity, occurred_at, title, content, reporter, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        event.category,
        event.factory_name,
        event.line_name,
        event.process_step,
        event.equipment_name,
        event.fault_message,
        event.severity,
        event.occurred_at,
        event.title,
        event.content,
        event.reporter,
        "open",
        created_at
    ))
    conn.commit()
    conn.close()
    
    event_dict = {
        "id": event_id,
        "category": event.category,
        "factory_name": event.factory_name,
        "line_name": event.line_name,
        "process_step": event.process_step,
        "equipment_name": event.equipment_name,
        "fault_message": event.fault_message,
        "severity": event.severity,
        "occurred_at": event.occurred_at,
        "title": event.title,
        "content": event.content,
        "reporter": event.reporter,
        "status": "open",
        "created_at": created_at
    }
    
    cfg = load_settings()
    webhook_status = "disabled"
    if cfg["webhook_enabled"]:
        background_tasks.add_task(trigger_webhook_background, event_dict)
        webhook_status = "sent"
        
    return {
        "id": event_id,
        "status": "open",
        "webhook": {
            "enabled": cfg["webhook_enabled"],
            "status": webhook_status,
            "target": cfg["webhook_target"]
        }
    }

@app.post("/api/factory/events/{event_id}/responses")
def create_response(event_id: str, res: ResponseCreate):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM factory_events WHERE id = ?", (event_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
        
    res_id = "fr-" + str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()
    
    c.execute("""
    INSERT INTO factory_responses (id, event_id, author, content, response_type, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (res_id, event_id, res.author, res.content, res.response_type, created_at))
    conn.commit()
    conn.close()
    
    return {"id": res_id, "event_id": event_id, "status": "created"}

@app.post("/api/factory/maintenance-tasks")
def create_maintenance_task(task: MaintenanceTaskCreate):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM factory_events WHERE id = ?", (task.factory_event_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
        
    task_id = "mt-" + str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()
    
    c.execute("""
    INSERT INTO maintenance_tasks (id, factory_event_id, equipment_name, fault_message, assigned_team, priority, message, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (task_id, task.factory_event_id, task.equipment_name, task.fault_message, task.assigned_team, task.priority, task.message, created_at))
    
    # Update event status if upgraded to show repeating/escalated status
    c.execute("UPDATE factory_events SET status = 'repeated' WHERE id = ?", (task.factory_event_id,))
    
    conn.commit()
    conn.close()
    
    return {
        "id": task_id,
        "event_id": task.factory_event_id,
        "status": "created",
        "assigned_team": task.assigned_team
    }

@app.post("/api/simulate/webhook/{event_id}")
def simulate_webhook(event_id: str, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM factory_events WHERE id = ?", (event_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event_dict = dict(row)
    background_tasks.add_task(trigger_webhook_background, event_dict)
    return {"status": "triggered", "event_id": event_id}

# Embedding Premium Front-End UI
HTML_CONTENT = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>공장 자동화 모의 시스템 (s2_factory_board)</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0c10;
            --panel-bg: #1f2833;
            --panel-sidebar: #151a21;
            --accent-color: #ffaa00; /* Industrial Amber */
            --accent-hover: #e09600;
            --text-main: #f1f1f1;
            --text-muted: #a1a1a1;
            --border-color: #2c3540;
            --success-color: #00e676;
            --failed-color: #ff1744;
            --comment-bg: #27303d;
            --task-bg: #322514;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', 'Noto Sans KR', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
            padding: 2rem;
            min-height: 100vh;
        }

        .container {
            max-width: 1500px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1.6fr 1.2fr;
            gap: 1.5rem;
        }

        header {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 1rem;
        }

        header h1 {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffaa00, #ff5500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .system-badge {
            background-color: rgba(255, 170, 0, 0.12);
            border: 1px solid var(--accent-color);
            color: var(--accent-color);
            padding: 0.4rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .panel {
            background-color: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.8rem;
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            height: 78vh;
        }

        .panel-header {
            margin-bottom: 1.2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-title {
            font-size: 1.25rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn {
            background-color: var(--accent-color);
            color: #000;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
        }

        .btn:hover {
            background-color: var(--accent-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background-color: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }

        .demo-story-panel {
            background-color: rgba(255, 170, 0, 0.04);
            border: 1px dashed var(--accent-color);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1.2rem;
        }

        .demo-story-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .demo-buttons-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }

        .btn-demo-inject {
            background-color: #27303d;
            color: #ffaa00;
            border: 1px solid #445366;
            padding: 0.5rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            text-align: left;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-demo-inject:hover {
            background-color: #384558;
            border-color: #ffaa00;
        }

        .event-list {
            overflow-y: auto;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }

        .event-item {
            border: 1px solid var(--border-color);
            background-color: rgba(255, 255, 255, 0.01);
            padding: 1rem;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
            position: relative;
        }

        .event-item:hover, .event-item.active {
            border-color: var(--accent-color);
            background-color: rgba(255, 170, 0, 0.03);
        }

        .event-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }

        .event-title {
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .event-tags {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }

        .badge {
            font-size: 0.7rem;
            padding: 0.1rem 0.5rem;
            border-radius: 4px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-fault {
            background-color: rgba(255, 23, 68, 0.15);
            color: #ff1744;
            border: 1px solid rgba(255, 23, 68, 0.3);
        }

        .badge-quality {
            background-color: rgba(170, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(170, 85, 247, 0.3);
        }

        .badge-severity-critical {
            background-color: #ff1744;
            color: #000;
        }

        .badge-severity-high {
            background-color: #ff5500;
            color: #fff;
        }

        .badge-severity-medium {
            background-color: #ffaa00;
            color: #000;
        }

        .badge-status-open {
            border: 1px solid var(--accent-color);
            color: var(--accent-color);
        }

        .badge-status-repeated {
            background-color: rgba(255, 170, 0, 0.15);
            color: #ffaa00;
            border: 1px solid var(--accent-color);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        .detail-scroll {
            overflow-y: auto;
            flex-grow: 1;
            padding-right: 0.5rem;
        }

        .detail-header-card {
            border: 1px solid var(--border-color);
            background-color: rgba(255, 255, 255, 0.01);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
        }

        .detail-title {
            font-size: 1.3rem;
            font-weight: 800;
            margin-bottom: 0.8rem;
            color: var(--accent-color);
        }

        .grid-props {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }

        .prop-item {
            display: flex;
            flex-direction: column;
        }

        .prop-label {
            color: var(--text-muted);
            font-size: 0.75rem;
            font-weight: 600;
        }

        .prop-val {
            font-weight: 500;
        }

        .detail-body {
            font-size: 0.95rem;
            background-color: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 8px;
            white-space: pre-line;
            border-left: 3px solid var(--accent-color);
        }

        .section-subtitle {
            font-size: 1.05rem;
            font-weight: 700;
            margin: 1.5rem 0 0.8rem 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.4rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .responses-list {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }

        .response-item {
            background-color: var(--comment-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.8rem 1rem;
        }

        .response-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.3rem;
        }

        .response-author {
            font-weight: 700;
            color: var(--accent-color);
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .badge-wf {
            background-color: rgba(0, 230, 118, 0.15);
            color: #00e676;
            border: 1px solid rgba(0, 230, 118, 0.3);
            font-size: 0.65rem;
            padding: 0.05rem 0.3rem;
            border-radius: 4px;
        }

        .tasks-list {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }

        .task-item {
            background-color: var(--task-bg);
            border: 1px solid #ffaa003a;
            border-left: 4px solid var(--accent-color);
            border-radius: 8px;
            padding: 1rem;
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.4rem;
        }

        .task-body {
            font-size: 0.88rem;
        }

        .write-comment-form {
            margin-top: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }

        .write-comment-form textarea {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: #fff;
            padding: 0.8rem;
            font-family: inherit;
            resize: none;
            height: 80px;
        }

        .write-comment-form textarea:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        .config-card {
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
        }

        .config-group {
            margin-bottom: 0.8rem;
        }

        .config-group label {
            display: block;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.3rem;
        }

        .toggle-switch {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            font-weight: 600;
        }

        .select-input, .text-input {
            width: 100%;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: white;
            padding: 0.5rem 0.8rem;
            font-family: inherit;
            font-size: 0.85rem;
        }

        .select-input:focus, .text-input:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        .log-section {
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            overflow: hidden;
        }

        .log-list {
            flex-grow: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            font-size: 0.8rem;
        }

        .log-item {
            border-left: 3px solid var(--border-color);
            background-color: rgba(255, 255, 255, 0.01);
            padding: 0.6rem 0.8rem;
            border-radius: 0 8px 8px 0;
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .log-item.success { border-left-color: var(--success-color); }
        .log-item.failed { border-left-color: var(--failed-color); }
        .log-item.pending { border-left-color: var(--accent-color); }

        .log-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .log-error {
            color: var(--failed-color);
            font-size: 0.75rem;
            word-break: break-all;
        }

        dialog {
            background-color: var(--panel-bg);
            color: white;
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            max-width: 550px;
            width: 90%;
            margin: auto;
        }

        dialog::backdrop {
            background-color: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
        }

        dialog form {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        dialog label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        dialog input, dialog textarea, dialog select {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: white;
            padding: 0.6rem 0.8rem;
            font-family: inherit;
            width: 100%;
        }

        dialog textarea {
            height: 80px;
            resize: none;
        }

        .dialog-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>공장 자동화 모의 게시판 시스템 <span>(s2_factory_board)</span></h1>
            <div class="system-badge">Port 8091 - SQLite Active</div>
        </header>

        <!-- Left Column: Event List -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">⚠️ 현장 고장 요청 건</div>
                <button class="btn" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;" onclick="openCreateModal()">수동 등록</button>
            </div>

            <!-- Demo Story Inject Panel -->
            <div class="demo-story-panel">
                <div class="demo-story-title">⚡ 데모 시나리오 순차 인입</div>
                <div class="demo-buttons-grid">
                    <button class="btn-demo-inject" onclick="injectDemo(1)">1. 첫 고장 접수 (용접기 압력 부족)</button>
                    <button class="btn-demo-inject" onclick="injectDemo(2)">2. 반복 고장 접수 (동일 압력 재발)</button>
                    <button class="btn-demo-inject" onclick="injectDemo(3)">3. 품질 불량 감지 (검사 카메라 이상)</button>
                </div>
            </div>

            <div class="event-list" id="eventList">
                <!-- Dynamic events render here -->
            </div>
        </div>

        <!-- Middle Column: Event Details & Responses & Work Orders -->
        <div class="panel" id="detailPanel">
            <div style="margin: auto; text-align: center; color: var(--text-muted);">
                <h3>조회할 요청을 선택하세요.</h3>
                <p style="margin-top: 0.5rem; font-size: 0.9rem;">왼쪽 목록의 이벤트를 클릭하면 상세 사양과 AI 댓글, 정비 지시서를 볼 수 있습니다.</p>
            </div>
        </div>

        <!-- Right Column: Settings & Webhook logs -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">⚙️ 시나리오 2 설정</div>
            </div>

            <div class="config-card">
                <div class="config-group">
                    <label class="toggle-switch">
                        <input type="checkbox" id="webhookToggle" onchange="saveSettings()">
                        <span>실시간 Webhook 자동 트리거</span>
                    </label>
                </div>

                <div class="config-group">
                    <label for="webhookMode">연동 실행 모드</label>
                    <select id="webhookMode" class="select-input" onchange="saveSettings()">
                        <option value="dry_run">Dry-run (검증 전용)</option>
                        <option value="post">Post (실제 댓글 등록)</option>
                    </select>
                </div>

                <div class="config-group">
                    <label for="webhookTarget">Webhook Target URL</label>
                    <input type="text" id="webhookTarget" class="text-input" onchange="saveSettings()">
                </div>
            </div>

            <div class="log-section">
                <div class="panel-header" style="margin-bottom: 0.6rem;">
                    <div class="panel-title" style="font-size: 0.95rem;">🔔 Webhook 실행 로그</div>
                    <button class="btn btn-secondary" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;" onclick="clearLogs()">비우기</button>
                </div>
                <div class="log-list" id="logList">
                    <!-- Webhook logs here -->
                </div>
            </div>
        </div>
    </div>

    <!-- Create Custom Event Dialog -->
    <dialog id="createDialog">
        <h2>수동 현장 요청 등록</h2>
        <form onsubmit="handleCreateEvent(event)">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div>
                    <label for="evtCategory">카테고리</label>
                    <select id="evtCategory" required>
                        <option value="equipment_fault">장비 고장 (Fault)</option>
                        <option value="quality_issue">품질 문제 (Quality)</option>
                        <option value="maintenance_request">정비 요청 (Maintenance)</option>
                    </select>
                </div>
                <div>
                    <label for="evtSeverity">심각도</label>
                    <select id="evtSeverity" required>
                        <option value="low">낮음 (Low)</option>
                        <option value="medium" selected>보통 (Medium)</option>
                        <option value="high">높음 (High)</option>
                        <option value="critical">긴급 (Critical)</option>
                    </select>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div>
                    <label for="evtFactory">공장명</label>
                    <input type="text" id="evtFactory" required value="세종 배터리팩 공장">
                </div>
                <div>
                    <label for="evtLine">라인명</label>
                    <input type="text" id="evtLine" required value="3번 조립 라인">
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div>
                    <label for="evtStep">공정단계</label>
                    <input type="text" id="evtStep" required placeholder="예: 용접 단계">
                </div>
                <div>
                    <label for="evtEquipment">대상설비</label>
                    <input type="text" id="evtEquipment" required placeholder="예: 배터리 탭 용접기">
                </div>
            </div>

            <div>
                <label for="evtFaultMessage">설비 오류 코드/메시지</label>
                <input type="text" id="evtFaultMessage" placeholder="예: E-404 압력 부족">
            </div>

            <div>
                <label for="evtTitle">요청 제목</label>
                <input type="text" id="evtTitle" required placeholder="요청 요약">
            </div>

            <div>
                <label for="evtContent">상세 내용</label>
                <textarea id="evtContent" required placeholder="현장의 고장 및 문제 발생 상세 설명"></textarea>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div>
                    <label for="evtReporter">보고자</label>
                    <input type="text" id="evtReporter" required value="현장 작업자">
                </div>
                <div>
                    <label for="evtOccurred">발생시각</label>
                    <input type="text" id="evtOccurred" required>
                </div>
            </div>

            <div class="dialog-actions">
                <button class="btn btn-secondary" type="button" onclick="closeCreateModal()">취소</button>
                <button class="btn" type="submit">등록</button>
            </div>
        </form>
    </dialog>

    <script>
        let events = [];
        let selectedId = null;

        // Formats ISO string into cleaner format
        function formatDate(isoStr) {
            try {
                if(!isoStr) return "";
                const d = new Date(isoStr);
                return d.toLocaleString('ko-KR', { hour12: false });
            } catch(e) {
                return isoStr;
            }
        }

        // Initialize view
        window.addEventListener('DOMContentLoaded', () => {
            fetchSettings();
            fetchEvents();
            fetchLogs();
            
            // Set current time for manual event popup
            document.getElementById('evtOccurred').value = new Date().toISOString();

            // Auto-refresh loops
            setInterval(() => {
                fetchEventsQuietly();
                fetchLogs();
                if (selectedId) {
                    fetchSelectedEventDetailQuietly(selectedId);
                }
            }, 3000);
        });

        async function fetchSettings() {
            try {
                const res = await fetch('/api/settings');
                const cfg = await res.json();
                document.getElementById('webhookToggle').checked = cfg.webhook_enabled;
                document.getElementById('webhookMode').value = cfg.webhook_mode;
                document.getElementById('webhookTarget').value = cfg.webhook_target;
            } catch(e) { console.error("Error settings:", e); }
        }

        async function saveSettings() {
            const webhook_enabled = document.getElementById('webhookToggle').checked;
            const webhook_mode = document.getElementById('webhookMode').value;
            const webhook_target = document.getElementById('webhookTarget').value.trim();
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ webhook_enabled, webhook_mode, webhook_target })
                });
            } catch(e) { console.error("Error saving settings:", e); }
        }

        async function fetchLogs() {
            try {
                const res = await fetch('/api/webhook-logs');
                const data = await res.json();
                renderLogs(data.logs);
            } catch(e) { console.error("Error logs:", e); }
        }

        function renderLogs(logs) {
            const listEl = document.getElementById('logList');
            if(logs.length === 0) {
                listEl.innerHTML = '<div style="margin: auto; color: var(--text-muted); font-size: 0.8rem; text-align:center; padding-top: 2rem;">로그가 없습니다.</div>';
                return;
            }
            listEl.innerHTML = logs.map(l => {
                let statusClass = l.status; // success, failed, pending
                return `
                    <div class="log-item ${statusClass}">
                        <div class="log-header">
                            <strong>${l.timestamp} [${l.mode.toUpperCase()}]</strong>
                            <span class="badge badge-status-${l.status}">${l.status}</span>
                        </div>
                        <div style="font-weight: 600; font-size: 0.78rem; margin: 0.1rem 0;">${l.title}</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted);">${l.event_id}</div>
                        ${l.error ? `<div class="log-error">${l.error}</div>` : ''}
                    </div>
                `;
            }).join('');
        }

        async function clearLogs() {
            try {
                await fetch('/api/webhook-logs/clear', { method: 'POST' });
                fetchLogs();
            } catch(e) { console.error(e); }
        }

        async function fetchEvents() {
            try {
                const res = await fetch('/api/factory/events');
                events = await res.json();
                renderEventList();
            } catch(e) { console.error(e); }
        }

        async function fetchEventsQuietly() {
            try {
                const res = await fetch('/api/factory/events');
                const fresh = await res.json();
                if(JSON.stringify(fresh) !== JSON.stringify(events)) {
                    events = fresh;
                    renderEventList();
                }
            } catch(e) { console.error(e); }
        }

        function renderEventList() {
            const container = document.getElementById('eventList');
            if(events.length === 0) {
                container.innerHTML = '<div style="margin:auto; color: var(--text-muted); padding-top: 4rem; text-align:center;">등록된 요청 건이 없습니다.</div>';
                return;
            }
            container.innerHTML = events.map(e => {
                const activeClass = e.id === selectedId ? 'active' : '';
                const catBadge = e.category === 'equipment_fault' 
                    ? '<span class="badge badge-fault">장비 고장</span>' 
                    : '<span class="badge badge-quality">품질 이상</span>';
                return `
                    <div class="event-item ${activeClass}" onclick="selectEvent('${e.id}')">
                        <div class="event-meta">
                            <span>${e.id}</span>
                            <span>${formatDate(e.occurred_at)}</span>
                        </div>
                        <div class="event-title">${e.title}</div>
                        <div class="event-tags">
                            ${catBadge}
                            <span class="badge badge-severity-${e.severity}">${e.severity}</span>
                            <span class="badge badge-status-${e.status}">${e.status}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function selectEvent(id) {
            selectedId = id;
            renderEventList(); // update active class
            fetchSelectedEventDetail(id);
        }

        async function fetchSelectedEventDetail(id) {
            const panel = document.getElementById('detailPanel');
            panel.innerHTML = '<div style="margin:auto; text-align:center;"><span style="color: var(--accent-color); font-weight:700;">상세 정보 로드 중...</span></div>';
            try {
                const res = await fetch(`/api/factory/events/${id}`);
                const event = await res.json();
                renderEventDetail(event);
            } catch(e) {
                panel.innerHTML = `<div style="margin:auto; text-align:center; color: var(--failed-color);">오류가 발생했습니다: ${e.message}</div>`;
            }
        }

        async function fetchSelectedEventDetailQuietly(id) {
            try {
                const res = await fetch(`/api/factory/events/${id}`);
                const event = await res.json();
                // Find and update comment lists quietly to prevent input focus jitter
                const commentsContainer = document.getElementById('commentsContainer');
                if (commentsContainer) {
                    const currentCommentCount = commentsContainer.querySelectorAll('.response-item').length;
                    if(event.responses.length !== currentCommentCount) {
                        renderResponsesOnly(event.responses);
                    }
                }
                const tasksContainer = document.getElementById('tasksContainer');
                if (tasksContainer) {
                    const currentTaskCount = tasksContainer.querySelectorAll('.task-item').length;
                    if(event.maintenance_tasks.length !== currentTaskCount) {
                        renderTasksOnly(event.maintenance_tasks);
                    }
                }
                // Also update status badges
                const statusBadgeEl = document.getElementById('detailStatusBadge');
                if(statusBadgeEl && statusBadgeEl.innerText !== event.status.toUpperCase()) {
                    statusBadgeEl.innerText = event.status.toUpperCase();
                    statusBadgeEl.className = `badge badge-status-${event.status}`;
                }
            } catch(e) { console.error(e); }
        }

        function renderResponsesOnly(responses) {
            const container = document.getElementById('commentsContainer');
            if(responses.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding: 0.5rem 0;">코멘트가 없습니다.</div>';
                return;
            }
            container.innerHTML = responses.map(r => {
                const isWf = r.author === 'ontology-workflow' ? '<span class="badge-wf">AI Workflow</span>' : '';
                return `
                    <div class="response-item">
                        <div class="response-meta">
                            <span class="response-author">${r.author} ${isWf}</span>
                            <span>${formatDate(r.created_at)}</span>
                        </div>
                        <div style="font-size: 0.9rem;">${r.content}</div>
                    </div>
                `;
            }).join('');
        }

        function renderTasksOnly(tasks) {
            const container = document.getElementById('tasksContainer');
            if(tasks.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding: 0.5rem 0;">등록된 정비지시서가 없습니다.</div>';
                return;
            }
            container.innerHTML = tasks.map(t => {
                return `
                    <div class="task-item">
                        <div class="task-header">
                            <span>지시 ID: ${t.id} (배정팀: ${t.assigned_team})</span>
                            <span class="badge badge-severity-${t.priority}">우선순위: ${t.priority}</span>
                        </div>
                        <div class="task-body">
                            <div style="font-weight: 700; margin-bottom: 0.2rem;">대상 설비: ${t.equipment_name} (${t.fault_message || ''})</div>
                            <div style="color: var(--text-muted); font-size:0.85rem;">내용: ${t.message}</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function renderEventDetail(event) {
            const panel = document.getElementById('detailPanel');
            panel.innerHTML = `
                <div class="panel-header">
                    <div class="panel-title">📡 현장 요청 상세 (${event.id})</div>
                    <div>
                        <span id="detailStatusBadge" class="badge badge-status-${event.status}">${event.status}</span>
                        <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size:0.75rem; margin-left:0.5rem;" onclick="simulateManualWebhook('${event.id}')">웹훅 수동 전송</button>
                    </div>
                </div>

                <div class="detail-scroll">
                    <div class="detail-header-card">
                        <div class="detail-title">${event.title}</div>
                        
                        <div class="grid-props">
                            <div class="prop-item">
                                <span class="prop-label">공장 / 라인</span>
                                <span class="prop-val">${event.factory_name} > ${event.line_name}</span>
                            </div>
                            <div class="prop-item">
                                <span class="prop-label">공정 / 설비</span>
                                <span class="prop-val">${event.process_step} > ${event.equipment_name}</span>
                            </div>
                            <div class="prop-item">
                                <span class="prop-label">에러 메시지</span>
                                <span class="prop-val" style="color: var(--failed-color);">${event.fault_message || '없음'}</span>
                            </div>
                            <div class="prop-item">
                                <span class="prop-label">발생 시각</span>
                                <span class="prop-val">${formatDate(event.occurred_at)}</span>
                            </div>
                        </div>

                        <div class="detail-body">${event.content}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem; text-align:right;">
                            보고자: ${event.reporter} | 등록시각: ${formatDate(event.created_at)}
                        </div>
                    </div>

                    <!-- Maintenance Tasks Section -->
                    <div class="section-subtitle">🛠️ 정비 지시서 (Maintenance Work Orders)</div>
                    <div class="tasks-list" id="tasksContainer"></div>

                    <!-- Responses Section -->
                    <div class="section-subtitle">💬 피드백 및 조치 댓글</div>
                    <div class="responses-list" id="commentsContainer"></div>

                    <!-- Manual Comment Form -->
                    <form class="write-comment-form" onsubmit="handlePostComment(event, '${event.id}')">
                        <textarea id="commentText" required placeholder="댓글 또는 수동 조치 사항을 작성해 주세요."></textarea>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.8rem; color:var(--text-muted);">작성자: 현장 관리인</span>
                            <button class="btn" style="padding: 0.4rem 1rem; font-size:0.8rem;" type="submit">댓글 등록</button>
                        </div>
                    </form>
                </div>
            `;
            
            // Render subsets
            renderResponsesOnly(event.responses);
            renderTasksOnly(event.maintenance_tasks);
        }

        async function handlePostComment(event, eventId) {
            event.preventDefault();
            const txt = document.getElementById('commentText').value.trim();
            if(!txt) return;
            try {
                await fetch(`/api/factory/events/${eventId}/responses`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ author: '현장 관리인', content: txt, response_type: 'comment' })
                });
                document.getElementById('commentText').value = "";
                fetchSelectedEventDetail(eventId);
            } catch(e) { alert("Error: " + e.message); }
        }

        async function simulateManualWebhook(eventId) {
            try {
                const res = await fetch(`/api/simulate/webhook/${eventId}`, { method: 'POST' });
                const out = await res.json();
                fetchLogs();
                alert("웹훅 전송 요청을 완료했습니다.");
            } catch(e) { alert(e.message); }
        }

        // Demo Inject helper
        async function injectDemo(step) {
            let payload = {};
            const baseTime = new Date().toISOString();
            
            if(step === 1) {
                payload = {
                    category: "equipment_fault",
                    factory_name: "세종 배터리팩 공장",
                    line_name: "3번 조립 라인",
                    process_step: "용접 단계",
                    equipment_name: "배터리 탭 용접기",
                    fault_message: "압력이 낮습니다",
                    severity: "high",
                    occurred_at: baseTime,
                    title: "[공장] 배터리 탭 용접기 압력 낮음 오류",
                    content: "오전 10시에 배터리 탭 용접기가 멈췄습니다. 화면에 압력이 낮습니다라는 오류가 떴습니다. 장비를 다시 기동하여 가동 상태를 주시 중입니다.",
                    reporter: "라인 작업자"
                };
            } else if(step === 2) {
                payload = {
                    category: "equipment_fault",
                    factory_name: "세종 배터리팩 공장",
                    line_name: "3번 조립 라인",
                    process_step: "용접 단계",
                    equipment_name: "배터리 탭 용접기",
                    fault_message: "압력이 낮습니다",
                    severity: "critical",
                    occurred_at: baseTime,
                    title: "[공장] 배터리 탭 용접기 압력 낮음 반복 고장",
                    content: "오전 11시에 같은 장비가 같은 오류로 다시 멈췄습니다. 금일 누적 2회째 고장 발생으로 용접 압력 실린더 계통의 점검이 시급해 보입니다. 작업이 약 15분 정도 중단되었습니다.",
                    reporter: "라인 작업자"
                };
            } else if(step === 3) {
                payload = {
                    category: "quality_issue",
                    factory_name: "세종 배터리팩 공장",
                    line_name: "3번 조립 라인",
                    process_step: "검사 단계",
                    equipment_name: "검사 카메라",
                    fault_message: "검사 카메라 불량 증가",
                    severity: "high",
                    occurred_at: baseTime,
                    title: "[품질] 3번 조립 라인 배터리 탭 불량 증가",
                    content: "용접기 재가동 이후부터 검사 카메라 측 모니터링 수율이 평소 대비 4% 이상 저하되어 불량이 대량 잡힙니다. 배터리 탭 외관 치수 점검 및 품질 위원회 조사가 권장됩니다.",
                    reporter: "품질 담당자"
                };
            }

            try {
                const res = await fetch('/api/factory/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                fetchEvents();
                selectEvent(data.id);
            } catch(e) { alert("Demo Inject Error: " + e.message); }
        }

        // Custom Manual Dialog
        function openCreateModal() {
            document.getElementById('evtOccurred').value = new Date().toISOString();
            document.getElementById('createDialog').showModal();
        }

        function closeCreateModal() {
            document.getElementById('createDialog').close();
        }

        async function handleCreateEvent(event) {
            event.preventDefault();
            const payload = {
                category: document.getElementById('evtCategory').value,
                severity: document.getElementById('evtSeverity').value,
                factory_name: document.getElementById('evtFactory').value,
                line_name: document.getElementById('evtLine').value,
                process_step: document.getElementById('evtStep').value,
                equipment_name: document.getElementById('evtEquipment').value,
                fault_message: document.getElementById('evtFaultMessage').value.trim() || null,
                title: document.getElementById('evtTitle').value.trim(),
                content: document.getElementById('evtContent').value.trim(),
                reporter: document.getElementById('evtReporter').value.trim(),
                occurred_at: document.getElementById('evtOccurred').value.trim()
            };

            try {
                const res = await fetch('/api/factory/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const out = await res.json();
                closeCreateModal();
                fetchEvents();
                selectEvent(out.id);
            } catch(e) { alert("Error: " + e.message); }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_dashboard_ui():
    return HTML_CONTENT

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8091, reload=True)
