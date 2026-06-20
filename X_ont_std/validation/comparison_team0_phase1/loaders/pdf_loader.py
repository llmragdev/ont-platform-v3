import json
import re
from pathlib import Path
from typing import List, Dict
import PyPDF2

class PDFLoader:
    def __init__(self, pdf_dir: Path):
        self.pdf_dir = Path(pdf_dir)
        self.documents = []

    def _clean_text(self, text: str) -> str:
        """정규식을 사용하여 줄바꿈, 다중 공백 등을 정제합니다."""
        if not text:
            return ""
        # 컨트롤 문자 제거
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # 다중 공백 및 줄바꿈 정제
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_metadata(self, filename: str, text: str) -> Dict:
        """파일명과 텍스트를 파싱하여 기본 메타데이터를 추출합니다."""
        name = Path(filename).stem
        
        # 카테고리 추출
        category = "NLP"
        if "국방" in name:
            category = "국방"
            
        # 연도 추출
        year_match = re.search(r"\b(20\d{2})\b", name)
        year = int(year_match.group(1)) if year_match else 2025
        
        # 제목 추출 (접두사 및 연도/저자 접미사 제거)
        title = name
        title = re.sub(r"^(NLP|국방)\s*-\s*(\[\d+\]\s*)?", "", title)
        title = re.sub(r"-\s*20\d{2}.*$", "", title)
        title = re.sub(r"\s*-\s*안은희.*$", "", title)
        title = title.strip()
        
        # 간단히 텍스트 내용에서 키워드 추출 (예시)
        # 실제 키워드는 extractors/metadata_extractor.py에서 더욱 고도화하여 추출할 예정
        keywords = []
        possible_keywords = ["온톨로지", "지식그래프", "RDF", "자연어", "감성분석", "국방", "RAG"]
        for kw in possible_keywords:
            if kw in text:
                keywords.append(kw)
                
        return {
            "category": category,
            "title": title,
            "year": year,
            "keywords": keywords[:5]
        }

    def _load_single_pdf(self, pdf_path: Path) -> Dict:
        """단일 PDF 파일을 로드하고 텍스트를 추출합니다."""
        pdf_path = Path(pdf_path)
        print(f"📄 Processing: {pdf_path.name}")
        
        text_content = []
        num_pages = 0
        
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                for page_idx in range(num_pages):
                    page = reader.pages[page_idx]
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            print(f"❌ Error reading {pdf_path.name}: {e}")
            
        full_text = "\n".join(text_content)
        cleaned_text = self._clean_text(full_text)
        
        # 메타데이터 추출
        metadata = self._extract_metadata(pdf_path.name, cleaned_text)
        
        return {
            "filename": pdf_path.name,
            "num_pages": num_pages,
            "text": cleaned_text,
            "text_length": len(cleaned_text),
            "metadata": metadata
        }

    def load_all_pdfs(self) -> List[Dict]:
        """디렉터리 내의 모든 PDF 파일을 로드합니다."""
        self.documents = []
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️ No PDF files found in {self.pdf_dir}")
            return []
            
        pdf_files = sorted(pdf_files)
        for idx, pdf_file in enumerate(pdf_files, 1):
            doc = self._load_single_pdf(pdf_file)
            doc["id"] = f"doc_{idx:03d}"
            self.documents.append(doc)
            
        return self.documents

    def save_documents(self, output_path: Path):
        """추출한 문서 데이터를 JSON 파일로 저장합니다."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 저장 시 텍스트 본문과 메타데이터 모두 저장
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=4)
        print(f"✅ Saved {len(self.documents)} documents to {output_path}")

if __name__ == "__main__":
    import sys
    # sys.path 설정 추가하여 config를 로드할 수 있게 함
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import TARGET_DOC_DIR, RESULTS_DIR
    
    loader = PDFLoader(TARGET_DOC_DIR)
    docs = loader.load_all_pdfs()
    loader.save_documents(RESULTS_DIR / "documents_metadata.json")
