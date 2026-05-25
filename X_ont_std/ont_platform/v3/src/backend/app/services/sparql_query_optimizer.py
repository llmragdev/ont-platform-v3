"""Phase 4 Week 6: SPARQL 쿼리 재작성 엔진 (Query Rewriting Engine)"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class QueryPattern:
    """쿼리 패턴"""
    subject: str
    predicate: str
    obj: str
    is_optional: bool = False
    has_filter: bool = False


@dataclass
class OptimizationStats:
    """최적화 통계"""
    original_time_ms: float = 0.0
    optimized_time_ms: float = 0.0
    improvement_percent: float = 0.0
    patterns_reordered: int = 0
    filters_pushed: int = 0


class SPARQLQueryOptimizer:
    """SPARQL 쿼리 자동 최적화 엔진"""

    def __init__(self):
        self.stats: Dict[str, Any] = {}
        self.optimization_history: List[Dict] = []

    def optimize_query(self, query_str: str) -> str:
        """쿼리 최적화 메인 메서드"""
        if not query_str or not isinstance(query_str, str):
            return query_str

        try:
            # 1. 쿼리 파싱
            patterns, filters, query_type = self._parse_query(query_str)

            if not patterns:
                return query_str

            # 2. 최적화 규칙 적용
            optimized_patterns = self._apply_optimization_rules(
                patterns, filters, query_type
            )

            # 3. 최적화된 쿼리 재구성
            optimized_query = self._reconstruct_query(
                query_str, optimized_patterns, filters, query_type
            )

            return optimized_query

        except Exception as e:
            return query_str

    def _parse_query(self, query_str: str) -> Tuple[List[QueryPattern], List[str], str]:
        """쿼리 파싱 및 패턴 추출"""
        query_upper = query_str.strip().upper()

        # 쿼리 타입 감지
        if query_upper.startswith("SELECT"):
            query_type = "SELECT"
        elif query_upper.startswith("ASK"):
            query_type = "ASK"
        elif query_upper.startswith("CONSTRUCT"):
            query_type = "CONSTRUCT"
        else:
            query_type = "UNKNOWN"

        # WHERE 절 추출
        where_match = re.search(r"WHERE\s*\{([^}]+)\}", query_str, re.IGNORECASE)
        if not where_match:
            return [], [], query_type

        where_clause = where_match.group(1)

        # FILTER 추출
        filters = self._extract_filters(where_clause)

        # 패턴 추출 (OPTIONAL 고려)
        patterns = self._extract_patterns(where_clause)

        return patterns, filters, query_type

    def _extract_patterns(self, where_clause: str) -> List[QueryPattern]:
        """WHERE 절에서 패턴 추출"""
        patterns = []

        # OPTIONAL 패턴 처리
        optional_pattern = r"OPTIONAL\s*\{\s*([^}]+)\}"
        optional_matches = re.finditer(optional_pattern, where_clause, re.IGNORECASE)

        optional_sections = set()
        for match in optional_matches:
            optional_sections.add(match.group(1))

        # 기본 트리플 패턴 추출: ?s ?p ?o
        triple_pattern = r"(\?\w+|\S+)\s+(\?\w+|\S+)\s+(\?\w+|\"[^\"]+\"|\S+)\s*\."

        for match in re.finditer(triple_pattern, where_clause):
            subject = match.group(1).strip()
            predicate = match.group(2).strip()
            obj = match.group(3).strip()

            is_in_optional = any(
                subject in opt_sec or predicate in opt_sec or obj in opt_sec
                for opt_sec in optional_sections
            )

            pattern = QueryPattern(
                subject=subject,
                predicate=predicate,
                obj=obj,
                is_optional=is_in_optional,
                has_filter=False
            )
            patterns.append(pattern)

        return patterns

    def _extract_filters(self, where_clause: str) -> List[str]:
        """WHERE 절에서 FILTER 조건 추출"""
        filters = []

        # FILTER(...) 패턴 추출
        filter_pattern = r"FILTER\s*\(([^)]+)\)"
        for match in re.finditer(filter_pattern, where_clause, re.IGNORECASE):
            filters.append(match.group(1))

        return filters

    def _apply_optimization_rules(
        self,
        patterns: List[QueryPattern],
        filters: List[str],
        query_type: str
    ) -> List[QueryPattern]:
        """최적화 규칙 적용"""

        # 규칙 1: FILTER 푸시다운 (FILTER를 가능한 빨리 실행)
        patterns = self._pushdown_filters(patterns, filters)

        # 규칙 2: 조인 순서 최적화 (선택도 기반)
        patterns = self._reorder_joins(patterns)

        # 규칙 3: OPTIONAL 패턴 분리
        patterns = self._separate_optional_patterns(patterns)

        return patterns

    def _pushdown_filters(
        self,
        patterns: List[QueryPattern],
        filters: List[str]
    ) -> List[QueryPattern]:
        """FILTER를 가능한 빨리 실행하도록 배치"""
        for filter_expr in filters:
            # FILTER의 변수 추출
            filter_vars = self._extract_variables(filter_expr)

            # 변수가 정의되는 첫 번째 패턴 찾기
            for i, pattern in enumerate(patterns):
                pattern_vars = self._get_pattern_variables(pattern)

                if filter_vars.issubset(pattern_vars):
                    pattern.has_filter = True
                    break

        return patterns

    def _reorder_joins(self, patterns: List[QueryPattern]) -> List[QueryPattern]:
        """선택도 기반 조인 순서 최적화"""
        if len(patterns) <= 1:
            return patterns

        # 각 패턴의 선택도 계산
        selectivity_list = [
            (i, pattern, self._estimate_selectivity(pattern))
            for i, pattern in enumerate(patterns)
        ]

        # 선택도가 낮은 순서대로 정렬 (제한적인 것부터)
        selectivity_list.sort(key=lambda x: x[2])

        # 정렬된 순서대로 패턴 재배열
        reordered = [pattern for _, pattern, _ in selectivity_list]

        return reordered

    def _estimate_selectivity(self, pattern: QueryPattern) -> float:
        """패턴의 선택도 추정 (0~1, 작을수록 선택적)"""
        selectivity = 0.5  # 기본값

        # 상수 객체를 가진 패턴: 낮은 선택도
        if self._is_constant(pattern.obj):
            selectivity = 0.1

        # FILTER가 있는 패턴: 선택도 감소
        elif pattern.has_filter:
            selectivity = 0.3

        # 변수만 있는 패턴: 높은 선택도
        elif self._is_variable(pattern.subject) and self._is_variable(
            pattern.obj
        ):
            selectivity = 0.8

        return selectivity

    def _separate_optional_patterns(
        self,
        patterns: List[QueryPattern]
    ) -> List[QueryPattern]:
        """OPTIONAL 패턴을 별도로 분리"""
        required = [p for p in patterns if not p.is_optional]
        optional = [p for p in patterns if p.is_optional]

        # 필수 패턴을 먼저 배치, 그 다음 OPTIONAL
        return required + optional

    def _reconstruct_query(
        self,
        original_query: str,
        optimized_patterns: List[QueryPattern],
        filters: List[str],
        query_type: str
    ) -> str:
        """최적화된 쿼리 재구성"""
        try:
            # SELECT 절 보존
            select_match = re.search(
                r"(SELECT[^{]*)\{", original_query, re.IGNORECASE
            )
            select_clause = select_match.group(1) if select_match else "SELECT * "

            # 최적화된 WHERE 절 구성
            where_patterns = self._build_where_clause(
                optimized_patterns, filters
            )

            # 전체 쿼리 재구성
            reconstructed = f"{select_clause}{{\n{where_patterns}\n}}"

            return reconstructed

        except Exception:
            return original_query

    def _build_where_clause(
        self,
        patterns: List[QueryPattern],
        filters: List[str]
    ) -> str:
        """WHERE 절 구성"""
        lines = []

        for pattern in patterns:
            triple_line = f"  {pattern.subject} {pattern.predicate} {pattern.obj} ."

            if pattern.is_optional:
                lines.append(f"  OPTIONAL {{\n{triple_line}\n  }}")
            else:
                lines.append(triple_line)

            if pattern.has_filter and filters:
                lines.append(f"  FILTER({filters[0]})")

        return "\n".join(lines)

    def _extract_variables(self, text: str) -> Set[str]:
        """텍스트에서 변수 추출"""
        return set(re.findall(r"\?(\w+)", text))

    def _get_pattern_variables(self, pattern: QueryPattern) -> Set[str]:
        """패턴의 변수 추출"""
        variables = set()

        for item in [pattern.subject, pattern.predicate, pattern.obj]:
            if self._is_variable(item):
                variables.add(item)

        return variables

    def _is_variable(self, value: str) -> bool:
        """변수인지 확인"""
        return value.startswith("?")

    def _is_constant(self, value: str) -> bool:
        """상수인지 확인"""
        return not self._is_variable(value) and value != "*"

    def get_optimization_stats(self) -> Dict[str, Any]:
        """최적화 통계 조회"""
        return {
            "total_optimizations": len(self.optimization_history),
            "avg_improvement": (
                sum(
                    h.get("improvement_percent", 0)
                    for h in self.optimization_history
                )
                / len(self.optimization_history)
                if self.optimization_history
                else 0
            ),
            "history": self.optimization_history[-10:],  # 최근 10개
        }
