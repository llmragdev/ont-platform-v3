import json
import re
from pathlib import Path
from typing import List, Dict

class MetadataExtractor:
    def __init__(self, documents: List[Dict]):
        self.documents = documents

    def extract_keywords(self, text: str) -> List[str]:
        """텍스트 상부에서 키워드를 파싱하거나 중요 어휘를 매칭하여 반환합니다."""
        text_first_part = text[:2000]
        
        # 키워드/핵심어 패턴 검색
        keywords_patterns = [
            r"(핵심어|주요어|색인어|핵심 단어|핵심용어|주요 용어|Keywords|Keyword)\s*:\s*([^.\n]+)",
            r"핵심어휘\s*:\s*([^.\n]+)",
        ]
        
        for pattern in keywords_patterns:
            match = re.search(pattern, text_first_part, re.IGNORECASE)
            if match:
                kws_str = match.group(2)
                # 쉼표, 세미콜론, 구분점 등으로 나누기
                kws = [k.strip() for k in re.split(r"[,;•\s\r\n/]+", kws_str) if k.strip()]
                # 한 글자 이하이거나 이상한 것 필터링
                kws = [k for k in kws if len(k) >= 2 and not any(x in k for x in ["학회", "학술", "페이지", "논문"])]
                if kws:
                    return kws[:5]
        
        # 매칭이 안 될 시 텍스트 상에서 주요 개념어 검색 빈도 체크
        domain_keywords = ["온톨로지", "지식그래프", "RDF", "자연어처리", "자연어", "감성분석", "국방", "지휘통제", "언어모델", "생성형AI", "Paraphrasing", "데이터베이스", "감정판별", "이질성", "지식표현"]
        found = []
        for kw in domain_keywords:
            if kw in text:
                found.append(kw)
        return found[:5]

    def extract_authors(self, text: str) -> List[str]:
        """텍스트 처음에 나타나는 저자명을 정규표현식이나 매칭 규칙을 통해 추출합니다."""
        text_first_part = text[:1500]
        
        # 저자 표시 패턴
        authors_patterns = [
            r"저\s*자\s*:\s*([^.\n\(\)]+)",
            r"저\s*자\s*([^.\n\(\)]+)",
        ]
        
        for pattern in authors_patterns:
            match = re.search(pattern, text_first_part)
            if match:
                authors_str = match.group(1).strip()
                authors = [a.strip() for a in re.split(r"[,·\s]+", authors_str) if a.strip()]
                authors = [a for a in authors if len(a) >= 2 and len(a) <= 5 and not any(x in a for x in ["교수", "학생", "연구", "대학", "학회"])]
                if authors:
                    return authors
                    
        # 타겟 문서의 저자 목록 직접 검색
        known_authors = ["안은희", "안정국", "장병탁", "이강원", "김형겸", "정희태", "박영민", "최소영", "한선관", "임희석"]
        found = []
        for author in known_authors:
            if author in text_first_part:
                found.append(author)
        return found if found else ["알수없음"]

    def classify_document_type(self, text: str) -> str:
        """문서 형식 분석 (학술논문/기술보고서 등)."""
        text_lower = text.lower()
        if "학술" in text_lower or "논문" in text_lower or "journal" in text_lower or "초록" in text_lower:
            return "research_paper"
        return "technical_report"

    def extract_abstract(self, text: str) -> str:
        """초록/요약(Abstract) 영역을 파싱하여 리턴합니다."""
        text_first_part = text[:3000]
        abstract_start = -1
        
        for keyword in ["초록", "요약", "Abstract", "ABSTRACT"]:
            idx = text_first_part.find(keyword)
            if idx != -1:
                abstract_start = idx + len(keyword)
                break
                
        if abstract_start == -1:
            return ""
            
        abstract_end = -1
        for keyword in ["1. 서론", "1. 머리말", "1. 도입", "1. Introduction", "Ⅰ. 서론"]:
            idx = text_first_part.find(keyword, abstract_start)
            if idx != -1:
                abstract_end = idx
                break
                
        if abstract_end == -1:
            abstract_end = abstract_start + 1000  # Fallback 범위
            
        abstract_text = text_first_part[abstract_start:abstract_end].strip()
        # 불필요한 기호나 줄바꿈 제거
        abstract_text = re.sub(r"^[:\s\r\n\-\.]+", "", abstract_text)
        return abstract_text[:800]

    def extract_all_metadata(self) -> Dict[str, Dict]:
        """모든 문서에 대해 상세 메타데이터를 추출합니다."""
        analysis = {}
        for doc in self.documents:
            doc_id = doc["id"]
            text = doc["text"]
            basic_meta = doc["metadata"]
            
            keywords = self.extract_keywords(text)
            if not keywords:
                keywords = basic_meta.get("keywords", [])
                
            authors = self.extract_authors(text)
            doc_type = self.classify_document_type(text)
            abstract = self.extract_abstract(text)
            
            analysis[doc_id] = {
                "title": basic_meta.get("title", doc["filename"]),
                "category": basic_meta.get("category", "NLP"),
                "document_type": doc_type,
                "year": basic_meta.get("year", 2025),
                "keywords": keywords,
                "authors": authors,
                "pages": doc["num_pages"],
                "abstract_extracted": len(abstract) > 0,
                "abstract": abstract
            }
        return analysis

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import RESULTS_DIR
    
    # documents_metadata.json을 읽어서 메타데이터 정밀 분석 수행
    docs_file = RESULTS_DIR / "documents_metadata.json"
    if not docs_file.exists():
        print(f"❌ Cannot find {docs_file}. Run pdf_loader.py first.")
        sys.exit(1)
        
    with open(docs_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    extractor = MetadataExtractor(docs)
    metadata_analysis = extractor.extract_all_metadata()
    
    output_file = RESULTS_DIR / "metadata_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metadata_analysis, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Saved metadata analysis to {output_file}")
