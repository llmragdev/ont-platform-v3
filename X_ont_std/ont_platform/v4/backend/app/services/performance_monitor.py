from typing import Dict, Any, List
from datetime import datetime
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

from dataclasses import dataclass
from prometheus_client import Histogram, Counter

# Prometheus Histograms & Counters
sparql_query_duration = Histogram(
    'sparql_query_duration_seconds',
    'SPARQL query duration in seconds',
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)
cache_hit_counter = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_level']
)
cache_miss_counter = Counter(
    'cache_misses_total',
    'Total cache misses'
)

@dataclass
class PerformanceMetric:
    """성능 메트릭 자료구조"""
    name: str
    value: float  # ms
    timestamp: datetime
    tags: Dict[str, str] = None

class PerformanceCollector:
    """성능 데이터 수집 및 시계열 분석기"""

    def __init__(self, redis: Any = None):
        self.redis = redis
        self.metrics: List[PerformanceMetric] = []

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """메트릭 기록 및 Prometheus/Redis 연동"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        self.metrics.append(metric)

        # Prometheus 히스토그램 관측
        if name == 'sparql_query_time':
            sparql_query_duration.observe(value / 1000.0)
        elif name == 'db_query_time':
            db_query_duration.observe(value / 1000.0)
            
        # Cache hits counters
        if name == 'cache_hit':
            lvl = (tags or {}).get('cache_level', 'L1')
            cache_hit_counter.labels(cache_level=lvl).inc()
        elif name == 'cache_miss':
            cache_miss_counter.inc()

        # Redis에 시계열 적재
        if self.redis:
            try:
                import json
                key = f"metric:{name}:{datetime.utcnow().timestamp()}"
                self.redis.setex(key, 3600, json.dumps({
                    'value': value,
                    'tags': tags
                }, ensure_ascii=False))
            except Exception as e:
                # 로컬에 경고 로그만 남김
                pass

    def get_statistics(self, metric_name: str) -> Dict[str, Any]:
        """지정된 메트릭의 P95, P99 통계 분석"""
        values = [m.value for m in self.metrics if m.name == metric_name]
        if not values:
            return {
                'count': 0,
                'min': 0.0,
                'max': 0.0,
                'avg': 0.0,
                'p95': 0.0,
                'p99': 0.0
            }
        
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        p95 = sorted_vals[int(n * 0.95)] if n > 0 else 0.0
        p99 = sorted_vals[int(n * 0.99)] if n > 0 else 0.0
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'p95': p95,
            'p99': p99
        }

