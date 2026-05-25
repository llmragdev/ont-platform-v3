from typing import Dict, Any, List
import numpy as np

class PerformanceMonitor:
    """성능 모니터링 대시보드 및 통계 메트릭 수집기"""

    _sparql_queries: List[Dict[str, Any]] = []
    _db_queries: List[Dict[str, Any]] = []

    @classmethod
    def clear_stats(cls):
        """기록된 모든 통계 초기화"""
        cls._sparql_queries.clear()
        cls._db_queries.clear()

    @classmethod
    def record_sparql_query(cls, query: str, elapsed_ms: int, cache_hit: bool = False):
        """SPARQL 쿼리 실행 기록"""
        # 간단한 쿼리 유형 파싱 (SELECT, CONSTRUCT, ASK, DESCRIBE)
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            q_type = "SELECT"
        elif query_upper.startswith("CONSTRUCT"):
            q_type = "CONSTRUCT"
        elif query_upper.startswith("ASK"):
            q_type = "ASK"
        elif query_upper.startswith("DESCRIBE"):
            q_type = "DESCRIBE"
        else:
            q_type = "UNKNOWN"

        cls._sparql_queries.append({
            'query': query,
            'query_type': q_type,
            'elapsed_ms': elapsed_ms,
            'cache_hit': cache_hit
        })

    @classmethod
    def record_db_query(cls, table: str, operation: str, elapsed_ms: int):
        """DB 쿼리 실행 기록"""
        cls._db_queries.append({
            'table': table,
            'operation': operation,
            'elapsed_ms': elapsed_ms
        })

    @classmethod
    def get_performance_stats(cls) -> Dict[str, Any]:
        """성능 통계 조회"""
        # SPARQL 쿼리 통계
        sparql_times = [q['elapsed_ms'] for q in cls._sparql_queries]
        cache_hits = sum(1 for q in cls._sparql_queries if q['cache_hit'])
        total_sparql = len(cls._sparql_queries)
        
        avg_sparql = float(np.mean(sparql_times)) if total_sparql > 0 else 0.0
        p95_sparql = float(np.percentile(sparql_times, 95)) if total_sparql > 0 else 0.0
        cache_hit_rate = float(cache_hits / total_sparql) if total_sparql > 0 else 0.0

        # DB 쿼리 통계
        db_times = [d['elapsed_ms'] for d in cls._db_queries]
        total_db = len(cls._db_queries)
        avg_db = float(np.mean(db_times)) if total_db > 0 else 0.0

        return {
            'avg_sparql_time': avg_sparql,
            'p95_sparql_time': p95_sparql,
            'cache_hit_rate': cache_hit_rate,
            'db_query_count': total_db,
            'avg_db_time': avg_db
        }
