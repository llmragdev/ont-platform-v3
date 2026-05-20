from pathlib import Path


class FileExtractor:
    """파일 포맷별 텍스트 추출 — 전략 패턴으로 확장 가능."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

    def extract(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".pdf":
            return self._extract_pdf(path)
        if ext == ".docx":
            return self._extract_docx(path)
        return self._extract_text(path)

    @staticmethod
    def _extract_text(path: Path) -> str:
        data = path.read_bytes()
        for encoding in ("utf-8", "cp949", "latin-1"):
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return data.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p for p in pages if p.strip())

    @staticmethod
    def _extract_docx(path: Path) -> str:
        from docx import Document
        doc = Document(str(path))
        return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
