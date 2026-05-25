"""Priority 1: JSONL-based Triple Store for persistence"""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class RDFTriple:
    """단일 RDF 트리플"""

    def __init__(self, subject: str, predicate: str, obj: str):
        self.subject = subject
        self.predicate = predicate
        self.obj = obj

    def to_dict(self) -> Dict[str, str]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.obj
        }

    def to_tuple(self) -> Tuple[str, str, str]:
        return (self.subject, self.predicate, self.obj)

    @staticmethod
    def from_dict(data: Dict[str, str]) -> RDFTriple:
        return RDFTriple(
            subject=data["subject"],
            predicate=data["predicate"],
            obj=data["object"]
        )


class TripleStore:
    """JSONL 기반 트리플 저장소 (영속성 보장)"""

    def __init__(self, store_path: Optional[Path] = None):
        """
        Args:
            store_path: JSONL 파일 경로. None이면 메모리만 사용.
        """
        self.store_path = store_path
        self.triples: List[RDFTriple] = []
        self.metadata = {
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "triple_count": 0
        }

    def add_triple(self, subject: str, predicate: str, obj: str) -> RDFTriple:
        """트리플 추가"""
        triple = RDFTriple(subject, predicate, obj)
        self.triples.append(triple)
        self.metadata["updated_at"] = datetime.now(UTC).isoformat()
        self.metadata["triple_count"] = len(self.triples)
        return triple

    def add_triples(self, triples: List[Tuple[str, str, str]]) -> List[RDFTriple]:
        """여러 트리플 일괄 추가"""
        result = []
        for s, p, o in triples:
            result.append(self.add_triple(s, p, o))
        return result

    def remove_triple(self, subject: str, predicate: str, obj: str) -> bool:
        """트리플 제거"""
        initial_count = len(self.triples)
        self.triples = [
            t for t in self.triples
            if not (t.subject == subject and t.predicate == predicate and t.obj == obj)
        ]
        if len(self.triples) < initial_count:
            self.metadata["updated_at"] = datetime.now(UTC).isoformat()
            self.metadata["triple_count"] = len(self.triples)
            return True
        return False

    def query(self, subject: Optional[str] = None,
              predicate: Optional[str] = None,
              obj: Optional[str] = None) -> List[RDFTriple]:
        """트리플 조회 (선택적 필터)"""
        results = []
        for triple in self.triples:
            if subject and triple.subject != subject:
                continue
            if predicate and triple.predicate != predicate:
                continue
            if obj and triple.obj != obj:
                continue
            results.append(triple)
        return results

    def get_all_triples(self) -> List[RDFTriple]:
        """모든 트리플 반환"""
        return self.triples.copy()

    def get_triple_count(self) -> int:
        """트리플 개수"""
        return len(self.triples)

    def clear(self) -> None:
        """모든 트리플 삭제"""
        self.triples.clear()
        self.metadata["updated_at"] = datetime.now(UTC).isoformat()
        self.metadata["triple_count"] = 0

    # ── 영속성 메서드 ──────────────────────────────────────

    def save_to_jsonl(self) -> None:
        """트리플을 JSONL 파일로 저장"""
        if not self.store_path:
            raise ValueError("store_path not configured")

        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.store_path, 'w', encoding='utf-8') as f:
            # 메타데이터 첫 줄
            meta_line = json.dumps({
                "type": "metadata",
                "data": self.metadata
            })
            f.write(meta_line + '\n')

            # 각 트리플
            for triple in self.triples:
                line = json.dumps({
                    "type": "triple",
                    "data": triple.to_dict()
                })
                f.write(line + '\n')

    def load_from_jsonl(self) -> int:
        """JSONL 파일에서 트리플 로드"""
        if not self.store_path or not self.store_path.exists():
            return 0

        loaded_count = 0
        with open(self.store_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)

                    if entry.get("type") == "metadata":
                        self.metadata = entry.get("data", self.metadata)
                    elif entry.get("type") == "triple":
                        triple_data = entry.get("data", {})
                        triple = RDFTriple.from_dict(triple_data)
                        self.triples.append(triple)
                        loaded_count += 1
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")

        return loaded_count

    def export_to_jsonl(self, path: Path) -> None:
        """다른 경로로 내보내기"""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            meta_line = json.dumps({
                "type": "metadata",
                "data": self.metadata
            })
            f.write(meta_line + '\n')

            for triple in self.triples:
                line = json.dumps({
                    "type": "triple",
                    "data": triple.to_dict()
                })
                f.write(line + '\n')

    def import_from_jsonl(self, path: Path) -> int:
        """다른 경로에서 임포트"""
        if not path.exists():
            return 0

        imported_count = 0
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)
                    if entry.get("type") == "triple":
                        triple_data = entry.get("data", {})
                        triple = RDFTriple.from_dict(triple_data)
                        self.triples.append(triple)
                        imported_count += 1
                except json.JSONDecodeError:
                    pass

        self.metadata["updated_at"] = datetime.now(UTC).isoformat()
        self.metadata["triple_count"] = len(self.triples)
        return imported_count

    # ── 검사 & 통계 ──────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """저장소 통계"""
        subjects = set(t.subject for t in self.triples)
        predicates = set(t.predicate for t in self.triples)
        objects = set(t.obj for t in self.triples)

        return {
            "total_triples": len(self.triples),
            "unique_subjects": len(subjects),
            "unique_predicates": len(predicates),
            "unique_objects": len(objects),
            "file_path": str(self.store_path) if self.store_path else None,
            "created_at": self.metadata.get("created_at"),
            "updated_at": self.metadata.get("updated_at")
        }

    def validate(self) -> Dict[str, Any]:
        """데이터 검증"""
        errors = []
        warnings = []

        # 공백 검사
        for i, triple in enumerate(self.triples):
            if not triple.subject or not triple.predicate or not triple.obj:
                errors.append(f"Triple {i}: empty field")

            # 중복 검사
            for j, other in enumerate(self.triples):
                if i < j and triple.to_tuple() == other.to_tuple():
                    warnings.append(f"Duplicate: triple {i} and {j}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_triples": len(self.triples)
        }
