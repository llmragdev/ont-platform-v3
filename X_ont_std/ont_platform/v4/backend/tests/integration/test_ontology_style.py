"""Tests for Phase 4 Week 1 - OntologyStyle and basic schema models."""
import sys
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from app.models.ontology_schema import (
    OntologyStyle,
    PropertyType,
    Cardinality,
    PropertyDefinition,
    SchemaConstraint,
    EntityType,
    RelationType,
    DomainSchema
)


class TestOntologyStyleEnum:
    """Test OntologyStyle enumeration."""

    def test_ontology_style_enum_exists(self):
        """Verify all 6 ontology styles are defined."""
        expected_styles = {
            "document",
            "rdf_triple",
            "property_graph",
            "semantic_web",
            "hierarchical",
            "multi_typed"
        }
        actual_styles = {style.value for style in OntologyStyle}
        assert expected_styles == actual_styles, f"Expected {expected_styles}, got {actual_styles}"

    def test_ontology_style_values(self):
        """Verify each style has correct value."""
        assert OntologyStyle.DOCUMENT.value == "document"
        assert OntologyStyle.RDF_TRIPLE.value == "rdf_triple"
        assert OntologyStyle.PROPERTY_GRAPH.value == "property_graph"
        assert OntologyStyle.SEMANTIC_WEB.value == "semantic_web"
        assert OntologyStyle.HIERARCHICAL.value == "hierarchical"
        assert OntologyStyle.MULTI_TYPED.value == "multi_typed"

    def test_ontology_style_string_conversion(self):
        """Verify style can be converted to string."""
        assert str(OntologyStyle.DOCUMENT) == "OntologyStyle.DOCUMENT"
        style_str = OntologyStyle.PROPERTY_GRAPH.value
        assert style_str == "property_graph"


class TestPropertyDefinition:
    """Test PropertyDefinition model."""

    def test_property_definition_basic(self):
        """Create a basic property definition."""
        prop = PropertyDefinition(
            name="project_name",
            display_name="Project Name",
            property_type=PropertyType.STRING,
            required=True
        )
        assert prop.name == "project_name"
        assert prop.display_name == "Project Name"
        assert prop.property_type == PropertyType.STRING
        assert prop.required is True

    def test_property_definition_validation(self):
        """Verify property definition handles all types."""
        types = [
            PropertyType.STRING,
            PropertyType.INTEGER,
            PropertyType.FLOAT,
            PropertyType.BOOLEAN,
            PropertyType.DATETIME,
            PropertyType.JSON,
            PropertyType.URI,
            PropertyType.LIST
        ]

        for prop_type in types:
            prop = PropertyDefinition(
                name="test_prop",
                display_name="Test Property",
                property_type=prop_type
            )
            assert prop.property_type == prop_type

    def test_property_definition_constraints(self):
        """Verify property with constraints."""
        constraints = [
            {"min_length": 1},
            {"max_length": 255},
            {"pattern": "^[A-Z]"}
        ]
        prop = PropertyDefinition(
            name="code",
            display_name="Code",
            property_type=PropertyType.STRING,
            constraints=constraints
        )
        assert len(prop.constraints) == 3
        assert prop.constraints[0]["min_length"] == 1

    def test_property_definition_with_default(self):
        """Verify property with default value."""
        prop = PropertyDefinition(
            name="status",
            display_name="Status",
            property_type=PropertyType.STRING,
            default_value="PENDING"
        )
        assert prop.default_value == "PENDING"


class TestEntityTypeDefinition:
    """Test EntityType model."""

    def test_entity_type_basic(self):
        """Create a basic entity type."""
        properties = {
            "name": PropertyDefinition(
                name="name",
                display_name="Name",
                property_type=PropertyType.STRING,
                required=True
            ),
            "budget": PropertyDefinition(
                name="budget",
                display_name="Budget",
                property_type=PropertyType.INTEGER
            )
        }
        entity = EntityType(
            name="PROJECT",
            display_name="Project",
            description="A research project",
            properties=properties
        )
        assert entity.name == "PROJECT"
        assert len(entity.properties) == 2
        assert "name" in entity.properties

    def test_entity_type_with_inheritance(self):
        """Verify entity type supports inheritance."""
        properties = {"title": PropertyDefinition(
            name="title",
            display_name="Title",
            property_type=PropertyType.STRING
        )}
        entity = EntityType(
            name="PERSON",
            display_name="Person",
            properties=properties,
            parent_types=["ENTITY"]
        )
        assert entity.parent_types == ["ENTITY"]

    def test_entity_type_metadata_fields(self):
        """Verify entity type includes metadata fields."""
        entity = EntityType(
            name="ORGANIZATION",
            display_name="Organization",
            properties={}
        )
        expected_metadata = ["created_by", "created_at", "updated_by", "updated_at", "version"]
        assert entity.metadata_fields == expected_metadata


class TestRelationTypeDefinition:
    """Test RelationType model."""

    def test_relation_type_basic(self):
        """Create a basic relation type."""
        rel = RelationType(
            name="leads",
            display_name="Leads",
            from_type="PERSON",
            to_type="PROJECT",
            cardinality=Cardinality.ONE_TO_MANY
        )
        assert rel.name == "leads"
        assert rel.from_type == "PERSON"
        assert rel.to_type == "PROJECT"
        assert rel.cardinality == Cardinality.ONE_TO_MANY

    def test_relation_type_cardinality(self):
        """Verify all cardinality types supported."""
        cardinalities = [
            Cardinality.ONE_TO_ONE,
            Cardinality.ONE_TO_MANY,
            Cardinality.MANY_TO_ONE,
            Cardinality.MANY_TO_MANY
        ]

        for card in cardinalities:
            rel = RelationType(
                name="test_rel",
                display_name="Test Relation",
                from_type="A",
                to_type="B",
                cardinality=card
            )
            assert rel.cardinality == card

    def test_relation_type_with_properties(self):
        """Verify relation type can have properties."""
        rel_prop = PropertyDefinition(
            name="start_date",
            display_name="Start Date",
            property_type=PropertyType.DATETIME
        )
        rel = RelationType(
            name="manages",
            display_name="Manages",
            from_type="MANAGER",
            to_type="TEAM",
            properties={"start_date": rel_prop}
        )
        assert len(rel.properties) == 1
        assert "start_date" in rel.properties


class TestDomainSchema:
    """Test DomainSchema model."""

    def test_domain_schema_basic(self):
        """Create a basic domain schema."""
        entity_types = {
            "PROJECT": EntityType(
                name="PROJECT",
                display_name="Project",
                properties={
                    "name": PropertyDefinition(
                        name="name",
                        display_name="Name",
                        property_type=PropertyType.STRING,
                        required=True
                    )
                }
            )
        }

        schema = DomainSchema(
            domain_id="ai-voucher-2025",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="AI Voucher System",
            entity_types=entity_types,
            relation_types={}
        )
        assert schema.domain_id == "ai-voucher-2025"
        assert schema.ontology_style == OntologyStyle.PROPERTY_GRAPH
        assert len(schema.entity_types) == 1

    def test_domain_schema_with_relations(self):
        """Verify domain schema with relationships."""
        entity_types = {
            "PERSON": EntityType(
                name="PERSON",
                display_name="Person",
                properties={}
            ),
            "PROJECT": EntityType(
                name="PROJECT",
                display_name="Project",
                properties={}
            )
        }

        relation_types = {
            "leads": RelationType(
                name="leads",
                display_name="Leads",
                from_type="PERSON",
                to_type="PROJECT",
                cardinality=Cardinality.ONE_TO_MANY
            )
        }

        schema = DomainSchema(
            domain_id="ai-voucher-2025",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="AI Voucher System",
            entity_types=entity_types,
            relation_types=relation_types
        )
        assert len(schema.entity_types) == 2
        assert len(schema.relation_types) == 1

    def test_domain_schema_style_specific(self):
        """Verify domain schema supports different styles."""
        styles = [
            (OntologyStyle.DOCUMENT, "ai-voucher-2025"),
            (OntologyStyle.RDF_TRIPLE, "knowledge-graph"),
            (OntologyStyle.PROPERTY_GRAPH, "manufacturing"),
            (OntologyStyle.SEMANTIC_WEB, "order-tracking"),
            (OntologyStyle.HIERARCHICAL, "org-structure")
        ]

        for style, domain in styles:
            schema = DomainSchema(
                domain_id=domain,
                ontology_style=style,
                display_name=f"Domain for {style.value}",
                entity_types={"TEST": EntityType(
                    name="TEST",
                    display_name="Test",
                    properties={}
                )},
                relation_types={}
            )
            assert schema.ontology_style == style

    def test_domain_schema_version(self):
        """Verify domain schema versioning."""
        schema = DomainSchema(
            domain_id="test-domain",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="Test",
            entity_types={"TEST": EntityType(
                name="TEST",
                display_name="Test",
                properties={}
            )},
            relation_types={},
            version="1.0.0"
        )
        assert schema.version == "1.0.0"
        assert isinstance(schema.created_at, datetime)

    def test_domain_schema_metadata(self):
        """Verify domain schema tracks metadata."""
        schema = DomainSchema(
            domain_id="test-domain",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="Test Domain",
            entity_types={"TEST": EntityType(
                name="TEST",
                display_name="Test",
                properties={}
            )},
            relation_types={},
            created_by="test_user"
        )
        assert schema.created_by == "test_user"
        assert schema.created_at is not None

    def test_domain_schema_with_constraints(self):
        """Verify domain schema with constraints."""
        constraint = SchemaConstraint(
            constraint_type="unique",
            description="Unique project name per domain",
            condition={"field": "name"}
        )
        schema = DomainSchema(
            domain_id="test",
            ontology_style=OntologyStyle.DOCUMENT,
            display_name="Test",
            entity_types={"TEST": EntityType(
                name="TEST",
                display_name="Test",
                properties={}
            )},
            relation_types={},
            constraints=[constraint]
        )
        assert len(schema.constraints) == 1
        assert schema.constraints[0].constraint_type == "unique"


# Integration test for the full Week 1 Task 1-1
class TestPhase4Week1Task1_1Integration:
    """Integration test for Phase 4 Week 1 Task 1-1: OntologyStyle + PropertyDefinition."""

    def test_complete_ontology_style_setup(self):
        """Test complete setup of ontology with all components."""
        # Define entity types for ai-voucher-2025 (property_graph style)
        project_entity = EntityType(
            name="PROJECT",
            display_name="Project",
            description="Research project",
            properties={
                "name": PropertyDefinition(
                    name="name",
                    display_name="Name",
                    property_type=PropertyType.STRING,
                    required=True,
                    indexed=True
                ),
                "budget": PropertyDefinition(
                    name="budget",
                    display_name="Budget",
                    property_type=PropertyType.INTEGER,
                    required=False
                ),
                "deadline": PropertyDefinition(
                    name="deadline",
                    display_name="Deadline",
                    property_type=PropertyType.DATETIME
                ),
                "metadata": PropertyDefinition(
                    name="metadata",
                    display_name="Metadata",
                    property_type=PropertyType.JSON
                )
            }
        )

        person_entity = EntityType(
            name="PERSON",
            display_name="Person",
            properties={
                "email": PropertyDefinition(
                    name="email",
                    display_name="Email",
                    property_type=PropertyType.STRING,
                    required=True,
                    unique=True
                )
            }
        )

        # Define relationships
        leads_relation = RelationType(
            name="leads",
            display_name="Leads",
            from_type="PERSON",
            to_type="PROJECT",
            cardinality=Cardinality.ONE_TO_MANY,
            properties={
                "start_date": PropertyDefinition(
                    name="start_date",
                    display_name="Start Date",
                    property_type=PropertyType.DATETIME
                )
            }
        )

        # Create domain schema
        schema = DomainSchema(
            domain_id="ai-voucher-2025",
            ontology_style=OntologyStyle.PROPERTY_GRAPH,
            display_name="AI Voucher 2025",
            description="AI voucher project management system",
            entity_types={
                "PROJECT": project_entity,
                "PERSON": person_entity
            },
            relation_types={
                "leads": leads_relation
            }
        )

        # Verify complete setup
        assert schema.domain_id == "ai-voucher-2025"
        assert schema.ontology_style == OntologyStyle.PROPERTY_GRAPH
        assert len(schema.entity_types) == 2
        assert len(schema.relation_types) == 1
        assert schema.entity_types["PROJECT"].properties["name"].indexed is True
        assert schema.relation_types["leads"].cardinality == Cardinality.ONE_TO_MANY
        assert "start_date" in schema.relation_types["leads"].properties
