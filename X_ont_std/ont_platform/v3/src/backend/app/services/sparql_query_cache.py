"""Phase 4 Week 6: SPARQL 쿼리 결과 캐싱"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional, List


class SPARQLQueryCache:
    """SPARQL 쿼리 결과 캐싱"""

    def __init__(self, ttl_seconds: int = 300):
        """
        Args:
            ttl_seconds: 캐시 유효 시간 (초)
        """
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = ttl_seconds
        self.hit_count = 0
        self.miss_count = 0
        self.access_log: List[Dict[str, Any]] = []

    def _hash_query(self, query: str) -> str:
        """쿼리 정규화 및 해싱"""
        # 1. 공백 정규화
        normalized = " ".join(query.split())

        # 2. 대소문자 정규화
        normalized = normalized.upper()

        # 3. MD5 해시
        return hashlib.md5(normalized.encode()).hexdigest()

    def get(self, query: str, graph_hash: str) -> Optional[Any]:
        """캐시 조회"""
        cache_key = f"{self._hash_query(query)}:{graph_hash}"

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]

            # TTL 확인
            age = (datetime.now(UTC) - timestamp).total_seconds()

            if age < self.ttl:
                self.hit_count += 1
                self.access_log.append(
                    {
                        "action": "hit",
                        "query_hash": self._hash_query(query),
                        "timestamp": datetime.now(UTC),
                        "age_seconds": age,
                    }
                )
                return result
            else:
                # 만료된 항목 제거
                del self.cache[cache_key]

        self.miss_count += 1
        self.access_log.append(
            {
                "action": "miss",
                "query_hash": self._hash_query(query),
                "timestamp": datetime.now(UTC),
            }
        )
        return None

    def set(self, query: str, graph_hash: str, result: Any) -> None:
        """캐시 저장"""
        cache_key = f"{self._hash_query(query)}:{graph_hash}"
        self.cache[cache_key] = (result, datetime.now(UTC))

    def invalidate_by_graph(self, graph_hash: str) -> int:
        """특정 그래프의 캐시 무효화"""
        keys_to_remove = [
            k for k in self.cache.keys() if k.endswith(f":{graph_hash}")
        ]

        for k in keys_to_remove:
            del self.cache[k]

        return len(keys_to_remove)

    def invalidate_all(self) -> None:
        """모든 캐시 무효화"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "total": total,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self.cache),
            "ttl_seconds": self.ttl,
        }

    def cleanup_expired(self) -> int:
        """만료된 캐시 항목 정리"""
        keys_to_remove = []
        now = datetime.now(UTC)

        for key, (_, timestamp) in self.cache.items():
            age = (now - timestamp).total_seconds()
            if age >= self.ttl:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.cache[key]

        return len(keys_to_remove)

    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """접근 로그 조회"""
        return self.access_log[-limit:]


class RDFGraphIndexer:
    """RDF 그래프 인덱싱"""

    def __init__(self, triples: List[tuple] = None):
        """
        Args:
            triples: (subject, predicate, object) 튜플 리스트
        """
        self.triples = triples or []
        self.indexes: Dict[str, Any] = {}

    def build_indexes(self) -> None:
        """전체 인덱스 구축"""
        # 인덱스 1: Subject 기반
        self.indexes["subject"] = self._build_subject_index()

        # 인덱스 2: Predicate 기반
        self.indexes["predicate"] = self._build_predicate_index()

        # 인덱스 3: Object 기반
        self.indexes["object"] = self._build_object_index()

        # 인덱스 4: SPO 조합 (자주 함께 나타나는 패턴)
        self.indexes["spo_pattern"] = self._build_spo_index()

    def _build_subject_index(self) -> Dict[str, List[tuple]]:
        """Subject → (Predicate, Object) 인덱스"""
        index: Dict[str, List[tuple]] = {}

        for s, p, o in self.triples:
            if s not in index:
                index[s] = []
            index[s].append((p, o))

        return index

    def _build_predicate_index(self) -> Dict[str, set]:
        """Predicate → Subjects 인덱스"""
        index: Dict[str, set] = {}

        for s, p, o in self.triples:
            if p not in index:
                index[p] = set()
            index[p].add(s)

        return index

    def _build_object_index(self) -> Dict[str, set]:
        """Object → Subjects 인덱스"""
        index: Dict[str, set] = {}

        for s, p, o in self.triples:
            if o not in index:
                index[o] = set()
            index[o].add(s)

        return index

    def _build_spo_index(self) -> Dict[tuple, int]:
        """자주 함께 나타나는 (S, P, O) 패턴 인덱스"""
        pattern_counts: Dict[tuple, int] = {}

        for s, p, o in self.triples:
            # 패턴 타입 감지
            s_type = "var" if s.startswith("?") else "const"
            p_type = "var" if p.startswith("?") else "const"
            o_type = "var" if o.startswith("?") else "const"

            pattern_key = (s_type, p_type, o_type)
            pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1

        return pattern_counts

    def lookup_by_subject(self, subject: str) -> List[tuple]:
        """Subject로 조회"""
        return self.indexes.get("subject", {}).get(subject, [])

    def lookup_by_predicate(self, predicate: str) -> set:
        """Predicate로 조회"""
        return self.indexes.get("predicate", {}).get(predicate, set())

    def lookup_by_object(self, obj: str) -> set:
        """Object로 조회"""
        return self.indexes.get("object", {}).get(obj, set())

    def get_index_stats(self) -> Dict[str, Any]:
        """인덱스 통계"""
        return {
            "total_triples": len(self.triples),
            "subject_index_size": len(self.indexes.get("subject", {})),
            "predicate_index_size": len(self.indexes.get("predicate", {})),
            "object_index_size": len(self.indexes.get("object", {})),
            "spo_patterns": len(self.indexes.get("spo_pattern", {})),
        }
