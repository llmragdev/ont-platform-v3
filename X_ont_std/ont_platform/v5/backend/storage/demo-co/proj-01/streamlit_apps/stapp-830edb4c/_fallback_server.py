import sys
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
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
                .warning { background: #fef3c7; border: 1px solid #fcd34d; padding: 12px; border-radius: 4px; margin-bottom: 20px; }
                .code { background: #f3f4f6; padding: 12px; border-radius: 4px; overflow-x: auto; }
                code { font-family: 'Courier New', monospace; }
                .instruction { background: #dbeafe; border: 1px solid #93c5fd; padding: 12px; border-radius: 4px; margin-top: 20px; }
                h1 { color: #1f2937; }
                h2 { color: #374151; margin-top: 20px; }
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
                    <code>import streamlit as st<br><br>st.set_page_config(page_title="streamlit 테스트", layout="wide")<br>st.title("streamlit 테스트")<br><br>st.write("AI Assistant에게 이 편집창을 선택한 상태로 코딩을 요청하세요.")<br></code>
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
    print(f'Fallback preview server running on port {port}')
    server.serve_forever()
