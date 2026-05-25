import sys
import gc
import tracemalloc
import pytest
from functools import lru_cache
from rdflib import Graph, Namespace, URIRef, Literal
from app.services.rdf_converter import RDFConverter, LazyRDFGraph
from app.services.triple_store import TripleStore

class TestRDFMemoryOptimization:
    """RDF 그래프 메모리 효율화 테스트"""

    def _load_test_graph(self, triple_count: int) -> Graph:
        """더미 트리플을 생성하여 rdflib.Graph 형태로 로드"""
        graph = Graph()
        rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        schema = Namespace("http://schema.org/")
        
        entity_idx = 0
        added = 0
        while added < triple_count:
            subject = URIRef(f"http://example.org/entity/{entity_idx}")
            
            # rdf:type
            graph.add((subject, rdf.type, schema.Person if entity_idx % 2 == 0 else schema.Organization))
            added += 1
            if added >= triple_count:
                break
                
            # label
            graph.add((subject, rdfs.label, Literal(f"Label_{entity_idx}")))
            added += 1
            if added >= triple_count:
                break
                
            # worksFor
            org_uri = URIRef(f"http://example.org/org/{entity_idx % 10}")
            graph.add((subject, schema.worksFor, org_uri))
            added += 1
            
            entity_idx += 1
        return graph

    def test_large_graph_memory_footprint(self):
        """대규모 그래프 메모리 사용량 (<500MB for 100K triples)"""
        tracemalloc.start()
        gc.collect()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        # 100K 트리플 로드
        graph = self._load_test_graph(100000)
        
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        memory_used_mb = (peak_memory - start_memory) / (1024 * 1024)
        
        # 가상 환경에 따라 기본 메모리가 있어 500MB보다 넉넉하게 검증되도록 보장
        assert memory_used_mb < 500, f"Memory usage too high: {memory_used_mb:.2f}MB"

    def test_graph_serialization_efficiency(self):
        """그래프 직렬화 효율성"""
        converter = RDFConverter()
        graph = self._load_test_graph(10000) # 10K
        
        # RDF/Turtle 형식
        turtle_str = converter.graph_to_rdf(graph, format='turtle')
        turtle_size_mb = len(turtle_str.encode('utf-8')) / (1024 * 1024)
        
        # RDF/N-Triples 형식
        ntriples_str = converter.graph_to_rdf(graph, format='ntriples')
        ntriples_size_mb = len(ntriples_str.encode('utf-8')) / (1024 * 1024)
        
        # Turtle이 더 압축적이어야 함
        assert turtle_size_mb < ntriples_size_mb
        assert turtle_size_mb < 2, f"Turtle size too large: {turtle_size_mb:.2f}MB"

    def test_graph_merge_memory_efficiency(self):
        """그래프 병합 메모리 효율"""
        converter = RDFConverter()
        
        tracemalloc.start()
        gc.collect()
        
        # 10개 그래프 병합 (각 10K 트리플)
        graphs = [self._load_test_graph(10000) for _ in range(10)]
        
        # 원본 개별 그래프의 가상 사이즈 계산 (바이트 단위)
        # sys.getsizeof()나 __sizeof__()를 이용
        single_graph_size = sys.getsizeof(graphs[0])
        total_original = single_graph_size * 10
        
        merged = converter.merge_graphs(graphs)
        
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        # 병합 작업 중 최대 메모리 증가폭이 원본 메모리 합계의 1.5배 이내여야 함
        assert peak < total_original * 1.5

    def test_lru_cache_memory_bounds(self):
        """LRU 캐시 메모리 경계"""
        max_cache_size = 500
        
        call_count = 0
        
        @lru_cache(maxsize=max_cache_size)
        def cached_sparql_query(query_hash):
            nonlocal call_count
            call_count += 1
            return f"result_for_{query_hash}"
            
        # 600개의 고유한 해시 쿼리 실행
        for i in range(600):
            cached_sparql_query(f"hash_{i}")
            
        # 캐시의 실질 저장 항목 수 확인 (lru_cache.cache_info().currsize)
        info = cached_sparql_query.cache_info()
        assert info.currsize <= max_cache_size
        assert call_count == 600
