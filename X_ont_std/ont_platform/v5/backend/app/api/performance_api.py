from fastapi import APIRouter, Response
from typing import Dict
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.services.performance_monitor import PerformanceCollector

router = APIRouter(prefix="/api/performance", tags=["performance"])

# 테스트/어플리케이션 전반에서 단일 수집기 인스턴스를 공유할 수 있도록 글로벌 변수 지정
# conftest.py나 api_route 등에서 이를 사용해 메트릭 적재
collector = PerformanceCollector()

@router.get("/metrics/{metric_name}")
async def get_metric_stats(metric_name: str) -> Dict:
    """단일 성능 메트릭 통계 조회"""
    return collector.get_statistics(metric_name)

@router.get("/dashboard")
async def get_performance_dashboard() -> Dict:
    """전체 시스템 성능 통계 대시보드"""
    # L1/L2 및 전체 캐시 히트율 연계 조회
    # (MultiLevelCache 통계를 mock 또는 수동 매핑)
    # 실제 MultiLevelCache 인스턴스를 호출할 수 없을 경우를 대비하여 모니터 스펙 제공
    return {
        'sparql_query': collector.get_statistics('sparql_query_time'),
        'rdf_load': collector.get_statistics('rdf_load_time'),
        'graph_merge': collector.get_statistics('graph_merge_time'),
        'db_query': collector.get_statistics('db_query_time'),
        'api_response': collector.get_statistics('api_response_time'),
        'cache_stats': {
            'hits_l1': collector.get_statistics('cache_hit').get('count', 0),
            'misses': collector.get_statistics('cache_miss').get('count', 0)
        }
    }

# Prometheus 메트릭 수집 엔드포인트
@router.get("/prometheus-metrics")
async def prometheus_metrics():
    """Prometheus Scraper용 /metrics 엔드포인트"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
