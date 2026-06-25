import time

import pytest

from app.services.cache_service import QueryCacheService
from app.services.graph_index import GraphIndex
from app.services.progressive_renderer import ProgressiveGraphRenderer


class TestQueryCacheService:

    def test_memory_ttl_expiration(self):
        cache = QueryCacheService(redis_url=None)
        cache.set_query("test-query", "tenant-a", {"value": 123}, ttl_seconds=1)

        assert cache.get_query("test-query", "tenant-a") == {"value": 123}
        time.sleep(1.1)
        assert cache.get_query("test-query", "tenant-a") is None

    def test_cache_hit_ratio(self):
        cache = QueryCacheService(redis_url=None)
        cache.set_query("test-query-2", "tenant-b", [1, 2, 3], ttl_seconds=10)
        assert cache.get_query("test-query-2", "tenant-b") == [1, 2, 3]
        assert cache.get_query("test-query-2", "tenant-b") == [1, 2, 3]
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 0
        assert stats["hit_ratio"] == 1.0


class TestGraphIndex:

    def test_lookup_neighborhood_returns_neighbors(self):
        triples = [
            ("http://example.com/A", "http://example.com/rel", "http://example.com/B"),
            ("http://example.com/A", "http://example.com/rel", "http://example.com/C"),
            ("http://example.com/B", "http://example.com/rel", "http://example.com/D"),
        ]
        graph_index = GraphIndex(triples=triples)

        result = graph_index.lookup_neighborhood("http://example.com/A", limit=2)

        assert result["centerNode"] == "http://example.com/A"
        assert any(node["id"] == "http://example.com/B" for node in result["nodes"])
        assert any(node["id"] == "http://example.com/C" for node in result["nodes"])
        assert result["has_more"] is False
        assert all(edge["predicate"] == "http://example.com/rel" for edge in result["edges"])


class TestProgressiveGraphRenderer:

    def test_render_with_priority_batches(self):
        renderer = ProgressiveGraphRenderer()
        graph_data = {
            "nodes": [
                {"id": f"node_{i}", "label": f"Node {i}", "x": (i % 50) * 16, "y": (i // 50) * 16}
                for i in range(300)
            ],
            "edges": [
                {"source": f"node_{i}", "target": f"node_{(i + 1) % 300}", "label": "connected"}
                for i in range(300)
            ],
        }

        batches = list(renderer.render_with_priority(graph_data, (800, 600)))

        assert len(batches) >= 3
        assert batches[0]["priority"] == "critical"
        assert batches[1]["priority"] == "high"
        assert batches[2]["priority"] == "low"
        assert batches[0]["nodes"]
