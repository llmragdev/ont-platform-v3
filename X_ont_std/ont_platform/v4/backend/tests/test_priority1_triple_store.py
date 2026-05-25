"""Priority 1: JSONL Triple Store unit tests"""
import sys
import json
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.triple_store import TripleStore, RDFTriple


class TestRDFTriple:
    """RDFTriple 기본 테스트"""

    def test_create_triple(self):
        """트리플 생성"""
        triple = RDFTriple("subject1", "predicate1", "object1")
        assert triple.subject == "subject1"
        assert triple.predicate == "predicate1"
        assert triple.obj == "object1"

    def test_to_dict(self):
        """트리플을 딕셔너리로 변환"""
        triple = RDFTriple("s", "p", "o")
        data = triple.to_dict()
        assert data["subject"] == "s"
        assert data["predicate"] == "p"
        assert data["object"] == "o"

    def test_from_dict(self):
        """딕셔너리에서 트리플 생성"""
        data = {"subject": "s", "predicate": "p", "object": "o"}
        triple = RDFTriple.from_dict(data)
        assert triple.subject == "s"
        assert triple.obj == "o"

    def test_to_tuple(self):
        """트리플을 튜플로 변환"""
        triple = RDFTriple("s", "p", "o")
        t = triple.to_tuple()
        assert t == ("s", "p", "o")


class TestTripleStoreBasics:
    """기본 CRUD 연산"""

    def test_add_single_triple(self):
        """단일 트리플 추가"""
        store = TripleStore()
        triple = store.add_triple("s1", "p1", "o1")
        assert store.get_triple_count() == 1
        assert triple.subject == "s1"

    def test_add_multiple_triples(self):
        """여러 트리플 추가"""
        store = TripleStore()
        triples = store.add_triples([
            ("s1", "p1", "o1"),
            ("s2", "p2", "o2"),
            ("s3", "p3", "o3")
        ])
        assert store.get_triple_count() == 3
        assert len(triples) == 3

    def test_remove_triple(self):
        """트리플 제거"""
        store = TripleStore()
        store.add_triple("s1", "p1", "o1")
        store.add_triple("s2", "p2", "o2")

        removed = store.remove_triple("s1", "p1", "o1")
        assert removed is True
        assert store.get_triple_count() == 1

    def test_remove_nonexistent_triple(self):
        """존재하지 않는 트리플 제거"""
        store = TripleStore()
        removed = store.remove_triple("s1", "p1", "o1")
        assert removed is False

    def test_clear(self):
        """모든 트리플 삭제"""
        store = TripleStore()
        store.add_triples([("s1", "p1", "o1"), ("s2", "p2", "o2")])
        store.clear()
        assert store.get_triple_count() == 0


class TestTripleStoreQuery:
    """쿼리 기능"""

    def test_query_by_subject(self):
        """주제별 조회"""
        store = TripleStore()
        store.add_triples([
            ("person:1", "type", "Person"),
            ("person:1", "name", "Alice"),
            ("person:2", "type", "Person")
        ])

        results = store.query(subject="person:1")
        assert len(results) == 2
        assert all(t.subject == "person:1" for t in results)

    def test_query_by_predicate(self):
        """술어별 조회"""
        store = TripleStore()
        store.add_triples([
            ("p1", "type", "Person"),
            ("p2", "type", "Organization"),
            ("p3", "name", "Alice")
        ])

        results = store.query(predicate="type")
        assert len(results) == 2

    def test_query_by_object(self):
        """객체별 조회"""
        store = TripleStore()
        store.add_triples([
            ("p1", "type", "Person"),
            ("p2", "type", "Person"),
            ("p3", "type", "Organization")
        ])

        results = store.query(obj="Person")
        assert len(results) == 2

    def test_query_by_multiple_fields(self):
        """여러 필드로 조회"""
        store = TripleStore()
        store.add_triples([
            ("p1", "type", "Person"),
            ("p1", "name", "Alice"),
            ("p2", "type", "Person")
        ])

        results = store.query(subject="p1", predicate="type")
        assert len(results) == 1
        assert results[0].obj == "Person"

    def test_get_all_triples(self):
        """모든 트리플 반환"""
        store = TripleStore()
        added = store.add_triples([("s1", "p1", "o1"), ("s2", "p2", "o2")])
        all_triples = store.get_all_triples()
        assert len(all_triples) == 2


class TestTripleStorePersistence:
    """JSONL 영속성"""

    def test_save_and_load(self):
        """저장 후 로드"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "triples.jsonl"
            store = TripleStore(store_path)

            # 저장
            store.add_triples([
                ("s1", "p1", "o1"),
                ("s2", "p2", "o2")
            ])
            store.save_to_jsonl()

            assert store_path.exists()

            # 새 저장소에서 로드
            store2 = TripleStore(store_path)
            loaded = store2.load_from_jsonl()

            assert loaded == 2
            assert store2.get_triple_count() == 2

    def test_jsonl_format(self):
        """JSONL 포맷 검증"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "triples.jsonl"
            store = TripleStore(store_path)

            store.add_triple("s1", "p1", "o1")
            store.save_to_jsonl()

            # 파일 내용 검증
            lines = store_path.read_text().strip().split('\n')
            assert len(lines) >= 2  # 메타데이터 + 트리플

            # 메타데이터 확인
            meta = json.loads(lines[0])
            assert meta["type"] == "metadata"
            assert "data" in meta

            # 트리플 확인
            triple = json.loads(lines[1])
            assert triple["type"] == "triple"
            assert triple["data"]["subject"] == "s1"

    def test_save_large_dataset(self):
        """대용량 데이터셋 저장"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "large.jsonl"
            store = TripleStore(store_path)

            # 1000개 트리플 추가
            for i in range(1000):
                store.add_triple(f"subject:{i}", "type", f"Class:{i % 10}")

            store.save_to_jsonl()

            # 로드 및 검증
            store2 = TripleStore(store_path)
            loaded = store2.load_from_jsonl()
            assert loaded == 1000
            assert store2.get_triple_count() == 1000

    def test_export_import(self):
        """내보내기/가져오기"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "store1.jsonl"
            path2 = Path(tmpdir) / "store2.jsonl"

            # 첫 번째 저장소
            store1 = TripleStore(path1)
            store1.add_triples([("s1", "p1", "o1"), ("s2", "p2", "o2")])

            # 내보내기
            store1.export_to_jsonl(path2)

            # 가져오기
            store3 = TripleStore()
            imported = store3.import_from_jsonl(path2)

            assert imported == 2
            assert store3.get_triple_count() == 2

    def test_load_from_nonexistent_file(self):
        """존재하지 않는 파일에서 로드"""
        store = TripleStore(Path("/nonexistent/path.jsonl"))
        loaded = store.load_from_jsonl()
        assert loaded == 0


class TestTripleStoreStats:
    """통계 및 검증"""

    def test_get_stats(self):
        """통계 조회"""
        store = TripleStore()
        store.add_triples([
            ("p1", "type", "Person"),
            ("p1", "name", "Alice"),
            ("p2", "type", "Person"),
            ("o1", "hasManager", "p1")
        ])

        stats = store.get_stats()
        assert stats["total_triples"] == 4
        assert stats["unique_subjects"] == 3
        assert stats["unique_predicates"] == 3
        assert stats["unique_objects"] == 3

    def test_validate_clean_data(self):
        """정상 데이터 검증"""
        store = TripleStore()
        store.add_triples([
            ("p1", "type", "Person"),
            ("p1", "name", "Alice")
        ])

        validation = store.validate()
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0

    def test_validate_duplicate_detection(self):
        """중복 검출"""
        store = TripleStore()
        store.add_triple("p1", "type", "Person")
        store.add_triple("p1", "type", "Person")  # 중복

        validation = store.validate()
        assert len(validation["warnings"]) > 0

    def test_validate_empty_fields(self):
        """빈 필드 검출"""
        store = TripleStore()
        store.triples.append(RDFTriple("", "p1", "o1"))  # 빈 주제

        validation = store.validate()
        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0


class TestTripleStoreMemoryMode:
    """메모리 전용 모드"""

    def test_memory_mode_without_path(self):
        """경로 없이 메모리 전용 모드"""
        store = TripleStore()  # store_path=None
        store.add_triples([("s1", "p1", "o1"), ("s2", "p2", "o2")])

        assert store.get_triple_count() == 2

        with pytest.raises(ValueError):
            store.save_to_jsonl()  # 에러 발생


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
