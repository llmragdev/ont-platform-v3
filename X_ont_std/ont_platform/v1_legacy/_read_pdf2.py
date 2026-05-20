import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

# pypdf가 없으면 claud_be 경로 추가
import importlib.util
if importlib.util.find_spec("pypdf") is None:
    import site
    be_site = r"C:\Users\nkchoi2\anaconda3\envs\claud_be\Lib\site-packages"
    sys.path.insert(0, be_site)

from pypdf import PdfReader

path = r"F:\01_강의자료_LLM RAG _MS azure_2025 2024_클라우드\바이브코딩\[패스트캠퍼스] 바이브코딩 상급 노하우_ 하네스 엔지니어링 편 (by. 유민수 개발자).pdf"
r = PdfReader(path)
print(f"총 {len(r.pages)}페이지")
for i, p in enumerate(r.pages):
    t = p.extract_text()
    if t and t.strip():
        print(f"\n=== p{i+1} ===")
        print(t[:2500])
