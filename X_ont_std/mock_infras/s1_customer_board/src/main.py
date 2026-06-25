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

app = FastAPI(title="Customer Mock Board API - Scenario 1", version="1.0.0")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "s1_customer_board.db")

# Global Configuration for Scenario 1-1 / 1-2
# Aligned with 11_REQUIREMENTS_ONT_PLATFORM.md
settings = {
    "webhook_enabled": True,
    "webhook_mode": "post",
    "webhook_target": "http://localhost:8001/api/extn/customer-questions/events"
}

# In-memory webhook event logs for UI visualization
webhook_logs = []

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # Create Comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        post_id TEXT NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
    )
    """)
    
    # Insert seed data if empty
    cursor.execute("SELECT COUNT(*) FROM posts")
    if cursor.fetchone()[0] == 0:
        post_id_1 = "q-001"
        cursor.execute(
            "INSERT INTO posts (id, title, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (post_id_1, "[시나리오1] 비밀번호 초기화 요청", "홍길동", "로그인 비밀번호가 기억나지 않습니다. 초기화 부탁드립니다.", datetime.utcnow().isoformat())
        )
        cursor.execute(
            "INSERT INTO posts (id, title, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "[시나리오1] 시스템 점검 일정 안내", "시스템관리자", "이번주 토요일 새벽 2시부터 6시까지 서버 점검이 있을 예정입니다.", datetime.utcnow().isoformat())
        )
        # Seed comment
        cursor.execute(
            "INSERT INTO comments (id, post_id, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), post_id_1, "시스템봇", "본 게시글은 접수 완료되었습니다. 잠시만 기다려주세요.", datetime.utcnow().isoformat())
        )
        conn.commit()
    
    conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

# Models
class PostCreate(BaseModel):
    title: str
    author: str
    content: str

class CommentCreate(BaseModel):
    author: str
    content: str

class SettingsUpdate(BaseModel):
    webhook_enabled: bool
    webhook_mode: str
    webhook_target: str

# Helper function to trigger the Event Webhook in background
def trigger_webhook_background(post_id: str, title: str, content: str):
    if not settings["webhook_enabled"]:
        return
        
    event_id = f"evt-{uuid.uuid4()}"
    payload = {
        "event_id": event_id,
        "event_type": "question.created",
        "question_id": post_id,
        "thread_id": f"thread-{post_id}",
        "post_id": post_id,
        "title": title,
        "content": content,
        "author": "customer-user",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "mode": settings["webhook_mode"]
    }
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "event_id": event_id,
        "post_id": post_id,
        "title": title,
        "status": "pending",
        "mode": settings["webhook_mode"],
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
                settings["webhook_target"],
                data=req_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-Company-Id': 'default',
                    'X-Project-Id': 'proj-default',
                    'X-User-Id': 'default-user'
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

# API Routes
@app.get("/api/settings")
def get_settings():
    return settings

@app.post("/api/settings")
def update_settings(update: SettingsUpdate):
    if update.webhook_mode not in ("dry_run", "post"):
        raise HTTPException(status_code=400, detail="Invalid webhook_mode. Must be 'dry_run' or 'post'.")
    settings["webhook_enabled"] = update.webhook_enabled
    settings["webhook_mode"] = update.webhook_mode
    settings["webhook_target"] = update.webhook_target
    return settings

@app.get("/api/webhook-logs")
def get_webhook_logs():
    return {"logs": webhook_logs}

@app.post("/api/webhook-logs/clear")
def clear_webhook_logs():
    webhook_logs.clear()
    return {"status": "cleared"}

@app.get("/api/posts")
def get_posts(status: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status == "open":
        cursor.execute("""
            SELECT p.* FROM posts p
            LEFT JOIN comments c ON p.id = c.post_id
            GROUP BY p.id
            HAVING COUNT(c.id) = 0
            ORDER BY p.created_at DESC
        """)
    else:
        cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts

@app.get("/api/posts/{post_id}")
def get_post(post_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post_row = cursor.fetchone()
    if not post_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = dict(post_row)
    
    cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY created_at ASC", (post_id,))
    comments = [dict(row) for row in cursor.fetchall()]
    post["comments"] = comments
    
    conn.close()
    return post

@app.post("/api/posts")
def create_post(post: PostCreate, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()
    post_id = "q-" + str(uuid.uuid4())[:8]
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT INTO posts (id, title, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (post_id, post.title, post.author, post.content, created_at)
    )
    conn.commit()
    conn.close()
    
    # Trigger S1-2 Event Webhook automatically if enabled
    if settings["webhook_enabled"]:
        background_tasks.add_task(trigger_webhook_background, post_id, post.title, post.content)
    
    return {"id": post_id, "title": post.title, "author": post.author, "content": post.content, "created_at": created_at}

@app.post("/api/posts/{post_id}/comments")
def create_comment(post_id: str, comment: CommentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment_id = "comment-" + str(uuid.uuid4())[:8]
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT INTO comments (id, post_id, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (comment_id, post_id, comment.author, comment.content, created_at)
    )
    conn.commit()
    conn.close()
    
    return {"id": comment_id, "post_id": post_id, "author": comment.author, "content": comment.content, "created_at": created_at}

# Simulation endpoint for Scenario 1-1 Polling
@app.post("/api/simulate/polling")
def simulate_batch_polling(background_tasks: BackgroundTasks):
    """
    Simulates Scenario 1-1 Polling.
    Scans the database for posts that have NO comments, and triggers the comment workflow for them.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find all posts
    cursor.execute("SELECT * FROM posts")
    posts = [dict(row) for row in cursor.fetchall()]
    
    triggered_count = 0
    triggered_posts = []
    
    for p in posts:
        post_id = p["id"]
        # Check if this post has any comments
        cursor.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
        comment_count = cursor.fetchone()[0]
        
        if comment_count == 0:
            # Trigger comment generation (acts as polling agent)
            background_tasks.add_task(trigger_webhook_background, post_id, p["title"], p["content"])
            triggered_posts.append({"id": post_id, "title": p["title"]})
            triggered_count += 1
            
    conn.close()
    return {
        "status": "success",
        "scanned_posts": len(posts),
        "triggered_count": triggered_count,
        "triggered_posts": triggered_posts,
        "message": f"배치 검사 결과, 댓글이 없는 미처리 문의글 {triggered_count}건에 대해 워크플로우 실행을 유도했습니다."
    }

# HTML Frontend UI Code
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>고객사 모의 게시판 시스템 - 시나리오 1</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d0e15;
            --panel-bg: #161925;
            --panel-sidebar: #1d2136;
            --accent-color: #6366f1;
            --accent-hover: #4f46e5;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --border-color: #2a2e3f;
            --success-color: #10b981;
            --failed-color: #ef4444;
            --comment-bg: #1e2235;
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
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1.8fr 1.2fr;
            gap: 1.5rem;
        }

        header {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }

        header h1 {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .system-badge {
            background-color: rgba(99, 102, 241, 0.15);
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
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
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
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
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

        .btn-simulate {
            background: linear-gradient(135deg, #a855f7, #ec4899);
            color: white;
            border: none;
            width: 100%;
            padding: 0.8rem;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
            margin-top: 0.5rem;
        }

        .btn-simulate:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        .post-list {
            overflow-y: auto;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }

        .post-item {
            border: 1px solid var(--border-color);
            background-color: rgba(255, 255, 255, 0.02);
            padding: 1rem;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
        }

        .post-item:hover, .post-item.active {
            border-color: var(--accent-color);
            background-color: rgba(99, 102, 241, 0.05);
        }

        .post-meta {
            display: flex;
            gap: 0.8rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }

        .post-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .post-preview {
            font-size: 0.85rem;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .post-detail-content {
            overflow-y: auto;
            flex-grow: 1;
        }

        .detail-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .detail-body {
            font-size: 0.95rem;
            margin: 1.2rem 0;
            padding-bottom: 1.2rem;
            border-bottom: 1px solid var(--border-color);
            white-space: pre-line;
        }

        .comments-section h4 {
            font-size: 1.05rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .comments-list {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            margin-bottom: 1.2rem;
        }

        .comment-item {
            background-color: var(--comment-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.8rem 1rem;
            position: relative;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .comment-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.3rem;
        }

        .comment-author {
            font-weight: 600;
            color: var(--accent-color);
        }

        .comment-content {
            font-size: 0.9rem;
        }

        .comment-form {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .comment-form input {
            flex-grow: 1;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: white;
            padding: 0.6rem 1rem;
            font-family: inherit;
        }

        .comment-form input:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        /* Config Card styling */
        .config-card {
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
        }

        .config-group {
            margin-bottom: 1rem;
        }

        .config-group label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }

        .toggle-switch {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            font-weight: 600;
        }

        .toggle-switch input {
            cursor: pointer;
        }

        .select-input, .text-input {
            width: 100%;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: white;
            padding: 0.5rem;
            font-family: inherit;
            font-size: 0.85rem;
        }

        /* Log card styling */
        .log-section {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .log-list {
            flex-grow: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            font-size: 0.8rem;
            padding-right: 0.2rem;
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

        .log-item.success {
            border-left-color: var(--success-color);
        }

        .log-item.failed {
            border-left-color: var(--failed-color);
        }

        .log-item.pending {
            border-left-color: var(--accent-color);
        }

        .log-meta {
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 0.75rem;
        }

        .log-detail {
            word-break: break-all;
            color: var(--text-muted);
        }

        /* Modal styling */
        dialog {
            background-color: var(--panel-bg);
            color: white;
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            max-width: 500px;
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
            gap: 1rem;
            margin-top: 1rem;
        }

        dialog label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        dialog input, dialog textarea {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: white;
            padding: 0.8rem;
            font-family: inherit;
            width: 100%;
        }

        dialog textarea {
            resize: none;
            height: 120px;
        }

        dialog input:focus, dialog textarea:focus {
            outline: none;
            border-color: var(--accent-color);
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
            <h1>고객사 모의 게시판 시스템 <span>(Scenario 1)</span></h1>
            <div class="header-actions">
                <div class="system-badge">Port 8090 - SQLite Active</div>
            </div>
        </header>

        <!-- Left Panel: Post List -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">게시글 목록</div>
                <button class="btn" onclick="openCreateModal()">새 문의 작성</button>
            </div>
            <div class="post-list" id="postList">
                <!-- Posts will be rendered here dynamically -->
            </div>
        </div>

        <!-- Middle Panel: Post Detail & Comments -->
        <div class="panel" id="detailPanel">
            <!-- Selected post details and comments will render here -->
            <div style="margin: auto; text-align: center; color: var(--text-muted);">
                <h3>문의글을 선택해 주세요.</h3>
                <p style="margin-top: 0.5rem;">왼쪽 목록에서 글을 선택하여 댓글을 조회하거나 작성할 수 있습니다.</p>
            </div>
        </div>

        <!-- Right Panel: Scenario 1 Config & Webhook Logs -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">⚙️ 시나리오 1 설정</div>
            </div>
            
            <div class="config-card">
                <div class="config-group">
                    <label class="toggle-switch">
                        <input type="checkbox" id="webhookToggle" onchange="saveSettings()">
                        <span>실시간 Webhook 자동 트리거<br><small style="font-weight: normal; color: var(--text-muted);">(시나리오 1-2 연동)</small></span>
                    </label>
                </div>
                
                <div class="config-group">
                    <label for="webhookMode">Webhook 실행 모드</label>
                    <select id="webhookMode" class="select-input" onchange="saveSettings()">
                        <option value="dry_run">Dry-run (검증 전용)</option>
                        <option value="post">Post (실제 댓글 등록)</option>
                    </select>
                </div>
                
                <div class="config-group">
                    <label for="webhookTarget">Webhook Target URL</label>
                    <input type="text" id="webhookTarget" class="text-input" onchange="saveSettings()">
                </div>
                
                <div style="margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
                    <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.5rem;">
                        시나리오 1-1 (배치 폴링) 시뮬레이션
                    </label>
                    <button class="btn-simulate" onclick="simulatePolling()">
                        ⚡ 솔루션 배치 폴링 수동 실행
                    </button>
                </div>
            </div>

            <div class="log-section">
                <div class="panel-header" style="margin-bottom: 0.6rem;">
                    <div class="panel-title" style="font-size: 1rem;">🔔 Webhook 실행 로그</div>
                    <button class="btn btn-secondary" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;" onclick="clearLogs()">비우기</button>
                </div>
                <div class="log-list" id="logList">
                    <!-- Logs will be rendered here dynamically -->
                </div>
            </div>
        </div>
    </div>

    <!-- Create Post Dialog -->
    <dialog id="postDialog">
        <h2>새 문의글 작성</h2>
        <form onsubmit="handleCreatePost(event)">
            <div>
                <label for="postTitle">제목</label>
                <input type="text" id="postTitle" required placeholder="예: [시나리오1] 비밀번호 변경">
            </div>
            <div>
                <label for="postAuthor">작성자</label>
                <input type="text" id="postAuthor" required value="홍길동">
            </div>
            <div>
                <label for="postContent">내용</label>
                <textarea id="postContent" required placeholder="문의 상세 내용을 입력하세요."></textarea>
            </div>
            <div class="dialog-actions">
                <button class="btn btn-secondary" type="button" onclick="closeCreateModal()">취소</button>
                <button class="btn" type="submit">등록</button>
            </div>
        </form>
    </dialog>

    <script>
        let posts = [];
        let selectedPostId = null;

        // Fetch settings and logs on load
        async function fetchSettings() {
            try {
                const res = await fetch('/api/settings');
                const config = await res.json();
                document.getElementById('webhookToggle').checked = config.webhook_enabled;
                document.getElementById('webhookMode').value = config.webhook_mode;
                document.getElementById('webhookTarget').value = config.webhook_target;
            } catch (err) {
                console.error("Error fetching settings:", err);
            }
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
            } catch (err) {
                console.error("Error saving settings:", err);
            }
        }

        async function fetchLogs() {
            try {
                const res = await fetch('/api/webhook-logs');
                const data = await res.json();
                renderLogs(data.logs);
            } catch (err) {
                console.error("Error fetching logs:", err);
            }
        }

        async function clearLogs() {
            try {
                await fetch('/api/webhook-logs/clear', { method: 'POST' });
                fetchLogs();
            } catch (err) {
                console.error("Error clearing logs:", err);
            }
        }

        function renderLogs(logs) {
            const listEl = document.getElementById('logList');
            listEl.innerHTML = '';
            
            if (logs.length === 0) {
                listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 2rem 0;">로그가 없습니다.</div>';
                return;
            }

            logs.forEach(log => {
                const item = document.createElement('div');
                item.className = `log-item ${log.status}`;
                
                let details = '';
                if (log.status === 'success') {
                    const res = log.response || {};
                    details = `<div class="log-detail">결과: status: ${res.status || 'unknown'}, event_id: ${res.event_id || 'null'}</div>`;
                } else if (log.status === 'failed') {
                    details = `<div class="log-detail" style="color: var(--failed-color);">오류: ${log.error}</div>`;
                } else {
                    details = `<div class="log-detail">전송 대기 중...</div>`;
                }

                item.innerHTML = `
                    <div class="log-meta">
                        <span>[${log.timestamp}] Post: ${escapeHtml(log.title)}</span>
                        <span style="font-weight: 700; text-transform: uppercase;">${log.status}</span>
                    </div>
                    <div style="font-size: 0.75rem;">모드: ${log.mode}</div>
                    ${details}
                `;
                listEl.appendChild(item);
            });
        }

        // Fetch all posts on load
        async function fetchPosts() {
            try {
                const res = await fetch('/api/posts');
                posts = await res.json();
                renderPostList();
                
                if (selectedPostId) {
                    selectPost(selectedPostId);
                } else if (posts.length > 0) {
                    selectPost(posts[0].id);
                }
            } catch (err) {
                console.error("Error fetching posts:", err);
            }
        }

        // Render posts inside the left sidebar list
        function renderPostList() {
            const listEl = document.getElementById('postList');
            listEl.innerHTML = '';
            
            posts.forEach(post => {
                const activeClass = post.id === selectedPostId ? 'active' : '';
                const date = new Date(post.created_at).toLocaleDateString('ko-KR', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                const item = document.createElement('div');
                item.className = `post-item ${activeClass}`;
                item.onclick = () => selectPost(post.id);
                item.innerHTML = `
                    <div class="post-meta">
                        <span>ID: ${post.id}</span>
                        <span>${post.author}</span>
                        <span>${date}</span>
                    </div>
                    <div class="post-title">${escapeHtml(post.title)}</div>
                    <div class="post-preview">${escapeHtml(post.content)}</div>
                `;
                listEl.appendChild(item);
            });
        }

        // Select a post and fetch its comments
        async function selectPost(id) {
            selectedPostId = id;
            
            const items = document.querySelectorAll('.post-item');
            posts.forEach((post, index) => {
                if (post.id === id) {
                    items[index]?.classList.add('active');
                } else {
                    items[index]?.classList.remove('active');
                }
            });

            try {
                const res = await fetch(`/api/posts/${id}`);
                const post = await res.json();
                renderPostDetail(post);
            } catch (err) {
                console.error("Error fetching post detail:", err);
            }
        }

        // Render post detail & comment section in the middle panel
        function renderPostDetail(post) {
            const panel = document.getElementById('detailPanel');
            const date = new Date(post.created_at).toLocaleString('ko-KR');
            
            panel.innerHTML = `
                <div class="post-detail-content">
                    <div class="post-meta">
                        <span>ID: ${post.id}</span>
                        <span>작성자: <strong>${post.author}</strong></span>
                        <span>${date}</span>
                    </div>
                    <div class="detail-title">${escapeHtml(post.title)}</div>
                    <div class="detail-body">${escapeHtml(post.content)}</div>
                    
                    <div class="comments-section">
                        <h4>💬 답변 댓글 (${post.comments.length})</h4>
                        <div class="comments-list">
                            ${post.comments.map(c => {
                                const cDate = new Date(c.created_at).toLocaleString('ko-KR');
                                return `
                                    <div class="comment-item">
                                        <div class="comment-meta">
                                            <span class="comment-author">${escapeHtml(c.author)}</span>
                                            <span>${cDate}</span>
                                        </div>
                                        <div class="comment-content">${escapeHtml(c.content)}</div>
                                    </div>
                                `;
                            }).join('')}
                            ${post.comments.length === 0 ? '<p style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 1.5rem 0;">아직 달린 답변이 없습니다.</p>' : ''}
                        </div>
                        
                        <form class="comment-form" onsubmit="handleCreateComment(event, '${post.id}')">
                            <input type="text" id="commentAuthorInput" placeholder="작성자" style="max-width: 120px;" required value="고객지원팀">
                            <input type="text" id="commentContentInput" placeholder="답변할 댓글 내용을 입력하세요..." required>
                            <button class="btn" type="submit">댓글 등록</button>
                        </form>
                    </div>
                </div>
            `;
        }

        // Submit comment
        async function handleCreateComment(e, postId) {
            e.preventDefault();
            const author = document.getElementById('commentAuthorInput').value;
            const content = document.getElementById('commentContentInput').value;

            try {
                const res = await fetch(`/api/posts/${postId}/comments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ author, content })
                });
                
                if (res.ok) {
                    selectPost(postId);
                }
            } catch (err) {
                console.error("Error creating comment:", err);
            }
        }

        // Create post modal actions
        const dialog = document.getElementById('postDialog');
        function openCreateModal() { dialog.showModal(); }
        function closeCreateModal() { dialog.close(); }

        // Submit post
        async function handleCreatePost(e) {
            e.preventDefault();
            const title = document.getElementById('postTitle').value;
            const author = document.getElementById('postAuthor').value;
            const content = document.getElementById('postContent').value;

            try {
                const res = await fetch('/api/posts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, author, content })
                });
                
                if (res.ok) {
                    const newPost = await res.json();
                    selectedPostId = newPost.id;
                    closeCreateModal();
                    await fetchPosts();
                    // Fetch logs immediately if webhook was triggered
                    setTimeout(fetchLogs, 500);
                }
            } catch (err) {
                console.error("Error creating post:", err);
            }
        }

        // Simulate Polling Mode 1-1
        async function simulatePolling() {
            try {
                const res = await fetch('/api/simulate/polling', { method: 'POST' });
                const result = await res.json();
                
                alert(`[시나리오 1-1 폴링 시뮬레이션 완료]\\n${result.message}`);
                
                // Fetch logs and refresh
                setTimeout(() => {
                    fetchLogs();
                    if (selectedPostId) selectPost(selectedPostId);
                }, 1000);
            } catch (err) {
                alert(`솔루션 배치 폴링 실행 실패: ${err.message}`);
            }
        }

        // Escaping HTML utility
        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        // Start polling for updates every 2 seconds to see new replies instantly
        setInterval(() => {
            if (selectedPostId) {
                fetch(`/api/posts/${selectedPostId}`)
                    .then(res => res.json())
                    .then(post => {
                        const listEl = document.querySelector('.comments-list');
                        if (listEl) {
                            const currentCount = listEl.querySelectorAll('.comment-item').length;
                            if (post.comments.length !== currentCount) {
                                renderPostDetail(post);
                            }
                        }
                    });
            }
            
            fetch('/api/posts')
                .then(res => res.json())
                .then(newPosts => {
                    if (newPosts.length !== posts.length) {
                        posts = newPosts;
                        renderPostList();
                    }
                });

            // Periodically refresh the webhook log list too
            fetchLogs();
        }, 2000);

        // Initial fetch
        fetchSettings();
        fetchPosts();
        fetchLogs();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_board_ui():
    return HTML_CONTENT

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
