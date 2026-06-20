from __future__ import annotations

import os
import sys
import subprocess
import socket
import time
import atexit
from pathlib import Path
from typing import Literal

from app.models.streamlit_app import StreamlitRunRequest, StreamlitRunResponse, StreamlitSaveRequest, StreamlitSaveResponse
from app.models.tenant_context import TenantContext


class StreamlitAppService:
    """Streamlit 앱 저장 및 실행 서비스"""

    def __init__(self, base_storage_path: str | None = None):
        if base_storage_path is None:
            # 절대경로: 현재 파일 기준으로 설정
            backend_dir = Path(__file__).resolve().parent.parent.parent
            base_storage_path = str(backend_dir / "storage")

        self.base_storage_path = base_storage_path
        self.active_processes: dict[str, subprocess.Popen] = {}
        self.app_to_port: dict[str, int] = {}

        # 백엔드 종료 시 프로세스 정리
        atexit.register(self._cleanup_all_processes)

    def get_app_storage_path(self, company_id: str, project_id: str, app_id: str) -> Path:
        """앱 저장 경로 반환"""
        path = Path(self.base_storage_path) / company_id / project_id / "streamlit_apps" / app_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_app_code(self, company_id: str, project_id: str, app_id: str,
                     file_name: str, code: str) -> Path:
        """앱 코드를 파일로 저장"""
        app_path = self.get_app_storage_path(company_id, project_id, app_id)
        file_path = app_path / file_name

        file_path.write_text(code, encoding='utf-8')
        return file_path

    def find_available_port(self, start_port: int = 8501, max_attempts: int = 10) -> int:
        """사용 가능한 포트 찾기"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    s.close()
                    return port
            except OSError:
                continue

        raise RuntimeError(f"포트를 할당할 수 없습니다 ({start_port}-{start_port + max_attempts})")

    def is_streamlit_installed(self) -> bool:
        """Streamlit 패키지 설치 여부 확인"""
        try:
            import streamlit
            return True
        except ImportError:
            return False

    def start_streamlit_server(self, file_path: Path, port: int) -> subprocess.Popen:
        """Streamlit 서버 시작"""
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(file_path),
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
            "--logger.level=error"
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 서버 시작 대기
        time.sleep(2)
        return proc

    def start_fallback_preview_server(self, file_path: Path, code: str, port: int) -> subprocess.Popen:
        """Fallback preview 서버 시작 (Streamlit 없을 때)"""
        preview_script = self._create_fallback_server_script(file_path, code)

        cmd = [
            sys.executable,
            str(preview_script),
            str(port)
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(1)
        return proc

    def _create_fallback_server_script(self, file_path: Path, code: str) -> Path:
        """Fallback preview 서버 스크립트 생성"""
        script_path = file_path.parent / "_fallback_server.py"

        # 코드를 HTML 이스케이프 처리
        escaped_code = code.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')

        fallback_script = f'''import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

class FallbackHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Streamlit Preview (Fallback)</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                .warning {{ background: #fef3c7; border: 1px solid #fcd34d; padding: 12px; border-radius: 4px; margin-bottom: 20px; }}
                .code {{ background: #f3f4f6; padding: 12px; border-radius: 4px; overflow-x: auto; }}
                code {{ font-family: 'Courier New', monospace; }}
                .instruction {{ background: #dbeafe; border: 1px solid #93c5fd; padding: 12px; border-radius: 4px; margin-top: 20px; }}
                h1 {{ color: #1f2937; }}
                h2 {{ color: #374151; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Streamlit Preview (Fallback Mode)</h1>

                <div class="warning">
                    <strong>⚠️ Fallback Preview</strong>
                    <p>Streamlit 패키지가 설치되어 있지 않아 fallback preview로 열었습니다.</p>
                </div>

                <h2>📝 작성된 코드</h2>
                <div class="code">
                    <code>{escaped_code}</code>
                </div>

                <div class="instruction">
                    <h3>실제 앱으로 실행하려면:</h3>
                    <ol>
                        <li>다음 명령어로 Streamlit을 설치하세요:</li>
                        <code>conda activate claud_be && pip install streamlit</code>
                        <li>서버를 다시 시작하세요</li>
                        <li>'코딩 실행' 버튼을 다시 클릭하세요</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """

        self.wfile.write(html.encode('utf-8'))

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    server = HTTPServer(('127.0.0.1', port), FallbackHandler)
    print(f'Fallback preview server running on port {{port}}')
    server.serve_forever()
'''

        script_path.write_text(fallback_script, encoding='utf-8')
        return script_path

    def run_app(self, request: StreamlitRunRequest, ctx: TenantContext) -> StreamlitRunResponse:
        """Streamlit 앱 실행"""
        # 1. 코드 저장
        file_path = self.save_app_code(
            ctx.company_id,
            ctx.project_id,
            request.app_id,
            request.file_name,
            request.code
        )

        # 2. 사용 가능한 포트 찾기
        port = self.find_available_port()
        self.app_to_port[request.app_id] = port

        # 3. Streamlit 또는 Fallback 서버 시작
        status: Literal["running", "fallback", "error"] = "error"
        mode: Literal["streamlit", "fallback"] = "fallback"
        message = ""

        try:
            if self.is_streamlit_installed():
                # Streamlit 실행
                proc = self.start_streamlit_server(file_path, port)
                self.active_processes[request.app_id] = proc
                status = "running"
                mode = "streamlit"
                message = "Streamlit app is running."
            else:
                # Fallback preview 실행
                proc = self.start_fallback_preview_server(file_path, request.code, port)
                self.active_processes[request.app_id] = proc
                status = "fallback"
                mode = "fallback"
                message = "Streamlit not installed. Fallback preview server is running. Install streamlit with: pip install streamlit"

        except Exception as e:
            status = "error"
            message = f"Failed to start app: {str(e)}"

        # 4. 응답 반환
        url = f"http://127.0.0.1:{port}/?app={request.file_name.replace('.py', '')}"

        return StreamlitRunResponse(
            app_id=request.app_id,
            status=status,
            mode=mode,
            url=url,
            file_path=str(file_path),
            port=port,
            message=message
        )

    def save_app(self, request: StreamlitSaveRequest, ctx: TenantContext) -> StreamlitSaveResponse:
        """Streamlit 앱 소스를 실행 없이 저장"""
        file_path = self.save_app_code(
            ctx.company_id,
            ctx.project_id,
            request.app_id,
            request.file_name,
            request.code,
        )
        return StreamlitSaveResponse(
            app_id=request.app_id,
            status="saved",
            file_path=str(file_path),
            message="Streamlit app source saved.",
        )

    def stop_app(self, app_id: str) -> bool:
        """Streamlit 앱 중지"""
        if app_id in self.active_processes:
            proc = self.active_processes[app_id]
            try:
                proc.terminate()
                proc.wait(timeout=5)
                del self.active_processes[app_id]
                if app_id in self.app_to_port:
                    del self.app_to_port[app_id]
                return True
            except:
                proc.kill()
                del self.active_processes[app_id]
                return False
        return False

    def _cleanup_all_processes(self) -> None:
        """백엔드 종료 시 모든 프로세스 정리 (atexit 훅)"""
        for app_id in list(self.active_processes.keys()):
            try:
                proc = self.active_processes[app_id]
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
            finally:
                del self.active_processes[app_id]
                if app_id in self.app_to_port:
                    del self.app_to_port[app_id]
