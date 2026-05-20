from __future__ import annotations

import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    english = re.findall(r"[a-zA-Z0-9]+", text.lower())
    korean_hints = []
    lower = text.lower()
    if "승인" in lower:
        korean_hints.extend(["approval", "approve", "approved"])
    if "계약" in lower:
        korean_hints.append("contract")
    if "위험" in lower or "리스크" in lower:
        korean_hints.append("risk")
    if "지원" in lower:
        korean_hints.append("support")
    return english + korean_hints


class BM25Search:
    def __init__(self, documents: list[dict], k1: float = 1.5, b: float = 0.75) -> None:
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(f"{doc['title']} {doc['text']}") for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.term_frequencies = [Counter(tokens) for tokens in self.doc_tokens]
        self.document_frequency = self._build_document_frequency()

    def _build_document_frequency(self) -> Counter:
        document_frequency = Counter()
        for tokens in self.doc_tokens:
            for token in set(tokens):
                document_frequency[token] += 1
        return document_frequency

    def _idf(self, term: str) -> float:
        total_docs = len(self.documents)
        doc_freq = self.document_frequency.get(term, 0)
        return math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def _score_document(self, query_terms: list[str], index: int) -> float:
        score = 0.0
        term_frequency = self.term_frequencies[index]
        doc_length = self.doc_lengths[index]
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue
            numerator = frequency * (self.k1 + 1)
            denominator = frequency + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            score += self._idf(term) * numerator / denominator
        return score

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        query_terms = tokenize(query)
        scored_documents = []
        for index, document in enumerate(self.documents):
            score = self._score_document(query_terms, index)
            scored_documents.append({"score": round(score, 4), "document": document})
        return sorted(scored_documents, key=lambda item: item["score"], reverse=True)[:top_k]


class SearchService:
    def __init__(self, documents: list[dict], policy) -> None:
        self.documents = documents
        self.policy = policy

    def search(self, query: str, user: dict, top_k: int = 3) -> list[dict]:
        visible_docs = [doc for doc in self.documents if self.policy.can_read_document(user, doc)]
        return BM25Search(visible_docs).search(query, top_k)

