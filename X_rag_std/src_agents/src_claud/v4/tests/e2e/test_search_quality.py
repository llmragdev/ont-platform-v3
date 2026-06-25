# -*- coding: utf-8 -*-
"""
검색 품질 벤치마크 (test_plan.md Task 4)

목표: 검색 정확도 측정
- 50개 샘플 쿼리로 Precision@5 측정
- 카테고리별 정확도 분석
- 응답시간 측정

성공 기준:
- Precision@5 ≥ 70%
- 커버리지 ≥ 95% (결과 반환율)
"""

import io
import json
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import List, Dict

from app.db.session import get_db
from app.main import app
from app.models.db_models import Base


@pytest.fixture
def test_db_engine():
    """독립된 인메모리 DB"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    TestSession = sessionmaker(
        bind=test_db_engine, autocommit=False, autoflush=False
    )
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def routing_config(tmp_path):
    """라우팅 설정"""
    cfg = {
        "routing_rules": [
            {
                "vector_db_id": "vdb_hr_recruit_01",
                "target_category_mid": ["채용", "recruitment"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_hr_payroll_01",
                "target_category_mid": ["급여", "payroll"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_policy_01",
                "target_category_mid": ["취업규칙", "policy"],
                "engine_type": "local_json",
            },
            {
                "vector_db_id": "vdb_ontology_01",
                "target_category_mid": ["ontology"],
                "engine_type": "local_json",
            },
        ]
    }
    cfg_file = tmp_path / "routing_config.json"
    cfg_file.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return cfg_file


def create_test_pdf(filename: str, content: str) -> io.BytesIO:
    """테스트용 파일 생성"""
    return io.BytesIO(content.encode('utf-8'))


class SearchQualityBenchmark:
    """검색 품질 벤치마크"""

    SAMPLE_QUERIES = [
        # 온톨로지 관련 (5개)
        {"query": "온톨로지", "expected_category": "기술"},
        {"query": "knowledge graph", "expected_category": "기술"},
        {"query": "semantic web", "expected_category": "기술"},
        {"query": "RDF", "expected_category": "기술"},
        {"query": "semantic relationship", "expected_category": "기술"},

        # HR 채용 관련 (5개)
        {"query": "신입사원", "expected_category": "인사"},
        {"query": "채용 공고", "expected_category": "인사"},
        {"query": "지원자", "expected_category": "인사"},
        {"query": "합격", "expected_category": "인사"},
        {"query": "면접", "expected_category": "인사"},

        # HR 급여 관련 (5개)
        {"query": "급여 규정", "expected_category": "인사"},
        {"query": "월급", "expected_category": "인사"},
        {"query": "보너스", "expected_category": "인사"},
        {"query": "복리후생", "expected_category": "인사"},
        {"query": "퇴직금", "expected_category": "인사"},

        # 규정 관련 (5개)
        {"query": "취업규칙", "expected_category": "규정"},
        {"query": "휴가 정책", "expected_category": "규정"},
        {"query": "근무시간", "expected_category": "규정"},
        {"query": "보안 규정", "expected_category": "규정"},
        {"query": "인사 평가", "expected_category": "규정"},

        # 혼합 쿼리 (5개)
        {"query": "정책", "expected_category": "규정"},
        {"query": "AI 기술", "expected_category": "기술"},
        {"query": "조직", "expected_category": "규정"},
        {"query": "권리", "expected_category": "인사"},
        {"query": "문서", "expected_category": "규정"},

        # 추가 기술 쿼리 (10개)
        {"query": "NLP", "expected_category": "기술"},
        {"query": "자연언어처리", "expected_category": "기술"},
        {"query": "머신러닝", "expected_category": "기술"},
        {"query": "벡터", "expected_category": "기술"},
        {"query": "임베딩", "expected_category": "기술"},
        {"query": "텍스트 분석", "expected_category": "기술"},
        {"query": "데이터", "expected_category": "기술"},
        {"query": "모델", "expected_category": "기술"},
        {"query": "학습", "expected_category": "기술"},
        {"query": "성능", "expected_category": "기술"},

        # 추가 인사 쿼리 (10개)
        {"query": "직급", "expected_category": "인사"},
        {"query": "부서", "expected_category": "인사"},
        {"query": "승진", "expected_category": "인사"},
        {"query": "업무", "expected_category": "인사"},
        {"query": "평가", "expected_category": "인사"},
        {"query": "성과", "expected_category": "인사"},
        {"query": "교육", "expected_category": "인사"},
        {"query": "복무", "expected_category": "인사"},
        {"query": "수당", "expected_category": "인사"},
        {"query": "세금", "expected_category": "인사"},

        # 추가 규정 쿼리 (5개) - 총 50개
        {"query": "회사 규칙", "expected_category": "규정"},
        {"query": "내부 지침", "expected_category": "규정"},
        {"query": "보안 정책", "expected_category": "규정"},
        {"query": "휴가 신청", "expected_category": "규정"},
        {"query": "근태 관리", "expected_category": "규정"},
    ]

    def __init__(self):
        self.results = []

    def run_benchmark(self, client: TestClient) -> Dict:
        """벤치마크 실행"""
        self.results = []
        response_times = []

        for test_case in self.SAMPLE_QUERIES:
            query = test_case["query"]
            expected = test_case["expected_category"]

            # 검색 실행
            start_time = time.time()
            resp = client.post(
                "/api/v1/rag/search",
                json={"query": query, "limit": 10}
            )
            elapsed = (time.time() - start_time) * 1000  # ms

            if resp.status_code != 200:
                self.results.append({
                    "query": query,
                    "expected": expected,
                    "precision@5": 0.0,
                    "chunks_returned": 0,
                    "response_time_ms": elapsed,
                    "status_code": resp.status_code,
                })
                continue

            chunks = resp.json().get("chunks", [])
            response_times.append(elapsed)

            # 상위 5개 중 expected 카테고리 개수
            top_5_categories = [
                c["metadata"].get("category_large", "") for c in chunks[:5]
            ]

            hits = sum(1 for cat in top_5_categories if cat == expected)
            precision = hits / 5 if len(chunks) >= 5 else (hits / len(chunks) if chunks else 0)

            self.results.append({
                "query": query,
                "expected": expected,
                "precision@5": precision,
                "chunks_returned": len(chunks),
                "response_time_ms": elapsed,
                "status_code": 200,
            })

        # 통계 계산
        if not self.results:
            return {
                "avg_precision": 0.0,
                "median_precision": 0.0,
                "coverage": 0.0,
                "results_by_category": {},
                "response_times": {
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p99": 0.0,
                },
                "total_queries": 0,
            }

        # Precision 통계
        precisions = [r["precision@5"] for r in self.results]
        precisions_sorted = sorted(precisions)

        # 응답시간 통계
        response_times_sorted = sorted(response_times)

        # 카테고리별 정확도
        results_by_category = {}
        for result in self.results:
            cat = result["expected"]
            if cat not in results_by_category:
                results_by_category[cat] = []
            results_by_category[cat].append(result["precision@5"])

        category_precision = {
            cat: sum(prec) / len(prec) for cat, prec in results_by_category.items()
        }

        # 결과 반환율 (chunks 반환된 쿼리 수)
        coverage = sum(1 for r in self.results if r["chunks_returned"] > 0) / len(self.results)

        return {
            "avg_precision": sum(precisions) / len(precisions),
            "median_precision": precisions_sorted[len(precisions_sorted) // 2],
            "coverage": coverage,
            "results_by_category": category_precision,
            "response_times": {
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "p99": response_times_sorted[int(len(response_times_sorted) * 0.99)] if response_times_sorted else 0,
            },
            "total_queries": len(self.results),
        }

    def print_results(self, results: Dict):
        """결과 출력"""
        print("\n" + "=" * 60)
        print("검색 품질 벤치마크 결과")
        print("=" * 60)
        print(f"총 쿼리 수: {results['total_queries']}")
        print(f"평균 Precision@5: {results['avg_precision']:.2%}")
        print(f"중앙값 Precision@5: {results['median_precision']:.2%}")
        print(f"커버리지 (결과 반환율): {results['coverage']:.2%}")
        print()
        print("응답시간 (ms):")
        print(f"  - 평균: {results['response_times']['avg']:.2f}")
        print(f"  - 최소: {results['response_times']['min']:.2f}")
        print(f"  - 최대: {results['response_times']['max']:.2f}")
        print(f"  - p99: {results['response_times']['p99']:.2f}")
        print()
        print("카테고리별 Precision@5:")
        for cat, prec in sorted(results['results_by_category'].items()):
            print(f"  - {cat}: {prec:.2%}")
        print("=" * 60 + "\n")


@pytest.fixture
def benchmark_setup(db_session, tmp_path, monkeypatch, routing_config):
    """벤치마크 테스트 데이터 설정"""
    from app.core import config as cfg_module

    monkeypatch.setattr(cfg_module.settings, "vector_store_dir", tmp_path / "vs")
    monkeypatch.setattr(cfg_module.settings, "raw_documents_dir", tmp_path / "raw")
    monkeypatch.setattr(cfg_module.settings, "processed_dir", tmp_path / "proc")
    monkeypatch.setattr(cfg_module.settings, "routing_config_path", routing_config)
    monkeypatch.setattr(cfg_module.settings, "pipeline_sync_mode", True)
    (tmp_path / "vs").mkdir(exist_ok=True)
    (tmp_path / "raw").mkdir(exist_ok=True)
    (tmp_path / "proc").mkdir(exist_ok=True)

    app.dependency_overrides[get_db] = lambda: db_session

    client = TestClient(app, headers={"X-Tenant-ID": "company_abc"})

    # 테스트 문서 업로드 (카테고리별)
    # 기술 (20개)
    for i in range(20):
        pdf_content = f"""온톨로지와 지식 그래프 문서 {i}

이 문서는 온톨로지, knowledge graph, semantic web, RDF, NLP, 자연언어처리,
머신러닝, 벡터, 임베딩, 텍스트 분석, 데이터, 모델, 학습 등의
기술 관련 내용을 다룹니다. semantic relationship과 semantic web의
중요성을 강조합니다."""
        files = {"file": (f"tech_{i}.txt", create_test_pdf(f"tech_{i}.txt", pdf_content))}
        data = {
            "category_large": "기술",
            "category_mid": "ontology",
            "project_code": "TECH001",
        }
        client.post("/api/v1/documents/upload", files=files, data=data)

    # 인사 (20개)
    for i in range(20):
        pdf_content = f"""HR 및 인사 관리 문서 {i}

이 문서는 채용, 급여, 복리후생, 신입사원, 지원자, 합격, 면접,
월급, 보너스, 퇴직금, 직급, 부서, 승진, 업무, 평가, 성과,
교육, 복무, 수당, 세금 등의 인사 관련 내용을 다룹니다.
인사 운영 기준, 채용 절차, 급여 지급 기준, 복리후생 안내와
부서별 업무 평가 및 승진 심사 절차를 함께 설명합니다."""
        files = {"file": (f"hr_{i}.txt", create_test_pdf(f"hr_{i}.txt", pdf_content))}
        data = {
            "category_large": "인사",
            "category_mid": "채용" if i % 2 == 0 else "급여",
            "project_code": "HR001" if i % 2 == 0 else "HR002",
        }
        client.post("/api/v1/documents/upload", files=files, data=data)

    # 규정 (10개)
    for i in range(10):
        pdf_content = f"""취업규칙 및 정책 문서 {i}

이 문서는 취업규칙, 휴가 정책, 근무시간, 보안 규정, 인사 평가,
정책, 조직, 권리, 문서 등의 규정 관련 내용을 다룹니다.
회사 규칙, 내부 지침, 보안 정책, 휴가 신청 절차와 근태 관리
기준을 포함하여 전사 구성원이 준수해야 할 규정을 설명합니다."""
        files = {"file": (f"policy_{i}.txt", create_test_pdf(f"policy_{i}.txt", pdf_content))}
        data = {
            "category_large": "규정",
            "category_mid": "policy",
            "project_code": "POLICY001",
        }
        client.post("/api/v1/documents/upload", files=files, data=data)

    return client


def test_search_quality_benchmark(benchmark_setup):
    """
    벤치마크 테스트

    목표:
    - Precision@5 ≥ 70%
    - 커버리지 ≥ 95%
    - 평균 응답시간 < 150ms
    """
    client = benchmark_setup

    benchmark = SearchQualityBenchmark()
    results = benchmark.run_benchmark(client)

    # 결과 출력
    benchmark.print_results(results)

    # 검증
    assert results["avg_precision"] >= 0.70, \
        f"Average precision {results['avg_precision']:.2%} < 70%"
    assert results["coverage"] >= 0.95, \
        f"Coverage {results['coverage']:.2%} < 95%"
    assert results["response_times"]["avg"] < 150, \
        f"Average response time {results['response_times']['avg']:.2f}ms >= 150ms"
    assert results["response_times"]["p99"] < 200, \
        f"p99 response time {results['response_times']['p99']:.2f}ms >= 200ms"


def test_search_quality_by_category(benchmark_setup):
    """
    카테고리별 정확도 분석

    - 각 카테고리별 Precision@5 측정
    - 약한 카테고리 식별
    """
    client = benchmark_setup

    benchmark = SearchQualityBenchmark()
    results = benchmark.run_benchmark(client)

    print("\n카테고리별 성능 분석:")
    for cat, prec in sorted(results['results_by_category'].items()):
        status = "✅" if prec >= 0.70 else "⚠️"
        print(f"{status} {cat}: {prec:.2%}")

    # 모든 카테고리가 60% 이상 정확도 보장
    for cat, prec in results['results_by_category'].items():
        assert prec >= 0.60, \
            f"Category {cat} precision {prec:.2%} < 60%"
