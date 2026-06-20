import json
import re
from pathlib import Path
from typing import List, Dict

class ChunkExtractor:
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        # 800자(공백 포함)는 한국어 약 400-500 토큰에 해당하며 512 토큰 기준에 잘 부합합니다.
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _find_sentence_boundaries(self, text: str) -> List[int]:
        """텍스트에서 마침표, 물음표, 느낌표 뒤의 문장 경계 위치를 찾습니다."""
        boundaries = []
        pattern = re.compile(r"([.?!])\s+")
        for match in pattern.finditer(text):
            boundaries.append(match.end())
        # 마지막 텍스트 끝 추가
        if not boundaries or boundaries[-1] < len(text):
            boundaries.append(len(text))
        return boundaries

    def split_into_chunks(self, text: str, doc_id: str) -> List[Dict]:
        """문장 경계를 지키면서 청크로 분할합니다."""
        boundaries = self._find_sentence_boundaries(text)
        chunks = []
        
        start_idx = 0
        sentence_start = 0
        
        for boundary in boundaries:
            # 현재 문장이 청크 크기를 초과하거나, 이전 문장부터 누적된 텍스트 크기가 한도를 넘는 경우 분할
            if boundary - start_idx > self.chunk_size:
                if sentence_start > start_idx:
                    chunk_text = text[start_idx:sentence_start].strip()
                    chunks.append({
                        "doc_id": doc_id,
                        "text": chunk_text,
                        "start_char": start_idx,
                        "end_char": sentence_start
                    })
                    # 겹침(overlap)을 고려한 다음 청크 시작 위치 설정
                    start_idx = max(0, sentence_start - self.overlap)
                else:
                    # 단일 문장이 너무 긴 특이 케이스는 강제 분할
                    chunk_text = text[start_idx:boundary].strip()
                    chunks.append({
                        "doc_id": doc_id,
                        "text": chunk_text,
                        "start_char": start_idx,
                        "end_char": boundary
                    })
                    start_idx = max(0, boundary - self.overlap)
            
            sentence_start = boundary
            
        # 남은 부분 처리
        if start_idx < len(text):
            chunk_text = text[start_idx:].strip()
            if len(chunk_text) > 30:  # 너무 짧은 꼬리 텍스트는 무시
                chunks.append({
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "start_char": start_idx,
                    "end_char": len(text)
                })
                
        # 청크 ID 부여
        for i, c in enumerate(chunks):
            c["id"] = f"{doc_id}_chunk_{i:03d}"
            
        return chunks

    def assign_chunk_metadata(self, chunks: List[Dict], doc_metadata: Dict) -> List[Dict]:
        """각 청크에 문서 단위 메타데이터를 상속시킵니다."""
        for c in chunks:
            c["metadata"] = {
                "doc_title": doc_metadata.get("title", ""),
                "category": doc_metadata.get("category", "NLP"),
                "keywords": doc_metadata.get("keywords", [])
            }
        return chunks

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from config import RESULTS_DIR
    
    # 1. 문서 메타데이터 로드
    docs_file = RESULTS_DIR / "documents_metadata.json"
    meta_file = RESULTS_DIR / "metadata_analysis.json"
    
    if not docs_file.exists() or not meta_file.exists():
        print("❌ Prerequisites missing. Run pdf_loader.py and metadata_extractor.py first.")
        sys.exit(1)
        
    with open(docs_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
    with open(meta_file, "r", encoding="utf-8") as f:
        meta_analysis = json.load(f)
        
    extractor = ChunkExtractor()
    all_chunks = []
    
    for doc in docs:
        doc_id = doc["id"]
        doc_meta = meta_analysis.get(doc_id, {})
        
        # 청크 분할
        chunks = extractor.split_into_chunks(doc["text"], doc_id)
        # 메타데이터 주입
        chunks = extractor.assign_chunk_metadata(chunks, doc_meta)
        all_chunks.extend(chunks)
        
    # 결과 저장
    output_file = RESULTS_DIR / "chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Created {len(all_chunks)} chunks and saved to {output_file}")
