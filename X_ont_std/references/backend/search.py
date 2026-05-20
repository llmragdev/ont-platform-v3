import math
from typing import List, Dict
from data import repo

class SearchService:
    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Improved tokenizer to handle punctuation
        import re
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9가-힣\s]', ' ', text)
        return text.split()

    @staticmethod
    def get_bm25_scores(query: str, documents: List[Dict]) -> List[Dict]:
        query_tokens = SearchService.tokenize(query)
        scored_docs = []
        
        # simplified BM25: TF-IDF based
        for doc in documents:
            doc_tokens = SearchService.tokenize(doc["text"] + " " + doc["title"])
            score = 0
            for token in query_tokens:
                if token in doc_tokens:
                    # Simple count-based score
                    score += doc_tokens.count(token)
            
            scored_doc = doc.copy()
            scored_doc["score"] = round(score, 2)
            scored_docs.append(scored_doc)
            
        # Sort by score descending
        return sorted(scored_docs, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def search(query: str, top_k: int = 2) -> List[Dict]:
        docs = repo.get_documents()
        scored = SearchService.get_bm25_scores(query, docs)
        return [d for d in scored if d["score"] > 0][:top_k]
