"""Integration tests for QueryCacheService checking lookup caching and tenant isolation."""
from __future__ import annotations

import sys
import time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.cache_service import QueryCacheService

def test_query_cache_basic_operations():
    """Verify basic set, get, hit/miss metrics."""
    cache = QueryCacheService()

    q = "SELECT ?x WHERE { ?x rdf:type ex:Project }"
    domain = "test_domain"
    result = {"results": [{"id": "entity_1", "name": "Alpha"}]}

    # Miss lookup
    val1 = cache.get_query(q, domain)
    assert val1 is None
    stats1 = cache.get_stats()
    assert stats1["misses"] == 1
    assert stats1["hits"] == 0

    # Set cache
    cache.set_query(q, domain, result)

    # Hit lookup
    val2 = cache.get_query(q, domain)
    assert val2 == result
    stats2 = cache.get_stats()
    assert stats2["hits"] == 1
    assert stats2["misses"] == 1


def test_query_cache_tenant_isolation():
    """Ensure query cache maintains strict domain isolation boundaries."""
    cache = QueryCacheService()
    
    q = "SELECT ?x WHERE { ?x rdf:type ex:Project }"
    
    result_d1 = {"results": [{"id": "d1"}]}
    result_d2 = {"results": [{"id": "d2"}]}

    cache.set_query(q, "domain_1", result_d1)
    cache.set_query(q, "domain_2", result_d2)

    assert cache.get_query(q, "domain_1") == result_d1
    assert cache.get_query(q, "domain_2") == result_d2


def test_query_cache_invalidation():
    """Check that cache invalidation wipes out keys for mutations."""
    cache = QueryCacheService()
    
    q = "SELECT ?x WHERE { ?x rdf:type ex:Project }"
    domain = "test_domain"
    result = {"results": [{"id": "entity_1"}]}

    cache.set_query(q, domain, result)
    assert cache.get_query(q, domain) == result

    cache.invalidate_by_domain(domain)
    
    assert cache.get_query(q, domain) is None
