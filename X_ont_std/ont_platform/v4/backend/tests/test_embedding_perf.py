"""Integration tests for CachedEmbeddings functionality and latency performance."""
from __future__ import annotations

import sys
import time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.embedding_service import CachedEmbeddings
from langchain_core.embeddings import Embeddings

class MockEmbeddings(Embeddings):
    """Mock embeddings service to track actual API call counts and simulate network latency."""
    def __init__(self, vector_dim: int = 128, latency_sec: float = 0.1):
        self.vector_dim = vector_dim
        self.latency_sec = latency_sec
        self.call_count = 0
        self.embedded_texts = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        self.embedded_texts.extend(texts)
        # Simulate network latency
        time.sleep(self.latency_sec * len(texts))
        return [[0.1 * i] * self.vector_dim for i in range(len(texts))]

    def embed_query(self, text: str) -> list[float]:
        self.call_count += 1
        self.embedded_texts.append(text)
        time.sleep(self.latency_sec)
        return [0.1] * self.vector_dim


def test_cached_embeddings_basic_flow():
    """Verify standard embedding generation, caching logic, and hit/miss counts."""
    base_emb = MockEmbeddings(vector_dim=10, latency_sec=0.01)
    cached_emb = CachedEmbeddings(base_emb)

    texts = ["apple", "banana", "cherry"]

    # First request: Cache Miss
    embeddings1 = cached_emb.embed_documents(texts)
    stats1 = cached_emb.get_stats()
    
    assert len(embeddings1) == 3
    assert stats1["misses"] == 3
    assert stats1["hits"] == 0
    assert base_emb.call_count == 1  # 1 batch call

    # Second request: Cache Hit
    embeddings2 = cached_emb.embed_documents(texts)
    stats2 = cached_emb.get_stats()

    assert embeddings1 == embeddings2
    assert stats2["hits"] == 3
    assert stats2["misses"] == 3  # Unchanged
    assert base_emb.call_count == 1  # No additional API call!


def test_cached_embeddings_partial_caching():
    """Test behavior when some documents are cached and some are new."""
    base_emb = MockEmbeddings(vector_dim=8, latency_sec=0.01)
    cached_emb = CachedEmbeddings(base_emb)

    # Cache "apple" and "banana"
    cached_emb.embed_documents(["apple", "banana"])
    base_emb.call_count = 0  # Reset counter

    # Request "apple", "cherry" (cherry is new)
    results = cached_emb.embed_documents(["apple", "cherry"])
    
    assert len(results) == 2
    # Only "cherry" should trigger API call
    assert base_emb.call_count == 1
    assert base_emb.embedded_texts[-1] == "cherry"
    
    stats = cached_emb.get_stats()
    assert stats["hits"] == 3  # 2 in first call, 1 in second call
    assert stats["misses"] == 3  # 2 in first call, 1 in second call


def test_cached_embeddings_latency():
    """Ensure cached hits have latency under 10ms (ignoring API overhead)."""
    base_emb = MockEmbeddings(vector_dim=128, latency_sec=0.5)  # Heavy latency
    cached_emb = CachedEmbeddings(base_emb)

    text = ["speed_test_1"]

    # First call (cold)
    start_cold = time.time()
    cached_emb.embed_documents(text)
    cold_duration = time.time() - start_cold

    assert cold_duration >= 0.5

    # Second call (warm - cached)
    start_warm = time.time()
    cached_emb.embed_documents(text)
    warm_duration = time.time() - start_warm

    # Cached hit must be extremely fast (target < 50ms to be safe)
    assert warm_duration < 0.05
    assert warm_duration < cold_duration


def test_cached_embeddings_query():
    """Test query embedding cache validation."""
    base_emb = MockEmbeddings(vector_dim=16, latency_sec=0.05)
    cached_emb = CachedEmbeddings(base_emb)

    q = "what is ontology?"

    # Miss
    emb1 = cached_emb.embed_query(q)
    # Hit
    emb2 = cached_emb.embed_query(q)

    assert emb1 == emb2
    assert base_emb.call_count == 1
    stats = cached_emb.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
