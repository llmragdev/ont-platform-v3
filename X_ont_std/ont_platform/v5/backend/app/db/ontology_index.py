"""Priority 1-2: SQLite 메타데이터 인덱스 (성능 최적화)"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional

from storage_config import STORAGE_ROOT


class OntologyIndex:
    """SQLite 기반 온톨로지 메타데이터 인덱스"""

    def __init__(self, company_id: str = "default", project_id: str = "default"):
        self.company_id = company_id
        self.project_id = project_id

        index_dir = STORAGE_ROOT / "indices"
        index_dir.mkdir(parents=True, exist_ok=True)

        db_name = f"{company_id}_{project_id}_entities.db"
        self.db_path = index_dir / db_name
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Entity index table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    name TEXT,
                    properties TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_doc_id ON entities(doc_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)")

            # Relationship index table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    relation_id TEXT PRIMARY KEY,
                    from_entity_id TEXT NOT NULL,
                    to_entity_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    properties TEXT,
                    created_at TEXT
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_from_entity ON relationships(from_entity_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_to_entity ON relationships(to_entity_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relation_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_doc_id ON relationships(doc_id)")

            # Metadata table (for tracking sync status)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)

            conn.commit()

    def index_entity(self, entity: Dict[str, Any], doc_id: str) -> None:
        """Index a single entity"""
        entity_id = entity.get("entity_id")
        if not entity_id:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO entities
                (entity_id, doc_id, entity_type, name, properties, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                doc_id,
                entity.get("type", ""),
                entity.get("name", entity.get("entity_id", "")),
                json.dumps({"description": entity.get("description", ""), **entity.get("properties", {})}),
                datetime.now(UTC).isoformat()
            ))
            conn.commit()

    def index_entities_batch(self, entities: List[Dict[str, Any]], doc_id: str) -> None:
        """Batch index entities (faster than individual inserts)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for entity in entities:
                entity_id = entity.get("entity_id")
                if not entity_id:
                    continue
                cursor.execute("""
                    INSERT OR REPLACE INTO entities
                    (entity_id, doc_id, entity_type, name, properties, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    doc_id,
                    entity.get("type", ""),
                    entity.get("name", entity.get("entity_id", "")),
                    json.dumps({"description": entity.get("description", ""), **entity.get("properties", {})}),
                    datetime.now(UTC).isoformat()
                ))
            conn.commit()

    def index_relationship(self, relation: Dict[str, Any], doc_id: str) -> None:
        """Index a single relationship"""
        relation_id = relation.get("relation_id")
        if not relation_id:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO relationships
                (relation_id, from_entity_id, to_entity_id, relation_type, doc_id, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                relation_id,
                relation.get("from_entity_id", ""),
                relation.get("to_entity_id", ""),
                relation.get("type", ""),
                doc_id,
                json.dumps(relation.get("properties", {})),
                datetime.now(UTC).isoformat()
            ))
            conn.commit()

    def index_relationships_batch(self, relations: List[Dict[str, Any]], doc_id: str) -> None:
        """Batch index relationships"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for relation in relations:
                relation_id = relation.get("relation_id")
                if not relation_id:
                    continue
                cursor.execute("""
                    INSERT OR REPLACE INTO relationships
                    (relation_id, from_entity_id, to_entity_id, relation_type, doc_id, properties, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    relation_id,
                    relation.get("from_entity_id", ""),
                    relation.get("to_entity_id", ""),
                    relation.get("type", ""),
                    doc_id,
                    json.dumps(relation.get("properties", {})),
                    datetime.now(UTC).isoformat()
                ))
            conn.commit()

    def query_entities(self, entity_type: Optional[str] = None,
                      doc_ids: Optional[List[str]] = None,
                      limit: int = 10000, offset: int = 0) -> List[Dict[str, Any]]:
        """Query entities by type and/or doc_ids (fast index lookup)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM entities WHERE 1=1"
            params = []

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            if doc_ids:
                placeholders = ",".join("?" * len(doc_ids))
                query += f" AND doc_id IN ({placeholders})"
                params.extend(doc_ids)

            query += f" LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def query_entities_by_property(self, prop_name: str, prop_value: Any,
                                   entity_type: Optional[str] = None,
                                   doc_ids: Optional[List[str]] = None,
                                   limit: int = 10000) -> List[Dict[str, Any]]:
        """Query entities by property value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM entities WHERE 1=1"
            params = []

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            if doc_ids:
                placeholders = ",".join("?" * len(doc_ids))
                query += f" AND doc_id IN ({placeholders})"
                params.extend(doc_ids)

            query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Filter by property in Python (JSON search in SQLite is complex)
            results = []
            for row in rows:
                properties = json.loads(row["properties"] or "{}")
                if properties.get(prop_name) == prop_value:
                    results.append(dict(row))

            return results

    def query_relationships(self, from_entity_id: Optional[str] = None,
                           to_entity_id: Optional[str] = None,
                           relation_type: Optional[str] = None,
                           limit: int = 10000) -> List[Dict[str, Any]]:
        """Query relationships"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM relationships WHERE 1=1"
            params = []

            if from_entity_id:
                query += " AND from_entity_id = ?"
                params.append(from_entity_id)

            if to_entity_id:
                query += " AND to_entity_id = ?"
                params.append(to_entity_id)

            if relation_type:
                query += " AND relation_type = ?"
                params.append(relation_type)

            query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def count_entities(self, entity_type: Optional[str] = None) -> int:
        """Count entities by type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if entity_type:
                cursor.execute("SELECT COUNT(*) FROM entities WHERE entity_type = ?", (entity_type,))
            else:
                cursor.execute("SELECT COUNT(*) FROM entities")

            return cursor.fetchone()[0]

    def count_relationships(self) -> int:
        """Count all relationships"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM relationships")
            return cursor.fetchone()[0]

    def clear_index(self) -> None:
        """Clear all indexed data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entities")
            cursor.execute("DELETE FROM relationships")
            cursor.execute("DELETE FROM metadata")
            conn.commit()

    def delete_doc_index(self, doc_id: str) -> None:
        """Delete all entities and relationships for a document"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entities WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM relationships WHERE doc_id = ?", (doc_id,))
            conn.commit()

    def get_index_stats(self) -> Dict[str, int]:
        """Get index statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entities")
            entity_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM relationships")
            rel_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT doc_id) FROM entities")
            doc_count = cursor.fetchone()[0]

        return {
            "total_entities": entity_count,
            "total_relationships": rel_count,
            "documents": doc_count,
            "db_path": str(self.db_path),
            "db_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
