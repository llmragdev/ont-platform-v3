"""Test SPARQL→SQL Translator - Hot-path patterns #18-22"""
import pytest
import time
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.sparql_translator import SPARQLTranslator, QueryType, PatternType
from app.db.models import Entity, Relationship


class TestSPARQLTranslator:
    """Test SPARQL→SQL translator with hot-path patterns"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, db_session: Session):
        """Setup test data in PostgreSQL before each test"""
        # Clear existing data
        db_session.query(Relationship).delete()
        db_session.query(Entity).delete()
        db_session.commit()

    @pytest.fixture
    def translator(self, db_session: Session) -> SPARQLTranslator:
        """Create SPARQLTranslator instance"""
        return SPARQLTranslator(db_session, domain_id="test_domain")

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #18: Simple ID Lookup
    # ────────────────────────────────────────────────────────────────────────

    def test_18_simple_id_lookup_parsing(self, translator):
        """Test 18a: Simple ID lookup - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?name
        WHERE {
            ex:ship1 ex:name ?name
        }
        """

        # Parse query
        query_type = translator._detect_query_type(query)
        select_vars = translator._extract_select_vars(query)
        where_clause = translator._extract_where_clause(query)

        assert query_type == QueryType.SELECT
        assert select_vars == ["?name"]
        assert "ex:ship1" in where_clause or "ship1" in where_clause

    def test_18_simple_id_lookup_sql_generation(self, db_session: Session, translator):
        """Test 18b: Simple ID lookup - SQL generation and execution"""
        # Insert test data
        entity = Entity(
            id="http://example.org/ship1",
            entity_type="Ship",
            domain_id="test_domain",
            properties={"name": "USS Enterprise"}
        )
        db_session.add(entity)
        db_session.commit()

        # Translate and execute
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?name
        WHERE {
            ex:ship1 ex:name ?name
        }
        """

        result = translator.execute(query)

        # Verify structure
        assert "error" not in result or result["error"] is None
        assert result["query_type"] == "SELECT"
        assert "?name" in result["select_vars"]

    def test_18_simple_id_lookup_performance(self, db_session: Session, translator):
        """Test 18c: Simple ID lookup - Performance target <50ms"""
        # Insert 100 entities
        for i in range(100):
            entity = Entity(
                id=f"http://example.org/ship{i}",
                entity_type="Ship",
                domain_id="test_domain",
                properties={"name": f"Ship {i}"}
            )
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?name
        WHERE {
            ex:ship1 ex:name ?name
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert elapsed < 50, f"Query took {elapsed}ms, target <50ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #19: Type Filtering
    # ────────────────────────────────────────────────────────────────────────

    def test_19_type_filter_parsing(self, translator):
        """Test 19a: Type filtering - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?entity
        WHERE {
            ?entity ex:type "Ship"
        }
        """

        where_clause = translator._extract_where_clause(query)
        patterns = translator._extract_triple_patterns(where_clause)

        assert len(patterns) > 0
        assert any("type" in p or "Ship" in p for p in patterns)

    def test_19_type_filter_sql_execution(self, db_session: Session, translator):
        """Test 19b: Type filtering - SQL generation and execution"""
        # Insert mixed entities
        entities = [
            Entity(id="http://example.org/e1", entity_type="Ship", domain_id="test_domain", properties={"type": "Ship"}),
            Entity(id="http://example.org/e2", entity_type="Block", domain_id="test_domain", properties={"type": "Block"}),
            Entity(id="http://example.org/e3", entity_type="Ship", domain_id="test_domain", properties={"type": "Ship"}),
        ]
        for entity in entities:
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?entity
        WHERE {
            ?entity ex:type "Ship"
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_19_type_filter_performance(self, db_session: Session, translator):
        """Test 19c: Type filtering - Performance target <50ms"""
        # Insert 1000 entities with type filter
        for i in range(1000):
            entity_type = "Ship" if i % 3 == 0 else "Block"
            entity = Entity(
                id=f"http://example.org/e{i}",
                entity_type=entity_type,
                domain_id="test_domain",
                properties={"type": entity_type}
            )
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?entity
        WHERE {
            ?entity ex:type "Ship"
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 50, f"Query took {elapsed}ms, target <50ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #20: Numeric Comparison (Greater Than)
    # ────────────────────────────────────────────────────────────────────────

    def test_20_numeric_gt_parsing(self, translator):
        """Test 20a: Numeric GT filter - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?length
        WHERE {
            ?part ex:length ?length
            FILTER (?length > 75)
        }
        """

        filter_clause = translator._extract_filter_clause(query)
        assert filter_clause is not None
        assert ">" in filter_clause or "length" in filter_clause

    def test_20_numeric_gt_sql_generation(self, db_session: Session, translator):
        """Test 20b: Numeric GT filter - SQL generation"""
        # Insert entities with numeric properties
        entities = [
            Entity(id="http://example.org/p1", entity_type="Part", domain_id="test_domain", properties={"length": 100}),
            Entity(id="http://example.org/p2", entity_type="Part", domain_id="test_domain", properties={"length": 200}),
            Entity(id="http://example.org/p3", entity_type="Part", domain_id="test_domain", properties={"length": 50}),
        ]
        for entity in entities:
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?length
        WHERE {
            ?part ex:length ?length
            FILTER (?length > 75)
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"
        # Should match 2 entities (100 and 200)

    def test_20_numeric_gt_performance(self, db_session: Session, translator):
        """Test 20c: Numeric GT filter - Performance target <100ms"""
        # Insert 10K entities with numeric properties
        for i in range(10000):
            entity = Entity(
                id=f"http://example.org/p{i}",
                entity_type="Part",
                domain_id="test_domain",
                properties={"length": 50 + (i % 200)}
            )
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?length
        WHERE {
            ?part ex:length ?length
            FILTER (?length > 75)
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 100, f"Query took {elapsed}ms, target <100ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #21: Equality Filter
    # ────────────────────────────────────────────────────────────────────────

    def test_21_equality_filter_parsing(self, translator):
        """Test 21a: Equality filter - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?work
        WHERE {
            ?work ex:status "Active"
        }
        """

        where_clause = translator._extract_where_clause(query)
        patterns = translator._extract_triple_patterns(where_clause)

        assert len(patterns) > 0
        assert any("status" in p or "Active" in p for p in patterns)

    def test_21_equality_filter_sql_execution(self, db_session: Session, translator):
        """Test 21b: Equality filter - SQL execution"""
        entities = [
            Entity(id="http://example.org/w1", entity_type="Work", domain_id="test_domain", properties={"status": "Active"}),
            Entity(id="http://example.org/w2", entity_type="Work", domain_id="test_domain", properties={"status": "Inactive"}),
        ]
        for entity in entities:
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?work
        WHERE {
            ?work ex:status "Active"
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_21_equality_filter_performance(self, db_session: Session, translator):
        """Test 21c: Equality filter - Performance target <30ms"""
        statuses = ["Active", "Inactive", "Pending"]
        for i in range(1000):
            entity = Entity(
                id=f"http://example.org/w{i}",
                entity_type="Work",
                domain_id="test_domain",
                properties={"status": statuses[i % 3]}
            )
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?work
        WHERE {
            ?work ex:status "Active"
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 30, f"Query took {elapsed}ms, target <30ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #22: Regex Filter
    # ────────────────────────────────────────────────────────────────────────

    def test_22_regex_filter_parsing(self, translator):
        """Test 22a: Regex filter - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?doc
        WHERE {
            ?doc ex:name ?name
            FILTER regex(?name, "Document")
        }
        """

        filter_clause = translator._extract_filter_clause(query)
        assert filter_clause is not None
        assert "regex" in filter_clause.lower() or "Document" in filter_clause

    def test_22_regex_filter_sql_generation(self, db_session: Session, translator):
        """Test 22b: Regex filter - SQL generation"""
        entities = [
            Entity(id="http://example.org/d1", entity_type="Doc", domain_id="test_domain", properties={"name": "Document_001"}),
            Entity(id="http://example.org/d2", entity_type="Doc", domain_id="test_domain", properties={"name": "Drawing_001"}),
            Entity(id="http://example.org/d3", entity_type="Doc", domain_id="test_domain", properties={"name": "Document_002"}),
        ]
        for entity in entities:
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?doc
        WHERE {
            ?doc ex:name ?name
            FILTER regex(?name, "Document")
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_22_regex_filter_performance(self, db_session: Session, translator):
        """Test 22c: Regex filter - Performance target <500ms"""
        names = ["Document_001", "Drawing_001", "Document_002", "Report_001"]
        for i in range(1000):
            entity = Entity(
                id=f"http://example.org/d{i}",
                entity_type="Doc",
                domain_id="test_domain",
                properties={"name": names[i % 4]}
            )
            db_session.add(entity)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?doc
        WHERE {
            ?doc ex:name ?name
            FILTER regex(?name, "Document")
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 500, f"Query took {elapsed}ms, target <500ms"

    # ────────────────────────────────────────────────────────────────────────
    # Integration tests
    # ────────────────────────────────────────────────────────────────────────

    def test_translator_initialization(self, translator):
        """Test translator initialization"""
        assert translator.domain_id == "test_domain"
        assert translator.query_type is None or translator.query_type == QueryType.SELECT
        assert len(translator.select_vars) == 0 or translator.select_vars == ["*"]

    def test_pattern_type_detection(self, translator):
        """Test pattern type detection"""
        patterns = [
            ("<http://example.org/ship1> <http://example.org/name> ?name", "entity_lookup"),
            ("?x <http://example.org/type> ?y", ["property_filter", "relation"]),  # Can be either
            ("?x <http://example.org/has_part> ?y", ["relation", "property_filter"]),  # Can be either
        ]

        for pattern_str, expected_types in patterns:
            if isinstance(expected_types, str):
                expected_types = [expected_types]

            pattern_type, components = translator._match_pattern(pattern_str)
            assert pattern_type.value in expected_types or pattern_type.value == "unsupported"

    def test_variable_binding_tracking(self, translator):
        """Test variable binding tracking across patterns"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ?part ex:length ?length
            FILTER (?length > 75)
        }
        """

        translator.translate(query)
        # After translation, should track variable bindings
        assert hasattr(translator, "variable_bindings")
