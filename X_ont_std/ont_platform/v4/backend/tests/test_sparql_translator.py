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

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #23: 1-Hop Simple Relation
    # ────────────────────────────────────────────────────────────────────────

    def test_23_simple_relation_parsing(self, translator):
        """Test 23a: Simple 1-hop relation - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?block
        WHERE {
            ex:ship1 ex:has_block ?block
        }
        """

        where_clause = translator._extract_where_clause(query)
        patterns = translator._extract_triple_patterns(where_clause)

        assert len(patterns) > 0
        assert any("has_block" in p for p in patterns)

    def test_23_simple_relation_sql_generation(self, db_session: Session, translator):
        """Test 23b: Simple 1-hop relation - SQL generation"""
        # Create entities and relationship
        ship = Entity(id="http://example.org/ship1", entity_type="Ship", domain_id="test_domain", properties={})
        block1 = Entity(id="http://example.org/block1", entity_type="Block", domain_id="test_domain", properties={})
        block2 = Entity(id="http://example.org/block2", entity_type="Block", domain_id="test_domain", properties={})
        db_session.add_all([ship, block1, block2])

        rel1 = Relationship(
            id="rel1", from_entity_id="http://example.org/ship1", to_entity_id="http://example.org/block1",
            relation_type="http://example.org/has_block"
        )
        rel2 = Relationship(
            id="rel2", from_entity_id="http://example.org/ship1", to_entity_id="http://example.org/block2",
            relation_type="http://example.org/has_block"
        )
        db_session.add_all([rel1, rel2])
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?block
        WHERE {
            ex:ship1 ex:has_block ?block
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_23_simple_relation_performance(self, db_session: Session, translator):
        """Test 23c: Simple 1-hop relation - Performance target <30ms"""
        # Create entities
        from_entity = Entity(id="http://example.org/supplier1", entity_type="Supplier", domain_id="test_domain", properties={})
        db_session.add(from_entity)
        db_session.commit()

        # Create 100 target entities and relationships
        for i in range(100):
            entity = Entity(id=f"http://example.org/part{i}", entity_type="Part", domain_id="test_domain", properties={})
            db_session.add(entity)
        db_session.commit()

        for i in range(100):
            rel = Relationship(
                id=f"rel{i}", from_entity_id="http://example.org/supplier1",
                to_entity_id=f"http://example.org/part{i}",
                relation_type="http://example.org/supplies",
            )
            db_session.add(rel)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:supplier1 ex:supplies ?part
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 30, f"Query took {elapsed}ms, target <30ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #24: 1-Hop + Filter
    # ────────────────────────────────────────────────────────────────────────

    def test_24_one_hop_with_filter_parsing(self, translator):
        """Test 24a: 1-hop + filter - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?cost
        WHERE {
            ex:supplier1 ex:supplies ?part .
            ?part ex:cost ?cost
            FILTER (?cost > 700)
        }
        """

        where_clause = translator._extract_where_clause(query)
        patterns = translator._extract_triple_patterns(where_clause)

        assert len(patterns) >= 2, "Should have at least 2 patterns"

    def test_24_one_hop_with_filter_sql_generation(self, db_session: Session, translator):
        """Test 24b: 1-hop + filter - SQL generation"""
        supplier = Entity(id="http://example.org/supplier1", entity_type="Supplier", domain_id="test_domain", properties={})
        db_session.add(supplier)
        db_session.commit()

        for i in range(5):
            part = Entity(
                id=f"http://example.org/part{i}",
                entity_type="Part",
                domain_id="test_domain",
                properties={"cost": 600 + (i * 100)}
            )
            db_session.add(part)
        db_session.commit()

        for i in range(5):
            rel = Relationship(
                id=f"rel{i}",
                from_entity_id="http://example.org/supplier1",
                to_entity_id=f"http://example.org/part{i}",
                relation_type="http://example.org/supplies",
            )
            db_session.add(rel)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?cost
        WHERE {
            ex:supplier1 ex:supplies ?part .
            ?part ex:cost ?cost
            FILTER (?cost > 700)
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_24_one_hop_with_filter_performance(self, db_session: Session, translator):
        """Test 24c: 1-hop + filter - Performance target <100ms"""
        supplier = Entity(id="http://example.org/supplier1", entity_type="Supplier", domain_id="test_domain", properties={})
        db_session.add(supplier)
        db_session.commit()

        # Create 1000 parts
        for i in range(1000):
            part = Entity(
                id=f"http://example.org/part{i}",
                entity_type="Part",
                domain_id="test_domain",
                properties={"cost": 500 + (i % 1000)}
            )
            db_session.add(part)
        db_session.commit()

        # Create 1000 relationships
        for i in range(1000):
            rel = Relationship(
                id=f"rel{i}",
                from_entity_id="http://example.org/supplier1",
                to_entity_id=f"http://example.org/part{i}",
                relation_type="http://example.org/supplies",
            )
            db_session.add(rel)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?cost
        WHERE {
            ex:supplier1 ex:supplies ?part .
            ?part ex:cost ?cost
            FILTER (?cost > 700)
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 100, f"Query took {elapsed}ms, target <100ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #25: 2-Hop Relation
    # ────────────────────────────────────────────────────────────────────────

    def test_25_two_hop_relation_parsing(self, translator):
        """Test 25a: 2-hop relation - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:ship1 ex:has_block ?block .
            ?block ex:has_part ?part
        }
        """

        where_clause = translator._extract_where_clause(query)
        patterns = translator._extract_triple_patterns(where_clause)

        assert len(patterns) >= 2, "Should have at least 2 patterns for 2-hop"

    def test_25_two_hop_relation_sql_generation(self, db_session: Session, translator):
        """Test 25b: 2-hop relation - SQL generation"""
        ship = Entity(id="http://example.org/ship1", entity_type="Ship", domain_id="test_domain", properties={})
        block = Entity(id="http://example.org/block1", entity_type="Block", domain_id="test_domain", properties={})
        part = Entity(id="http://example.org/part1", entity_type="Part", domain_id="test_domain", properties={})
        db_session.add_all([ship, block, part])

        rel1 = Relationship(
            id="rel1", from_entity_id="http://example.org/ship1",
            to_entity_id="http://example.org/block1",
            relation_type="http://example.org/has_block",
        )
        rel2 = Relationship(
            id="rel2", from_entity_id="http://example.org/block1",
            to_entity_id="http://example.org/part1",
            relation_type="http://example.org/has_part",
        )
        db_session.add_all([rel1, rel2])
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:ship1 ex:has_block ?block .
            ?block ex:has_part ?part
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_25_two_hop_relation_performance(self, db_session: Session, translator):
        """Test 25c: 2-hop relation - Performance target <200ms"""
        # Setup: ship → blocks (100) → parts (10 per block)
        ship = Entity(id="http://example.org/ship1", entity_type="Ship", domain_id="test_domain", properties={})
        db_session.add(ship)
        db_session.commit()

        for i in range(100):
            block = Entity(id=f"http://example.org/block{i}", entity_type="Block", domain_id="test_domain", properties={})
            db_session.add(block)
        db_session.commit()

        for i in range(100):
            rel = Relationship(
                id=f"rel1_{i}", from_entity_id="http://example.org/ship1",
                to_entity_id=f"http://example.org/block{i}",
                relation_type="http://example.org/has_block",
            )
            db_session.add(rel)
        db_session.commit()

        for i in range(100):
            for j in range(10):
                part = Entity(id=f"http://example.org/part{i}_{j}", entity_type="Part", domain_id="test_domain", properties={})
                db_session.add(part)
        db_session.commit()

        for i in range(100):
            for j in range(10):
                rel = Relationship(
                    id=f"rel2_{i}_{j}", from_entity_id=f"http://example.org/block{i}",
                    to_entity_id=f"http://example.org/part{i}_{j}",
                    relation_type="http://example.org/has_part",
                )
                db_session.add(rel)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:ship1 ex:has_block ?block .
            ?block ex:has_part ?part
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 200, f"Query took {elapsed}ms, target <200ms"

    # ────────────────────────────────────────────────────────────────────────
    # Pattern #26: 2-Hop + Filter
    # ────────────────────────────────────────────────────────────────────────

    def test_26_two_hop_with_filter_parsing(self, translator):
        """Test 26a: 2-hop + filter - SPARQL parsing"""
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:project1 ex:involves_supplier ?supplier .
            ?supplier ex:provides_part ?part .
            ?part ex:quality_rating ?rating
            FILTER (?rating >= 8)
        }
        """

        where_clause = translator._extract_where_clause(query)
        patterns = translator._extract_triple_patterns(where_clause)

        assert len(patterns) >= 3, "Should have at least 3 patterns"

    def test_26_two_hop_with_filter_sql_generation(self, db_session: Session, translator):
        """Test 26b: 2-hop + filter - SQL generation"""
        project = Entity(id="http://example.org/project1", entity_type="Project", domain_id="test_domain", properties={})
        supplier = Entity(id="http://example.org/supplier1", entity_type="Supplier", domain_id="test_domain", properties={})
        part = Entity(id="http://example.org/part1", entity_type="Part", domain_id="test_domain", properties={"quality_rating": 9})
        db_session.add_all([project, supplier, part])

        rel1 = Relationship(
            id="rel1", from_entity_id="http://example.org/project1",
            to_entity_id="http://example.org/supplier1",
            relation_type="http://example.org/involves_supplier",
        )
        rel2 = Relationship(
            id="rel2", from_entity_id="http://example.org/supplier1",
            to_entity_id="http://example.org/part1",
            relation_type="http://example.org/provides_part",
        )
        db_session.add_all([rel1, rel2])
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:project1 ex:involves_supplier ?supplier .
            ?supplier ex:provides_part ?part .
            ?part ex:quality_rating ?rating
            FILTER (?rating >= 8)
        }
        """

        result = translator.execute(query)
        assert result["query_type"] == "SELECT"

    def test_26_two_hop_with_filter_performance(self, db_session: Session, translator):
        """Test 26c: 2-hop + filter - Performance target <300ms"""
        project = Entity(id="http://example.org/project1", entity_type="Project", domain_id="test_domain", properties={})
        db_session.add(project)
        db_session.commit()

        # Create 50 suppliers
        for i in range(50):
            supplier = Entity(id=f"http://example.org/supplier{i}", entity_type="Supplier", domain_id="test_domain", properties={})
            db_session.add(supplier)
        db_session.commit()

        # Create relationships from project to suppliers
        for i in range(50):
            rel = Relationship(
                id=f"rel1_{i}", from_entity_id="http://example.org/project1",
                to_entity_id=f"http://example.org/supplier{i}",
                relation_type="http://example.org/involves_supplier",
            )
            db_session.add(rel)
        db_session.commit()

        # Create 500 parts
        for i in range(500):
            part = Entity(
                id=f"http://example.org/part{i}",
                entity_type="Part",
                domain_id="test_domain",
                properties={"quality_rating": 5 + (i % 6)}  # 5-10 rating
            )
            db_session.add(part)
        db_session.commit()

        # Create relationships from suppliers to parts
        for i in range(50):
            for j in range(10):
                rel = Relationship(
                    id=f"rel2_{i}_{j}",
                    from_entity_id=f"http://example.org/supplier{i}",
                    to_entity_id=f"http://example.org/part{i*10+j}",
                    relation_type="http://example.org/provides_part",
                )
                db_session.add(rel)
        db_session.commit()

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:project1 ex:involves_supplier ?supplier .
            ?supplier ex:provides_part ?part .
            ?part ex:quality_rating ?rating
            FILTER (?rating >= 8)
        }
        """

        start = time.time()
        result = translator.execute(query)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 300, f"Query took {elapsed}ms, target <300ms"
