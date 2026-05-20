"""Phase 4 Week 3: SPARQL 엔진 및 엔드포인트"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.rdf_model import SPARQLQuery, SPARQLResult, RDFTriple


class SPARQLEngine:
    """간단한 SPARQL 쿼리 엔진 (시뮬레이션)"""

    def __init__(self):
        self.triples: List[RDFTriple] = []
        self.query_history: List[SPARQLResult] = []

    def add_triples(self, triples: List[RDFTriple]) -> None:
        """트리플 추가"""
        self.triples.extend(triples)

    def execute_query(self, query: SPARQLQuery) -> SPARQLResult:
        """SPARQL 쿼리 실행"""
        start_time = time.time()
        query_id = f"query-{int(start_time * 1000)}"

        try:
            # 쿼리 타입 판정
            query_type = self._detect_query_type(query.query_string)

            if query_type == "SELECT":
                results = self._execute_select(query)
            elif query_type == "CONSTRUCT":
                results = self._execute_construct(query)
            elif query_type == "DESCRIBE":
                results = self._execute_describe(query)
            elif query_type == "ASK":
                results = self._execute_ask(query)
            else:
                results = []

            execution_time = (time.time() - start_time) * 1000

            result = SPARQLResult(
                query_id=query_id,
                variables=self._extract_variables(query.query_string),
                results=results,
                result_count=len(results),
                execution_time_ms=execution_time,
                query_timestamp=datetime.utcnow()
            )

            self.query_history.append(result)
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SPARQLResult(
                query_id=query_id,
                variables=[],
                results=[{"error": str(e)}],
                result_count=0,
                execution_time_ms=execution_time,
                query_timestamp=datetime.utcnow()
            )

    def _detect_query_type(self, query_string: str) -> str:
        """쿼리 타입 감지"""
        upper_query = query_string.upper().strip()

        if upper_query.startswith("SELECT"):
            return "SELECT"
        elif upper_query.startswith("CONSTRUCT"):
            return "CONSTRUCT"
        elif upper_query.startswith("DESCRIBE"):
            return "DESCRIBE"
        elif upper_query.startswith("ASK"):
            return "ASK"
        else:
            return "UNKNOWN"

    def _extract_variables(self, query_string: str) -> List[str]:
        """쿼리에서 변수 추출"""
        # 정규식으로 ?변수명 추출
        pattern = r"\?(\w+)"
        matches = re.findall(pattern, query_string)
        return list(dict.fromkeys(matches))  # 중복 제거, 순서 유지

    def _execute_select(self, query: SPARQLQuery) -> List[Dict[str, Any]]:
        """SELECT 쿼리 실행"""
        results = []

        # 간단한 패턴 매칭 (실제 SPARQL 엔진은 훨씬 복잡)
        # 예: "SELECT ?x WHERE { ?x rdf:type ex:Person }"

        pattern = self._extract_where_clause(query.query_string)
        variables = self._extract_variables(query.query_string)

        if not pattern:
            return results

        # 트리플 매칭
        for triple in self.triples:
            match = self._match_pattern(pattern, triple)
            if match:
                result_row = {}
                for var in variables:
                    if var in match:
                        result_row[f"?{var}"] = match[var]
                if result_row:
                    results.append(result_row)

        # LIMIT 적용
        if query.limit:
            results = results[:query.limit]

        # OFFSET 적용
        if query.offset:
            results = results[query.offset:]

        return results

    def _execute_construct(self, query: SPARQLQuery) -> List[Dict[str, Any]]:
        """CONSTRUCT 쿼리 실행 (트리플 생성)"""
        # CONSTRUCT는 새로운 트리플을 생성하는 쿼리
        # 시뮬레이션: WHERE 절 결과를 CONSTRUCT 패턴으로 변환

        results = []
        where_results = self._execute_select_where(query.query_string)

        for result in where_results:
            # 각 바인딩에 대해 CONSTRUCT 패턴 적용
            triple_dict = {
                "subject": result.get("?subject", ""),
                "predicate": result.get("?predicate", ""),
                "object": result.get("?object", "")
            }
            results.append(triple_dict)

        return results

    def _execute_describe(self, query: SPARQLQuery) -> List[Dict[str, Any]]:
        """DESCRIBE 쿼리 실행 (리소스 정보 반환)"""
        results = []

        # DESCRIBE는 지정된 리소스의 모든 정보 반환
        variables = self._extract_variables(query.query_string)

        for var in variables:
            for triple in self.triples:
                if triple.subject == var or (var.startswith("?") and triple.subject.endswith(var[1:])):
                    results.append({
                        "subject": triple.subject,
                        "predicate": triple.predicate,
                        "object": triple.object
                    })

        return results

    def _execute_ask(self, query: SPARQLQuery) -> List[Dict[str, Any]]:
        """ASK 쿼리 실행 (Boolean 결과)"""
        # ASK는 패턴이 매칭되는지 여부만 반환
        where_results = self._execute_select_where(query.query_string)

        return [{"boolean": len(where_results) > 0}]

    def _extract_where_clause(self, query_string: str) -> Optional[str]:
        """WHERE 절 추출"""
        match = re.search(r"WHERE\s*\{([^}]+)\}", query_string, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _execute_select_where(self, query_string: str) -> List[Dict[str, Any]]:
        """WHERE 절만 실행"""
        results = []
        where_clause = self._extract_where_clause(query_string)

        if not where_clause:
            return results

        # 간단한 트리플 패턴 매칭
        patterns = [p.strip() for p in where_clause.split(".") if p.strip()]

        for pattern in patterns:
            for triple in self.triples:
                match = self._match_pattern(pattern, triple)
                if match:
                    results.append(match)

        return results

    def _match_pattern(self, pattern: str, triple: RDFTriple) -> Optional[Dict[str, str]]:
        """패턴과 트리플 매칭"""
        # 간단한 패턴 매칭
        # 예: "?x rdf:type ex:Person"

        parts = pattern.split()
        if len(parts) < 3:
            return None

        subject_pattern = parts[0]
        predicate_pattern = parts[1]
        object_pattern = parts[2]

        bindings = {}

        # Subject 매칭
        if subject_pattern.startswith("?"):
            bindings[subject_pattern[1:]] = triple.subject
        elif subject_pattern != triple.subject:
            return None

        # Predicate 매칭
        if predicate_pattern.startswith("?"):
            bindings[predicate_pattern[1:]] = triple.predicate
        elif predicate_pattern != triple.predicate:
            return None

        # Object 매칭
        if object_pattern.startswith("?"):
            bindings[object_pattern[1:]] = triple.object
        elif object_pattern != triple.object:
            return None

        return bindings if bindings else {"matched": "true"}

    def get_query_history(self, limit: int = 100) -> List[SPARQLResult]:
        """쿼리 이력 조회"""
        return self.query_history[-limit:]

    def clear_triples(self) -> None:
        """모든 트리플 제거"""
        self.triples.clear()

    def get_triple_count(self) -> int:
        """트리플 개수"""
        return len(self.triples)
