from pathlib import Path
import re


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
        raw_text = "\n\n".join(p for p in pages if p.strip())
        # PDF 추출 후 텍스트 정규화
        return FileExtractor._normalize_text(raw_text)

    @staticmethod
    def _extract_docx(path: Path) -> str:
        from docx import Document
        doc = Document(str(path))
        raw_text = "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
        # DOCX 추출 후 텍스트 정규화
        return FileExtractor._normalize_text(raw_text)

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        추출된 텍스트 정규화
        - 단일 \n → 스페이스 (의미 보존)
        - 문단 \n\n → 유지 (문단 구조 보존)
        - 다중 공백 → 단일 공백

        Args:
            text: 원본 텍스트

        Returns:
            정규화된 텍스트
        """
        if not text:
            return text

        # 1. 문단 구분자 임시 치환 (보호)
        text = text.replace('\n\n', '\x00PARA\x00')

        # 2. 단일 줄바꿈을 스페이스로 변환
        text = text.replace('\n', ' ')

        # 3. 문단 구분자 복원
        text = text.replace('\x00PARA\x00', '\n\n')

        # 4. 다중 공백 정규화 (먼저 \n\n 주변 공백 처리)
        text = text.replace('\n\n ', '\n\n').replace(' \n\n', '\n\n')

        # 5. 문단 구분을 보존한 채 일반 공백만 정규화
        paragraphs = [
            re.sub(r"[ \t\r\f\v]+", " ", paragraph).strip()
            for paragraph in text.split("\n\n")
        ]
        text = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)

        return text
