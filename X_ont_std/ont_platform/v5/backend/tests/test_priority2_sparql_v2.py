"""Priority 2: Advanced SPARQL Engine with rdflib Tests"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from app.services.sparql_service_v2 import SPARQLServiceV2
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False
    SPARQLServiceV2 = None


@pytest.mark.skipif(not RDFLIB_AVAILABLE, reason="rdflib not installed")
class TestSPARQLServiceV2:
    """Test advanced SPARQL with rdflib"""

    @pytest.fixture
    def service(self):
        return SPARQLServiceV2()

    def test_service_creation(self, service):
        """Test service creation"""
        assert service.graph is not None
        assert service.get_triple_count() == 0

    def test_add_triple(self, service):
        """Test adding a triple"""
        service.add_triple(
            "http://example.org/subject1",
            "http://example.org/predicate1",
            "http://example.org/object1"
        )
        assert service.get_triple_count() == 1

    def test_add_multiple_triples(self, service):
        """Test adding multiple triples"""
        triples = [
            ("http://example.org/person1", "http://example.org/name", "http://example.org/Alice"),
            ("http://example.org/person1", "http://example.org/age", "http://example.org/30"),
            ("http://example.org/person2", "http://example.org/name", "http://example.org/Bob"),
        ]
        for s, p, o in triples:
            service.add_triple(s, p, o)

        assert service.get_triple_count() == 3

    def test_add_literal(self, service):
        """Test adding triples with literals"""
        service.add_triple_literal(
            "http://example.org/person1",
            "http://example.org/name",
            "Alice"
        )
        service.add_triple_literal(
            "http://example.org/person1",
            "http://example.org/age",
            "30",
            datatype="http://www.w3.org/2001/XMLSchema#integer"
        )

        assert service.get_triple_count() == 2

    def test_select_query_basic(self, service):
        """Test basic SELECT query"""
        service.add_triple_literal(
            "http://example.org/person1",
            "http://example.org/name",
            "Alice"
        )
        service.add_triple_literal(
            "http://example.org/person2",
            "http://example.org/name",
            "Bob"
        )

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?person ?name
        WHERE {
            ?person ex:name ?name
        }
        """

        result = service.query(query)
        assert result["type"] == "SELECT"
        assert len(result["results"]) == 2

    def test_ask_query(self, service):
        """Test ASK query (boolean result)"""
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/knows",
            "http://example.org/person2"
        )

        query = """
        PREFIX ex: <http://example.org/>
        ASK {
            ex:person1 ex:knows ex:person2
        }
        """

        result = service.query(query)
        assert result["type"] == "ASK"
        assert result["boolean"] is True

    def test_ask_query_false(self, service):
        """Test ASK query with negative result"""
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/knows",
            "http://example.org/person2"
        )

        query = """
        PREFIX ex: <http://example.org/>
        ASK {
            ex:person1 ex:knows ex:person3
        }
        """

        result = service.query(query)
        assert result["type"] == "ASK"
        assert result["boolean"] is False

    def test_construct_query(self, service):
        """Test CONSTRUCT query (builds new RDF)"""
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/name",
            "http://example.org/Alice"
        )
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/age",
            "http://example.org/30"
        )

        query = """
        PREFIX ex: <http://example.org/>
        CONSTRUCT {
            ?person ex:label ?name
        }
        WHERE {
            ?person ex:name ?name
        }
        """

        result = service.query(query)
        assert result["type"] == "CONSTRUCT"
        assert len(result["triples"]) > 0

    def test_describe_query(self, service):
        """Test DESCRIBE query (returns all info about resource)"""
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/name",
            "http://example.org/Alice"
        )
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/age",
            "http://example.org/30"
        )
        service.add_triple(
            "http://example.org/person1",
            "http://example.org/knows",
            "http://example.org/person2"
        )

        query = """
        PREFIX ex: <http://example.org/>
        DESCRIBE ex:person1
        """

        result = service.query(query)
        assert result["type"] == "DESCRIBE"
        assert len(result["triples"]) >= 3

    def test_query_with_filter(self, service):
        """Test SELECT with FILTER"""
        service.add_triple_literal(
            "http://example.org/person1",
            "http://example.org/name",
            "Alice"
        )
        service.add_triple_literal(
            "http://example.org/person1",
            "http://example.org/age",
            "30",
            datatype="http://www.w3.org/2001/XMLSchema#integer"
        )
        service.add_triple_literal(
            "http://example.org/person2",
            "http://example.org/name",
            "Bob"
        )
        service.add_triple_literal(
            "http://example.org/person2",
            "http://example.org/age",
            "25",
            datatype="http://www.w3.org/2001/XMLSchema#integer"
        )

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?person ?name
        WHERE {
            ?person ex:name ?name ;
                    ex:age ?age
            FILTER (?age > 25)
        }
        """

        result = service.query(query)
        assert result["type"] == "SELECT"
        # Should return at least person1 (age 30)
        assert len(result["results"]) >= 1

    def test_query_with_union(self, service):
        """Test SELECT with UNION"""
        service.add_triple_literal(
            "http://example.org/alice",
            "http://example.org/type",
            "Person"
        )
        service.add_triple_literal(
            "http://example.org/company",
            "http://example.org/type",
            "Organization"
        )

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?entity
        WHERE {
            { ?entity ex:type "Person" }
            UNION
            { ?entity ex:type "Organization" }
        }
        """

        result = service.query(query)
        assert result["type"] == "SELECT"
        assert len(result["results"]) >= 2

    def test_clear_graph(self, service):
        """Test clearing graph"""
        service.add_triple(
            "http://example.org/s1",
            "http://example.org/p1",
            "http://example.org/o1"
        )
        assert service.get_triple_count() == 1

        service.clear()
        assert service.get_triple_count() == 0

    def test_get_subjects(self, service):
        """Test getting unique subjects"""
        service.add_triple("http://example.org/s1", "http://example.org/p1", "http://example.org/o1")
        service.add_triple("http://example.org/s1", "http://example.org/p2", "http://example.org/o2")
        service.add_triple("http://example.org/s2", "http://example.org/p3", "http://example.org/o3")

        subjects = service.get_subjects()
        assert len(subjects) == 2

    def test_get_predicates(self, service):
        """Test getting unique predicates"""
        service.add_triple("http://example.org/s1", "http://example.org/p1", "http://example.org/o1")
        service.add_triple("http://example.org/s2", "http://example.org/p1", "http://example.org/o2")
        service.add_triple("http://example.org/s3", "http://example.org/p2", "http://example.org/o3")

        predicates = service.get_predicates()
        assert len(predicates) == 2

    def test_get_objects(self, service):
        """Test getting unique objects"""
        service.add_triple("http://example.org/s1", "http://example.org/p1", "http://example.org/o1")
        service.add_triple("http://example.org/s2", "http://example.org/p2", "http://example.org/o1")
        service.add_triple("http://example.org/s3", "http://example.org/p3", "http://example.org/o2")

        objects = service.get_objects()
        assert len(objects) == 2

    def test_invalid_query_error_handling(self, service):
        """Test error handling for invalid queries"""
        invalid_query = "INVALID SPARQL SYNTAX !!!"
        result = service.query(invalid_query)

        assert "error" in result

    def test_complex_ontology_scenario(self, service):
        """Test complex ontology with multiple entity types and relationships"""
        # Define persons
        service.add_triple_literal("http://example.org/alice", "http://example.org/type", "Person")
        service.add_triple_literal("http://example.org/alice", "http://example.org/name", "Alice")
        service.add_triple_literal("http://example.org/bob", "http://example.org/type", "Person")
        service.add_triple_literal("http://example.org/bob", "http://example.org/name", "Bob")

        # Define organization
        service.add_triple_literal("http://example.org/company", "http://example.org/type", "Organization")
        service.add_triple_literal("http://example.org/company", "http://example.org/name", "TechCorp")

        # Define relationships
        service.add_triple("http://example.org/alice", "http://example.org/works_at", "http://example.org/company")
        service.add_triple("http://example.org/bob", "http://example.org/works_at", "http://example.org/company")
        service.add_triple("http://example.org/alice", "http://example.org/knows", "http://example.org/bob")

        # Query all employees
        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?person ?name
        WHERE {
            ?person ex:type "Person" ;
                    ex:name ?name ;
                    ex:works_at ex:company
        }
        """

        result = service.query(query)
        assert len(result["results"]) == 2

    # ────────────────────────────────────────────────────────────────────────
    # Hot-path query patterns (Supported Profile: 18-30)
    # ────────────────────────────────────────────────────────────────────────

    def test_simple_lookup_by_id(self, service):
        """Test 18: Simple ID lookup (hot-path)"""
        service.add_triple_literal("http://example.org/ship1", "http://example.org/name", "USS Enterprise")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?name
        WHERE {
            ex:ship1 ex:name ?name
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 1
        assert result["results"][0]["name"]["value"] == "USS Enterprise"

    def test_entity_by_type_filter(self, service):
        """Test 19: Filter by entity type"""
        service.add_triple_literal("http://example.org/e1", "http://example.org/type", "Ship")
        service.add_triple_literal("http://example.org/e2", "http://example.org/type", "Block")
        service.add_triple_literal("http://example.org/e3", "http://example.org/type", "Ship")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?entity
        WHERE {
            ?entity ex:type "Ship"
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 2

    def test_property_filter_greater_than(self, service):
        """Test 20: Property filter with GT comparison"""
        service.add_triple_literal("http://example.org/p1", "http://example.org/length", "100")
        service.add_triple_literal("http://example.org/p2", "http://example.org/length", "200")
        service.add_triple_literal("http://example.org/p3", "http://example.org/length", "50")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?length
        WHERE {
            ?part ex:length ?length
            FILTER (?length > 75)
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 2

    def test_property_filter_equals(self, service):
        """Test 21: Property filter with EQUALS"""
        service.add_triple_literal("http://example.org/w1", "http://example.org/status", "Active")
        service.add_triple_literal("http://example.org/w2", "http://example.org/status", "Inactive")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?work
        WHERE {
            ?work ex:status "Active"
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 1

    def test_property_filter_like(self, service):
        """Test 22: Property filter with REGEX"""
        service.add_triple_literal("http://example.org/d1", "http://example.org/name", "Document_001")
        service.add_triple_literal("http://example.org/d2", "http://example.org/name", "Drawing_001")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?doc
        WHERE {
            ?doc ex:name ?name
            FILTER regex(?name, "Document")
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 1

    def test_one_hop_relation_simple(self, service):
        """Test 23: One-hop relation query"""
        service.add_triple("http://example.org/ship1", "http://example.org/has_block", "http://example.org/block1")
        service.add_triple("http://example.org/ship1", "http://example.org/has_block", "http://example.org/block2")
        service.add_triple("http://example.org/ship2", "http://example.org/has_block", "http://example.org/block3")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?block
        WHERE {
            ex:ship1 ex:has_block ?block
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 2

    def test_one_hop_with_filter(self, service):
        """Test 24: One-hop relation with filter"""
        service.add_triple("http://example.org/supplier1", "http://example.org/supplies", "http://example.org/part1")
        service.add_triple_literal("http://example.org/part1", "http://example.org/cost", "1000")
        service.add_triple("http://example.org/supplier1", "http://example.org/supplies", "http://example.org/part2")
        service.add_triple_literal("http://example.org/part2", "http://example.org/cost", "500")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part ?cost
        WHERE {
            ex:supplier1 ex:supplies ?part .
            ?part ex:cost ?cost
            FILTER (?cost > 700)
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 1

    def test_two_hop_relation(self, service):
        """Test 25: Two-hop relation query"""
        service.add_triple("http://example.org/ship1", "http://example.org/has_block", "http://example.org/block1")
        service.add_triple("http://example.org/block1", "http://example.org/has_part", "http://example.org/part1")
        service.add_triple("http://example.org/block1", "http://example.org/has_part", "http://example.org/part2")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?part
        WHERE {
            ex:ship1 ex:has_block ?block .
            ?block ex:has_part ?part
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 2

    def test_two_hop_with_filter(self, service):
        """Test 26: Two-hop with filter condition"""
        service.add_triple("http://example.org/project1", "http://example.org/involves_supplier", "http://example.org/supplier1")
        service.add_triple("http://example.org/supplier1", "http://example.org/provides_part", "http://example.org/part1")
        service.add_triple_literal("http://example.org/part1", "http://example.org/quality_rating", "9")
        service.add_triple("http://example.org/supplier1", "http://example.org/provides_part", "http://example.org/part2")
        service.add_triple_literal("http://example.org/part2", "http://example.org/quality_rating", "5")

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
        result = service.query(query)
        assert len(result["results"]) == 1

    def test_filter_with_and(self, service):
        """Test 27: Filter with AND condition"""
        service.add_triple_literal("http://example.org/task1", "http://example.org/priority", "High")
        service.add_triple_literal("http://example.org/task1", "http://example.org/status", "Open")
        service.add_triple_literal("http://example.org/task2", "http://example.org/priority", "High")
        service.add_triple_literal("http://example.org/task2", "http://example.org/status", "Closed")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?task
        WHERE {
            ?task ex:priority ?p ;
                  ex:status ?s
            FILTER (?p = "High" && ?s = "Open")
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 1

    def test_filter_with_or(self, service):
        """Test 28: Filter with OR condition"""
        service.add_triple_literal("http://example.org/item1", "http://example.org/type", "Critical")
        service.add_triple_literal("http://example.org/item2", "http://example.org/type", "Warning")
        service.add_triple_literal("http://example.org/item3", "http://example.org/type", "Info")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?item
        WHERE {
            ?item ex:type ?t
            FILTER (?t = "Critical" || ?t = "Warning")
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 2

    def test_limit_and_offset(self, service):
        """Test 29: LIMIT and OFFSET"""
        for i in range(1, 6):
            service.add_triple_literal(f"http://example.org/item{i}", "http://example.org/name", f"Item{i}")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT ?item ?name
        WHERE {
            ?item ex:name ?name
        }
        LIMIT 2
        OFFSET 1
        """
        result = service.query(query)
        assert len(result["results"]) == 2

    def test_distinct_results(self, service):
        """Test 30: DISTINCT keyword"""
        service.add_triple_literal("http://example.org/person1", "http://example.org/city", "New York")
        service.add_triple_literal("http://example.org/person2", "http://example.org/city", "New York")
        service.add_triple_literal("http://example.org/person3", "http://example.org/city", "Boston")

        query = """
        PREFIX ex: <http://example.org/>
        SELECT DISTINCT ?city
        WHERE {
            ?person ex:city ?city
        }
        """
        result = service.query(query)
        assert len(result["results"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
